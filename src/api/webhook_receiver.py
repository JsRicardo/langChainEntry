import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from src.config import get_config
from src.ai import create_ai_assessment_service
from src.notification import create_wecom_notification_service

logger = logging.getLogger(__name__)

app = FastAPI(title="代码变更分析系统", description="接收GitLab Webhook并分析代码变更")

config = get_config()

ALLOWED_BRANCHES = config.get("webhook.allowed_branches", ["main", "master", "develop"])
logger.info(f"允许的分支: {ALLOWED_BRANCHES}")

GITLAB_WEBHOOK_TOKEN = config.get("webhook.gitlab_token")

@app.post("/webhook/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token")
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
        
        event_name = payload.get('event_name')
        if event_name != 'push':
            logger.info(f"忽略非push事件: {event_name}")
            return JSONResponse(content={"status": "success", "message": "忽略非push事件"})
        
        ref = payload.get('ref')  # 格式: refs/heads/branch_name
        if not ref:
            logger.warning("未找到分支信息")
            raise HTTPException(status_code=400, detail="未找到分支信息")
        
        branch_name = ref.split('/')[-1]
        if branch_name not in ALLOWED_BRANCHES:
            logger.info(f"忽略不允许的分支: {branch_name}")
            return JSONResponse(content={"status": "success", "message": f"忽略不允许的分支: {branch_name}"})
        
        # 提取提交信息
        commit_info = extract_commit_info(payload)
        logger.info(f"处理分支 {branch_name} 的代码变更，提交人: {commit_info.get('author')}")
        
        await process_code_changes(commit_info, payload)
        
        return JSONResponse(content={"status": "success", "message": "Webhook已接收并正在处理"})
        
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
    last_commit = payload.get('commits', [{}])[-1] if payload.get('commits') else {}
    
    return {
        "author": payload.get('user_name', last_commit.get('author', {}).get('name', '未知')),
        "email": last_commit.get('author', {}).get('email', ''),
        "time": last_commit.get('timestamp', ''),
        "branch": payload.get('ref', '').split('/')[-1],
        "message": last_commit.get('message', ''),
        "commit_id": last_commit.get('id', ''),
        "total_commits": payload.get('total_commits_count', 0),
        "project_id": payload.get('project_id', ''),
        "project_name": payload.get('project', {}).get('name', '')
    }

async def process_code_changes(commit_info: Dict[str, Any], payload: Dict[str, Any]):
    """处理代码变更，进行AI评估并发送通知"""
    try:
        # 获取代码变更信息
        commits = payload.get('commits', [])
        
        # 合并所有变更的文件
        all_changed_files = []
        for commit in commits:
            # 处理新增、修改、删除的文件
            all_changed_files.extend(commit.get('added', []))
            all_changed_files.extend(commit.get('modified', []))
            all_changed_files.extend(commit.get('removed', []))
        
        # 去重
        all_changed_files = list(set(all_changed_files))
        
        logger.info(f"代码变更文件数量: {len(all_changed_files)}")
        
        # 构建代码变更描述
        code_changes_description = f"提交人: {commit_info['author']}\n"
        code_changes_description += f"分支: {commit_info['branch']}\n"
        code_changes_description += f"提交信息: {commit_info['message']}\n"
        code_changes_description += f"变更文件数量: {len(all_changed_files)}\n"
        code_changes_description += "变更文件列表:\n"
        for file in all_changed_files[:20]:  # 只显示前20个文件
            code_changes_description += f"- {file}\n"
        
        if len(all_changed_files) > 20:
            code_changes_description += f"... 还有 {len(all_changed_files) - 20} 个文件省略\n"
        
        # 示例系统上下文信息
        system_context = f"项目名称: {commit_info['project_name']}\n"
        system_context += f"项目ID: {commit_info['project_id']}\n"
        system_context += "这是一个基于Python的代码变更分析系统，用于自动分析代码变更并生成评估报告。"
        
        # 创建AI评估服务实例
        ai_service = create_ai_assessment_service()
        
        logger.info("开始评估代码变更")
        assessment_result = ai_service.assess_code_changes(code_changes_description)
        
        logger.info("开始分析变更影响")
        impact_result = ai_service.analyze_impact(code_changes_description, system_context)
        
        logger.info("开始生成综合报告")
        combined_report = ai_service.generate_combined_report(code_changes_description, system_context)
        
        try:
            wecom_service = create_wecom_notification_service()
            
            markdown_report = f"""# 代码变更评估报告

## 变更基本信息
- **提交人**: {commit_info['author']}
- **提交时间**: {commit_info['time']}
- **分支**: {commit_info['branch']}
- **提交信息**: {commit_info['message']}
- **变更文件数量**: {len(all_changed_files)}

## 变更文件列表
{chr(10).join([f"- `{file}`" for file in all_changed_files[:10]])}
{"\n- ... 还有更多文件省略" if len(all_changed_files) > 10 else ""}

## 代码变更评估摘要
{assessment_result[:300]}...

## 影响分析摘要
{impact_result[:300]}...

## 综合评估报告
{combined_report[:300]}...
"""
            
            if wecom_service.webhook_url and "your-key" not in wecom_service.webhook_url:
                wecom_service.send_markdown_notification(markdown_report)
                logger.info("企业微信通知发送成功")
            else:
                logger.info("企业微信Webhook未配置或使用默认值，跳过发送通知")
                logger.info(f"生成的报告内容: {markdown_report}")
        except Exception as e:
            logger.error(f"创建企业微信通知服务或发送通知失败: {str(e)}")
            
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