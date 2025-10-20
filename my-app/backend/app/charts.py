import time
from fastapi import APIRouter, HTTPException
import pymysql
import pandas as pd
import numpy as np
from datetime import datetime
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


@router.get("/device_list")
async def get_device_list():
    """
    获取 test 表中所有唯一的 machine_name 和 machine_model 组合
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = """
              SELECT DISTINCT machine_name, machine_model
              FROM test
              WHERE machine_name IS NOT NULL
                AND machine_model IS NOT NULL
              ORDER BY machine_name, machine_model \
              """
        cursor.execute(sql)
        results = cursor.fetchall()

        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/cell")
async def get_one_device(machine_name: str, machine_model: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取数据
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10, cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
              ORDER BY date, time \
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "voltage": {},
            }

        # 组合 date 和 time 成 datetime
        # 处理 time 可能是 timedelta 类型的情况
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 步骤1: 计算每个cell的zero_ratio，排除>0.8的cell
        valid_cells = []
        for i in range(1, 21):  # cell_1 到 cell_20
            cell_field = f'cell_{i}'

            if cell_field not in df.columns:
                continue

            # 创建副本避免警告
            cell_df = df[['datetime', cell_field]].copy()
            cell_df.columns = ['datetime', 'value']

            # 转换为数值类型
            cell_df['value'] = pd.to_numeric(cell_df['value'], errors='coerce')

            # 找到第一个非0且>1400的值的索引
            mask = (cell_df['value'] > 0) & (cell_df['value'] > 1400)
            valid_indices = cell_df[mask].index

            if len(valid_indices) == 0:
                continue

            # 从第一个>1400的值开始计算
            start_idx = valid_indices[0]
            cell_df = cell_df.loc[start_idx:].copy()

            # 计算临时时间差用于分组
            temp_start_time = cell_df.iloc[0]['datetime']
            cell_df['time_diff'] = ((cell_df['datetime'] - temp_start_time).dt.total_seconds() / 3600).astype(int)

            # 分组计算 y=0 比例
            grouped_temp = cell_df.groupby('time_diff').agg({
                'value': 'mean'
            }).reset_index()
            grouped_temp.columns = ['x', 'y']
            grouped_temp['y'] = grouped_temp['y'].round(2)

            zero_ratio = (grouped_temp['y'] == 0).sum() / len(grouped_temp) if len(grouped_temp) > 0 else 0

            # 只保留zero_ratio <= 0.8的cell
            if zero_ratio <= 0.8:
                valid_cells.append(cell_field)

        # 如果没有有效的cell，返回空数据
        if len(valid_cells) == 0:
            return {
                "status": "success",
                "data": {},
            }

        # 步骤2: 获取剩余cell的起始时间点，为所有cell均>1400的最小时间点
        # 对每个有效cell，找到它第一次>1400的时间点
        start_time_candidates = []
        for cell_field in valid_cells:
            cell_df = df[['datetime', cell_field]].copy()
            cell_df.columns = ['datetime', 'value']
            cell_df['value'] = pd.to_numeric(cell_df['value'], errors='coerce')

            # 找到第一个非0且>1400的值
            mask = (cell_df['value'] > 0) & (cell_df['value'] > 1400)
            valid_indices = cell_df[mask].index

            if len(valid_indices) > 0:
                start_time = cell_df.loc[valid_indices[0], 'datetime']
                start_time_candidates.append(start_time)

        # 使用最晚的起始时间，确保所有cell在这个时间点都>1400
        global_start_time = max(start_time_candidates)

        # 步骤3: 根据起始时间点计算作图需要的数据
        voltage_data = {}
        for cell_field in valid_cells:
            # 创建副本避免警告
            cell_df = df[['datetime', cell_field]].copy()
            cell_df.columns = ['datetime', 'value']

            # 转换为数值类型
            cell_df['value'] = pd.to_numeric(cell_df['value'], errors='coerce')

            # 使用全局起始时间筛选数据
            cell_df = cell_df[cell_df['datetime'] >= global_start_time].copy()

            # 过滤掉 value < 1400 的数据
            cell_df = cell_df[cell_df['value'] >= 1400].copy()

            if cell_df.empty:
                continue

            # 计算时间差（小时），向下取整
            cell_df['time_diff'] = ((cell_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            # 按小时分组计算平均值，同时获取每个小时的起始时间
            grouped = cell_df.groupby('time_diff').agg({
                'value': 'mean',
                'datetime': 'first'  # 获取每个小时的第一个时间点
            }).reset_index()

            # 重命名列为图表格式：x, y, t
            grouped.columns = ['x', 'y', 't']
            grouped['y'] = grouped['y'].round(2)
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            voltage_data[cell_field] = {
                'x': grouped['x'].tolist(),
                'y': grouped['y'].tolist(),
                't': grouped['t'].tolist()
            }

        return {
            "status": "success",
            "data": voltage_data,
            "global_start_time": global_start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/voltage_avg")
async def get_voltage_avg(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 avg_voltage 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, avg_voltage
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND avg_voltage IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['avg_voltage'] = pd.to_numeric(df['avg_voltage'], errors='coerce')

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        # 过滤掉 value < 1400 的数据
        df = df[df['avg_voltage'] >= 1400].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'avg_voltage': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/voltage_range")
async def get_voltage_range(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 voltage_range 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, voltage_range
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND voltage_range IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['voltage_range'] = pd.to_numeric(df['voltage_range'], errors='coerce')

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'voltage_range': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/pump_pressure")
async def get_pump_pressure(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 pump_pressure 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, pump_pressure
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND pump_pressure IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['pump_pressure'] = pd.to_numeric(df['pump_pressure'], errors='coerce')

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'pump_pressure': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/specific_gravity")
async def get_specific_gravity(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 specific_gravity 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, specific_gravity
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND specific_gravity IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['specific_gravity'] = pd.to_numeric(df['specific_gravity'], errors='coerce')

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'specific_gravity': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/hydrogen_flow_meter")
async def get_hydrogen_flow_meter(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 hydrogen_flow_meter 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, hydrogen_flow_meter
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND hydrogen_flow_meter IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta，直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型，转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['hydrogen_flow_meter'] = pd.to_numeric(df['hydrogen_flow_meter'], errors='coerce')

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'hydrogen_flow_meter': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/inlet_outlet_pressure")
async def get_inlet_outlet_pressure(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 inlet_pressure 和 oxygen_outlet_pressure 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, inlet_pressure, oxygen_outlet_pressure
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND inlet_pressure IS NOT NULL
                AND oxygen_outlet_pressure IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"inlet_pressure": {"x": [], "y": []}, "oxygen_outlet_pressure": {"x": [], "y": []}},
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        result_data = {}

        for field in ['inlet_pressure', 'oxygen_outlet_pressure']:
            df[field] = pd.to_numeric(df[field], errors='coerce')

            # 从起始时间开始筛选数据
            field_df = df[df['datetime'] >= global_start_time].copy()

            if field_df.empty:
                result_data[field] = {"x": [], "y": [], "t": []}
                continue

            field_df['time_diff'] = ((field_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            grouped = field_df.groupby('time_diff').agg({
                field: 'mean',
                'datetime': 'first'  # 获取每个小时的第一个时间点
            }).reset_index()

            grouped.columns = ['x', 'y', 't']
            grouped['y'] = grouped['y'].round(2)
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            result_data[field] = {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()}

        return {
            "status": "success",
            "data": result_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/oxygen_hydrogen_outlet_pressure")
async def get_oxygen_hydrogen_outlet_pressure(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 oxygen_outlet_pressure 和 hydrogen_outlet_pressure 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, oxygen_outlet_pressure, hydrogen_outlet_pressure
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND oxygen_outlet_pressure IS NOT NULL
                AND hydrogen_outlet_pressure IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"oxygen_outlet_pressure": {"x": [], "y": []}, "hydrogen_outlet_pressure": {"x": [], "y": []}},
            }

        df['date'] = pd.to_datetime(df['date'])

        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        result_data = {}

        for field in ['oxygen_outlet_pressure', 'hydrogen_outlet_pressure']:
            df[field] = pd.to_numeric(df[field], errors='coerce')

            # 从起始时间开始筛选数据
            field_df = df[df['datetime'] >= global_start_time].copy()

            if field_df.empty:
                result_data[field] = {"x": [], "y": [], "t": []}
                continue

            field_df['time_diff'] = ((field_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            grouped = field_df.groupby('time_diff').agg({
                field: 'mean',
                'datetime': 'first'  # 获取每个小时的第一个时间点
            }).reset_index()

            grouped.columns = ['x', 'y', 't']
            grouped['y'] = grouped['y'].round(2)
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            result_data[field] = {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()}

        return {
            "status": "success",
            "data": result_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/oxygen_hydrogen_outlet_temp")
async def get_oxygen_hydrogen_outlet_temp(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 oxygen_outlet_temp 和 hydrogen_outlet_temp 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, oxygen_outlet_temp, hydrogen_outlet_temp
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND oxygen_outlet_temp IS NOT NULL
                AND hydrogen_outlet_temp IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"oxygen_outlet_temp": {"x": [], "y": []}, "hydrogen_outlet_temp": {"x": [], "y": []}},
            }

        df['date'] = pd.to_datetime(df['date'])

        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        result_data = {}

        for field in ['oxygen_outlet_temp', 'hydrogen_outlet_temp']:
            df[field] = pd.to_numeric(df[field], errors='coerce')

            # 从起始时间开始筛选数据
            field_df = df[df['datetime'] >= global_start_time].copy()

            if field_df.empty:
                result_data[field] = {"x": [], "y": [], "t": []}
                continue

            field_df['time_diff'] = ((field_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            grouped = field_df.groupby('time_diff').agg({
                field: 'mean',
                'datetime': 'first'  # 获取每个小时的第一个时间点
            }).reset_index()

            grouped.columns = ['x', 'y', 't']
            grouped['y'] = grouped['y'].round(2)
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            result_data[field] = {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()}

        return {
            "status": "success",
            "data": result_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/oxygen_hydrogen_cross")
async def get_oxygen_hydrogen_cross(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取 oxygen_in_hydrogen 和 hydrogen_in_oxygen 数据
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, oxygen_in_hydrogen, hydrogen_in_oxygen
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND oxygen_in_hydrogen IS NOT NULL
                AND hydrogen_in_oxygen IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"oxygen_in_hydrogen": {"x": [], "y": []}, "hydrogen_in_oxygen": {"x": [], "y": []}},
            }

        df['date'] = pd.to_datetime(df['date'])

        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        result_data = {}

        for field in ['oxygen_in_hydrogen', 'hydrogen_in_oxygen']:
            df[field] = pd.to_numeric(df[field], errors='coerce')

            # 从起始时间开始筛选数据
            field_df = df[df['datetime'] >= global_start_time].copy()

            if field_df.empty:
                result_data[field] = {"x": [], "y": [], "t": []}
                continue

            field_df['time_diff'] = ((field_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            grouped = field_df.groupby('time_diff').agg({
                field: 'mean',
                'datetime': 'first'  # 获取每个小时的第一个时间点
            }).reset_index()

            grouped.columns = ['x', 'y', 't']
            grouped['y'] = grouped['y'].round(2)
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            result_data[field] = {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()}

        return {
            "status": "success",
            "data": result_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("/one_device/pressure_difference")
async def get_pressure_difference(machine_name: str, machine_model: str, start_time: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取电解槽进出口压差
    计算公式: inlet_pressure - oxygen_outlet_pressure
    使用传入的 start_time 作为统一的起始时间
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = '''
              SELECT date, time, inlet_pressure, oxygen_outlet_pressure
              FROM test
              WHERE machine_name = %s
                AND machine_model = %s
                AND inlet_pressure IS NOT NULL
                AND oxygen_outlet_pressure IS NOT NULL
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        df['date'] = pd.to_datetime(df['date'])

        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # 转换为数值类型
        df['inlet_pressure'] = pd.to_numeric(df['inlet_pressure'], errors='coerce')
        df['oxygen_outlet_pressure'] = pd.to_numeric(df['oxygen_outlet_pressure'], errors='coerce')

        # 计算压差: inlet_pressure - oxygen_outlet_pressure
        df['pressure_difference'] = df['inlet_pressure'] - df['oxygen_outlet_pressure']

        # 使用传入的 start_time 作为起始时间
        global_start_time = pd.to_datetime(start_time)

        # 从起始时间开始筛选数据
        df = df[df['datetime'] >= global_start_time].copy()

        if df.empty:
            return {
                "status": "success",
                "data": {"x": [], "y": []},
            }

        # 计算时间差（小时），向下取整
        df['time_diff'] = ((df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # 按小时分组计算平均值，同时获取每个小时的起始时间
        grouped = df.groupby('time_diff').agg({
            'pressure_difference': 'mean',
            'datetime': 'first'  # 获取每个小时的第一个时间点
        }).reset_index()

        # 重命名列为图表格式：x, y, t
        grouped.columns = ['x', 'y', 't']
        grouped['y'] = grouped['y'].round(2)
        # 将时间转换为字符串格式
        grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "status": "success",
            "data": {"x": grouped['x'].tolist(), "y": grouped['y'].tolist(), "t": grouped['t'].tolist()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()
