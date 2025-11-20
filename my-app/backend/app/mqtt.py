import paho.mqtt.client as mqtt
import threading
import uuid
from datetime import datetime, timedelta
from collections import deque
from fastapi import APIRouter
from typing import Optional
import json
import pymysql
from dateutil import parser
from .config import DB_CONFIG, MQTT_CONFIG

router = APIRouter()

# MQTT配置
MQTT_BROKER = MQTT_CONFIG["broker"]
MQTT_PORT = MQTT_CONFIG["port"]
MQTT_KEEPALIVE = MQTT_CONFIG["keepalive"]
MQTT_TOPIC = MQTT_CONFIG["topic"]

# 全局变量
mqtt_client: Optional[mqtt.Client] = None
mqtt_connected = False
mqtt_lock = threading.Lock()
mqtt_logs = deque(maxlen=2000)  # 最多保存2000条日志

# 消息处理队列
message_queue = []  # 消息列表,存储所有接收到的消息
message_queue_lock = threading.Lock()  # 消息队列锁

# 数据合并触发机制 (消息间隔检测)
last_message_time = None  # 最后一条消息的接收时间
merge_lock = threading.Lock()  # 合并操作锁,防止重复触发
MESSAGE_IDLE_THRESHOLD = 20  # 消息间隔阈值(秒),超过此时间无新消息则触发合并
merge_timer = None  # 消息间隔检测定时器


def on_connect(client, userdata, flags, rc):
    """MQTT连接成功回调"""
    global mqtt_connected
    if rc == 0:
        msg = f"[MQTT] 成功连接到MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}"
        with mqtt_lock:
            mqtt_connected = True
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": msg
            })
        # 订阅主题
        client.subscribe(MQTT_TOPIC)
        subscribe_msg = f"[MQTT] 已订阅主题: {MQTT_TOPIC}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": subscribe_msg
            })
    else:
        msg = f"[MQTT] 连接失败，返回码: {rc}"
        with mqtt_lock:
            mqtt_connected = False
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": msg
            })


def on_disconnect(client, userdata, rc):
    """MQTT断开连接回调"""
    global mqtt_connected
    with mqtt_lock:
        mqtt_connected = False
    if rc != 0:
        msg = f"[MQTT] 意外断开连接，返回码: {rc}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "警告",
                "message": msg
            })
    else:
        msg = "[MQTT] 正常断开连接"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": msg
            })


def on_message(client, userdata, msg):
    """MQTT消息接收回调 - 快速接收并放入列表"""
    global last_message_time, merge_timer
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        # 放入消息列表
        with message_queue_lock:
            message_queue.append((topic, payload))

        # 更新最后消息时间
        with merge_lock:
            last_message_time = datetime.now()

            # 取消之前的定时器
            if merge_timer is not None:
                merge_timer.cancel()

            # 启动新的间隔检测定时器
            merge_timer = threading.Timer(MESSAGE_IDLE_THRESHOLD, trigger_merge_on_idle)
            merge_timer.daemon = True
            merge_timer.start()

    except Exception as e:
        error_msg = f"[MQTT] 接收消息时出错: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def trigger_merge_on_idle():
    """
    消息间隔检测触发数据清洗和上传
    当超过MESSAGE_IDLE_THRESHOLD秒没有新消息时触发
    """
    try:
        with merge_lock:
            # 检查是否真的超过阈值(防止定时器延迟导致的误触发)
            if last_message_time is not None:
                elapsed = (datetime.now() - last_message_time).total_seconds()
                if elapsed >= MESSAGE_IDLE_THRESHOLD:
                    msg = f"[数据处理] 检测到消息间隔超过{MESSAGE_IDLE_THRESHOLD}秒,触发数据清洗和上传"
                    with mqtt_lock:
                        mqtt_logs.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "level": "信息",
                            "message": msg
                        })

                    # 执行数据清洗和上传操作
                    clean_and_upload_data()

    except Exception as e:
        error_msg = f"[数据处理] 间隔检测触发时出错: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def clean_and_upload_data():
    """
    数据清洗和上传函数
    从message_queue获取所有数据,清洗后直接上传到wincc表
    """
    global message_queue
    conn = None
    cursor = None

    try:
        # 1. 获取所有消息并清空队列
        with message_queue_lock:
            messages = message_queue.copy()
            message_queue = []  # 清空队列

        if not messages:
            msg = "[数据处理] 没有需要处理的数据"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "信息",
                    "message": msg
                })
            return

        msg = f"[数据处理] 开始处理{len(messages)}条消息..."
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": msg
            })

        # 2. 解析和清洗数据
        temp_data = []
        for topic, payload in messages:
            try:
                # 解析JSON格式的payload
                data = json.loads(payload)

                # 提取字段
                name = data.get('name')
                value = data.get('value')
                time_str = data.get('time')

                # 验证必需字段
                if name is None or value is None or time_str is None:
                    continue

                # 转换时间格式 (ISO 8601 -> YYYY-MM-DD HH:mm:ss, UTC+0 -> UTC+8)
                dt = parser.isoparse(time_str)
                dt_utc8 = dt + timedelta(hours=8)
                formatted_time = dt_utc8.strftime("%Y-%m-%d %H:%M:%S")

                temp_data.append({
                    'name': name,
                    'value': str(value),
                    'time': formatted_time
                })

            except (json.JSONDecodeError, Exception) as e:
                error_msg = f"[数据处理] 数据解析失败: {payload[:50]}..., 错误: {str(e)}"
                with mqtt_lock:
                    mqtt_logs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "level": "错误",
                        "message": error_msg
                    })
                continue

        if not temp_data:
            msg = "[数据处理] 没有有效的数据可处理"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "信息",
                    "message": msg
                })
            return

        # 3. 按设备分组数据 (通过name字段识别设备编号)
        devices_data = {}  # {machine_name: {field_name: value, time: datetime}}

        for row in temp_data:
            name = row['name']
            value = row['value']
            time_val = row['time']

            # 确保time_val是datetime对象
            if isinstance(time_val, str):
                time_val = datetime.strptime(time_val, "%Y-%m-%d %H:%M:%S")

            # 解析设备编号 (从name中提取)
            machine_name = extract_machine_name(name)

            if machine_name not in devices_data:
                devices_data[machine_name] = {'time': time_val}

            # 映射字段名
            field_name = map_mqtt_to_db_field(name, machine_name)
            if field_name:
                devices_data[machine_name][field_name] = value
                # 保留最新的时间
                if time_val > devices_data[machine_name]['time']:
                    devices_data[machine_name]['time'] = time_val

        # 4. 连接数据库并为每个设备插入数据到wincc表
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        inserted_count = 0
        for machine_name, data in devices_data.items():
            try:
                # 提取时间字段
                dt = data.pop('time')
                date_val = dt.date()
                time_val = dt.time()

                # 构建插入SQL (设备编号加上井号)
                fields = ['machine_name', 'date', 'time']
                values = [f"{machine_name}#", date_val, time_val]
                placeholders = ['%s', '%s', '%s']

                # 添加其他字段
                for field_name, value in data.items():
                    fields.append(field_name)
                    values.append(value)
                    placeholders.append('%s')

                insert_sql = f"""
                    INSERT INTO wincc ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                """

                cursor.execute(insert_sql, values)
                inserted_count += 1

                # 记录详细的插入日志
                detail_msg = f"[数据处理] 设备{machine_name}数据已插入,包含{len(data)}个字段"
                with mqtt_lock:
                    mqtt_logs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "level": "成功",
                        "message": detail_msg
                    })

            except Exception as e:
                error_msg = f"[数据处理] 设备{machine_name}数据插入失败: {str(e)}"
                with mqtt_lock:
                    mqtt_logs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "level": "错误",
                        "message": error_msg
                    })

        # 提交事务
        conn.commit()

        success_msg = f"[数据处理] 数据处理完成,共处理{len(temp_data)}条记录,插入{inserted_count}个设备的数据"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": success_msg
            })

    except pymysql.Error as db_error:
        if conn:
            conn.rollback()
        error_msg = f"[数据处理] 数据库错误: {str(db_error)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })
    except Exception as e:
        if conn:
            conn.rollback()
        error_msg = f"[数据处理] 数据处理失败: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def extract_machine_name(mqtt_name: str) -> str:
    """
    从MQTT字段名中提取设备编号
    例如: SYS_T/CM_H -> 1, SYS_T/CM_H_1 -> 2, SYS_T/CM_H_2 -> 3, ... SYS_T/CM_H_14 -> 15
         CELL1 -> 1, CELL1_1 -> 2, CELL1_2 -> 3, ... CELL1_14 -> 15
         1_Type -> 1, 2_Type -> 2, ... 15_Type -> 15
    """
    # 检查是否是 数字_Type 格式
    if '_Type' in mqtt_name:
        parts = mqtt_name.split('_Type')
        if parts[0].isdigit():
            return parts[0]

    # 查找最后一个下划线后的数字
    parts = mqtt_name.split('_')

    # 从后往前查找,找到第一个纯数字部分
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].isdigit():
            device_suffix = int(parts[i])
            # 后缀从1开始对应设备2, 后缀14对应设备15
            return str(device_suffix + 1)

    # 没有数字后缀的是设备1
    return '1'


def map_mqtt_to_db_field(mqtt_name: str, machine_name: str) -> str:
    """
    将MQTT字段名映射到数据库字段名

    参数:
    - mqtt_name: MQTT字段名 (如: SYS_T/CM_H, SYS_T/CM_H_1, CELL1, CELL1_2)
    - machine_name: 设备编号 (如: '1', '2', ...)

    返回:
    - 数据库字段名
    """
    base_name = mqtt_name

    # 检查是否是 数字_Type 格式 (映射到 machine_model)
    if '_Type' in base_name:
        return 'machine_model'

    # 去掉设备编号后缀,获取基础字段名
    if machine_name != '1':
        # 移除 _数字 后缀
        suffix = f"_{int(machine_name) - 1}"
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]

    # 字段映射表 (基于mqtt说明.md)
    field_mapping = {
        'SYS_T/CM_H': 'hours',
        'ELE_I': 'total_current',
        'ELE_V': 'total_voltage',
        'CELL1': 'cell_1',
        'CELL2': 'cell_2',
        'CELL3': 'cell_3',
        'CELL4': 'cell_4',
        'CELL5': 'cell_5',
        'CELL6': 'cell_6',
        'CELL7': 'cell_7',
        'CELL8': 'cell_8',
        'CELL9': 'cell_9',
        'CELL10': 'cell_10',
        'CELL11': 'cell_11',
        'CELL12': 'cell_12',
        'CELL13': 'cell_13',
        'CELL14': 'cell_14',
        'CELL15': 'cell_15',
        'CELL16': 'cell_16',
        'CELL17': 'cell_17',
        'CELL18': 'cell_18',
        'CELL19': 'cell_19',
        'CELL20': 'cell_20',
        'CELL21': 'cell_21',
        'CELL22': 'cell_22',
        'CELL23': 'cell_23',
        'CELL24': 'cell_24',
        'CELL25': 'cell_25',
        'cell_max': 'max_voltage',
        'cell_min': 'min_voltage',
        'cell_ave': 'avg_voltage',
        'cell_range': 'voltage_range',
        'PUMP_P': 'pump_pressure',
        'LCP_OUT': 'pump_opening',
        'FAN_OUT': 'fan_opening',
        'DT118': 'specific_gravity',
        'PT102': 'inlet_pressure',
        'LIT109': 'liquid_level',
        'PT104': 'oxygen_outlet_pressure',
        'PT105': 'hydrogen_outlet_pressure',
        'TT103': 'oxygen_outlet_temp',
        'TT101': 'alkali_inlet_temp',
        'TT106': 'hydrogen_outlet_temp',
        'TT114': 'hydrogen_gas_temp',
        'FIT109': 'alkali_flow_meter',
        'AT132': 'oxygen_in_hydrogen',
        'AT131': 'hydrogen_in_oxygen',
        '当前能耗': 'current_power',
        'ELE_PDT': 'pressure_diff',
        'SEP_PDT': 'sep_pressure_diff',
        '标准差': 'std_deviation',
        '当前产氢量': 'hydrogen_flow_meter'
    }

    return field_mapping.get(base_name, None)


def start_mqtt_client():
    """启动MQTT客户端"""
    global mqtt_client, mqtt_connected

    try:
        # 生成随机的客户端ID，避免重复连接冲突
        random_client_id = f"fastapi_backend_{uuid.uuid4().hex[:8]}"

        # 创建MQTT客户端实例
        mqtt_client = mqtt.Client(client_id=random_client_id)

        startup_msg = f"[MQTT] 使用客户端ID: {random_client_id}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": startup_msg
            })

        # 设置回调函数
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message

        # 连接到MQTT Broker
        connecting_msg = f"[MQTT] 正在连接到 {MQTT_BROKER}:{MQTT_PORT}..."
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": connecting_msg
            })

        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)

        # 在后台线程中运行MQTT客户端循环
        mqtt_client.loop_start()

        started_msg = "[MQTT] MQTT客户端已启动"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": started_msg
            })

    except Exception as e:
        error_msg = f"[MQTT] 启动失败: {str(e)}"
        with mqtt_lock:
            mqtt_connected = False
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def stop_mqtt_client():
    """停止MQTT客户端"""
    global mqtt_client, mqtt_connected, merge_timer

    if mqtt_client:
        try:
            # 取消定时器
            if merge_timer is not None:
                merge_timer.cancel()

            mqtt_client.loop_stop()
            mqtt_client.disconnect()

            stopped_msg = "[MQTT] MQTT客户端已停止"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "信息",
                    "message": stopped_msg
                })
        except Exception as e:
            error_msg = f"[MQTT] 停止MQTT客户端时出错: {str(e)}"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "错误",
                    "message": error_msg
                })
        finally:
            with mqtt_lock:
                mqtt_connected = False


@router.get("/status")
async def get_mqtt_status():
    """
    获取MQTT连接状态

    返回:
    {
        "connected": true/false,
        "broker": "124.222.161.163",
        "port": 1883,
        "topic": "WinCC/#"
    }
    """
    with mqtt_lock:
        return {
            "connected": mqtt_connected,
            "broker": MQTT_BROKER,
            "port": MQTT_PORT,
            "topic": MQTT_TOPIC
        }


@router.get("/logs")
async def get_mqtt_logs():
    """
    获取MQTT日志列表

    返回:
    {
        "logs": [
            {
                "timestamp": "2025-01-24 10:30:45",
                "level": "成功",
                "message": "[MQTT] 成功连接到MQTT Broker: 124.222.161.163:1883"
            },
            ...
        ],
        "total": 5
    }
    """
    with mqtt_lock:
        logs_list = list(mqtt_logs)

    return {
        "logs": logs_list,
        "total": len(logs_list)
    }
