# 临时方案 爬取数据 token每7天需要更换
# 弃用此方案
import requests
import urllib3
import pymysql
import time
from datetime import datetime
from typing import List, Dict
from .config import DB_CONFIG

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_field_mapping():
    """
    返回网站字段到数据库字段的映射关系
    """
    return {
        "date": "date",
        "dateTime": "time",
        "mechine_num": "machine_name",
        "mechine_model": "machine_model",
        "hours": "hours",
        "total_current_a": "total_current",
        "cell_1": "cell_1",
        "cell_2": "cell_2",
        "cell_3": "cell_3",
        "cell_4": "cell_4",
        "cell_5": "cell_5",
        "cell_6": "cell_6",
        "cell_7": "cell_7",
        "cell_8": "cell_8",
        "cell_9": "cell_9",
        "cell_10": "cell_10",
        "cell_11": "cell_11",
        "cell_12": "cell_12",
        "cell_13": "cell_13",
        "cell_14": "cell_14",
        "cell_15": "cell_15",
        "cell_16": "cell_16",
        "cell_17": "cell_17",
        "cell_18": "cell_18",
        "cell_19": "cell_19",
        "cell_20": "cell_20",
        "voltage_max_mv": "max_voltage",
        "voltage_min_mv": "min_voltage",
        "voltage_avg_mv": "avg_voltage",
        "voltage_range_mv": "voltage_range",
        "pump_outlet_pressure_mpa": "pump_pressure",
        "pump_frequency_hz": "pump_opening",
        "fan_opening": "fan_opening",
        "density_mg_cm3": "specific_gravity",
        "inlet_pressure_mpa": "inlet_pressure",
        "liquid_level_mm": "liquid_level",
        "alkali_replenish": "is_alkali_refill",
        "o2_outlet_pressure_mpa": "oxygen_outlet_pressure",
        "h2_outlet_pressure_mpa": "hydrogen_outlet_pressure",
        "o2_outlet_temp_c": "oxygen_outlet_temp",
        "h2_outlet_temp_c": "hydrogen_outlet_temp",
        "h2_gas_temp_c": "hydrogen_gas_temp",
        "h2_flow_rate": "hydrogen_flow_meter",
        "collected_water_mm": "water_collection",
        "total_drain_ml": "cumulative_drainage",
        "o2_in_h2_ppm": "oxygen_in_hydrogen",
        "h2_in_o2_ppm": "hydrogen_in_oxygen"
    }


def transform_data(raw_data: List[Dict]) -> List[Dict]:
    """
    将原始数据转换为数据库格式

    参数:
        raw_data: 从API获取的原始数据列表

    返回:
        转换后的数据列表
    """
    field_mapping = get_field_mapping()
    transformed_data = []

    for item in raw_data:
        new_item = {}
        for api_field, db_field in field_mapping.items():
            if api_field in item:
                value = item[api_field]

                # 数据清洗: 去除字符串两端空格
                if isinstance(value, str):
                    value = value.strip()
                    # 将空字符串转换为 None
                    if value == '':
                        value = None

                # 特殊处理: is_alkali_refill 字段
                if db_field == "is_alkali_refill":
                    # "是" 转换为 1, 空字符或其他值转换为 0
                    if value == "是":
                        value = 1
                    else:
                        value = 0

                new_item[db_field] = value
        transformed_data.append(new_item)

    return transformed_data


def get_db_connection():
    """获取数据库连接，最多重试10次，每次间隔1秒"""
    last_error = None
    for attempt in range(10):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            last_error = e
            if attempt < 9:
                time.sleep(1)
    # 所有重试均失败
    return None


def upload_to_database(data_dict: Dict[int, List[Dict]]) -> Dict[str, any]:
    """
    将获取的数据上传到数据库（只上传比数据库时间更新的数据）

    参数:
        data_dict: 按设备编号分组的数据字典

    返回:
        上传结果统计信息
    """
    connection = get_db_connection()
    if not connection:
        return {"success": False, "message": "数据库连接失败", "total": 0, "inserted": 0, "failed": 0, "skipped": 0}

    total_count = 0
    inserted_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 按设备编号排序处理
        for device_num in sorted(data_dict.keys()):
            records = data_dict[device_num]
            machine_name = f"{device_num}#"

            # 获取该设备在数据库中的最大时间
            max_time_sql = """
                SELECT date, time 
                FROM test 
                WHERE machine_name = %s 
                ORDER BY date DESC, time DESC 
                LIMIT 1
            """
            cursor.execute(max_time_sql, (machine_name,))
            max_time_result = cursor.fetchone()

            # 确定数据库中的最大时间
            if max_time_result and max_time_result.get('date') and max_time_result.get('time'):
                max_date = max_time_result['date']
                max_time = max_time_result['time']
                # 将date和time转换为字符串进行比较
                if hasattr(max_date, 'strftime'):
                    max_date_str = max_date.strftime("%Y-%m-%d")
                else:
                    max_date_str = str(max_date)

                if hasattr(max_time, 'strftime'):
                    max_time_str = max_time.strftime("%H:%M:%S")
                else:
                    max_time_str = str(max_time)

                max_datetime_str = f"{max_date_str} {max_time_str}"
                # 转换为datetime对象
                try:
                    max_datetime_obj = datetime.strptime(max_datetime_str, "%Y-%m-%d %H:%M:%S")
                except:
                    max_datetime_obj = datetime.min
            else:
                # 如果数据库中没有该设备的数据，设置为最小值
                max_datetime_str = "0000-00-00 00:00:00"
                max_datetime_obj = datetime.min

            for record in records:
                total_count += 1

                # 获取当前记录的时间
                record_date = record.get("date", "")
                record_time = record.get("time", "")

                # 将记录时间转换为字符串
                if hasattr(record_date, 'strftime'):
                    record_date_str = record_date.strftime("%Y-%m-%d")
                else:
                    record_date_str = str(record_date) if record_date else ""
                    # 将日期格式从 2025/10/27 转换为 2025-10-27
                    record_date_str = record_date_str.replace("/", "-")

                if hasattr(record_time, 'strftime'):
                    record_time_str = record_time.strftime("%H:%M:%S")
                else:
                    record_time_str = str(record_time) if record_time else ""

                record_datetime_str = f"{record_date_str} {record_time_str}"

                # 转换为datetime对象进行比较
                try:
                    record_datetime_obj = datetime.strptime(record_datetime_str, "%Y-%m-%d %H:%M:%S")
                except:
                    # 如果转换失败，跳过该记录
                    skipped_count += 1
                    continue

                # 只上传比数据库时间更新的数据
                if record_datetime_obj <= max_datetime_obj:
                    skipped_count += 1
                    continue

                try:
                    # 构建INSERT语句
                    sql = """
                          INSERT INTO test (date, time, machine_name, machine_model, hours, total_current,
                                            cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8, cell_9,
                                            cell_10,
                                            cell_11, cell_12, cell_13, cell_14, cell_15, cell_16, cell_17, cell_18,
                                            cell_19, cell_20,
                                            max_voltage, min_voltage, avg_voltage, voltage_range,
                                            pump_pressure, pump_opening, fan_opening, specific_gravity, inlet_pressure,
                                            liquid_level,
                                            is_alkali_refill, oxygen_outlet_pressure, hydrogen_outlet_pressure,
                                            oxygen_outlet_temp, hydrogen_outlet_temp, hydrogen_gas_temp,
                                            hydrogen_flow_meter,
                                            water_collection, cumulative_drainage, oxygen_in_hydrogen,
                                            hydrogen_in_oxygen)
                          VALUES (%s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s,
                                  %s, %s, %s, %s,
                                  %s, %s, %s, %s) \
                          """

                    # 转换日期格式：将 2025/10/27 转换为 2025-10-27
                    date_value = record.get("date", "")
                    if date_value:
                        date_value = str(date_value).replace("/", "-")

                    values = (
                        date_value, record.get("time"), record.get("machine_name"),
                        record.get("machine_model"), record.get("hours"), record.get("total_current"),
                        record.get("cell_1"), record.get("cell_2"), record.get("cell_3"), record.get("cell_4"),
                        record.get("cell_5"), record.get("cell_6"), record.get("cell_7"), record.get("cell_8"),
                        record.get("cell_9"), record.get("cell_10"), record.get("cell_11"), record.get("cell_12"),
                        record.get("cell_13"), record.get("cell_14"), record.get("cell_15"), record.get("cell_16"),
                        record.get("cell_17"), record.get("cell_18"), record.get("cell_19"), record.get("cell_20"),
                        record.get("max_voltage"), record.get("min_voltage"), record.get("avg_voltage"),
                        record.get("voltage_range"), record.get("pump_pressure"), record.get("pump_opening"),
                        record.get("fan_opening"), record.get("specific_gravity"), record.get("inlet_pressure"),
                        record.get("liquid_level"), record.get("is_alkali_refill"),
                        record.get("oxygen_outlet_pressure"), record.get("hydrogen_outlet_pressure"),
                        record.get("oxygen_outlet_temp"), record.get("hydrogen_outlet_temp"),
                        record.get("hydrogen_gas_temp"), record.get("hydrogen_flow_meter"),
                        record.get("water_collection"), record.get("cumulative_drainage"),
                        record.get("oxygen_in_hydrogen"), record.get("hydrogen_in_oxygen")
                    )

                    cursor.execute(sql, values)
                    inserted_count += 1

                except Exception as e:
                    failed_count += 1

        # 提交事务
        connection.commit()

        result = {
            "success": True,
            "message": "数据上传完成",
            "total": total_count,
            "inserted": inserted_count,
            "failed": failed_count,
            "skipped": skipped_count
        }

    except Exception as e:
        connection.rollback()
        result = {
            "success": False,
            "message": f"数据上传失败: {type(e).__name__} - {e}",
            "total": total_count,
            "inserted": inserted_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
    finally:
        cursor.close()
        connection.close()

    return result


def fetch_latest_device_data(page: int = 1, page_size: int = 90, upload_to_db: bool = True) -> Dict[str, any]:
    """
    获取所有设备的最新数据（单次请求），并可选择上传到数据库

    参数:
        page: 页码，默认为1
        page_size: 每页数据条数，默认为90（可获取所有设备的最新数据）
        upload_to_db: 是否上传到数据库，默认为True

    返回:
        字典，包含数据和上传结果
        {
            "data": {1: [...], 2: [...], ...},  # 按设备编号排序
            "upload_result": {...} # 上传结果（仅在upload_to_db=True时）
        }
    """
    url = "https://m.yankon-xm.com:9898/prod-api/api/winCC/page"

    # TODO: token需要每7天更新一次
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-cn",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjY5NTM3MTc4MzYwMjI1NiwiVGVuYW50SWQiOjEzMDAwMDAwMDAxMDEsIkFjY291bnQiOiIwMDI2MDkwIiwiUmVhbE5hbWUiOiLmoZHpvpnlgaUiLCJBY2NvdW50VHlwZSI6Nzc3LCJPcmdJZCI6NjQ3MDE3NjIyMDg1NzA4LCJPcmdOYW1lIjoi55S16Kej5qe9Juezu-e7n-W8gOWPkemDqCIsIk9yZ1R5cGUiOiI1MDEiLCJpYXQiOjE3NjE1NTE2NzEsIm5iZiI6MTc2MTU1MTY3MSwiZXhwIjoxNzYyMTU2NDcxLCJpc3MiOiJBZG1pbi5ORVQiLCJhdWQiOiJBZG1pbi5ORVQifQ.fWvLYKC8M6loRQrWRR9YH9YEnrxU-IHGhibH0qFcmBE",
        "content-type": "application/json-patch+json",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    result = {}

    try:
        # 单次请求获取所有设备数据
        payload = {
            "page": page,
            "pageSize": page_size
        }

        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 检查响应格式
            if data.get("code") == 200:
                items = data.get("result", {}).get("items", [])

                # 转换数据格式
                if items:
                    transformed_items = transform_data(items)

                    # 按设备编号分组
                    for item in transformed_items:
                        machine_name = item.get("machine_name", "").strip()
                        # 提取设备编号（假设格式为 "1#" 或 "1"）
                        if machine_name:
                            device_num_str = machine_name.replace("#", "").strip()
                            try:
                                device_num = int(device_num_str)
                                if device_num not in result:
                                    result[device_num] = []
                                result[device_num].append(item)
                            except ValueError:
                                # 如果无法转换为整数，跳过该条数据
                                pass

    except Exception as e:
        print(f"获取设备数据失败: {type(e).__name__} - {e}")

    # 对每个设备的数据按照date和time升序排序
    for device_num in result:
        result[device_num] = sorted(
            result[device_num],
            key=lambda x: (x.get("date") or "", x.get("time") or "")
        )

    # 按设备编号排序
    sorted_result = dict(sorted(result.items()))

    # 根据参数决定是否上传到数据库
    response = {"data": sorted_result}

    if upload_to_db and sorted_result:
        upload_result = upload_to_database(sorted_result)
        response["upload_result"] = upload_result
        print(f"数据上传结果: {upload_result}")

    return response


if __name__ == "__main__":
    # 测试函数
    fetch_latest_device_data(page=1, page_size=90, upload_to_db=True)