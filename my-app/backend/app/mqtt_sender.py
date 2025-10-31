"""
MQTT模拟数据发送工具
根据wincc_table.sql建表语句生成15个设备的模拟数据并通过MQTT发送
每10分钟定时发送一次
"""
import json
import time
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import sys
import os
# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MQTT_CONFIG

# MQTT配置
MQTT_BROKER = MQTT_CONFIG["broker"]
MQTT_PORT = MQTT_CONFIG["port"]
MQTT_KEEPALIVE = 60  # 发送工具使用较短的keepalive

# 发送配置
TOTAL_SEND_TIME = 5  # 总发送时间(秒)
SEND_INTERVAL_MINUTES = 5  # 定时发送间隔(分钟)
NUM_DEVICES = 15  # 设备数量

# 统计信息
send_stats = {
    'total': 0,
    'success': 0,
    'failed': 0
}

# 数据库字段到MQTT字段名的映射 (根据mqtt.py中的map_mqtt_to_db_field反向映射)
DB_TO_MQTT_MAPPING = {
    'hours': 'SYS_T/CM_H',
    'total_current': 'ELE_I',
    'total_voltage': 'ELE_V',
    'cell_1': 'CELL1',
    'cell_2': 'CELL2',
    'cell_3': 'CELL3',
    'cell_4': 'CELL4',
    'cell_5': 'CELL5',
    'cell_6': 'CELL6',
    'cell_7': 'CELL7',
    'cell_8': 'CELL8',
    'cell_9': 'CELL9',
    'cell_10': 'CELL10',
    'cell_11': 'CELL11',
    'cell_12': 'CELL12',
    'cell_13': 'CELL13',
    'cell_14': 'CELL14',
    'cell_15': 'CELL15',
    'cell_16': 'CELL16',
    'cell_17': 'CELL17',
    'cell_18': 'CELL18',
    'cell_19': 'CELL19',
    'cell_20': 'CELL20',
    'cell_21': 'CELL21',
    'cell_22': 'CELL22',
    'cell_23': 'CELL23',
    'cell_24': 'CELL24',
    'cell_25': 'CELL25',
    'max_voltage': 'cell_max',
    'min_voltage': 'cell_min',
    'avg_voltage': 'cell_ave',
    'voltage_range': 'cell_range',
    'pump_pressure': 'PUMP_P',
    'pump_opening': 'LCP_OUT',
    'fan_opening': 'FAN_OUT',
    'specific_gravity': 'DT118',
    'inlet_pressure': 'PT102',
    'liquid_level': 'LIT109',
    'oxygen_outlet_pressure': 'PT104',
    'hydrogen_outlet_pressure': 'PT105',
    'oxygen_outlet_temp': 'TT103',
    'alkali_inlet_temp': 'TT101',
    'hydrogen_outlet_temp': 'TT106',
    'hydrogen_gas_temp': 'TT114',
    'hydrogen_flow_meter': 'FIT109',
    'oxygen_in_hydrogen': 'AT132',
    'hydrogen_in_oxygen': 'AT131',
    'current_power': '当前能耗',
    'pressure_diff': 'ELE_PDT',
    'sep_pressure_diff': 'SEP_PDT',
    'std_deviation': '标准差',
}



def generate_random_value(field_name, data_type):
    """
    根据字段名和数据类型生成随机值
    
    参数:
    - field_name: 数据库字段名
    - data_type: 数据类型 ('INT', 'DECIMAL', 等)
    
    返回:
    - 随机生成的值
    """
    # INT类型字段
    if data_type == 'INT':
        if field_name == 'hours':
            return random.randint(1000, 50000)  # 运行小时数
        elif 'cell_' in field_name:
            return random.randint(1800, 2200)  # 小室电压 (mV)
        elif field_name in ['max_voltage', 'min_voltage', 'voltage_range']:
            return random.randint(1800, 2200)  # 电压统计 (mV)
        elif field_name in ['oxygen_in_hydrogen', 'hydrogen_in_oxygen']:
            return random.randint(0, 100)  # 气体含量 (ppm)
        else:
            return random.randint(0, 1000)
    
    # DECIMAL(10,1) - 总电流、总电压、平均电压
    elif data_type == 'DECIMAL_1':
        if field_name == 'total_current':
            return round(random.uniform(800.0, 1200.0), 1)  # 总电流 (A)
        elif field_name == 'total_voltage':
            return round(random.uniform(400.0, 600.0), 1)  # 总电压 (V)
        elif field_name == 'avg_voltage':
            return round(random.uniform(1900.0, 2100.0), 1)  # 平均电压 (mV)
        else:
            return round(random.uniform(0.0, 100.0), 1)
    
    # DECIMAL(10,2) - 开度、温度、液位
    elif data_type == 'DECIMAL_2':
        if field_name in ['pump_opening', 'fan_opening']:
            return round(random.uniform(30.0, 70.0), 2)  # 开度 (Hz)
        elif field_name == 'liquid_level':
            return round(random.uniform(500.0, 800.0), 2)  # 液位 (mm)
        elif 'temp' in field_name:
            return round(random.uniform(70.0, 90.0), 2)  # 温度 (℃)
        else:
            return round(random.uniform(0.0, 100.0), 2)
    
    # DECIMAL(10,4) - 压力、比重、流量、能耗、标准差
    elif data_type == 'DECIMAL_4':
        if 'pressure' in field_name:
            return round(random.uniform(0.1, 3.0), 4)  # 压力 (MPa)
        elif field_name == 'specific_gravity':
            return round(random.uniform(1.25, 1.35), 4)  # 比重 (mg/cm³)
        elif field_name == 'hydrogen_flow_meter':
            return round(random.uniform(50.0, 150.0), 4)  # 流量
        elif field_name == 'current_power':
            return round(random.uniform(400.0, 600.0), 4)  # 能耗
        elif field_name == 'std_deviation':
            return round(random.uniform(5.0, 20.0), 4)  # 标准差
        else:
            return round(random.uniform(0.0, 10.0), 4)
    
    return 0


def generate_device_data(device_num):
    """
    为单个设备生成所有字段的数据
    
    参数:
    - device_num: 设备编号 (1-15)
    
    返回:
    - 消息列表 [(topic, payload), ...]
    """
    messages = []
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    # 字段定义: (db_field_name, data_type)
    fields = [
        ('hours', 'INT'),
        ('total_current', 'DECIMAL_1'),
        ('total_voltage', 'DECIMAL_1'),
        ('cell_1', 'INT'),
        ('cell_2', 'INT'),
        ('cell_3', 'INT'),
        ('cell_4', 'INT'),
        ('cell_5', 'INT'),
        ('cell_6', 'INT'),
        ('cell_7', 'INT'),
        ('cell_8', 'INT'),
        ('cell_9', 'INT'),
        ('cell_10', 'INT'),
        ('cell_11', 'INT'),
        ('cell_12', 'INT'),
        ('cell_13', 'INT'),
        ('cell_14', 'INT'),
        ('cell_15', 'INT'),
        ('cell_16', 'INT'),
        ('cell_17', 'INT'),
        ('cell_18', 'INT'),
        ('cell_19', 'INT'),
        ('cell_20', 'INT'),
        ('cell_21', 'INT'),
        ('cell_22', 'INT'),
        ('cell_23', 'INT'),
        ('cell_24', 'INT'),
        ('cell_25', 'INT'),
        ('max_voltage', 'INT'),
        ('min_voltage', 'INT'),
        ('avg_voltage', 'DECIMAL_1'),
        ('voltage_range', 'INT'),
        ('std_deviation', 'DECIMAL_4'),
        ('pump_pressure', 'DECIMAL_4'),
        ('pump_opening', 'DECIMAL_2'),
        ('fan_opening', 'DECIMAL_2'),
        ('specific_gravity', 'DECIMAL_4'),
        ('liquid_level', 'DECIMAL_2'),
        ('inlet_pressure', 'DECIMAL_4'),
        ('oxygen_outlet_pressure', 'DECIMAL_4'),
        ('hydrogen_outlet_pressure', 'DECIMAL_4'),
        ('pressure_diff', 'DECIMAL_4'),
        ('sep_pressure_diff', 'DECIMAL_4'),
        ('alkali_inlet_temp', 'DECIMAL_2'),
        ('oxygen_outlet_temp', 'DECIMAL_2'),
        ('hydrogen_outlet_temp', 'DECIMAL_2'),
        ('hydrogen_gas_temp', 'DECIMAL_2'),
        ('hydrogen_flow_meter', 'DECIMAL_4'),
        ('oxygen_in_hydrogen', 'INT'),
        ('hydrogen_in_oxygen', 'INT'),
        ('current_power', 'DECIMAL_4'),
    ]
    
    for db_field, data_type in fields:
        # 获取MQTT字段名
        mqtt_field = DB_TO_MQTT_MAPPING.get(db_field)
        if not mqtt_field:
            continue
        
        # 添加设备编号后缀 (1号设备不加后缀, 2号设备加_1, 3号设备加_2, 以此类推)
        if device_num == 1:
            mqtt_name = mqtt_field
        else:
            mqtt_name = f"{mqtt_field}_{device_num - 1}"
        
        # 生成随机值
        value = generate_random_value(db_field, data_type)
        
        # 构建payload
        payload = {
            "name": mqtt_name,
            "value": value,
            "qualityCode": 128,
            "time": current_time
        }
        
        # 构建topic
        topic = f"WinCC/AEM_SYS/{mqtt_name}"
        
        messages.append((topic, payload))
    
    return messages


def generate_all_devices_data():
    """
    生成所有15个设备的数据
    
    返回:
    - 所有消息列表 [(topic, payload), ...]
    """
    all_messages = []
    
    for device_num in range(1, NUM_DEVICES + 1):
        device_messages = generate_device_data(device_num)
        all_messages.extend(device_messages)
    
    return all_messages


def save_messages_to_file(messages, filename='mqtt_data.txt'):
    """
    将消息数据保存到txt文件（追加模式）
    
    参数:
    - messages: [(topic, payload), ...] 消息列表
    - filename: 保存的文件名
    """
    total_messages = len(messages)
    if total_messages == 0:
        print("[警告] 没有消息需要保存")
        return
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            # 写入时间戳
            f.write(f"\n{'='*80}\n")
            f.write(f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            
            # 按设备分组保存
            for device_num in range(1, NUM_DEVICES + 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"设备 {device_num} 的数据:\n")
                f.write(f"{'='*80}\n\n")
                
                # 获取该设备的消息
                start_idx = (device_num - 1) * 51
                end_idx = start_idx + 51
                device_msgs = messages[start_idx:end_idx]
                
                # 保存所有payload
                for i, (topic, payload) in enumerate(device_msgs):
                    f.write(f"{json.dumps(payload, ensure_ascii=False)}\n")
                
                f.write("\n")
        
    except Exception as e:
        print(f"[错误] 保存文件失败: {e}")


def send_message(client, topic, payload, index, total):
    """
    发送单条MQTT消息
    """
    try:
        # 转换payload为JSON字符串
        payload_str = json.dumps(payload, ensure_ascii=False)
        
        # 发布消息
        result = client.publish(topic, payload_str, qos=0)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            send_stats['success'] += 1
            return True
        else:
            send_stats['failed'] += 1
            return False
    
    except Exception as e:
        send_stats['failed'] += 1
        return False


def send_messages_to_mqtt(messages, send_time=5):
    """
    使用单线程顺序发送所有消息到MQTT
    
    参数:
    - messages: [(topic, payload), ...] 消息列表
    - send_time: 总发送时间(秒)
    """
    total_messages = len(messages)
    if total_messages == 0:
        return
    
    # 初始化统计
    send_stats['total'] = total_messages
    send_stats['success'] = 0
    send_stats['failed'] = 0
    
    # 创建MQTT客户端
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=f"mock_sender_{int(time.time())}"
    )
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        client.loop_start()
    except Exception as e:
        print(f"[错误] 连接失败: {e}")
        return
    
    # 计算每条消息的发送延迟
    delay_per_message = send_time / total_messages if total_messages > 0 else 0
    
    start_time = time.time()
    
    # 顺序发送消息
    for index, (topic, payload) in enumerate(messages):
        # 计算应该在什么时间发送这条消息
        target_time = start_time + (index * delay_per_message)
        current_time = time.time()
        
        # 如果还没到发送时间,等待
        if current_time < target_time:
            time.sleep(target_time - current_time)
        
        # 发送消息
        send_message(client, topic, payload, index, total_messages)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 停止客户端
    try:
        client.loop_stop()
        client.disconnect()
    except:
        pass


def send_once():
    """执行一次完整的发送流程"""
    send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 生成所有设备的数据
    messages = generate_all_devices_data()
    
    if not messages:
        return
    
    # 保存数据到文件
    save_messages_to_file(messages, 'mqtt_data.txt')
    
    # 发送消息到MQTT
    send_messages_to_mqtt(messages, TOTAL_SEND_TIME)
    
    # 输出简化日志
    print(f"[{send_time}] 发送完成 - 数据量: {len(messages)} 条")


def main():
    """主函数 - 定时发送模式"""
    print(f"MQTT模拟数据发送工具已启动 - 间隔{SEND_INTERVAL_MINUTES}分钟\n")
    
    # 立即执行第一次发送
    send_once()
    
    # 持续运行定时任务
    try:
        while True:
            # 等待指定的分钟数
            time.sleep(SEND_INTERVAL_MINUTES * 60)
            send_once()
    except KeyboardInterrupt:
        print("\n程序已停止")


if __name__ == "__main__":
    main()

