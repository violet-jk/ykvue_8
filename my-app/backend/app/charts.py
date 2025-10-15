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

        voltage_data = {}

        for i in range(1, 21):  # cell_1 到 cell_20
            cell_field = f'cell_{i}'

            if cell_field not in df.columns:
                voltage_data[cell_field] = []
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

            # 获取起始时间
            start_idx = valid_indices[0]
            start_time = cell_df.loc[start_idx, 'datetime']

            # 从起始时间开始筛选数据
            cell_df = cell_df.loc[start_idx:].copy()

            # 计算时间差（小时），向下取整
            cell_df['time_diff'] = ((cell_df['datetime'] - start_time).dt.total_seconds() / 3600).astype(int)

            # 先分组所有数据计算 y=0 比例（在过滤<1400之前）
            grouped_all = cell_df.groupby('time_diff').agg({
                'value': 'mean'
            }).reset_index()
            grouped_all.columns = ['x', 'y']
            grouped_all['y'] = grouped_all['y'].round(2)
            zero_ratio = (grouped_all['y'] == 0).sum() / len(grouped_all) if len(grouped_all) > 0 else 0
            print(zero_ratio)
            if zero_ratio > 0.8:
                continue
            else:
                # 过滤掉 value < 1400 的数据
                cell_df = cell_df[cell_df['value'] >= 1400].copy()

                # 按小时分组计算平均值
                grouped = cell_df.groupby('time_diff').agg({
                    'value': 'mean'
                }).reset_index()

                # 重命名列为图表格式：x, y
                grouped.columns = ['x', 'y']
                grouped['y'] = grouped['y'].round(2)

                voltage_data[cell_field] = {'x': grouped['x'].tolist(), 'y': grouped['y'].tolist()}

        return {
            "status": "success",
            "data": voltage_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()
