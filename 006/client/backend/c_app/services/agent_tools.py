# FastAPI 后端的基础 URL
import json
import os
from typing import Union, Dict, Optional, List

import requests

BASE_API_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8001")

# --- 工具函数 (调用 FastAPI) ---
# (工具函数 _call_api, get_product_details, search_products, get_order_status,
#  get_active_promotions, get_policy, check_return_eligibility,
#  submit_return_request, log_feedback 保持不变 - 此处省略)
def _call_api(method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Union[Dict, str]:
    """通用 API 调用函数"""
    url = f"{BASE_API_URL}{endpoint}"
    try:
        response = requests.request(method, url, params=params, json=json_data, timeout=15)
        response.raise_for_status() # 如果状态码不是 2xx，则引发 HTTPError
        try:
            return response.json()
        except json.JSONDecodeError:
            if not response.text:
                 return {"status": "success", "message": "操作成功完成，无内容返回。"}
            return response.text
    except requests.exceptions.RequestException as e:
        error_message = f"API 调用失败: {url} - {str(e)}"
        try:
            error_detail = e.response.json() if e.response else str(e)
            error_message += f" | 详情: {error_detail}"
        except:
             error_message += f" | 无法解析错误详情。"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"处理 API 响应时发生未知错误: {url} - {str(e)}"
        print(error_message)
        return error_message

def get_product_details(product_id: int) -> Union[Dict, str]:
    """根据商品 ID 获取商品的详细信息。"""
    print(f"工具调用: get_product_details(product_id={product_id})")
    if not isinstance(product_id, int) or product_id <= 0:
        return "错误：product_id 必须是一个正整数。"
    return _call_api("GET", f"/products/{product_id}")

def search_products(query: str) -> Union[List[Dict], str]:
    """根据关键词搜索商品。"""
    print(f"工具调用: search_products(query='{query}')")
    if not isinstance(query, str) or len(query) < 2:
        return "错误：搜索关键词必须是至少包含2个字符的字符串。"
    return _call_api("GET", "/products/", params={"query": query, "limit": 5})

def get_order_status(order_number: str) -> Union[Dict, str]:
    """根据订单号查询订单状态和物流信息。"""
    print(f"工具调用: get_order_status(order_number='{order_number}')")
    if not isinstance(order_number, str) or not order_number:
        return "错误：订单号不能为空字符串。"
    return _call_api("GET", f"/orders/status/{order_number}")

def cancel_order(order_number: str) -> Union[Dict, str]:
    """
    取消指定订单号的订单。
    只有处于特定状态（如 'pending', 'processing'）的订单才能被取消。
    成功取消后会恢复订单中商品的库存。
    """
    print(f"工具调用: cancel_order(order_number='{order_number}')")
    if not isinstance(order_number, str) or not order_number:
        return "错误：订单号不能为空字符串。"
    return _call_api("POST", f"/orders/{order_number}/cancel")

def get_active_promotions() -> Union[List[Dict], str]:
    """获取当前有效的促销活动。"""
    print("工具调用: get_active_promotions()")
    return _call_api("GET", "/promotions/active")

def get_policy(policy_type: str) -> Union[Dict, str]:
    """获取指定类型的店铺政策。

    参数:
    policy_type (str): 政策类型，如 'return', 'shipping', 'payment', 'privacy', 'terms'。
    """
    print(f"工具调用: get_policy(policy_type='{policy_type}')")
    valid_types = ['return', 'shipping', 'payment', 'privacy', 'terms']
    if policy_type not in valid_types:
        return f"错误：无效的政策类型 '{policy_type}'。有效类型为: {', '.join(valid_types)}"
    return _call_api("GET", f"/policies/{policy_type}")

def check_return_eligibility(order_number: str, product_sku: str) -> Union[Dict, str]:
    """检查商品退货资格。"""
    print(f"工具调用: check_return_eligibility(order_number='{order_number}', product_sku='{product_sku}')")
    if not order_number or not product_sku:
         return "错误：订单号和商品 SKU 不能为空。"
    payload = {"order_number": order_number, "product_sku": product_sku}
    return _call_api("POST", "/returns/check-eligibility", json_data=payload)

MOCK_USER_ID = 1 # 模拟用户 ID

def submit_return_request(order_id: int, product_id: int, reason: str) -> Union[Dict, str]:
    """提交退货请求。"""
    print(f"工具调用: submit_return_request(order_id={order_id}, product_id={product_id}, reason='{reason}')")
    if not all([isinstance(order_id, int), isinstance(product_id, int), isinstance(reason, str)]) or not reason:
        return "错误：订单ID、商品ID必须是整数，原因不能为空。"
    payload = {
        "order_id": order_id,
        "product_id": product_id,
        "reason": reason,
        "user_id": MOCK_USER_ID
    }
    return _call_api("POST", "/returns/", json_data=payload)

def log_feedback(feedback_type: str, content: str, subject: Optional[str] = None, email: Optional[str] = None) -> Union[Dict, str]:
    """记录用户反馈。"""
    print(f"工具调用: log_feedback(feedback_type='{feedback_type}', ...)")
    valid_types = ['complaint', 'suggestion', 'praise']
    if feedback_type not in valid_types:
         return f"错误：无效的反馈类型 '{feedback_type}'。有效类型为: {', '.join(valid_types)}"
    if not content:
        return "错误：反馈内容不能为空。"
    payload = {
        "feedback_type": feedback_type,
        "content": content,
        "subject": subject,
        "email": email,
        "user_id": MOCK_USER_ID
    }
    return _call_api("POST", "/feedback/", json_data=payload)
