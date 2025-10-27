from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .charts import router as charts_router
from .auth import router as auth_router
from .home import router as home_router
from .mqtt import router as mqtt_router, start_mqtt_client, stop_mqtt_client
from .scrapy import fetch_latest_device_data

# 创建定时调度器
scheduler = BackgroundScheduler()


def scheduled_data_fetch():
    """定时获取并上传设备数据"""
    try:
        print("开始执行定时数据采集任务...")
        result = fetch_latest_device_data(page=1, page_size=90, upload_to_db=True)
        if result.get("upload_result"):
            upload_result = result["upload_result"]
            print(f"定时任务完成 - 总数: {upload_result['total']}, "
                  f"插入: {upload_result['inserted']}, "
                  f"跳过: {upload_result['skipped']}, "
                  f"失败: {upload_result['failed']}")
    except Exception as e:
        print(f"定时任务执行失败: {type(e).__name__} - {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    start_mqtt_client()

    # 启动定时任务调度器
    # 在每小时的0, 10, 20, 30, 40, 50分钟时执行
    scheduler.add_job(
        scheduled_data_fetch,
        trigger=CronTrigger(minute='0,10,20,30,40,50'),
        id='fetch_device_data',
        name='获取设备数据',
        replace_existing=True
    )
    scheduler.start()
    print("定时任务调度器已启动 - 每10分钟在0,10,20,30,40,50分时执行数据采集")

    yield

    # 关闭时执行
    scheduler.shutdown()
    print("定时任务调度器已关闭")
    stop_mqtt_client()


app = FastAPI(title="My FastAPI Backend", lifespan=lifespan)

# 允许跨域访问（生产环境不限制来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024
)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(charts_router, prefix="/api/get")
app.include_router(home_router, prefix="/api/home")
app.include_router(mqtt_router, prefix="/api/mqtt", tags=["MQTT"])