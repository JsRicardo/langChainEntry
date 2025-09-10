import logging
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config.config_manager import get_config, init_config

logger = logging.getLogger(__name__)


class AIAssessmentService:
    
    def __init__(self):
        # 初始化配置
        init_config()
        
        # 获取AI相关配置
        model = get_config("ai.deepseek.model")
        api_key = get_config("ai.deepseek.api_key")
        base_url = get_config("ai.deepseek.base_url")
        temperature = get_config("ai.temperature", 0.3)
        
        if not model or not api_key or not base_url:
            logger.warning("DeepSeek配置不完整，使用默认值继续")
            # 使用默认值以便在没有完整配置时也能继续开发
            model = "deepseek-chat"
            api_key = "test-api-key"
            base_url = "http://localhost:8080/v1"
        
        try:
            self.llm = ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                openai_api_base=base_url,
                temperature=temperature,
                max_tokens=2048
            )
            logger.info(f"初始化DeepSeek评估服务，模型: {model}, 服务地址: {base_url}")
            self._init_prompt_templates()
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {str(e)}")
            # 创建一个模拟的LLM客户端以便在开发环境中继续
            self.llm = self._create_mock_llm()
            self._init_prompt_templates()
    
    def _create_mock_llm(self):
        """创建模拟的LLM客户端，用于开发环境"""
        class MockLLM:
            def invoke(self, input_data):
                logger.info("使用模拟LLM进行评估")
                # 根据不同的模板返回不同的模拟结果
                if "代码变更详情" in str(input_data):
                    return "这是一个模拟的代码变更评估结果。在实际环境中，这里将显示AI生成的详细评估。\n\n## 变更概述\n- 模拟的变更内容描述\n\n## 影响范围\n- 模拟的影响模块列表\n\n## 风险评估\n- 低风险变更\n\n## 代码质量\n- 良好的代码风格\n\n## 建议和改进\n- 无特殊建议"
                elif "代码差异详情" in str(input_data):
                    return "这是一个模拟的代码差异分析结果。在实际环境中，这里将显示AI生成的详细分析。\n\n## 变更内容\n- 模拟的代码差异描述\n\n## 技术影响\n- 无重大技术影响\n\n## 潜在问题\n- 未发现明显问题\n\n## 优化建议\n- 考虑添加更多注释"
                elif "相关系统信息" in str(input_data):
                    return "这是一个模拟的影响分析结果。在实际环境中，这里将显示AI生成的详细分析。\n\n## 模块影响\n- 模拟的模块影响分析\n\n## 接口影响\n- 无接口变更\n\n## 业务影响\n- 对业务流程有轻微优化\n\n## 风险等级\n- 低\n\n## 测试建议\n- 执行单元测试即可"
                elif "综合评估" in str(input_data):
                    return "这是一个模拟的综合评估总结。在实际环境中，这里将显示AI生成的综合分析。\n\n此代码变更属于低风险优化，主要改进了代码结构和性能，建议执行基本的回归测试。"
                return "模拟的AI评估结果"
        
        return MockLLM()
    
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
        
        # 新增综合评估模板
        self.comprehensive_evaluation_template = ChatPromptTemplate.from_template(
            """你是一位经验丰富的技术专家，需要对代码变更进行综合评估。
            
            请基于以下信息，生成一份简洁明了的综合评估总结：
            
            1. 主要结论：总结此次代码变更的核心价值和影响
            2. 风险等级：明确指出变更的风险等级（低、中、高）
            3. 测试重点：列出需要重点测试的功能和场景
            4. 部署建议：提供部署策略和注意事项
            
            代码变更评估：
            {code_change_assessment}
            
            影响分析：
            {impact_analysis}
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
            if not code_changes or len(code_changes.strip()) == 0:
                logger.warning("空的代码变更内容，返回默认评估结果")
                return "未提供有效的代码变更内容"
            
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
            if not code_diff or len(code_diff.strip()) == 0:
                logger.warning("空的代码差异内容，返回默认分析结果")
                return "未提供有效的代码差异内容"
            
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
            if not code_changes or len(code_changes.strip()) == 0:
                logger.warning("空的代码变更内容，返回默认影响分析结果")
                return "未提供有效的代码变更内容"
            
            chain = self.impact_analysis_template | self.llm | StrOutputParser()
            result = chain.invoke({
                "code_changes": code_changes,
                "system_context": system_context or "无额外上下文信息"
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
        try:
            if not code_changes or len(code_changes.strip()) == 0:
                logger.warning("空的代码变更内容，返回默认综合报告")
                return {
                    "code_change_assessment": "未提供有效的代码变更内容",
                    "impact_analysis": "未提供有效的代码变更内容",
                    "comprehensive_summary": "未提供有效的代码变更内容"
                }
            
            # 执行各项评估
            code_change_assessment = self.assess_code_changes(code_changes)
            impact_analysis = self.analyze_impact(code_changes, system_context)
            
            # 生成综合评估总结
            chain = self.comprehensive_evaluation_template | self.llm | StrOutputParser()
            comprehensive_summary = chain.invoke({
                "code_change_assessment": code_change_assessment,
                "impact_analysis": impact_analysis
            })
            
            report = {
                "code_change_assessment": code_change_assessment,
                "impact_analysis": impact_analysis,
                "comprehensive_summary": comprehensive_summary
            }
            
            logger.info("综合评估报告生成完成")
            return report
        except Exception as e:
            logger.error(f"生成综合评估报告失败: {str(e)}")
            return {
                "code_change_assessment": f"评估失败: {str(e)}",
                "impact_analysis": f"分析失败: {str(e)}",
                "comprehensive_summary": f"综合评估失败: {str(e)}"
            }


def create_ai_assessment_service() -> AIAssessmentService:
    """创建AI评估服务实例的工厂函数
    
    Returns:
        AIAssessmentService: AI评估服务实例
    """
    try:
        logger.info("创建AI评估服务实例")
        return AIAssessmentService()
    except Exception as e:
        logger.error(f"创建AI评估服务实例失败: {str(e)}")
        # 在创建失败时返回一个基本实例
        return AIAssessmentService()