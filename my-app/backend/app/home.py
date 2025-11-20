from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import pymysql
import time
import csv
import io
from datetime import datetime, timedelta
from urllib.parse import quote
from .config import DB_CONFIG

router = APIRouter()


def get_db_connection():
    """获取数据库连接，最多重试10次，每次间隔1秒"""
    last_error: Exception
    for attempt in range(10):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            last_error = e
            if attempt < 9:
                time.sleep(1)
    # 所有重试均失败，抛出HTTP异常
    raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(last_error)}")


@router.get("/overview")
async def get_overview(
    day: int = Query(1, description="查询天数: 1, 7, 15, 30"),
    last_query_time: str = Query(None, description="上次查询时间，用于增量更新"),
    isfake: int = Query(0, description="是否开启虚拟数据填充: 0-否, 1-是"),
):
    """
    获取15个设备的电压概览数据

    参数:
    - day: 查询天数，默认为1天，可选值：1, 7, 15, 30
    - last_query_time: 上次查询时间，如果提供则只返回新增数据
    - isfake: 是否开启虚拟数据填充，默认为0

    返回:
    {
        "query_time": "YYYY-MM-DD HH:mm:ss",
        "devices": [
            {
                "machine_name": "1#",
                "voltage_data": [
                    {"date": "YYYY-MM-DD", "time": "HH:mm:ss", "avg_voltage": 220.5},
                    ...
                ]
            },
            ...
        ],
        "is_incremental": true/false
    }
    """
    if day not in [1, 7, 15, 30]:
        raise HTTPException(status_code=400, detail="day参数只能是1, 7, 15 或 30")

    connection = None
    try:
        # 获取当前时间作为查询时间点
        query_time = datetime.now()
        query_time_str = query_time.strftime("%Y-%m-%d %H:%M:%S")

        # 判断是否为增量查询
        is_incremental = last_query_time is not None

        # 计算开始时间
        if is_incremental:
            # 增量查询：从上次查询时间开始
            try:
                start_time = datetime.strptime(last_query_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="last_query_time格式错误，应为: YYYY-MM-DD HH:MM:SS",
                )
        else:
            # 全量查询：往前推day天
            start_time = query_time - timedelta(days=day)

        start_date = start_time.strftime("%Y-%m-%d")

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        devices_data = []

        # 构建完整的时间戳范围
        start_datetime = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_datetime = query_time.strftime("%Y-%m-%d %H:%M:%S")

        # 准备机器名称列表
        target_machines = [f"{i}#" for i in range(1, 16)]

        # 构建占位符
        placeholders = ",".join(["%s"] * len(target_machines))

        # 优化后的SQL查询：一次查询所有设备的数据
        sql = f"""
            SELECT machine_name, machine_model, date, time, avg_voltage
            FROM wincc
            WHERE machine_name IN ({placeholders})
              AND CONCAT(date, ' ', time) >= %s
              AND CONCAT(date, ' ', time) <= %s
            ORDER BY date ASC, time ASC
        """

        # 执行查询
        params = target_machines + [start_datetime, end_datetime]
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # 数据分组处理
        devices_map = {name: [] for name in target_machines}
        models_map = {name: "" for name in target_machines}

        for row in rows:
            m_name = row["machine_name"]

            # 更新机器型号（由于是按时间升序排列，最后一次更新的就是最新的型号）
            if row["machine_model"]:
                models_map[m_name] = row["machine_model"]

            if m_name in devices_map and row["avg_voltage"] is not None:
                devices_map[m_name].append(
                    {
                        "date": (
                            row["date"].strftime("%Y-%m-%d")
                            if hasattr(row["date"], "strftime")
                            else str(row["date"])
                        ),
                        "time": (
                            row["time"].strftime("%H:%M:%S")
                            if hasattr(row["time"], "strftime")
                            else str(row["time"])
                        ),
                        "avg_voltage": float(row["avg_voltage"]),
                    }
                )

        # 处理虚拟数据填充
        if isfake == 1:
            for m_name in target_machines:
                data_list = devices_map[m_name]
                if not data_list:
                    continue

                # 获取最后一条数据的时间
                last_item = data_list[-1]
                try:
                    last_dt_str = f"{last_item['date']} {last_item['time']}"
                    last_dt = datetime.strptime(last_dt_str, "%Y-%m-%d %H:%M:%S")

                    # 检查与查询时间的差值
                    diff = query_time - last_dt

                    # 如果差值 >= 15分钟
                    if diff >= timedelta(minutes=15):
                        # 从最大时间之后 每隔10分钟添加一个虚拟数据
                        next_dt = last_dt + timedelta(minutes=10)
                        while next_dt <= query_time:
                            data_list.append(
                                {
                                    "date": next_dt.strftime("%Y-%m-%d"),
                                    "time": next_dt.strftime("%H:%M:%S"),
                                    "avg_voltage": 0.0,
                                }
                            )
                            next_dt += timedelta(minutes=10)

                except (ValueError, TypeError):
                    continue

        # 转换为列表格式
        for machine_name in target_machines:
            devices_data.append(
                {
                    "machine_name": machine_name,
                    "machine_model": models_map[machine_name],
                    "voltage_data": devices_map[machine_name],
                }
            )

        cursor.close()

        return {
            "query_time": query_time_str,
            "devices": devices_data,
            "is_incremental": is_incremental,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询电压数据失败: {str(e)}")
    finally:
        if connection:
            connection.close()


@router.get("/export")
async def export_data(
    start_datetime: str = Query(..., description="起始时间 格式: YYYY-MM-DD HH:MM:SS"),
    end_datetime: str = Query(..., description="截止时间 格式: YYYY-MM-DD HH:MM:SS"),
):
    """
    导出指定时间范围内的所有设备数据为CSV文件

    参数:
    - start_datetime: 起始时间
    - end_datetime: 截止时间

    返回: CSV文件流
    """
    connection = None
    try:
        # 验证时间格式
        try:
            start_dt = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="时间格式错误，应为: YYYY-MM-DD HH:MM:SS"
            )

        # 验证时间范围
        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="起始时间必须早于截止时间")

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 查询所有设备在指定时间范围内的所有字段数据，按device, date, time升序
        sql = """
            SELECT machine_name, machine_model, date, time, hours, 
                   total_current, total_voltage,
                   cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10,
                   cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20,
                   max_voltage, min_voltage, avg_voltage, voltage_range, std_deviation,
                   pump_pressure, pump_opening, fan_opening,
                   specific_gravity, liquid_level,
                   inlet_pressure, oxygen_outlet_pressure, hydrogen_outlet_pressure, 
                   pressure_diff, sep_pressure_diff,
                   alkali_inlet_temp, oxygen_outlet_temp, hydrogen_outlet_temp, hydrogen_gas_temp,
                   hydrogen_flow_meter, oxygen_in_hydrogen, hydrogen_in_oxygen,
                   current_power
            FROM wincc
            WHERE CONCAT(date, ' ', time) >= %s
              AND CONCAT(date, ' ', time) <= %s
            ORDER BY machine_name ASC, date ASC, time ASC
        """

        cursor.execute(sql, (start_datetime, end_datetime))
        rows = cursor.fetchall()

        cursor.close()

        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头（带BOM用于Excel正确识别UTF-8）
        headers = [
            "机器名",
            "机器型号",
            "日期",
            "时间",
            "运行小时数/h",
            "总电流/A",
            "总电压/V",
            "cell-1/mV",
            "cell-2/mV",
            "cell-3/mV",
            "cell-4/mV",
            "cell-5/mV",
            "cell-6/mV",
            "cell-7/mV",
            "cell-8/mV",
            "cell-9/mV",
            "cell-10/mV",
            "cell-11/mV",
            "cell-12/mV",
            "cell-13/mV",
            "cell-14/mV",
            "cell-15/mV",
            "cell-16/mV",
            "cell-17/mV",
            "cell-18/mV",
            "cell-19/mV",
            "cell-20/mV",
            "电压最大值/mV",
            "电压最小值/mV",
            "平均电压/mV",
            "电压极差/mV",
            "小室电压标准差/mV",
            "泵后压力/MPa",
            "泵的开度/Hz",
            "风扇开度/Hz",
            "碱液比重/mg/cm³",
            "液位/mm",
            "进槽压力/MPa",
            "氧侧出槽压力/MPa",
            "氢侧出槽压力/MPa",
            "电解槽进出口压差/MPa",
            "氢氧侧压差/MPa",
            "碱液入口温度/℃",
            "氧侧出槽温度/℃",
            "氢气出槽温度/℃",
            "氢侧出气温度/℃",
            "氢气流量",
            "氧中氢/ppm",
            "氢中氧/ppm",
            "当前能耗（直流电耗）",
        ]
        writer.writerow(headers)

        # 写入数据
        for row in rows:
            date_str = (
                row["date"].strftime("%Y-%m-%d")
                if hasattr(row["date"], "strftime")
                else str(row["date"])
            )
            time_str = (
                row["time"].strftime("%H:%M:%S")
                if hasattr(row["time"], "strftime")
                else str(row["time"])
            )

            # 格式化数值，如果为None则显示空字符串
            def format_value(value, decimals=2):
                if value is None:
                    return ""
                try:
                    return f"{float(value):.{decimals}f}"
                except (ValueError, TypeError):
                    return str(value) if value else ""

            writer.writerow(
                [
                    row["machine_name"] or "",
                    row["machine_model"] or "",
                    date_str,
                    time_str,
                    format_value(row["hours"], 0),
                    format_value(row["total_current"], 1),
                    format_value(row["total_voltage"], 1),
                    format_value(row["cell_1"], 0),
                    format_value(row["cell_2"], 0),
                    format_value(row["cell_3"], 0),
                    format_value(row["cell_4"], 0),
                    format_value(row["cell_5"], 0),
                    format_value(row["cell_6"], 0),
                    format_value(row["cell_7"], 0),
                    format_value(row["cell_8"], 0),
                    format_value(row["cell_9"], 0),
                    format_value(row["cell_10"], 0),
                    format_value(row["cell_11"], 0),
                    format_value(row["cell_12"], 0),
                    format_value(row["cell_13"], 0),
                    format_value(row["cell_14"], 0),
                    format_value(row["cell_15"], 0),
                    format_value(row["cell_16"], 0),
                    format_value(row["cell_17"], 0),
                    format_value(row["cell_18"], 0),
                    format_value(row["cell_19"], 0),
                    format_value(row["cell_20"], 0),
                    format_value(row["max_voltage"], 0),
                    format_value(row["min_voltage"], 0),
                    format_value(row["avg_voltage"], 1),
                    format_value(row["voltage_range"], 0),
                    format_value(row["std_deviation"], 4),
                    format_value(row["pump_pressure"], 4),
                    format_value(row["pump_opening"], 2),
                    format_value(row["fan_opening"], 2),
                    format_value(row["specific_gravity"], 4),
                    format_value(row["liquid_level"], 2),
                    format_value(row["inlet_pressure"], 4),
                    format_value(row["oxygen_outlet_pressure"], 4),
                    format_value(row["hydrogen_outlet_pressure"], 4),
                    format_value(row["pressure_diff"], 4),
                    format_value(row["sep_pressure_diff"], 4),
                    format_value(row["alkali_inlet_temp"], 2),
                    format_value(row["oxygen_outlet_temp"], 2),
                    format_value(row["hydrogen_outlet_temp"], 2),
                    format_value(row["hydrogen_gas_temp"], 2),
                    format_value(row["hydrogen_flow_meter"], 4),
                    format_value(row["oxygen_in_hydrogen"], 0),
                    format_value(row["hydrogen_in_oxygen"], 0),
                    format_value(row["current_power"], 4),
                ]
            )

        # 生成文件名
        start_str = start_dt.strftime("%Y%m%d%H%M%S")
        end_str = end_dt.strftime("%Y%m%d%H%M%S")
        filename = f"设备数据_{start_str}_{end_str}.csv"

        # URL编码文件名以支持中文字符
        encoded_filename = quote(filename)

        # 返回CSV文件（添加BOM以支持Excel正确显示中文）
        csv_content = "\ufeff" + output.getvalue()
        output.close()

        return StreamingResponse(
            iter([csv_content.encode("utf-8")]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")
    finally:
        if connection:
            connection.close()
