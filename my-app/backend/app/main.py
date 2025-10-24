from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from .charts import router as charts_router
from .auth import router as auth_router
from .home import router as home_router
from .mqtt import router as mqtt_router, start_mqtt_client, stop_mqtt_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[应用] 正在启动...")
    start_mqtt_client()
    yield
    # 关闭时执行
    print("[应用] 正在关闭...")
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
