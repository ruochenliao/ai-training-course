"""
智能体工具类
"""
from typing import List, Dict, Any, Optional
from app.config.autogen_config import (
    AGENT_CONFIGS,
    COLLABORATION_MODES,
    TASK_AGENT_MAPPING,
    COLLABORATIVE_TASK_MAPPING
)


class AgentManager:
    """智能体管理器"""
    
    @staticmethod
    def get_available_agents() -> List[Dict[str, Any]]:
        """获取所有可用的智能体信息"""
        agents = []
        for agent_key, config in AGENT_CONFIGS.items():
            agents.append({
                "key": agent_key,
                "name": config["name"],
                "description": config["system_message"][:100] + "...",
                "temperature": config.get("temperature", 0.7),
                "max_replies": config.get("max_consecutive_auto_reply", 3)
            })
        return agents
    
    @staticmethod
    def get_collaboration_modes() -> List[Dict[str, Any]]:
        """获取所有协作模式"""
        modes = []
        for mode_key, config in COLLABORATION_MODES.items():
            modes.append({
                "key": mode_key,
                "description": config["description"],
                "agents": config["agents"],
                "max_rounds": config["max_rounds"]
            })
        return modes
    
    @staticmethod
    def get_agent_for_task(task_type: str) -> Optional[str]:
        """根据任务类型获取智能体键"""
        return TASK_AGENT_MAPPING.get(task_type)
    
    @staticmethod
    def get_collaboration_for_task(task_type: str) -> Optional[str]:
        """根据任务类型获取协作模式键"""
        return COLLABORATIVE_TASK_MAPPING.get(task_type)
    
    @staticmethod
    def validate_agent_combination(agents: List[str]) -> bool:
        """验证智能体组合是否有效"""
        available_agents = set(AGENT_CONFIGS.keys())
        requested_agents = set(agents)
        return requested_agents.issubset(available_agents)
    
    @staticmethod
    def get_recommended_agents_for_task(task_description: str) -> List[str]:
        """根据任务描述推荐智能体组合"""
        task_lower = task_description.lower()
        
        # 基于关键词推荐智能体
        recommendations = []
        
        if any(keyword in task_lower for keyword in ["写作", "创作", "文章", "内容"]):
            recommendations.append("writer")
        
        if any(keyword in task_lower for keyword in ["润色", "改进", "优化", "修改"]):
            recommendations.append("polisher")
        
        if any(keyword in task_lower for keyword in ["大纲", "结构", "框架", "规划"]):
            recommendations.append("outliner")
        
        if any(keyword in task_lower for keyword in ["研究", "分析", "调查", "资料"]):
            recommendations.append("researcher")
        
        if any(keyword in task_lower for keyword in ["评审", "检查", "评估", "反馈"]):
            recommendations.append("reviewer")
        
        if any(keyword in task_lower for keyword in ["创意", "创新", "想象", "故事"]):
            recommendations.append("creative")
        
        # 如果没有匹配到特定智能体，返回默认组合
        if not recommendations:
            recommendations = ["writer", "reviewer"]
        
        # 确保至少有一个智能体
        if len(recommendations) == 1 and recommendations[0] != "reviewer":
            recommendations.append("reviewer")
        
        return recommendations[:4]  # 最多推荐4个智能体
    
    @staticmethod
    def get_task_complexity_score(prompt: str, context: Optional[str] = None) -> int:
        """评估任务复杂度（1-5分）"""
        score = 1
        
        # 基于提示长度
        prompt_length = len(prompt)
        if prompt_length > 500:
            score += 2
        elif prompt_length > 200:
            score += 1
        
        # 基于上下文
        if context and len(context) > 1000:
            score += 1
        
        # 基于关键词复杂度
        complex_keywords = [
            "分析", "研究", "深入", "全面", "详细", "专业", 
            "多角度", "系统性", "综合", "对比", "评估"
        ]
        
        for keyword in complex_keywords:
            if keyword in prompt:
                score += 0.5
        
        return min(int(score), 5)
    
    @staticmethod
    def suggest_collaboration_strategy(
        task_type: str, 
        complexity_score: int,
        prompt: str
    ) -> Dict[str, Any]:
        """建议协作策略"""
        
        # 根据复杂度选择协作模式
        if complexity_score >= 4:
            mode = "full_collaboration"
        elif complexity_score >= 3:
            if "创意" in prompt or "故事" in prompt:
                mode = "creative_writing"
            elif "研究" in prompt or "分析" in prompt:
                mode = "research_writing"
            else:
                mode = "writing"
        else:
            if task_type == "ai_polish":
                mode = "polish_review"
            else:
                mode = "writing"
        
        mode_config = COLLABORATION_MODES.get(mode, COLLABORATION_MODES["writing"])
        
        return {
            "mode": mode,
            "agents": mode_config["agents"],
            "max_rounds": mode_config["max_rounds"],
            "description": mode_config["description"],
            "estimated_time": complexity_score * 30,  # 估算时间（秒）
            "complexity": complexity_score
        }


# 全局智能体管理器实例
agent_manager = AgentManager()
