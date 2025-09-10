import os
import logging
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

class DependencyGraph:
    """代码依赖图模型
    
    用于表示项目中文件之间的依赖关系，并提供分析工具
    """
    def __init__(self):
        # 邻接表表示的依赖图 {file_path: [dependent_files]}
        self.dependencies: Dict[str, List[str]] = {}
        # 反向依赖表 {file_path: [files_that_depend_on_it]}
        self.reverse_dependencies: Dict[str, List[str]] = {}
        # 文件内容哈希缓存 {file_path: hash_value}
        self.file_hashes: Dict[str, str] = {}
        
    def add_file(self, file_path: str):
        """添加文件到依赖图"""
        if file_path not in self.dependencies:
            self.dependencies[file_path] = []
        if file_path not in self.reverse_dependencies:
            self.reverse_dependencies[file_path] = []
    
    def add_dependency(self, source_file: str, target_file: str):
        """添加文件之间的依赖关系
        
        source_file 依赖于 target_file
        即 target_file 的变更可能会影响 source_file
        """
        # 确保两个文件都在图中
        self.add_file(source_file)
        self.add_file(target_file)
        
        # 添加依赖关系
        if target_file not in self.dependencies[source_file]:
            self.dependencies[source_file].append(target_file)
        
        # 添加反向依赖关系
        if source_file not in self.reverse_dependencies[target_file]:
            self.reverse_dependencies[target_file].append(source_file)
    
    def get_dependents(self, file_path: str) -> List[str]:
        """获取依赖于指定文件的所有文件
        
        即指定文件的变更可能会影响的所有文件
        """
        if file_path not in self.reverse_dependencies:
            return []
        return self.reverse_dependencies[file_path]
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """获取指定文件依赖的所有文件
        
        即指定文件依赖哪些文件
        """
        if file_path not in self.dependencies:
            return []
        return self.dependencies[file_path]
    
    def find_affected_files(self, changed_files: List[str], depth: int = 2) -> List[str]:
        """查找受变更影响的所有文件
        
        Args:
            changed_files: 变更的文件列表
            depth: 影响分析的深度，默认为2层
        
        Returns:
            受影响的所有文件列表
        """
        affected_files: Set[str] = set(changed_files)
        current_files = set(changed_files)
        
        # 逐层查找受影响的文件
        for _ in range(depth):
            next_level: Set[str] = set()
            for file_path in current_files:
                dependents = self.get_dependents(file_path)
                next_level.update(dependents)
            
            # 过滤掉已经处理过的文件
            next_level = next_level - affected_files
            if not next_level:
                break
            
            affected_files.update(next_level)
            current_files = next_level
        
        return list(affected_files)
    
    def calculate_impact_score(self, changed_files: List[str]) -> float:
        """计算代码变更的影响评分
        
        基于受影响文件的数量、重要程度等因素
        """
        affected_files = self.find_affected_files(changed_files)
        
        # 基础影响分数 = 受影响文件数量
        base_score = len(affected_files)
        
        # 可以根据文件类型、重要程度等添加加权因子
        # 这里简单实现，实际项目中可以根据需求扩展
        weighted_score = base_score
        
        return weighted_score
    
    def find_critical_paths(self, changed_files: List[str]) -> List[List[str]]:
        """查找变更的关键影响路径
        
        目前简单实现，返回所有受影响的文件链
        """
        critical_paths: List[List[str]] = []
        
        # 这里简化实现，实际项目中可以使用更复杂的图算法
        for file_path in changed_files:
            dependents = self.get_dependents(file_path)
            if dependents:
                for dependent in dependents:
                    critical_paths.append([file_path, dependent])
        
        return critical_paths
    
    def clear(self):
        """清空依赖图"""
        self.dependencies.clear()
        self.reverse_dependencies.clear()
        self.file_hashes.clear()
    
    def save_cache(self, cache_file: str):
        """保存依赖图缓存到文件"""
        try:
            import json
            data = {
                "dependencies": self.dependencies,
                "reverse_dependencies": self.reverse_dependencies,
                "file_hashes": self.file_hashes
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"依赖图缓存已保存到 {cache_file}")
        except Exception as e:
            logger.error(f"保存依赖图缓存失败: {str(e)}")
    
    def load_cache(self, cache_file: str):
        """从文件加载依赖图缓存"""
        try:
            import json
            if not os.path.exists(cache_file):
                logger.warning(f"缓存文件不存在: {cache_file}")
                return False
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.dependencies = data.get("dependencies", {})
            self.reverse_dependencies = data.get("reverse_dependencies", {})
            self.file_hashes = data.get("file_hashes", {})
            
            logger.info(f"依赖图缓存已从 {cache_file} 加载")
            return True
        except Exception as e:
            logger.error(f"加载依赖图缓存失败: {str(e)}")
            return False