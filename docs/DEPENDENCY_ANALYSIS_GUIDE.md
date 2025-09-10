# 依赖分析功能使用指南

## 功能概述

依赖分析功能可以帮助您在代码变更时识别受影响的文件，从而更准确地分析代码变更的影响范围。该功能通过解析项目中的导入语句，构建代码依赖图，并计算变更的影响评分和关键影响路径。

## 核心组件

依赖分析功能由以下核心组件组成：

1. **DependencyGraph** - 依赖图模型，用于管理依赖关系和计算影响范围
2. **DependencyAnalyzer** - 依赖分析器，用于解析文件导入和构建依赖图
3. **Webhook集成** - 在Webhook接收器中集成依赖分析功能

## 配置选项

在 `configs/config.json` 文件中，您可以配置以下与依赖分析相关的选项：

```json
{
  "dependency_analysis": {
    "enabled": true,                // 是否启用依赖分析功能
    "max_affected_files": 50,       // 最大返回的受影响文件数量
    "max_critical_paths": 10,       // 最大返回的关键路径数量
    "ignore_patterns": [            // 忽略的文件和目录模式
      "node_modules/",
      "dist/",
      "build/",
      "venv/",
      "__pycache__/",
      ".git/",
      ".idea/",
      ".vscode/",
      "*.test.js",
      "*.spec.js",
      "*.test.ts",
      "*.spec.ts"
    ]
  }
}
```

## 使用方法

### 1. 配置依赖分析选项

首先，在 `configs/config.json` 文件中添加依赖分析相关的配置选项。

### 2. 启动服务

启动FastAPI服务，依赖分析功能会自动集成到Webhook处理流程中：

```bash
python src/main.py
```

### 3. 测试依赖分析功能

使用提供的测试脚本测试依赖分析功能：

```bash
# 使用默认示例文件进行测试
python examples/test_dependency_analysis.py

# 交互式测试，手动输入要测试的文件
python examples/test_dependency_analysis.py --interactive
```

### 4. 查看依赖分析结果

当Webhook接收到代码变更事件时，依赖分析功能会自动执行，并将结果添加到：

1. **AI评估服务的输入** - 依赖分析结果会被添加到代码变更描述中，帮助AI更准确地评估代码变更
2. **企业微信通知** - 依赖分析结果会作为独立章节显示在通知消息中

## 依赖分析结果说明

依赖分析会提供以下结果：

- **受影响的文件数量** - 代码变更可能影响的文件总数
- **影响评分** - 代码变更的影响程度，范围从0到100
- **关键影响路径** - 代码变更可能通过依赖关系影响的主要路径

## 自定义开发

### 扩展支持的文件类型

要支持更多文件类型的导入解析，可以在 `DependencyAnalyzer` 类中添加相应的导入模式：

```python
# 在 DependencyAnalyzer.__init__ 方法中添加
self.import_patterns['.your_ext'] = [
    # 添加适合该文件类型的导入模式正则表达式
]
```

### 自定义依赖解析逻辑

如果您的项目有特殊的模块解析规则，可以重写 `DependencyAnalyzer.resolve_import_path` 方法：

```python
# 自定义依赖解析逻辑
class CustomDependencyAnalyzer(DependencyAnalyzer):
    def resolve_import_path(self, source_file: str, import_path: str) -> Optional[str]:
        # 实现自定义的导入路径解析逻辑
        # ...
```

## 注意事项

1. **性能考虑** - 依赖分析可能会增加Webhook处理的时间，特别是对于大型项目
2. **路径转换** - Webhook提供的文件路径是相对路径，系统会尝试将其转换为绝对路径
3. **错误处理** - 依赖分析失败不会中断主要的Webhook处理流程
4. **文件系统访问** - 依赖分析需要访问本地文件系统来读取和解析文件

## 故障排除

### 依赖分析未执行

- 检查 `configs/config.json` 中的 `dependency_analysis.enabled` 是否设置为 `true`
- 确保Webhook提供的文件路径可以正确转换为绝对路径
- 查看日志以获取详细的错误信息

### 依赖分析结果不准确

- 可能需要调整 `DependencyAnalyzer` 中的导入模式正则表达式
- 对于特殊的项目结构，可能需要自定义 `resolve_import_path` 方法
- 确保 `ignore_patterns` 配置正确，排除了不需要分析的文件和目录