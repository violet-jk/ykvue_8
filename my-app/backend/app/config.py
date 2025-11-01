DB_CONFIG = {
    "host": "gz-cdb-bqpsb1r0.sql.tencentcdb.com",
    "port": 21325,
    "user": "root",
    "password": "Yorha213",
    "database": "yk8",
    "charset": "utf8mb4",
}

# MQTT配置
MQTT_CONFIG = {
    "broker": "124.222.161.163",
    "port": 1883,
    "keepalive": 120,
    "topic": "WinCC/#",  # 订阅WinCC下的所有主题
}

# debug 模式
debug = False