import uvicorn
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # 使用绝对导入路径
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="asyncio"
    )
