from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import secrets

router = APIRouter()
security = HTTPBearer()

# 在内存中存储API密钥（重启服务会重置）
# 生产环境建议使用环境变量或配置文件
API_KEY = "api_key_123456"

# 存储已登录的token（简单的内存缓存）
active_tokens = set()


class LoginRequest(BaseModel):
    api_key: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    登录接口:验证API密钥
    """
    if request.api_key == API_KEY:
        # 生成一个随机token
        token = secrets.token_urlsafe(32)
        active_tokens.add(token)
        return LoginResponse(
            success=True,
            message="登录成功",
            token=token
        )
    else:
        raise HTTPException(status_code=401, detail="API密钥错误")


@router.post("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    验证token是否有效
    """
    token = credentials.credentials
    if token in active_tokens:
        return {"success": True, "message": "Token有效"}
    else:
        raise HTTPException(status_code=401, detail="Token无效或已过期")


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    登出接口:移除token
    """
    token = credentials.credentials
    if token in active_tokens:
        active_tokens.remove(token)
    return {"success": True, "message": "登出成功"}


def verify_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    依赖项:验证请求的token
    """
    token = credentials.credentials
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="未授权：Token无效或已过期")
    return token

