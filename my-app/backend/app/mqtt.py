import paho.mqtt.client as mqtt
import threading
import uuid
from datetime import datetime, timedelta
from collections import deque
from queue import Queue
from fastapi import APIRouter
from typing import Optional
import json
import pymysql
from dateutil import parser
from config import DB_CONFIG

router = APIRouter()

# MQTT配置
MQTT_BROKER = "124.222.161.163"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 120
MQTT_TOPIC = "WinCC/#"  # 订阅WinCC下的所有主题

# 全局变量
mqtt_client: Optional[mqtt.Client] = None
mqtt_connected = False
mqtt_lock = threading.Lock()
mqtt_logs = deque(maxlen=1000)  # 最多保存2000条日志

# 消息处理队列和工作线程
message_queue = Queue(maxsize=1000)  # 消息队列,最多缓冲1000条消息
processing_threads = []  # 工作线程列表

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
    """MQTT消息接收回调 - 快速接收并放入队列"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        # 非阻塞放入队列
        if not message_queue.full():
            message_queue.put_nowait((topic, payload))
        else:
            # 队列满时记录警告
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "警告",
                    "message": f"[MQTT] 消息队列已满({message_queue.qsize()}/{message_queue.maxsize}),消息被丢弃"
                })

    except Exception as e:
        error_msg = f"[MQTT] 接收消息时出错: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def message_worker():
    """消息处理工作线程 - 从队列中取出消息并处理"""
    global last_message_time, merge_timer

    while True:
        try:
            # 阻塞获取消息
            topic, payload = message_queue.get()

            # 执行耗时的数据清洗和存储
            clean_and_store_data(topic, payload)

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

            # 标记任务完成
            message_queue.task_done()

        except Exception as e:
            error_msg = f"[MQTT] 处理消息时出错: {str(e)}"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "错误",
                    "message": error_msg
                })


def trigger_merge_on_idle():
    """
    消息间隔检测触发合并
    当超过MESSAGE_IDLE_THRESHOLD秒没有新消息时触发
    """
    try:
        with merge_lock:
            # 检查是否真的超过阈值(防止定时器延迟导致的误触发)
            if last_message_time is not None:
                elapsed = (datetime.now() - last_message_time).total_seconds()
                if elapsed >= MESSAGE_IDLE_THRESHOLD:
                    msg = f"[合并] 检测到消息间隔超过{MESSAGE_IDLE_THRESHOLD}秒,触发数据合并"
                    with mqtt_lock:
                        mqtt_logs.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "level": "信息",
                            "message": msg
                        })

                    # 执行数据合并操作
                    merge_data()

    except Exception as e:
        error_msg = f"[合并] 间隔检测触发合并时出错: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def merge_data():
    """
    数据合并函数
    将wincc_temp表中的数据合并到主表
    TODO: 后续实现具体的合并逻辑
    """
    try:
        msg = "[合并] 开始执行数据合并操作..."
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": msg
            })

        # TODO: 这里后续实现具体的合并逻辑
        # 例如:
        # 1. 从wincc_temp读取is_uploaded=0的数据
        # 2. 按照业务规则合并到主表
        # 3. 更新wincc_temp中的is_uploaded标记为1

        success_msg = "[合并] 数据合并操作完成(待实现)"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": success_msg
            })

    except Exception as e:
        error_msg = f"[合并] 数据合并失败: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def clean_and_store_data(topic: str, payload: str):
    """
    数据清洗和存储函数

    参数:
    - topic: MQTT主题
    - payload: 消息内容 (JSON格式: {"time":"2025-10-30T04:37:59.933Z","name":"ELE_I_1","value":0,"qualityCode":128})
    """
    try:
        # 1. 解析JSON格式的payload
        data = json.loads(payload)

        # 提取字段
        name = data.get('name')
        value = data.get('value')
        time_str = data.get('time')

        # 验证必需字段
        if name is None or value is None or time_str is None:
            error_msg = f"[MQTT] 数据缺少必需字段: {payload}"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "警告",
                    "message": error_msg
                })
            return

        # 2. 转换时间格式 (ISO 8601 -> YYYY-MM-DD HH:mm:ss, UTC+0 -> UTC+8)
        # 解析ISO 8601格式时间
        dt = parser.isoparse(time_str)

        # 转换为UTC+8时区
        dt_utc8 = dt + timedelta(hours=8)

        # 格式化为 YYYY-MM-DD HH:mm:ss
        formatted_time = dt_utc8.strftime("%Y-%m-%d %H:%M:%S")

        # 3. 存入数据库
        conn = None
        cursor = None
        try:
            # 连接数据库
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 插入数据
            sql = """
                  INSERT INTO wincc_temp (name, value, time, is_uploaded)
                  VALUES (%s, %s, %s, 0) \
                  """
            cursor.execute(sql, (name, str(value), formatted_time))
            conn.commit()

            # 记录成功日志
            success_msg = f"[MQTT] 数据已存储: name={name}, value={value}, time={formatted_time}"
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "成功",
                    "message": success_msg
                })

        except pymysql.Error as db_error:
            error_msg = f"[MQTT] 数据库错误: {str(db_error)}"
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

    except json.JSONDecodeError as e:
        error_msg = f"[MQTT] JSON解析失败: {payload}, 错误: {str(e)}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })
    except Exception as e:
        error_msg = f"[MQTT] 数据清洗失败: {str(e)}, payload: {payload}"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def start_mqtt_client():
    """启动MQTT客户端"""
    global mqtt_client, mqtt_connected, processing_threads

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

        # 启动3个消息处理工作线程
        num_workers = 3
        for i in range(num_workers):
            worker = threading.Thread(
                target=message_worker,
                daemon=True,
                name=f"MQTT-Worker-{i + 1}"
            )
            worker.start()
            processing_threads.append(worker)

        worker_msg = f"[MQTT] 已启动 {num_workers} 个消息处理工作线程"
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": worker_msg
            })

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
