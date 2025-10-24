import paho.mqtt.client as mqtt
import threading
import uuid
from datetime import datetime
from collections import deque
from fastapi import APIRouter
from typing import Optional

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
mqtt_logs = deque(maxlen=100)  # 最多保存100条日志


def on_connect(client, userdata, flags, rc):
    """MQTT连接成功回调"""
    global mqtt_connected
    if rc == 0:
        msg = f"[MQTT] 成功连接到MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}"
        print(msg)
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
        print(subscribe_msg)
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": subscribe_msg
            })
    else:
        msg = f"[MQTT] 连接失败，返回码: {rc}"
        print(msg)
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
        print(msg)
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "警告",
                "message": msg
            })
    else:
        msg = "[MQTT] 正常断开连接"
        print(msg)
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": msg
            })


def on_message(client, userdata, msg):
    """MQTT消息接收回调"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        # 限制日志消息长度
        log_payload = payload[:100] if len(payload) > 100 else payload
        message_msg = f"[MQTT] 收到消息 - 主题: {topic}, 数据: {log_payload}"

        print(message_msg)

        # 记录日志
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "信息",
                "message": message_msg
            })

        # TODO: 这里添加数据清洗逻辑
        # clean_and_store_data(topic, payload)

    except Exception as e:
        error_msg = f"[MQTT] 处理消息时出错: {str(e)}"
        print(error_msg)
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def clean_and_store_data(topic: str, payload: str):
    """
    数据清洗和存储函数
    TODO: 实现数据清洗逻辑

    参数:
    - topic: MQTT主题
    - payload: 消息内容
    """
    pass


def start_mqtt_client():
    """启动MQTT客户端"""
    global mqtt_client, mqtt_connected

    try:
        # 生成随机的客户端ID，避免重复连接冲突
        random_client_id = f"fastapi_backend_{uuid.uuid4().hex[:8]}"

        # 创建MQTT客户端实例
        mqtt_client = mqtt.Client(client_id=random_client_id)

        startup_msg = f"[MQTT] 使用客户端ID: {random_client_id}"
        print(startup_msg)
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
        print(connecting_msg)
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
        print(started_msg)
        with mqtt_lock:
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "成功",
                "message": started_msg
            })

    except Exception as e:
        error_msg = f"[MQTT] 启动失败: {str(e)}"
        print(error_msg)
        with mqtt_lock:
            mqtt_connected = False
            mqtt_logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "错误",
                "message": error_msg
            })


def stop_mqtt_client():
    """停止MQTT客户端"""
    global mqtt_client, mqtt_connected

    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

            stopped_msg = "[MQTT] MQTT客户端已停止"
            print(stopped_msg)
            with mqtt_lock:
                mqtt_logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "信息",
                    "message": stopped_msg
                })
        except Exception as e:
            error_msg = f"[MQTT] 停止MQTT客户端时出错: {str(e)}"
            print(error_msg)
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


