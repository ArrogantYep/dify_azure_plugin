## Azure Document Intelligence Plugin for Dify

**Author:** lucas
**Version:** 0.0.1
**Type:** tool

### Description

这是一个基于Azure Document Intelligence的Dify插件，用于解析各种文档格式。该插件支持以下功能：

- 支持解析PDF、Word、PowerPoint和文本文件
- 支持输出Markdown、JSON和纯文本格式
- 保留文档的原始布局和结构
- 提取表格、段落和页面信息

### 使用方法

1. 配置Azure Document Intelligence凭证：
   - 在Azure门户创建Document Intelligence资源
   - 获取Endpoint和API Key
   - 在Dify中配置凭证

2. 使用插件：
   - 提供文档路径（file_path）
   - 选择输出格式（output_format，可选，默认为markdown）
   - 插件将返回解析后的文档内容

### 输出格式说明

- **Markdown**：保留文档的原始结构和格式
- **JSON**：提供详细的文档信息，包括页面、表格和段落
- **Text**：提供纯文本内容

### 环境变量

- `DOCUMENTINTELLIGENCE_ENDPOINT`：Azure Document Intelligence服务的Endpoint
- `DOCUMENTINTELLIGENCE_API_KEY`：Azure Document Intelligence服务的API Key

### 注意事项

- 确保文档文件存在且可访问
- 确保Azure Document Intelligence服务正常运行
- 确保凭证有效且有足够的权限