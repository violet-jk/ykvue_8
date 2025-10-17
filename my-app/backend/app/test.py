from fastapi import APIRouter, Request, Body
from typing import Any, Dict, List, Union
import json
from datetime import datetime

router = APIRouter()

@router.post("/parse")
async def parse_data(request: Request, data: Any = Body(None)):
    """
    接受任意类型的数据并解析输出
    Accept any type of data and parse/output its content
    """
    # 获取原始请求体
    raw_body = await request.body()

    # 解析结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "content_type": request.headers.get("content-type", "unknown"),
        "data_type": type(data).__name__,
        "raw_body_size": len(raw_body),
        "parsed_data": data,
        "analysis": {}
    }

    # 详细分析数据
    if isinstance(data, dict):
        result["analysis"] = {
            "type": "字典/对象",
            "keys": list(data.keys()),
            "key_count": len(data.keys()),
            "structure": {key: type(value).__name__ for key, value in data.items()}
        }
    elif isinstance(data, list):
        result["analysis"] = {
            "type": "列表/数组",
            "length": len(data),
            "item_types": list(set(type(item).__name__ for item in data)),
            "first_items": data[:5] if len(data) > 5 else data
        }
    elif isinstance(data, str):
        result["analysis"] = {
            "type": "字符串",
            "length": len(data),
            "preview": data[:100] if len(data) > 100 else data
        }
    elif isinstance(data, (int, float)):
        result["analysis"] = {
            "type": "数字",
            "value": data,
            "is_integer": isinstance(data, int)
        }
    elif isinstance(data, bool):
        result["analysis"] = {
            "type": "布尔值",
            "value": data
        }
    elif data is None:
        result["analysis"] = {
            "type": "空值",
            "note": "未提供数据或数据为null"
        }
    else:
        result["analysis"] = {
            "type": "其他类型",
            "str_representation": str(data)
        }

    return result


@router.get("/parse-query")
async def parse_query_params(request: Request):
    """
    解析URL查询参数
    Parse URL query parameters
    """
    query_params = dict(request.query_params)

    return {
        "timestamp": datetime.now().isoformat(),
        "query_params": query_params,
        "param_count": len(query_params),
        "analysis": {
            "keys": list(query_params.keys()),
            "structure": {key: type(value).__name__ for key, value in query_params.items()}
        }
    }


@router.post("/parse-form")
async def parse_form_data(request: Request):
    """
    解析表单数据
    Parse form data
    """
    try:
        form_data = await request.form()
        form_dict = {key: value for key, value in form_data.items()}

        return {
            "timestamp": datetime.now().isoformat(),
            "form_data": form_dict,
            "field_count": len(form_dict),
            "analysis": {
                "fields": list(form_dict.keys()),
                "structure": {key: type(value).__name__ for key, value in form_dict.items()}
            }
        }
    except Exception as e:
        return {
            "error": "无法解析表单数据",
            "message": str(e)
        }


@router.post("/parse-json")
async def parse_json_data(data: Dict[str, Any] = Body(...)):
    """
    专门解析JSON数据
    Parse JSON data specifically
    """
    def analyze_structure(obj, depth=0, max_depth=5):
        """递归分析数据结构"""
        if depth > max_depth:
            return "..."

        if isinstance(obj, dict):
            return {key: analyze_structure(value, depth + 1, max_depth) for key, value in obj.items()}
        elif isinstance(obj, list):
            if len(obj) == 0:
                return "[]"
            elif len(obj) <= 3:
                return [analyze_structure(item, depth + 1, max_depth) for item in obj]
            else:
                return f"Array[{len(obj)}] of {type(obj[0]).__name__}"
        else:
            return type(obj).__name__

    return {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "structure": analyze_structure(data),
        "summary": {
            "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
            "data_type": type(data).__name__,
            "json_string": json.dumps(data, ensure_ascii=False, indent=2)
        }
    }


@router.post("/echo")
async def echo_data(request: Request, data: Any = Body(None)):
    """
    回显接收到的所有数据（包括请求头）
    Echo all received data including headers
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "body": data,
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None
        }
    }

