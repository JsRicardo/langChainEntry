# 代码变更分析系统

一个基于Python和AI的代码变更分析与测试通知系统，用于在代码提交后自动检查变更并推送影响信息。

## 项目结构

```
├── src/                    # 主源码目录
│   ├── webhook/            # Webhook接收器模块
│   ├── file_processor/     # 文件类型识别与处理模块
│   ├── ast_parser/         # AST解析引擎
│   ├── change_analyzer/    # 代码变更分析器
│   ├── ai_analysis/        # AI评估模块
│   ├── notification/       # 企业微信通知器
│   ├── config/             # 配置管理模块
│   ├── plugin/             # 插件系统
│   ├── models/             # 数据模型定义
│   └── utils/              # 通用工具函数
├── tests/                  # 测试目录
├── scripts/                # 辅助脚本
├── configs/                # 配置文件目录
├── docs/                   # 文档目录
├── CODE-CHANGE-ANALYSIS-SYSTEM-DESIGN.md  # 系统设计文档
├── LICENSE                 # 许可证文件
├── requirements.txt        # Python依赖包列表
├── setup.py                # 项目安装脚本
└── README.md               # 项目说明文档
```

## 核心功能

1. **Webhook接收**：处理GitLab事件通知
2. **文件类型识别**：识别不同类型的前端文件
3. **AST解析**：解析各类文件生成抽象语法树
4. **代码变更分析**：分析代码变更点和影响范围
5. **AI评估**：使用大语言模型进行智能分析
6. **企业微信通知**：推送Markdown格式的分析报告
7. **配置管理**：管理系统配置和项目特定设置

## 技术栈

- **主要语言**：Python 3.9+
- **Web框架**：FastAPI
- **AI框架**：LangChain
- **JavaScript解析**：通过调用Node.js工具链实现
- **依赖管理**：pip

## 安装说明

1. 克隆项目代码
2. 安装Python依赖：`pip install -r requirements.txt`
3. 安装Node.js依赖：`cd scripts && npm install`
4. 配置系统参数：复制`configs/config.example.json`到`configs/config.json`并修改配置
5. 启动服务：`python -m src.main`

## 使用说明

1. 在GitLab中配置Webhook，指向系统的Webhook接收URL
2. 配置项目特定设置（可选）
3. 提交代码后，系统会自动分析变更并发送通知

## 开发指南

请参考`docs/development_guide.md`文件。