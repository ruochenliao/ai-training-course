"""
模型管理API
基于ModelScope的Qwen嵌入模型和重排模型管理接口
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from ....config.vector_db_config import model_manager, vector_db_config
from ....schemas.knowledge import ModelDownloadRequest
from ....utils.model_downloader import get_model_downloader

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get("/status", response_model=Dict[str, Any])
async def get_models_status(
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    获取模型状态
    
    返回嵌入模型和重排模型的下载状态、缓存信息等。
    """
    try:
        logger.info("获取模型状态")
        
        # 获取模型下载器
        downloader = get_model_downloader()
        
        # 获取模型信息
        model_info = downloader.get_model_info()
        
        # 获取模型管理器状态
        embedding_model_loaded = model_manager._embedding_model is not None
        reranker_model_loaded = model_manager._reranker_model is not None
        
        # 构建响应数据
        status_data = {
            "cache_directory": model_info["cache_dir"],
            "models": model_info["models"],
            "runtime_status": {
                "embedding_model_loaded": embedding_model_loaded,
                "reranker_model_loaded": reranker_model_loaded,
                "use_reranker": vector_db_config.USE_RERANKER
            },
            "configuration": {
                "embedding_model_name": vector_db_config.EMBEDDING_MODEL_NAME,
                "reranker_model_name": vector_db_config.RERANKER_MODEL_NAME,
                "use_local_embedding": vector_db_config.USE_LOCAL_EMBEDDING,
                "use_local_reranker": vector_db_config.USE_LOCAL_RERANKER
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "获取模型状态成功",
                "data": status_data
            }
        )
        
    except Exception as e:
        logger.error(f"获取模型状态错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取模型状态失败")


@router.post("/download", response_model=Dict[str, Any])
async def download_model(
    request: ModelDownloadRequest,
    background_tasks: BackgroundTasks,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    下载模型
    
    从ModelScope下载指定的嵌入模型或重排模型。
    支持后台下载，避免阻塞API响应。
    """
    try:
        if request.model_type not in ["embedding", "reranker", "all"]:
            raise HTTPException(
                status_code=400, 
                detail="模型类型必须是 'embedding'、'reranker' 或 'all'"
            )
        
        logger.info(f"开始下载模型 - 类型: {request.model_type}, 强制下载: {request.force_download}")
        
        # 获取模型下载器
        downloader = get_model_downloader()
        
        if request.model_type == "all":
            # 下载所有模型
            background_tasks.add_task(
                _download_all_models_background,
                downloader,
                request.force_download
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": "模型下载任务已启动（后台执行）",
                    "data": {
                        "model_type": "all",
                        "force_download": request.force_download,
                        "status": "downloading"
                    }
                }
            )
        else:
            # 下载单个模型
            background_tasks.add_task(
                _download_single_model_background,
                downloader,
                request.model_type,
                request.force_download
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "success": True,
                    "message": f"{request.model_type}模型下载任务已启动（后台执行）",
                    "data": {
                        "model_type": request.model_type,
                        "force_download": request.force_download,
                        "status": "downloading"
                    }
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载模型错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="下载模型失败")


@router.post("/validate", response_model=Dict[str, Any])
async def validate_models(
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    验证模型
    
    验证已下载的模型是否可以正常加载和使用。
    """
    try:
        logger.info("开始验证模型")
        
        validation_results = {
            "embedding_model": {"status": "unknown", "message": ""},
            "reranker_model": {"status": "unknown", "message": ""}
        }
        
        # 验证嵌入模型
        try:
            embedding_model = model_manager.get_embedding_model()
            if embedding_model is not None:
                # 测试嵌入功能
                test_text = "这是一个测试文本"
                embedding = embedding_model.encode(test_text)
                if embedding is not None and len(embedding) > 0:
                    validation_results["embedding_model"] = {
                        "status": "valid",
                        "dimension": len(embedding),
                        "message": "嵌入模型验证成功"
                    }
                else:
                    validation_results["embedding_model"] = {
                        "status": "invalid",
                        "message": "嵌入模型无法生成有效向量"
                    }
            else:
                validation_results["embedding_model"] = {
                    "status": "not_loaded",
                    "message": "嵌入模型未加载"
                }
        except Exception as e:
            validation_results["embedding_model"] = {
                "status": "error",
                "message": f"嵌入模型验证失败: {str(e)}"
            }
        
        # 验证重排模型
        try:
            if vector_db_config.USE_RERANKER:
                reranker_model = model_manager.get_reranker_model()
                if reranker_model is not None:
                    # 测试重排功能
                    test_pairs = [("测试查询", "测试文档")]
                    scores = reranker_model.predict(test_pairs)
                    if scores is not None and len(scores) > 0:
                        validation_results["reranker_model"] = {
                            "status": "valid",
                            "message": "重排模型验证成功"
                        }
                    else:
                        validation_results["reranker_model"] = {
                            "status": "invalid",
                            "message": "重排模型无法生成有效分数"
                        }
                else:
                    validation_results["reranker_model"] = {
                        "status": "not_loaded",
                        "message": "重排模型未加载"
                    }
            else:
                validation_results["reranker_model"] = {
                    "status": "disabled",
                    "message": "重排模型已禁用"
                }
        except Exception as e:
            validation_results["reranker_model"] = {
                "status": "error",
                "message": f"重排模型验证失败: {str(e)}"
            }
        
        # 判断整体状态
        overall_status = "healthy"
        if validation_results["embedding_model"]["status"] not in ["valid"]:
            overall_status = "degraded"
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "模型验证完成",
                "data": {
                    "overall_status": overall_status,
                    "validation_results": validation_results
                }
            }
        )
        
    except Exception as e:
        logger.error(f"验证模型错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="验证模型失败")


@router.delete("/cache", response_model=Dict[str, Any])
async def clear_model_cache(
    model_type: Optional[str] = None,
    token: Optional[str] = Depends(security)
) -> JSONResponse:
    """
    清理模型缓存
    
    清理指定模型的缓存文件，释放磁盘空间。
    """
    try:
        logger.info(f"清理模型缓存 - 类型: {model_type or 'all'}")
        
        # 获取模型下载器
        downloader = get_model_downloader()
        
        # 清理缓存
        downloader.clear_cache(model_type)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"模型缓存清理成功 - {model_type or 'all'}",
                "data": {
                    "cleared_model_type": model_type or "all",
                    "cleared_at": "now"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"清理模型缓存错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="清理模型缓存失败")


async def _download_single_model_background(downloader, model_type: str, force_download: bool):
    """后台下载单个模型"""
    try:
        logger.info(f"后台下载模型开始 - 类型: {model_type}")
        model_path = await downloader.download_model_async(model_type, force_download)
        logger.info(f"后台下载模型完成 - 类型: {model_type}, 路径: {model_path}")
    except Exception as e:
        logger.error(f"后台下载模型失败 - 类型: {model_type}, 错误: {e}")


async def _download_all_models_background(downloader, force_download: bool):
    """后台下载所有模型"""
    try:
        logger.info("后台下载所有模型开始")
        results = await downloader.download_all_models_async(force_download)
        logger.info(f"后台下载所有模型完成 - 结果: {results}")
    except Exception as e:
        logger.error(f"后台下载所有模型失败 - 错误: {e}")
