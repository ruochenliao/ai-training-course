from autogen_core import CancellationToken, MessageContext, ClosureContext
from fastapi import APIRouter
import asyncio
import logging
from starlette.websockets import WebSocket, WebSocketDisconnect

from c_app.schemas.text2sql import ResponseMessage
from c_app.services.text2sql_service_v2 import Text2SQLService, StreamResponseCollector, QUERY_ANALYZER_NAME, \
    VISUALIZATION_RECOMMENDER_NAME, SQL_EXECUTOR_NAME, SQL_EXPLAINER_NAME, SQL_GENERATOR_NAME

router = APIRouter()

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建一个反馈消息队列
feedback_queue = asyncio.Queue()

@router.websocket("/websocket")
async def text2sql_websocket(websocket: WebSocket):
    """WebSocket端点处理Text2SQL查询

    建立WebSocket连接，接收前端发送的查询请求，并将处理结果实时发送回前端
    """
    try:
        logger.info(f"收到WebSocket连接请求: {websocket.client}，请求头: {websocket.headers}")

        # 记录请求详情以便调试
        origin = websocket.headers.get("origin", "未知")
        logger.info(f"请求来源: {origin}")

        # 接受所有WebSocket连接，不做任何限制
        await websocket.accept()
        logger.info("WebSocket连接已建立成功")

        # 发送一条欢迎消息
        await websocket.send_json({
            "type": "message",
            "source": "系统",
            "content": "WebSocket连接已建立，可以开始查询",
            "region": "process"
        })
        # 循环处理消息
        while True:
            try:
                # 等待接收消息
                data = await websocket.receive_json()
                logger.info(f"收到查询: {data}")

                # 检查是否是反馈消息
                if data.get("is_feedback"):
                    # 如果是反馈消息，放入队列供user_input函数获取
                    await feedback_queue.put(data)
                    logger.info("检测到用户反馈消息，已放入队列")
                    continue  # 跳过普通消息处理流程

                # 检查消息格式
                if "query" not in data:
                    await websocket.send_json({
                        "type": "error",
                        "content": "缺少查询参数'query'"
                    })
                    continue

                # 处理查询
                query_text = data["query"]
                await process_websocket_query(query_text, websocket)
                print("哈哈哈哈")
            except WebSocketDisconnect:
                logger.info("客户端断开连接")
                break
            except Exception as msg_error:
                logger.error(f"处理消息时出错: {str(msg_error)}")
                import traceback
                logger.error(traceback.format_exc())

                # 尝试发送错误消息
                try:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"处理查询时出错: {str(msg_error)}"
                    })
                except:
                    logger.error("无法发送错误响应")
                    break
    except Exception as conn_error:
        logger.error(f"WebSocket连接处理出错: {str(conn_error)}")
        import traceback
        logger.error(traceback.format_exc())
        return

# 处理查询的独立函数，供WebSocket调用
async def process_websocket_query(query: str, websocket: WebSocket):
    """处理Text2SQL查询并通过WebSocket发送结果"""
    try:
        # 创建Text2SQL服务
        service = Text2SQLService()
        collector = StreamResponseCollector()
        # 清空之前的反馈队列
        global feedback_queue
        while not feedback_queue.empty():
            try:
                feedback_queue.get_nowait()
            except:
                pass
        # 设置消息回调函数，将消息发送到WebSocket
        async def message_callback(ctx: ClosureContext, message: ResponseMessage, message_ctx: MessageContext) -> None:
            try:
                # 转换为字典，添加消息类型
                msg_dict = message.model_dump()

                # 根据消息来源确定区域
                region = "process"  # 默认
                if message.source == QUERY_ANALYZER_NAME:
                    region = "analysis"
                elif message.source == SQL_GENERATOR_NAME:
                    region = "sql"
                elif message.source == SQL_EXPLAINER_NAME:
                    region = "explanation"
                elif message.source == SQL_EXECUTOR_NAME:
                    region = "data"
                elif message.source == VISUALIZATION_RECOMMENDER_NAME:
                    region = "visualization"
                elif message.source == "user_proxy":
                    region = "user_proxy"

                msg_dict["region"] = region
                msg_dict["type"] = "message"

                logger.info(f"发送WebSocket消息: {message.source}, {message.content[:50]}...")
                await websocket.send_json(msg_dict)

            except Exception as e:
                logger.error(f"发送WebSocket消息错误: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        async def user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
            # 等待前端发送消息,功能类似 input函数的效果
            # data = await websocket.receive_json()
            # return data
            global feedback_queue
            logger.info(f"等待用户输入: {prompt}")

            # 等待反馈队列中的消息
            data = await feedback_queue.get()
            logger.info(f"收到用户反馈: {data}")
            return data.get("content")


        # 设置收集器回调
        collector.set_callback(message_callback)
        collector.set_user_input(user_input)
        # 发送开始处理的消息
        await websocket.send_json({
            "type": "message",
            "source": "系统",
            "content": f"开始处理查询: {query}",
            "region": "process"
        })

        # 处理查询
        try:
            await service.process_query(query, collector)
            logger.info(f"查询处理完成: {query}")
        except Exception as e:
            logger.error(f"查询处理错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            await websocket.send_json({
                "type": "error",
                "content": f"处理查询时出错: {str(e)}"
            })

    except Exception as e:
        logger.error(f"WebSocket查询处理异常: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"处理查询时发生错误: {str(e)}"
            })
        except:
            pass
