import os
import re
import logging
import subprocess
import os
from typing import Dict, List, Set, Optional
from src.models.dependency_graph import DependencyGraph
from src.utils.gitlab_client import create_gitlab_client, GitLabClient

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """代码依赖分析器
    
    用于分析项目中的代码依赖关系，构建依赖图
    """
    def __init__(self):
        self.graph = DependencyGraph()
        self.project_root = None
        self.gitlab_client = None
        self.gitlab_project_id = None
        self.gitlab_branch = 'main'
        
        # 文件类型的导入模式
        self.import_patterns = {
            '.js': [
                # ES6 import
                re.compile(r'import\s+.*?from\s+[\\\'"](.+?)[\\\'"]'),
                # CommonJS require
                re.compile(r'require\([\\\'"](.+?)[\\\'"]\)')
            ],
            '.ts': [
                # TypeScript import
                re.compile(r'import\s+.*?from\s+[\\\'"](.+?)[\\\'"]'),
                # TypeScript require
                re.compile(r'require\([\\\'"](.+?)[\\\'"]\)')
            ],
            '.jsx': [
                # JSX import
                re.compile(r'import\s+.*?from\s+[\\\'"](.+?)[\\\'"]'),
                # JSX require
                re.compile(r'require\([\\\'"](.+?)[\\\'"]\)')
            ],
            '.tsx': [
                # TSX import
                re.compile(r'import\s+.*?from\s+[\\\'"](.+?)[\\\'"]'),
                # TSX require
                re.compile(r'require\([\\\'"](.+?)[\\\'"]\)')
            ],
            '.vue': [
                # Vue script import
                re.compile(r'import\s+.*?from\s+[\\\'"](.+?)[\\\'"]'),
                # Vue require
                re.compile(r'require\([\\\'"](.+?)[\\\'"]\)')
            ],
            '.py': [
                # Python import
                re.compile(r'^\s*import\s+(.+?)(?:\s+as\s+.+?)?(?:\s*$|\s*#)'),
                # Python from import
                re.compile(r'^\s*from\s+(.+?)\s+import\s+.+?(?:\s*$|\s*#)')
            ]
        }
        
        # 忽略的文件和目录模式
        self.ignore_patterns = [
            'node_modules/',
            'dist/',
            'build/',
            'venv/',
            '.venv/',
            '__pycache__/',
            '.git/',
            '.idea/',
            '.vscode/',
            '*.test.js',
            '*.spec.js',
            '*.test.ts',
            '*.spec.ts',
            '*.test.tsx',
            '*.spec.tsx'
        ]
    
    def set_gitlab_client(self, project_id: int, branch: str = 'main', gitlab_client: Optional[GitLabClient] = None):
        """设置GitLab客户端
        
        Args:
            project_id: GitLab项目ID
            branch: Git分支名，默认为'main'
            gitlab_client: GitLab客户端实例，如果为None则自动创建
        """
        self.gitlab_project_id = project_id
        self.gitlab_branch = branch
        
        if gitlab_client:
            self.gitlab_client = gitlab_client
        else:
            self.gitlab_client = create_gitlab_client()
            
        if self.gitlab_client:
            logger.info(f"GitLab客户端已设置，项目ID: {project_id}, 分支: {branch}")
        else:
            logger.warning("无法设置GitLab客户端")
    
    def set_project_root(self, project_root: str):
        """设置项目根目录"""
        if os.path.exists(project_root) and os.path.isdir(project_root):
            self.project_root = project_root
            logger.info(f"项目根目录已设置为: {project_root}")
        else:
            logger.error(f"无效的项目根目录: {project_root}")
            raise ValueError(f"无效的项目根目录: {project_root}")
    
    def should_ignore(self, file_path: str) -> bool:
        """检查文件是否应该被忽略"""
        for pattern in self.ignore_patterns:
            # 简单的模式匹配
            if pattern.startswith('*'):
                if file_path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('/'):
                if pattern in file_path:
                    return True
        return False
    
    def normalize_path(self, file_path: str) -> str:
        """标准化文件路径"""
        if self.project_root:
            # 转换为相对路径
            rel_path = os.path.relpath(file_path, self.project_root)
            # 统一使用正斜杠
            return rel_path.replace('\\', '/')
        return file_path.replace('\\', '/')
    
    def find_imports(self, file_path: str) -> List[str]:
        """查找文件中的导入依赖"""
        try:
            # 获取文件扩展名
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # 检查是否支持该文件类型
            if ext not in self.import_patterns:
                return []
            
            # 尝试读取文件内容
            content = None
            
            # 首先尝试本地文件
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"读取本地文件 {file_path} 失败: {str(e)}")
            
            # 如果本地文件不存在或读取失败，但配置了GitLab客户端，则尝试从GitLab获取
            if not content and self.gitlab_client and self.gitlab_project_id:
                # 转换为项目相对路径
                if self.project_root:
                    try:
                        rel_path = os.path.relpath(file_path, self.project_root)
                        # 统一使用正斜杠
                        gitlab_file_path = rel_path.replace('\\', '/')
                        
                        logger.debug(f"尝试从GitLab获取文件内容: {gitlab_file_path}")
                        content = self.gitlab_client.get_file_content(
                            self.gitlab_project_id, 
                            gitlab_file_path, 
                            self.gitlab_branch
                        )
                    except Exception as e:
                        logger.error(f"转换文件路径时出错: {str(e)}")
            
            # 如果仍然没有内容，则返回空列表
            if not content:
                logger.warning(f"无法获取文件内容: {file_path}")
                return []
            
            # 查找导入语句
            imports = []
            for pattern in self.import_patterns[ext]:
                matches = pattern.findall(content)
                imports.extend(matches)
            
            # 对Python的导入进行特殊处理
            if ext == '.py':
                processed_imports = []
                for imp in imports:
                    # 处理多行导入
                    if ',' in imp:
                        parts = imp.split(',')
                        processed_imports.extend([p.strip() for p in parts])
                    else:
                        processed_imports.append(imp.strip())
                imports = processed_imports
            
            return imports
        except Exception as e:
            logger.error(f"解析文件 {file_path} 的导入依赖失败: {str(e)}")
            return []
    
    def resolve_import_path(self, source_file: str, import_path: str) -> Optional[str]:
        """解析导入路径为实际文件路径"""
        if not self.project_root:
            logger.warning("未设置项目根目录，无法解析导入路径")
            return None
        
        # 处理相对导入
        source_dir = os.path.dirname(source_file)
        
        # 尝试不同的文件扩展名和目录组合
        extensions = ['.js', '.ts', '.jsx', '.tsx', '.vue', '.py']
        
        # 相对路径导入
        if import_path.startswith('./') or import_path.startswith('../'):
            # 构建绝对路径
            abs_path = os.path.join(source_dir, import_path)
            
            # 尝试直接作为文件
            for ext in extensions:
                if os.path.exists(abs_path + ext):
                    return abs_path + ext
            
            # 尝试作为目录，查找index文件
            for ext in extensions:
                index_path = os.path.join(abs_path, 'index' + ext)
                if os.path.exists(index_path):
                    return index_path
        
        # 模块导入（简化处理）
        # 在实际项目中，这里需要根据项目的模块解析规则进行更复杂的处理
        # 例如package.json中的exports字段、TypeScript配置等
        
        # 简单尝试在项目根目录查找
        for ext in extensions:
            # 尝试直接路径
            candidate_path = os.path.join(self.project_root, import_path + ext)
            if os.path.exists(candidate_path):
                return candidate_path
            
            # 尝试src目录
            candidate_path = os.path.join(self.project_root, 'src', import_path + ext)
            if os.path.exists(candidate_path):
                return candidate_path
        
        # 如果本地文件不存在，但配置了GitLab客户端，则检查GitLab仓库中是否存在该文件
        if self.gitlab_client and self.gitlab_project_id:
            # 构建在GitLab仓库中的可能路径
            gitlab_paths_to_try = []
            
            # 处理相对路径
            if import_path.startswith('./') or import_path.startswith('../'):
                # 转换为相对项目根目录的路径
                if os.path.exists(source_file):
                    try:
                        # 获取source_file相对于项目根目录的目录
                        source_rel_dir = os.path.dirname(os.path.relpath(source_file, self.project_root))
                        # 构建导入文件的相对路径
                        gitlab_rel_path = os.path.normpath(os.path.join(source_rel_dir, import_path))
                        gitlab_paths_to_try.append(gitlab_rel_path.replace('\\', '/'))
                    except Exception as e:
                        logger.error(f"构建GitLab相对路径时出错: {str(e)}")
            
            # 添加直接路径
            gitlab_paths_to_try.append(import_path)
            # 添加src目录路径
            gitlab_paths_to_try.append(f"src/{import_path}")
            
            # 尝试所有可能的路径和扩展名
            for path in gitlab_paths_to_try:
                for ext in extensions:
                    # 检查文件是否存在于GitLab仓库中
                    # 注意：这里我们不能直接检查文件是否存在，只能尝试获取内容
                    # 如果内容不为None，则认为文件存在
                    logger.debug(f"尝试从GitLab解析导入路径: {path}{ext}")
                    
                    # 这里我们只需要验证文件是否存在，不需要实际获取内容
                    # 但由于GitLab API限制，我们只能通过尝试获取内容来验证
                    # 为了避免不必要的API调用，我们可以先构建一个本地路径作为缓存键
                    local_candidate_path = os.path.join(self.project_root, path + ext)
                    
                    # 如果本地文件不存在，并且我们有GitLab客户端，则标记这个路径为可能存在的远程文件
                    # 注意：这里我们不实际验证，而是假设它存在，由find_imports方法在需要时尝试获取内容
                    # 这样可以避免过多的API调用
                    if not os.path.exists(local_candidate_path):
                        logger.debug(f"假设GitLab中存在文件: {path}{ext}")
                        return local_candidate_path
        
        return None
    
    def analyze_file(self, file_path: str):
        """分析单个文件的依赖关系"""
        if self.should_ignore(file_path):
            return
        
        logger.debug(f"分析文件: {file_path}")
        
        # 标准化文件路径
        normalized_path = self.normalize_path(file_path)
        
        # 查找导入依赖
        imports = self.find_imports(file_path)
        
        # 解析并添加依赖关系
        for import_path in imports:
            # 解析导入路径
            resolved_path = self.resolve_import_path(file_path, import_path)
            
            if resolved_path and not self.should_ignore(resolved_path):
                normalized_resolved_path = self.normalize_path(resolved_path)
                
                # 添加依赖关系
                self.graph.add_dependency(normalized_path, normalized_resolved_path)
                logger.debug(f"添加依赖: {normalized_path} -> {normalized_resolved_path}")
    
    def analyze_project(self, start_dir: str = None):
        """分析整个项目的依赖关系"""
        if not start_dir:
            if not self.project_root:
                raise ValueError("未设置项目根目录")
            start_dir = self.project_root
        
        logger.info(f"开始分析项目依赖关系: {start_dir}")
        
        # 遍历项目目录
        for root, dirs, files in os.walk(start_dir):
            # 过滤掉忽略的目录
            dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]
            
            # 分析每个文件
            for file in files:
                file_path = os.path.join(root, file)
                
                # 过滤掉忽略的文件
                if not self.should_ignore(file_path):
                    self.analyze_file(file_path)
        
        logger.info(f"项目依赖关系分析完成，总文件数: {len(self.graph.dependencies)}")
    
    def analyze_changes(self, changed_files: List[str]) -> Dict:
        """分析代码变更的影响范围"""
        # 标准化变更文件路径
        normalized_changed_files = [self.normalize_path(f) for f in changed_files]
        
        # 查找受影响的文件
        affected_files = self.graph.find_affected_files(normalized_changed_files)
        
        # 计算影响评分
        impact_score = self.graph.calculate_impact_score(normalized_changed_files)
        
        # 查找关键影响路径
        critical_paths = self.graph.find_critical_paths(normalized_changed_files)
        
        return {
            "changed_files": normalized_changed_files,
            "affected_files": affected_files,
            "impact_score": impact_score,
            "critical_paths": critical_paths
        }