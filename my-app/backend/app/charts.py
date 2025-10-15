import time
from fastapi import APIRouter, HTTPException
import pymysql
from .config import DB_CONFIG
from collections import defaultdict

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


@router.get("/one_device")
async def get_one_device(machine_name: str, machine_model: str):
    """
    根据 machine_name 和 machine_model 从 test 表获取数据
    """
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        sql = "SELECT * FROM test WHERE machine_name = %s AND machine_model = %s ORDER BY date,time"
        cursor.execute(sql, (machine_name, machine_model))
        results = cursor.fetchall()

        # 处理数据：为每个 cell 计算按 hours 分组的平均值
        data = defaultdict(lambda: defaultdict(list))
        voltage_range_data = defaultdict(list)
        for row in results:
            hours = row.get('hours')
            if hours is None:
                continue
            for i in range(1, 21):
                cell = f'cell_{i}'
                if cell in row and row[cell] is not None:
                    data[cell][hours].append(row[cell])
            if 'voltage_range' in row and row['voltage_range'] is not None:
                voltage_range_data[hours].append(row['voltage_range'])
        print(voltage_range_data)
        processed = {}
        for cell, hour_dict in data.items():
            all_values = []
            for h in hour_dict:
                all_values.extend(hour_dict[h])
            if not all_values:
                continue
            zero_count = sum(1 for v in all_values if v == 0)
            if zero_count / len(all_values) >= 0.8:
                continue  # 舍弃该 cell
            sorted_hours = sorted(hour_dict.keys())
            x = []
            y = []
            for h in sorted_hours:
                filtered = [v for v in hour_dict[h] if v >= 1400]
                if filtered:
                    avg = sum(filtered) / len(filtered)
                    x.append(h)
                    y.append(int(round(avg)))
            processed[cell] = {'x': x, 'y': y}

        # Process voltage_range
        processed_voltage_range = {}
        sorted_hours_vr = sorted(voltage_range_data.keys())
        x_vr = []
        y_vr = []
        for h in sorted_hours_vr:
            values = voltage_range_data[h]
            if values:
                avg_vr = sum(values) / len(values)
                x_vr.append(h)
                y_vr.append(int(round(avg_vr)))
        processed_voltage_range = {'x': x_vr, 'y': y_vr}

        return {
            "status": "success",
            "voltage": processed,
            "avg_voltage": None,
            "voltage_range": processed_voltage_range,
            "pump_pressure": None,
            "specific_gravity": None,
            "hydrogen_flow_meter": None,
            "oxygen_in_hydrogen":None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    finally:
        cursor.close()
        connection.close()
