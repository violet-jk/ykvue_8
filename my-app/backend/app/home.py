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
async def get_overview(day: int = Query(1, description="查询天数: 1 或 7")):
    """
    获取15个设备的电压概览数据

    参数:
    - day: 查询天数，默认为1天，可选值：1 或 7

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
        ]
    }
    """
    if day not in [1, 7]:
        raise HTTPException(status_code=400, detail="day参数只能是1或7")

    connection = None
    try:
        # 获取当前时间作为查询时间点
        query_time = datetime.now()
        query_time_str = query_time.strftime("%Y-%m-%d %H:%M:%S")

        # 计算开始时间（往前推day天）
        start_time = query_time - timedelta(days=day)
        start_date = start_time.strftime("%Y-%m-%d")

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        devices_data = []

        # 查询15个设备的数据
        for machine_id in range(1, 16):
            machine_name = f"{machine_id}#"

            # SQL查询：从test表获取指定设备在指定时间范围内的电压数据
            # 将date和time组合成完整的时间戳进行查询
            sql = """
                SELECT date, time, avg_voltage
                FROM test
                WHERE machine_name = %s 
                  AND CONCAT(date, ' ', time) >= %s
                  AND CONCAT(date, ' ', time) <= %s
                ORDER BY date ASC, time ASC
            """

            # 构建完整的时间戳范围
            start_datetime = start_time.strftime("%Y-%m-%d %H:%M:%S")
            end_datetime = query_time.strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(sql, (machine_name, start_datetime, end_datetime))
            rows = cursor.fetchall()

            device_info = {
                "machine_name": machine_name,
                "voltage_data": [
                    {
                        "date": row['date'].strftime("%Y-%m-%d") if hasattr(row['date'], 'strftime') else str(row['date']),
                        "time": row['time'].strftime("%H:%M:%S") if hasattr(row['time'], 'strftime') else str(row['time']),
                        "avg_voltage": float(row['avg_voltage'])
                    }
                    for row in rows
                ]
            }
            devices_data.append(device_info)

        cursor.close()

        return {
            "query_time": query_time_str,
            "devices": devices_data
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
    end_datetime: str = Query(..., description="截止时间 格式: YYYY-MM-DD HH:MM:SS")
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
            raise HTTPException(status_code=400, detail="时间格式错误，应为: YYYY-MM-DD HH:MM:SS")

        # 验证时间范围
        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="起始时间必须早于截止时间")

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 查询所有设备在指定时间范围内的所有字段数据，按device, date, time升序
        sql = """
            SELECT machine_name, machine_model, date, time, hours, total_current,
                   cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10,
                   cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20,
                   max_voltage, min_voltage, avg_voltage, voltage_range,
                   pump_pressure, pump_opening, fan_opening, specific_gravity,
                   inlet_pressure, liquid_level, is_alkali_refill,
                   oxygen_outlet_pressure, hydrogen_outlet_pressure,
                   oxygen_outlet_temp, hydrogen_outlet_temp, hydrogen_gas_temp,
                   hydrogen_flow_meter, water_collection, cumulative_drainage,
                   oxygen_in_hydrogen, hydrogen_in_oxygen
            FROM test
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
            '机器名', '机器型号', '日期', '时间', '小时数', '总电流/A',
            'cell-1', 'cell-2', 'cell-3', 'cell-4', 'cell-5', 'cell-6', 'cell-7', 'cell-8', 'cell-9', 'cell-10',
            'cell-11', 'cell-12', 'cell-13', 'cell-14', 'cell-15', 'cell-16', 'cell-17', 'cell-18', 'cell-19', 'cell-20',
            '电压最大值/mV', '电压最小值/mV', '平均电压/mV', '极差/mV',
            '泵后压力/Mpa', '泵的开度/Hz', '风扇开度', '比重 mg/cm3',
            '进槽压力/Mpa', '液位/mm', '是否补碱',
            '氧侧出槽压力/Mpa', '氢侧出槽压力/Mpa',
            '氧侧出槽温度/℃', '氢气出槽温度/℃', '氢侧出气温度 /℃',
            '氢气流量计', '集水量/mm', '累计排水量mL',
            '氧中氢/ppm', '氢中氧/ppm'
        ]
        writer.writerow(headers)

        # 写入数据
        for row in rows:
            date_str = row['date'].strftime("%Y-%m-%d") if hasattr(row['date'], 'strftime') else str(row['date'])
            time_str = row['time'].strftime("%H:%M:%S") if hasattr(row['time'], 'strftime') else str(row['time'])

            # 格式化数值，如果为None则显示空字符串
            def format_value(value, decimals=2):
                if value is None:
                    return ''
                try:
                    return f"{float(value):.{decimals}f}"
                except (ValueError, TypeError):
                    return str(value) if value else ''

            writer.writerow([
                row['machine_name'] or '',
                row['machine_model'] or '',
                date_str,
                time_str,
                format_value(row['hours'], 1),
                format_value(row['total_current'], 2),
                format_value(row['cell_1'], 2),
                format_value(row['cell_2'], 2),
                format_value(row['cell_3'], 2),
                format_value(row['cell_4'], 2),
                format_value(row['cell_5'], 2),
                format_value(row['cell_6'], 2),
                format_value(row['cell_7'], 2),
                format_value(row['cell_8'], 2),
                format_value(row['cell_9'], 2),
                format_value(row['cell_10'], 2),
                format_value(row['cell_11'], 2),
                format_value(row['cell_12'], 2),
                format_value(row['cell_13'], 2),
                format_value(row['cell_14'], 2),
                format_value(row['cell_15'], 2),
                format_value(row['cell_16'], 2),
                format_value(row['cell_17'], 2),
                format_value(row['cell_18'], 2),
                format_value(row['cell_19'], 2),
                format_value(row['cell_20'], 2),
                format_value(row['max_voltage'], 2),
                format_value(row['min_voltage'], 2),
                format_value(row['avg_voltage'], 2),
                format_value(row['voltage_range'], 2),
                format_value(row['pump_pressure'], 2),
                format_value(row['pump_opening'], 2),
                format_value(row['fan_opening'], 2),
                format_value(row['specific_gravity'], 2),
                format_value(row['inlet_pressure'], 2),
                format_value(row['liquid_level'], 2),
                row['is_alkali_refill'] or '',
                format_value(row['oxygen_outlet_pressure'], 2),
                format_value(row['hydrogen_outlet_pressure'], 2),
                format_value(row['oxygen_outlet_temp'], 2),
                format_value(row['hydrogen_outlet_temp'], 2),
                format_value(row['hydrogen_gas_temp'], 2),
                format_value(row['hydrogen_flow_meter'], 2),
                format_value(row['water_collection'], 2),
                format_value(row['cumulative_drainage'], 2),
                format_value(row['oxygen_in_hydrogen'], 2),
                format_value(row['hydrogen_in_oxygen'], 2)
            ])

        # 生成文件名
        start_str = start_dt.strftime("%Y%m%d%H%M%S")
        end_str = end_dt.strftime("%Y%m%d%H%M%S")
        filename = f"设备数据_{start_str}_{end_str}.csv"

        # URL编码文件名以支持中文字符
        encoded_filename = quote(filename)

        # 返回CSV文件（添加BOM以支持Excel正确显示中文）
        csv_content = '\ufeff' + output.getvalue()
        output.close()

        return StreamingResponse(
            iter([csv_content.encode('utf-8')]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")
    finally:
        if connection:
            connection.close()
