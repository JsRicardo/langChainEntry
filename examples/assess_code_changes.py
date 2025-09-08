"""
代码变更评估示例脚本
演示如何使用AI评估服务来评估代码变更
"""
import os
import sys
import logging
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 初始化日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.ai import create_ai_assessment_service
from src.notification import create_wecom_notification_service
from src.config import init_config


def main():
    """主函数，演示代码变更评估流程"""
    try:
        # 初始化配置
        init_config()
        logger.info("配置初始化完成")
        
        # 创建AI评估服务实例（默认使用DeepSeek模型）
        ai_service = create_ai_assessment_service()
        logger.info("AI评估服务创建成功")
        

        
        # 示例系统上下文信息
        system_context = """
这是一个基于Python的代码变更分析系统，用于自动分析代码变更并生成评估报告。
系统架构包括：
- 代码解析模块：负责解析Git仓库中的代码变更
- AI评估模块：使用大语言模型评估代码变更的影响
- 通知模块：将评估报告通过企业微信发送给相关人员
        """
        
        # 执行代码变更评估
        logger.info("开始评估代码变更")
        assessment_result = ai_service.assess_code_changes(example_code_changes)
        print("\n=== 代码变更评估报告 ===")
        print(assessment_result)
        print("====================\n")
        
        # 执行影响分析
        logger.info("开始分析变更影响")
        impact_result = ai_service.analyze_impact(example_code_changes, system_context)
        print("\n=== 影响分析报告 ===")
        print(impact_result)
        print("================\n")
        
        # 生成综合报告
        logger.info("开始生成综合报告")
        combined_report = ai_service.generate_combined_report(example_code_changes, system_context)
        print("\n=== 综合评估报告 ===")
        print(f"代码变更评估: {combined_report['code_change_assessment'][:100]}...")
        print(f"影响分析: {combined_report['impact_analysis'][:100]}...")
        print("==================\n")
        
        # 尝试创建企业微信通知服务（可选）
        try:
            wecom_service = create_wecom_notification_service()
            
            # 生成Markdown格式的报告
            markdown_report = f"""# 代码变更评估报告

## 变更概述
{assessment_result.split('## 变更概述')[1].split('## 影响范围')[0] if '## 变更概述' in assessment_result else ''}

## 影响分析
{impact_result.split('## 风险等级')[0] if '## 风险等级' in impact_result else ''}

## 风险等级
{impact_result.split('## 风险等级')[1] if '## 风险等级' in impact_result else ''}
"""
            
            # 发送通知（如果配置了Webhook）
            if wecom_service.webhook_url and "your-key" not in wecom_service.webhook_url:
                wecom_service.send_markdown_message(markdown_report)
                logger.info("企业微信通知发送成功")
            else:
                logger.info("企业微信Webhook未配置或使用默认值，跳过发送通知")
        except Exception as e:
            logger.error(f"创建企业微信通知服务失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()