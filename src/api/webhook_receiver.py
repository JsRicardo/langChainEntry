import json
import logging
import os
import json
from typing import Dict, Any, List, Tuple, Optional

from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse

from src.config import get_config
from src.ai import create_ai_assessment_service
from src.notification import create_wecom_notification_service
from src.utils.dependency_analyzer import DependencyAnalyzer
from src.utils.change_impact_analyzer import ChangeImpactAnalyzer

logger = logging.getLogger(__name__)

app = FastAPI(title="代码变更分析系统", description="接收GitLab Webhook并分析代码变更")

ALLOWED_BRANCHES = get_config("webhook.allowed_branches", ["main", "master", "develop"])
logger.info(f"允许的分支: {ALLOWED_BRANCHES}")

GITLAB_WEBHOOK_TOKEN = get_config("webhook.gitlab_token")

DEPENDENCY_ANALYSIS_CONFIG = get_config("dependency_analysis", {})
DEPENDENCY_ANALYSIS_ENABLED = get_config("dependency_analysis.enabled", True)
MAX_AFFECTED_FILES = get_config("dependency_analysis.max_affected_files", 50)
MAX_CRITICAL_PATHS = get_config("dependency_analysis.max_critical_paths", 10)

logger.info(f"依赖分析功能已{'启用' if DEPENDENCY_ANALYSIS_ENABLED else '禁用'}")


# 支持两个端点路径以兼容不同的客户端调用
@app.post("/api/webhook/gitlab")
async def gitlab_webhook(
    request: Request, x_gitlab_token: str = Header(None, alias="X-Gitlab-Token")
):
    """处理GitLab Webhook事件

    接收GitLab的代码提交事件，验证token，检查分支，然后分析代码变更
    """
    try:
        if GITLAB_WEBHOOK_TOKEN and x_gitlab_token != GITLAB_WEBHOOK_TOKEN:
            logger.warning("GitLab Webhook token验证失败")
            raise HTTPException(status_code=403, detail="Token验证失败")

        payload = await request.json()
        logger.info(f"接收到GitLab Webhook事件: {payload.get('event_name')}")

        event_name = payload.get("event_name")
        if event_name != "push":
            logger.info(f"忽略非push事件: {event_name}")
            return JSONResponse(
                content={"status": "success", "message": "忽略非push事件"}
            )

        ref = payload.get("ref")  # 格式: refs/heads/branch_name
        if not ref:
            logger.warning("未找到分支信息")
            raise HTTPException(status_code=400, detail="未找到分支信息")

        branch_name = ref.split("/")[-1]
        if branch_name not in ALLOWED_BRANCHES:
            logger.info(f"忽略不允许的分支: {branch_name}")
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"忽略不允许的分支: {branch_name}",
                }
            )

        # 提取提交信息
        commit_info = extract_commit_info(payload)
        logger.info(
            f"处理分支 {branch_name} 的代码变更，提交人: {commit_info.get('author')}"
        )

        await process_code_changes(commit_info, payload)

        return JSONResponse(
            content={"status": "success", "message": "Webhook已接收并正在处理"}
        )

    except json.JSONDecodeError:
        logger.error("请求体不是有效的JSON格式")
        raise HTTPException(status_code=400, detail="请求体不是有效的JSON格式")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理GitLab Webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")


def extract_commit_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """从payload中提取提交信息"""
    # 获取最新的提交
    last_commit = payload.get("commits", [{}])[-1] if payload.get("commits") else {}

    return {
        "author": payload.get(
            "user_name", last_commit.get("author", {}).get("name", "未知")
        ),
        "email": last_commit.get("author", {}).get("email", ""),
        "time": last_commit.get("timestamp", ""),
        "branch": payload.get("ref", "").split("/")[-1],
        "message": last_commit.get("message", ""),
        "commit_id": last_commit.get("id", ""),
        "total_commits": payload.get("total_commits_count", 0),
        "project_id": payload.get("project_id", ""),
        "project_name": payload.get("project", {}).get("name", ""),
    }


def get_changed_files(payload: Dict[str, Any]) -> List[str]:
    """从payload中提取并合并所有变更的文件"""
    commits = payload.get("commits", [])
    all_changed_files = []

    for commit in commits:
        all_changed_files.extend(commit.get("added", []))
        all_changed_files.extend(commit.get("modified", []))
        all_changed_files.extend(commit.get("removed", []))

    # 去重
    return list(set(all_changed_files))


def build_code_changes_description(
    commit_info: Dict[str, Any], all_changed_files: List[str]
) -> str:
    """构建代码变更的文本描述"""
    description = f"提交人: {commit_info['author']}\n"
    description += f"分支: {commit_info['branch']}\n"
    description += f"提交信息: {commit_info['message']}\n"
    description += f"变更文件数量: {len(all_changed_files)}\n"
    description += "变更文件列表:\n"

    for file in all_changed_files[:20]:  # 只显示前20个文件
        description += f"- {file}\n"

    if len(all_changed_files) > 20:
        description += f"... 还有 {len(all_changed_files) - 20} 个文件省略\n"

    return description


def perform_dependency_analysis(
    commit_info: Dict[str, Any],
    all_changed_files: List[str],
    code_changes_description: str,
) -> Tuple[Optional[Dict], str]:
    """执行代码依赖分析"""
    if not DEPENDENCY_ANALYSIS_ENABLED:
        logger.info("依赖分析功能已禁用")
        return None, code_changes_description

    try:
        analyzer = DependencyAnalyzer()
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        analyzer.set_project_root(project_root)

        # 从配置中更新忽略模式
        if DEPENDENCY_ANALYSIS_CONFIG.get("ignore_patterns"):
            analyzer.ignore_patterns = DEPENDENCY_ANALYSIS_CONFIG["ignore_patterns"]

        # 设置GitLab客户端，用于获取远程文件内容
        project_id = commit_info.get("project_id")
        branch = commit_info.get("branch", "main")

        if project_id:
            logger.info(f"设置GitLab客户端，项目ID: {project_id}, 分支: {branch}")
            analyzer.set_gitlab_client(project_id, branch)
        else:
            logger.warning("无法获取项目ID，无法设置GitLab客户端")

        # 构建变更文件的绝对路径
        absolute_changed_files = [
            os.path.join(project_root, file_path) for file_path in all_changed_files
        ]

        if absolute_changed_files:
            for file_path in absolute_changed_files:
                analyzer.analyze_file(file_path)

            dependency_analysis_result = analyzer.analyze_changes(
                absolute_changed_files
            )

            code_changes_description += "\n## 依赖分析结果\n"
            code_changes_description += f"受影响的文件数量: {len(dependency_analysis_result['affected_files'])}\n"
            code_changes_description += (
                f"影响评分: {dependency_analysis_result['impact_score']}\n"
            )

            if dependency_analysis_result["critical_paths"]:
                code_changes_description += "关键影响路径:\n"
                max_paths = min(MAX_CRITICAL_PATHS, 5)  # 最多显示5条路径
                for path in dependency_analysis_result["critical_paths"][:max_paths]:
                    code_changes_description += f"- {' -> '.join(path)}\n"

            logger.info(
                f"依赖分析完成，受影响的文件数量: {len(dependency_analysis_result['affected_files'])}"
            )
            return dependency_analysis_result, code_changes_description
        else:
            logger.warning("无法找到任何变更文件的绝对路径，跳过依赖分析")
            code_changes_description += "\n## 依赖分析结果\n"
            code_changes_description += (
                "警告：无法找到变更文件的绝对路径，无法执行依赖分析\n"
            )
            return None, code_changes_description
    except Exception as e:
        logger.error(f"执行依赖分析时出错: {str(e)}")
        code_changes_description += "\n## 依赖分析结果\n"
        code_changes_description += f"错误: 依赖分析执行失败 - {str(e)}\n"
        return None, code_changes_description


def generate_dependency_analysis_section(
    dependency_analysis_result: Optional[Dict],
) -> str:
    """生成依赖分析详情部分"""
    if not dependency_analysis_result:
        return ""

    section = f"\n## 依赖分析详情\n"
    section += (
        f"- **受影响的文件数量**: {len(dependency_analysis_result['affected_files'])}\n"
    )
    section += f"- **影响评分**: {dependency_analysis_result['impact_score']}\n"

    if dependency_analysis_result["critical_paths"]:
        section += "\n**关键影响路径**:\n"
        max_paths = min(MAX_CRITICAL_PATHS, 5)  # 最多显示5条路径
        for path in dependency_analysis_result["critical_paths"][:max_paths]:
            section += f"- {' -> '.join(path)}\n"

    return section


def generate_markdown_report(
    commit_info: Dict[str, Any],
    all_changed_files: List[str],
    assessment_result: str,
    impact_result: str,
    combined_report: str,
    dependency_analysis_section: str,
) -> str:
    """生成完整的Markdown报告"""
    file_list_section = chr(10).join([f"- `{file}`" for file in all_changed_files[:10]])
    file_list_section += (
        "\n- ... 还有更多文件省略" if len(all_changed_files) > 10 else ""
    )

    return f"""# 代码变更评估报告

## 变更基本信息
- **提交人**: {commit_info['author']}
- **提交时间**: {commit_info['time']}
- **分支**: {commit_info['branch']}
- **提交信息**: {commit_info['message']}
- **变更文件数量**: {len(all_changed_files)}

## 变更文件列表
{file_list_section}

## 代码变更评估摘要
{assessment_result[:300]}...

## 影响分析摘要
{impact_result[:300]}...

## 综合评估报告
{combined_report[:300]}...
{dependency_analysis_section}
"""


def send_wecom_notification(report: str) -> None:
    """发送企业微信通知"""
    try:
        wecom_service = create_wecom_notification_service()

        if wecom_service.webhook_url and "your-key" not in wecom_service.webhook_url:
            wecom_service.send_markdown_notification(report)
            logger.info("企业微信通知发送成功")
        else:
            logger.info("企业微信Webhook未配置或使用默认值，跳过发送通知")
            logger.info(f"生成的报告内容: {report}")
    except Exception as e:
        logger.error(f"创建企业微信通知服务或发送通知失败: {str(e)}")


async def process_code_changes(commit_info: Dict[str, Any], payload: Dict[str, Any]):
    """处理代码变更，进行AI评估并发送通知"""
    try:
        # 获取代码变更文件
        all_changed_files = get_changed_files(payload)
        logger.info(f"代码变更文件数量: {len(all_changed_files)}")

        # 构建代码变更描述
        code_changes_description = build_code_changes_description(
            commit_info, all_changed_files
        )

        # 执行依赖分析
        dependency_analysis_result, code_changes_description = (
            perform_dependency_analysis(
                commit_info, all_changed_files, code_changes_description
            )
        )

        # 构建系统上下文
        system_context = f"项目名称: {commit_info['project_name']}\n"
        system_context += f"项目ID: {commit_info['project_id']}\n"
        system_context += (
            "这是一个基于Python的代码变更分析系统，用于自动分析代码变更并生成评估报告。"
        )

        # 创建AI评估服务并执行评估
        ai_service = create_ai_assessment_service()

        logger.info("开始评估代码变更")
        assessment_result = ai_service.assess_code_changes(code_changes_description)

        logger.info("开始分析变更影响")
        impact_result = ai_service.analyze_impact(
            code_changes_description, system_context
        )

        logger.info("开始生成综合报告")
        combined_report = ai_service.generate_combined_report(
            code_changes_description, system_context
        )

        # 生成依赖分析详情部分
        dependency_analysis_section = generate_dependency_analysis_section(
            dependency_analysis_result
        )

        # 生成并发送Markdown报告
        markdown_report = generate_markdown_report(
            commit_info,
            all_changed_files,
            assessment_result,
            impact_result,
            combined_report,
            dependency_analysis_section,
        )

        send_wecom_notification(markdown_report)

    except Exception as e:
        logger.error(f"处理代码变更失败: {str(e)}")
        raise


@app.get("/")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "代码变更分析系统运行中"}


@app.get("/api/docs")
def docs_redirect():
    """重定向到API文档"""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")


@app.post("/api/analyze-code-impact")
async def analyze_code_impact(
    request: Request, depth: int = Query(3, ge=1, le=10, description="递归查询深度")
):
    """分析代码变更影响并生成测试用例

    Args:
        file_paths: 要分析的文件路径列表
        depth: 递归查询深度，默认为3层

    Returns:
        JSONResponse: 分析结果和测试用例
    """
    try:
        # 从请求体中获取文件路径列表
        request_data = await request.json()
        file_paths = request_data.get("file_paths", [])

        if not file_paths or not isinstance(file_paths, list):
            raise HTTPException(
                status_code=400, detail="无效的file_paths参数，必须是非空列表"
            )

        logger.info(
            f"开始分析代码变更影响，文件数量: {len(file_paths)}, 查询深度: {depth}"
        )

        # 初始化分析器
        analyzer = ChangeImpactAnalyzer()
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        analyzer.dependency_analyzer.set_project_root(project_root)

        # 构建项目依赖图
        analyzer.build_dependency_graph(project_root)

        # 分析文件变更影响
        results = analyzer.batch_analyze_and_generate_tests(file_paths)

        # 处理每个文件的分析结果
        final_results = {}
        for file_path, result in results.items():
            # 标准化文件路径以便于比较
            normalized_path = os.path.normpath(file_path)
            final_results[normalized_path] = result

        logger.info(f"代码变更影响分析完成，处理文件数量: {len(final_results)}")

        return JSONResponse(
            content={
                "status": "success",
                "message": "代码变更影响分析完成",
                "results": final_results,
            }
        )

    except Exception as e:
        logger.error(f"分析代码变更影响失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析代码变更影响失败: {str(e)}")
