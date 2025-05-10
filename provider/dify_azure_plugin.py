from typing import Any
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.exceptions import HttpResponseError
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class DifyAzurePluginProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # 获取凭证
            endpoint = os.getenv("AZURE_ENDPOINT")
            key = os.getenv("AZURE_KEY")
            
            if not endpoint or not key:
                raise ValueError("缺少必要的凭证信息")
                
            # 验证endpoint格式
            if not endpoint.startswith("https://") or not endpoint.endswith(".cognitiveservices.azure.com/"):
                raise ValueError("无效的endpoint格式")
                
            # 验证key格式
            if len(key) < 32:
                raise ValueError("无效的API key格式")
                
            # 验证凭证
            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            
            try:
                # 尝试调用API验证凭证
                document_intelligence_client.get_resource_info()
            except HttpResponseError as e:
                if e.status_code == 401:
                    raise ValueError("API key无效")
                elif e.status_code == 404:
                    raise ValueError("服务不可用")
                else:
                    raise ValueError(f"服务错误: {str(e)}")
            
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"凭证验证失败: {str(e)}")
