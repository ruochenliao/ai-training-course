from fastapi import APIRouter, Depends
from typing import List

from app.controllers.model import model_controller
from app.core.dependency import DependAuth
from app.schemas import Success, Fail

router = APIRouter()


@router.get("/modelList", summary="获取模型列表")
async def get_model_list():
    """
    获取当前用户的模型列表
    """
    try:
        # 尝试从数据库获取模型列表
        total, models = await model_controller.get_active_models(page_size=100)

        if models:
            # 如果数据库中有模型数据，返回数据库数据
            model_list = []
            for model in models:
                model_dict = await model.to_dict()
                # 转换字段名以匹配前端期望的格式
                formatted_model = {
                    "id": model_dict["id"],
                    "category": model_dict["category"],
                    "modelName": model_dict["model_name"],
                    "modelDescribe": model_dict["model_describe"],
                    "modelPrice": float(model_dict["model_price"]) if model_dict["model_price"] else 0,
                    "modelType": model_dict["model_type"],
                    "modelShow": model_dict["model_show"],
                    "systemPrompt": model_dict["system_prompt"],
                    "apiHost": model_dict["api_host"],
                    "apiKey": model_dict["api_key"],
                    "remark": model_dict["remark"]
                }
                model_list.append(formatted_model)
            return Success(data=model_list)
        else:
            # 如果数据库中没有数据，返回模拟数据
            mock_models = [
                {
                    "id": 1,
                    "category": "对话模型",
                    "modelName": "GPT-3.5-turbo",
                    "modelDescribe": "OpenAI GPT-3.5 Turbo 模型，适用于对话和文本生成",
                    "modelPrice": 0.002,
                    "modelType": "chat",
                    "modelShow": "GPT-3.5",
                    "systemPrompt": "你是一个有用的AI助手。",
                    "apiHost": "https://api.openai.com",
                    "apiKey": "",
                    "remark": "默认对话模型"
                },
                {
                    "id": 2,
                    "category": "对话模型",
                    "modelName": "GPT-4",
                    "modelDescribe": "OpenAI GPT-4 模型，更强大的推理能力",
                    "modelPrice": 0.03,
                    "modelType": "chat",
                    "modelShow": "GPT-4",
                    "systemPrompt": "你是一个专业的AI助手，具有强大的推理和分析能力。",
                    "apiHost": "https://api.openai.com",
                    "apiKey": "",
                    "remark": "高级对话模型"
                },
                {
                    "id": 3,
                    "category": "本地模型",
                    "modelName": "Qwen2-7B-Chat",
                    "modelDescribe": "阿里云通义千问2代7B参数对话模型",
                    "modelPrice": 0.0,
                    "modelType": "chat",
                    "modelShow": "通义千问",
                    "systemPrompt": "你是通义千问，由阿里云开发的AI助手。",
                    "apiHost": "http://localhost:8000",
                    "apiKey": "",
                    "remark": "本地部署模型"
                }
            ]
            return Success(data=mock_models)

    except Exception as e:
        return Fail(msg=f"获取模型列表失败: {str(e)}")
