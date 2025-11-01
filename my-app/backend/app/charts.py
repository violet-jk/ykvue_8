import time
from fastapi import APIRouter, HTTPException
import pymysql
import pandas as pd
import numpy as np
from datetime import datetime
from .config import DB_CONFIG

router = APIRouter()


def get_db_connection():
    """获取数据库连接,最多重试10次,每次间隔1秒"""
    last_error: Exception
    for attempt in range(10):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            last_error = e
            if attempt < 9:
                time.sleep(1)
    # 所有重试均失败,抛出HTTP异常
    raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(last_error)}")


@router.get("/device_list")
async def get_device_list():
    """
    获取 wincc 表中所有唯一的 machine_name 和 machine_model 组合
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = """
              SELECT DISTINCT machine_name, machine_model
              FROM wincc
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


@router.get("/one_device/all_data")
async def get_all_device_data(machine_name: str, machine_model: str):
    """
    优化版本: 一次性获取设备的所有数据
    1. 只进行一次数据库查询
    2. 基于cell数据过滤后的时间点来确保所有数据的时间一致性
    3. 返回所有图表所需的数据
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        # 一次性查询所有需要的字段
        sql = '''
              SELECT date, time, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9, cell_10, cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18, cell_19, cell_20, avg_voltage, voltage_range, pump_pressure, specific_gravity, hydrogen_flow_meter, inlet_pressure, oxygen_outlet_pressure, hydrogen_outlet_pressure, oxygen_outlet_temp, hydrogen_outlet_temp, oxygen_in_hydrogen, hydrogen_in_oxygen, pressure_diff
              FROM wincc
              WHERE machine_name = %s
                AND machine_model = %s
              ORDER BY date, time
              '''
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 使用 pandas 处理数据
        df = pd.DataFrame(results)

        if df.empty:
            return {
                "status": "success",
                "data": {},
                "global_start_time": None
            }

        # 组合 date 和 time 成 datetime
        df['date'] = pd.to_datetime(df['date'])

        # 如果 time 是 timedelta,直接加到 date 上
        if pd.api.types.is_timedelta64_dtype(df['time']) or isinstance(df['time'].iloc[0], pd.Timedelta):
            df['datetime'] = df['date'] + df['time']
        else:
            # 如果 time 是字符串或时间类型,转换为 timedelta
            df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))

        # ===== 步骤1: 处理cell数据,计算每个cell的zero_ratio,排除>0.8的cell =====
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

        # 如果没有有效的cell,返回空数据
        if len(valid_cells) == 0:
            return {
                "status": "success",
                "data": {},
                "global_start_time": None
            }

        # ===== 步骤2: 获取剩余cell的起始时间点,为所有cell均>1400的最小时间点 =====
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

        # 使用最晚的起始时间,确保所有cell在这个时间点都>1400
        global_start_time = max(start_time_candidates)

        # ===== 步骤3: 基于global_start_time过滤数据,并获取实际的时间点列表 =====
        # 先处理cell数据,获取过滤后的实际时间点
        cell_df_filtered = df[['datetime'] + valid_cells].copy()

        # 转换所有cell列为数值类型
        for cell_field in valid_cells:
            cell_df_filtered[cell_field] = pd.to_numeric(cell_df_filtered[cell_field], errors='coerce')

        # 使用全局起始时间筛选数据
        cell_df_filtered = cell_df_filtered[cell_df_filtered['datetime'] >= global_start_time].copy()

        # 过滤掉任意cell < 1400 的行,确保所有cell都>=1400
        mask = pd.Series([True] * len(cell_df_filtered), index=cell_df_filtered.index)
        for cell_field in valid_cells:
            mask &= (cell_df_filtered[cell_field] >= 1400)

        cell_df_filtered = cell_df_filtered[mask].copy()

        if cell_df_filtered.empty:
            return {
                "status": "success",
                "data": {},
                "global_start_time": global_start_time.strftime('%Y-%m-%d %H:%M:%S')
            }

        # 获取过滤后的有效时间点列表(这是基准时间点,用于过滤其他数据)
        valid_datetimes = cell_df_filtered['datetime'].unique()
        valid_datetimes = pd.Series(valid_datetimes).sort_values().reset_index(drop=True)

        # 计算时间差(小时),向下取整,用于分组
        cell_df_filtered['time_diff'] = ((cell_df_filtered['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

        # ===== 步骤4: 处理cell电压数据 =====
        voltage_data = {}
        for cell_field in valid_cells:
            # 按time_diff分组计算平均值,同时获取每组的第一个时间点
            grouped = cell_df_filtered.groupby('time_diff').agg({
                cell_field: 'mean',
                'datetime': 'first'
            }).reset_index()

            # 重命名列为图表格式: x, y, t
            grouped.columns = ['x', 'y', 't']
            # 先round,再替换NaN为None,避免JSON序列化错误
            grouped['y'] = grouped['y'].round(2)
            grouped['y'] = grouped['y'].replace({np.nan: None})
            # 将时间转换为字符串格式
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            voltage_data[cell_field] = {
                'x': grouped['x'].tolist(),
                'y': grouped['y'].tolist(),
                't': grouped['t'].tolist()
            }

        # ===== 步骤5: 使用相同的时间点过滤其他指标数据 =====
        # 创建一个辅助函数来处理单个字段
        def process_field(field_name, filter_condition=None):
            """处理单个字段,使用valid_datetimes中的时间点"""
            if field_name not in df.columns:
                return {"x": [], "y": [], "t": []}

            field_df = df[['datetime', field_name]].copy()
            field_df[field_name] = pd.to_numeric(field_df[field_name], errors='coerce')

            # 应用额外的过滤条件(如avg_voltage >= 1400)
            if filter_condition is not None:
                field_df = field_df[filter_condition(field_df[field_name])].copy()

            # 只保留valid_datetimes中存在的时间点(这是关键:使用cell过滤后的原始时间点)
            field_df = field_df[field_df['datetime'].isin(valid_datetimes)].copy()

            if field_df.empty:
                return {"x": [], "y": [], "t": []}

            # 计算时间差(小时),向下取整,用于分组
            field_df['time_diff'] = ((field_df['datetime'] - global_start_time).dt.total_seconds() / 3600).astype(int)

            # 按time_diff分组计算平均值,同时获取每组的第一个时间点
            grouped = field_df.groupby('time_diff').agg({
                field_name: 'mean',
                'datetime': 'first'
            }).reset_index()

            # 重命名列
            grouped.columns = ['x', 'y', 't']
            # 先round,再替换NaN为None,避免JSON序列化错误
            grouped['y'] = grouped['y'].round(2)
            grouped['y'] = grouped['y'].replace({np.nan: None})
            grouped['t'] = grouped['t'].dt.strftime('%Y-%m-%d %H:%M:%S')

            return {
                'x': grouped['x'].tolist(),
                'y': grouped['y'].tolist(),
                't': grouped['t'].tolist()
            }

        # 处理各个指标
        result_data = {
            "voltage": voltage_data,
            "avg_voltage": process_field('avg_voltage'),
            "voltage_range": process_field('voltage_range'),
            "pump_pressure": process_field('pump_pressure'),
            "specific_gravity": process_field('specific_gravity'),
            "hydrogen_flow_meter": process_field('hydrogen_flow_meter'),
            "inlet_outlet_pressure": {
                "inlet_pressure": process_field('inlet_pressure'),
                "oxygen_outlet_pressure": process_field('oxygen_outlet_pressure')
            },
            "oxygen_hydrogen_outlet_pressure": {
                "oxygen_outlet_pressure": process_field('oxygen_outlet_pressure'),
                "hydrogen_outlet_pressure": process_field('hydrogen_outlet_pressure')
            },
            "oxygen_hydrogen_outlet_temp": {
                "oxygen_outlet_temp": process_field('oxygen_outlet_temp'),
                "hydrogen_outlet_temp": process_field('hydrogen_outlet_temp')
            },
            "oxygen_hydrogen_cross": {
                "oxygen_in_hydrogen": process_field('oxygen_in_hydrogen'),
                "hydrogen_in_oxygen": process_field('hydrogen_in_oxygen')
            },
            "pressure_difference": process_field('pressure_diff')
        }

        return {
            "status": "success",
            "data": result_data,
            "global_start_time": global_start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()
