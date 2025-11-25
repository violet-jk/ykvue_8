import asyncio
import csv
import io
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import quote
from itertools import groupby
import pandas as pd
import pymysql
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

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
              SELECT machine_name,
                     machine_model, date, time, hours, total_current, total_voltage, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10, cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20, max_voltage, min_voltage, avg_voltage, voltage_range, std_deviation, pump_pressure, pump_opening, fan_opening, specific_gravity, liquid_level, inlet_pressure, oxygen_outlet_pressure, hydrogen_outlet_pressure, pressure_diff, sep_pressure_diff, alkali_inlet_temp, oxygen_outlet_temp, hydrogen_outlet_temp, hydrogen_gas_temp, hydrogen_flow_meter, oxygen_in_hydrogen, hydrogen_in_oxygen, current_power, alkali_flow_meter
              FROM wincc
              WHERE CONCAT(date
                  , ' '
                  , time) >= %s
                AND CONCAT(date
                  , ' '
                  , time) <= %s
              ORDER BY machine_name ASC, date ASC, time ASC \
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
            "碱液流量L/min",
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
                    format_value(row["alkali_flow_meter"], 4)
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


def process_single_machine_timeline(machine_name: str, machine_model: str, db_config: dict):
    """
    处理单个机器的时间轴数据（用于多进程执行）

    Args:
        machine_name: 机器名称
        machine_model: 机器型号
        db_config: 数据库配置

    Returns:
        Dict: 包含机器时间轴数据的字典
    """
    connection = None
    try:
        # 建立数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 查询机器数据
        sql = """
              SELECT machine_name,
                     machine_model, date, time, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10, cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20
              FROM wincc
              WHERE machine_name = %s
                AND machine_model = %s
              ORDER BY date ASC, time ASC \
              """
        cursor.execute(sql, (machine_name, machine_model))
        machine_rows = cursor.fetchall()
        cursor.close()

        if not machine_rows:
            return {
                "machine_model": machine_model,
                "machine_name": machine_name,
                "time": [],
            }

        # 使用 pandas 处理数据
        df = pd.DataFrame(machine_rows)

        # 组合 date 和 time 成 datetime
        df["date"] = pd.to_datetime(df["date"])

        # 处理 time 字段
        if pd.api.types.is_timedelta64_dtype(df["time"]) or isinstance(
                df["time"].iloc[0], pd.Timedelta
        ):
            df["datetime"] = df["date"] + df["time"]
        else:
            df["datetime"] = pd.to_datetime(
                df["date"].astype(str) + " " + df["time"].astype(str)
            )

        # ===== 步骤1: 处理cell数据，计算每个cell的zero_ratio，排除>0.8的cell =====
        valid_cells = []
        for i in range(1, 21):  # cell_1 到 cell_20
            cell_field = f"cell_{i}"

            if cell_field not in df.columns:
                continue

            # 创建副本避免警告
            cell_df = df[["datetime", cell_field]].copy()
            cell_df.columns = ["datetime", "value"]

            # 转换为数值类型
            cell_df["value"] = pd.to_numeric(
                cell_df["value"], errors="coerce"
            )

            # 找到第一个非0且>1680的值的索引
            mask = (cell_df["value"] > 0) & (cell_df["value"] > 1680)
            valid_indices = cell_df[mask].index

            if len(valid_indices) == 0:
                continue

            # 从第一个>1680的值开始计算
            start_idx = valid_indices[0]
            cell_df = cell_df.loc[start_idx:].copy()

            # 计算临时时间差用于分组
            temp_start_time = cell_df.iloc[0]["datetime"]
            cell_df["time_diff"] = (
                    (cell_df["datetime"] - temp_start_time).dt.total_seconds()
                    / 3600
            ).astype(int)

            # 分组计算 y=0 比例
            grouped_temp = (
                cell_df.groupby("time_diff")
                .agg({"value": "mean"})
                .reset_index()
            )
            grouped_temp.columns = ["x", "y"]
            grouped_temp["y"] = grouped_temp["y"].round(2)

            zero_ratio = (
                (grouped_temp["y"] == 0).sum() / len(grouped_temp)
                if len(grouped_temp) > 0
                else 0
            )

            # 只保留zero_ratio <= 0.8的cell
            if zero_ratio <= 0.8:
                valid_cells.append(cell_field)

        # 如果没有有效的cell，返回空数据
        if len(valid_cells) == 0:
            return {
                "machine_model": machine_model,
                "machine_name": machine_name,
                "time": [],
            }

        # ===== 步骤2: 获取剩余cell的起始时间点，为所有cell均>1680的最小时间点 =====
        start_time_candidates = []
        for cell_field in valid_cells:
            cell_df = df[["datetime", cell_field]].copy()
            cell_df.columns = ["datetime", "value"]
            cell_df["value"] = pd.to_numeric(
                cell_df["value"], errors="coerce"
            )

            # 找到第一个非0且>1680的值
            mask = (cell_df["value"] > 0) & (cell_df["value"] > 1680)
            valid_indices = cell_df[mask].index

            if len(valid_indices) > 0:
                start_time = cell_df.loc[valid_indices[0], "datetime"]
                start_time_candidates.append(start_time)

        # 使用最晚的起始时间，确保所有cell在这个时间点都>1680
        global_start_time = max(start_time_candidates)

        # ===== 步骤3: 基于global_start_time过滤数据，并获取实际的时间点列表 =====
        cell_df_filtered = df[["datetime"] + valid_cells].copy()

        # 转换所有cell列为数值类型
        for cell_field in valid_cells:
            cell_df_filtered[cell_field] = pd.to_numeric(
                cell_df_filtered[cell_field], errors="coerce"
            )

        # 使用全局起始时间筛选数据
        cell_df_filtered = cell_df_filtered[
            cell_df_filtered["datetime"] >= global_start_time
            ].copy()

        # 过滤掉任意cell < 1680 的行，确保所有cell都>=1680
        mask = pd.Series(
            [True] * len(cell_df_filtered), index=cell_df_filtered.index
        )
        for cell_field in valid_cells:
            mask &= cell_df_filtered[cell_field] >= 1680

        cell_df_filtered = cell_df_filtered[mask].copy()

        if cell_df_filtered.empty:
            return {
                "machine_model": machine_model,
                "machine_name": machine_name,
                "time": [],
            }

        # 获取过滤后的有效时间点列表
        valid_datetimes = cell_df_filtered["datetime"].unique()
        valid_datetimes = (
            pd.Series(valid_datetimes).sort_values().reset_index(drop=True)
        )

        # 转换为字符串格式
        valid_times = [
            dt.strftime("%Y-%m-%d %H:%M:%S") for dt in valid_datetimes
        ]

        return {
            "machine_model": machine_model,
            "machine_name": machine_name,
            "start_time": global_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "time": valid_times,
        }

    except Exception as e:
        print(f"处理机器 {machine_name} 时出错: {e}")
        return {
            "machine_model": machine_model,
            "machine_name": machine_name,
            "time": [],
        }
    finally:
        if connection:
            connection.close()


def get_machine_timeline():
    """
    获取所有设备的时间轴（使用多进程并行处理）

    Returns:
        List[Dict]: 返回格式为 [{"machine_model": "A", "machine_name": "B", "time": [...]}, ...]
    """
    connection = None
    try:
        # 准备机器名称列表
        machine_names = [f"{i}#" for i in range(1, 16)]
        # 建立MySQL连接
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 步骤1: 一次性查询所有machine_name的最新machine_model
        placeholders = ",".join(["%s"] * len(machine_names))
        sql = f"""
            SELECT t1.machine_name, t1.machine_model
            FROM wincc t1
            INNER JOIN (
                SELECT machine_name, MAX(CONCAT(date, ' ', time)) as max_datetime
                FROM wincc
                WHERE machine_name IN ({placeholders})
                GROUP BY machine_name
            ) t2 ON t1.machine_name = t2.machine_name 
                AND CONCAT(t1.date, ' ', t1.time) = t2.max_datetime
        """
        cursor.execute(sql, tuple(machine_names))
        latest_records = cursor.fetchall()
        cursor.close()
        connection.close()
        connection = None

        # 构建machine_name到machine_model的映射
        machine_model_map = {
            row["machine_name"]: row["machine_model"] for row in latest_records
        }

        # 筛选出有效的machine_name(有machine_model)
        valid_machines = []
        result = []

        for machine_name in machine_names:
            machine_model = machine_model_map.get(machine_name)

            # 如果没有数据或machine_model为空,添加空结果
            if not machine_model:
                result.append(
                    {
                        "machine_model": machine_model,
                        "machine_name": machine_name,
                        "time": [],
                    }
                )
            else:
                valid_machines.append((machine_name, machine_model))

        # 步骤2: 使用进程池并行处理有效的机器
        if valid_machines:
            # 使用进程池并行处理（最多5个进程）
            with ProcessPoolExecutor(max_workers=5) as executor:
                # 提交所有任务
                futures = []
                for machine_name, machine_model in valid_machines:
                    future = executor.submit(
                        process_single_machine_timeline,
                        machine_name,
                        machine_model,
                        DB_CONFIG
                    )
                    futures.append(future)

                # 收集结果
                for future in futures:
                    try:
                        machine_result = future.result(timeout=30)  # 每个机器最多等待30秒
                        result.append(machine_result)
                    except Exception as e:
                        print(f"获取机器结果失败: {e}")
                        # 如果失败，不添加结果，保持原有顺序

        return result

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
        return []
    except Exception as e:
        print(f"处理时间轴数据错误: {e}")
        return []
    finally:
        if connection:
            connection.close()


@router.get("/hours")
async def get_electrolyzer_hours():
    """
    从MySQL数据库获取允许访问的电解槽的运行时长数据
    通过时间轴计算运行时长（使用多进程并行处理，不阻塞其他请求）

    Returns:
        List[Dict]: 返回格式为 [{"name": "1#", "hours": 7}, ...]
    """

    # 在线程池中执行 get_machine_timeline，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    timeline_data = await loop.run_in_executor(None, get_machine_timeline)

    result = []

    for machine_data in timeline_data:
        machine_name = machine_data["machine_name"]
        times = machine_data["time"]

        # 如果时间为空，运行时长为0
        if not times:
            result.append(
                {
                    "name": machine_name,
                    "total_hours": 0,
                    "current_hours": 0,
                    "model": None,
                    "start_time": None,
                }
            )
            continue

        # 计算运行时长
        total_hours = 0.0
        current_hours = 0.0
        for i in range(1, len(times)):
            prev_time = datetime.strptime(times[i - 1], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.strptime(times[i], "%Y-%m-%d %H:%M:%S")

            # 计算时间差（分钟）
            time_diff_minutes = (current_time - prev_time).total_seconds() / 60

            # 如果时间差 <= 60分钟，加上实际时间差
            if time_diff_minutes <= 60:
                total_hours += time_diff_minutes / 60
                current_hours += time_diff_minutes / 60
            # 如果时间差 > 60分钟，加上0小时
            else:
                total_hours += 0
                current_hours = 0

        # 判断最后一个时间点与当前时间的差值
        if times:
            last_time = datetime.strptime(times[-1], "%Y-%m-%d %H:%M:%S")
            current_query_time = datetime.now()
            time_diff_minutes = (current_query_time - last_time).total_seconds() / 60
            if time_diff_minutes > 60:
                current_hours = 0

        result.append(
            {
                "name": machine_name,
                "total_hours": round(total_hours, 2),
                "current_hours": round(current_hours, 2),
                "model": machine_data.get("machine_model"),
                "start_time": machine_data.get("start_time"),
            }
        )

    return result


@router.get("/table-data")
async def get_table_data(
        machine_name: str = Query(None, description="设备名称，如：1#"),
        start_datetime: str = Query(None, description="开始时间，格式：YYYY-MM-DD HH:mm:ss"),
        end_datetime: str = Query(None, description="结束时间，格式：YYYY-MM-DD HH:mm:ss"),
        page: int = Query(1, description="页码，从1开始"),
        size: int = Query(20, description="每页数量"),
):
    """
    获取WinCC表中的数据，支持分页和筛选

    参数:
    - machine_name: 设备名称（可选）
    - start_datetime: 开始时间（可选）
    - end_datetime: 结束时间（可选）
    - page: 页码
    - size: 每页数量

    返回:
    {
        "total": 总记录数,
        "data": [数据列表]
    }
    """
    connection = None
    try:
        # 验证分页参数
        if page < 1:
            raise HTTPException(status_code=400, detail="页码必须大于0")
        if size < 1 or size > 120:
            raise HTTPException(status_code=400, detail="每页数量必须在1-120之间")

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 构建WHERE条件
        where_conditions = []
        params = []

        if machine_name:
            where_conditions.append("machine_name = %s")
            params.append(machine_name)

        # 处理日期时间范围
        if start_datetime:
            # 验证时间格式
            try:
                datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
                where_conditions.append("CONCAT(date, ' ', time) >= %s")
                params.append(start_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式错误，应为: YYYY-MM-DD HH:MM:SS")

        if end_datetime:
            # 验证时间格式
            try:
                datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
                where_conditions.append("CONCAT(date, ' ', time) <= %s")
                params.append(end_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式错误，应为: YYYY-MM-DD HH:MM:SS")

        # 构建WHERE子句
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 1. 先获取总数
        count_sql = f"SELECT COUNT(*) as total FROM wincc {where_clause}"
        cursor.execute(count_sql, tuple(params))
        total_result = cursor.fetchone()
        total = total_result["total"] if total_result else 0

        # 2. 获取分页数据
        offset = (page - 1) * size

        # 按照 date DESC, time DESC 排序
        data_sql = f"""
            SELECT *
            FROM wincc
            {where_clause}
            ORDER BY date DESC, time DESC
            LIMIT %s OFFSET %s
        """

        data_params = params + [size, offset]
        cursor.execute(data_sql, tuple(data_params))
        rows = cursor.fetchall()

        cursor.close()

        # 格式化数据，排除 id 和 cell_21 到 cell_25
        formatted_data = []
        excluded_fields = {'id', 'cell_21', 'cell_22', 'cell_23', 'cell_24', 'cell_25'}

        for row in rows:
            formatted_row = {}
            for key, value in row.items():
                # 跳过排除的字段
                if key in excluded_fields:
                    continue

                if key == "date" and value:
                    # 格式化日期为 YYYY-MM-DD，确保年月日都是两位数
                    if hasattr(value, "strftime"):
                        formatted_row[key] = value.strftime("%Y-%m-%d")
                    else:
                        formatted_row[key] = str(value)
                elif key == "time" and value:
                    # 格式化时间为 HH:mm:ss，确保时分秒都是两位数
                    if hasattr(value, "strftime"):
                        formatted_row[key] = value.strftime("%H:%M:%S")
                    elif isinstance(value, timedelta):
                        # 如果是 timedelta 类型，转换为 HH:mm:ss 格式
                        total_seconds = int(value.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        formatted_row[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        formatted_row[key] = str(value)
                else:
                    formatted_row[key] = value
            formatted_data.append(formatted_row)

        # 二次排序：如果 date 和 time 相同，按 machine_name 的数字排序
        def get_machine_number(machine_name):
            """从 machine_name 中提取数字，例如 '1#' -> 1, '15#' -> 15"""
            if not machine_name:
                return 0
            try:
                # 去除 # 符号并转换为整数
                return int(machine_name.replace('#', '').strip())
            except (ValueError, AttributeError):
                return 0

        # 由于已经格式化为字符串，我们需要确保排序键的格式正确
        # 按 (date, time) 分组，组内按 machine_name 数字升序排序
        # 先按 date DESC, time DESC 排序
        # 字符串格式 "YYYY-MM-DD" 和 "HH:mm:ss" 可以直接字典序比较
        formatted_data.sort(key=lambda x: (
            x.get('date', '') or '',
            x.get('time', '') or ''
        ), reverse=True)

        # 然后对每组 (date, time) 相同的数据按 machine_name 数字升序排序
        result_data = []
        for key, group in groupby(formatted_data, key=lambda x: (x.get('date', ''), x.get('time', ''))):
            # 将组内数据按 machine_name 数字升序排序
            group_list = sorted(list(group), key=lambda x: get_machine_number(x.get('machine_name', '')))
            result_data.extend(group_list)

        return {
            "total": total,
            "data": result_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")
    finally:
        if connection:
            connection.close()
