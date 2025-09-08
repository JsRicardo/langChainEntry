import logging
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import get_config

logger = logging.getLogger(__name__)


class AIAssessmentService:
    
    def __init__(self):
        config = get_config()
        ai_config = config.get("ai", {})
        deepseek_config = ai_config.get("deepseek", {})
        
        model = deepseek_config.get("model")
        api_key = deepseek_config.get("api_key")
        base_url = deepseek_config.get("base_url")
        temperature = ai_config.get("temperature", 0.3)
        
        if not model or not api_key or not base_url:
            raise ValueError("DeepSeek配置不完整，请检查config.json中的ai.deepseek配置")
        
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
            max_tokens=2048
        )
        
        logger.info(f"初始化DeepSeek评估服务，模型: {model}, 服务地址: {base_url}")
        self._init_prompt_templates()
    
    def _init_prompt_templates(self):
        self.code_change_template = ChatPromptTemplate.from_template(
            """你是一位经验丰富的代码审查专家，负责评估代码变更的影响。
            
            请分析以下代码变更，并提供详细的评估报告：
            
            1. 变更概述：简要描述此次代码变更的主要内容和目的
            2. 影响范围：分析变更可能影响的功能模块、接口和依赖关系
            3. 风险评估：识别潜在的bug、性能问题或兼容性风险
            4. 代码质量：评估代码的可读性、可维护性和最佳实践遵循情况
            5. 建议和改进：针对发现的问题提供具体的改进建议
            
            代码变更详情：
            {code_changes}
            """
        )
        
        self.code_diff_template = ChatPromptTemplate.from_template(
            """你是一位经验丰富的软件工程师，擅长分析代码差异。
            
            请分析以下代码差异，并提供详细的分析报告：
            
            1. 变更内容：详细解释每个变更点的具体修改
            2. 技术影响：分析变更对系统架构、性能和安全性的影响
            3. 潜在问题：识别可能引入的bug或副作用
            4. 优化建议：提供代码优化和改进建议
            
            代码差异详情：
            {code_diff}
            """
        )
        
        self.impact_analysis_template = ChatPromptTemplate.from_template(
            """你是一位经验丰富的系统架构师，负责评估代码变更的系统性影响。
            
            请对以下代码变更进行全面的影响分析：
            
            1. 模块影响：分析变更对相关模块的影响
            2. 接口影响：评估变更对API接口和调用关系的影响
            3. 业务影响：分析变更对业务流程和功能的影响
            4. 风险等级：评估变更的风险等级（低、中、高）
            5. 测试建议：提供针对性的测试策略和测试用例建议
            
            代码变更详情：
            {code_changes}
            相关系统信息：
            {system_context}
            """
        )
    
    def assess_code_changes(self, code_changes: str) -> str:
        """评估代码变更
        
        Args:
            code_changes: 代码变更内容
        
        Returns:
            str: 评估报告
        """
        try:
            chain = self.code_change_template | self.llm | StrOutputParser()
            result = chain.invoke({"code_changes": code_changes})
            logger.info("代码变更评估完成")
            return result
        except Exception as e:
            logger.error(f"代码变更评估失败: {str(e)}")
            return f"评估失败: {str(e)}"
    
    def analyze_code_diff(self, code_diff: str) -> str:
        """分析代码差异
        
        Args:
            code_diff: 代码差异内容
        
        Returns:
            str: 分析报告
        """
        try:
            chain = self.code_diff_template | self.llm | StrOutputParser()
            result = chain.invoke({"code_diff": code_diff})
            logger.info("代码差异分析完成")
            return result
        except Exception as e:
            logger.error(f"代码差异分析失败: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def analyze_impact(self, code_changes: str, system_context: str = "") -> str:
        """分析代码变更的影响
        
        Args:
            code_changes: 代码变更内容
            system_context: 相关系统上下文信息
        
        Returns:
            str: 影响分析报告
        """
        try:
            chain = self.impact_analysis_template | self.llm | StrOutputParser()
            result = chain.invoke({
                "code_changes": code_changes,
                "system_context": system_context
            })
            logger.info("影响分析完成")
            return result
        except Exception as e:
            logger.error(f"影响分析失败: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def generate_combined_report(self, code_changes: str, system_context: str = "") -> Dict[str, str]:
        """生成综合评估报告
        
        Args:
            code_changes: 代码变更内容
            system_context: 相关系统上下文信息
        
        Returns:
            Dict[str, str]: 包含各项评估结果的综合报告
        """
        report = {
            "code_change_assessment": self.assess_code_changes(code_changes),
            "impact_analysis": self.analyze_impact(code_changes, system_context)
        }
        return report


def create_ai_assessment_service() -> AIAssessmentService:
    """创建AI评估服务实例的工厂函数
    
    Returns:
        AIAssessmentService: AI评估服务实例
    """
    return AIAssessmentService()