from collections.abc import Generator
from typing import Any, Dict, List
import os
import json
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.exceptions import HttpResponseError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import PyPDF2

class DifyAzurePluginTool(Tool):
    # 支持的文件类型映射
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.tiff': 'image/tiff',
        '.bmp': 'image/bmp',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.txt': 'text/plain',
        '.md': 'text/markdown'
    }

    def _safe_get_attribute(self, obj, attr, default=None):
        return getattr(obj, attr, default)

    def _safe_get_content(self, obj):
        if hasattr(obj, 'content'):
            return obj.content
        elif hasattr(obj, 'value'):
            return obj.value
        return ""

    def _convert_to_output_format(self, result: AnalyzeResult, output_format: str) -> dict:
        filename = f"document_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_format == "json":
            filename += ".json"
            mime_type = "application/json"
            # 构建JSON结构
            content = {
                "content": self._safe_get_content(result),
                "pages": [],
                "tables": [],
                "paragraphs": []
            }
            
            # 添加页面信息
            if hasattr(result, 'pages'):
                for page in result.pages:
                    page_info = {
                        "page_number": self._safe_get_attribute(page, 'page_number', 0),
                        "width": self._safe_get_attribute(page, 'width', 0),
                        "height": self._safe_get_attribute(page, 'height', 0),
                        "unit": self._safe_get_attribute(page, 'unit', 'pixel'),
                        "spans": []
                    }
                    
                    # 处理spans
                    if hasattr(page, 'spans'):
                        for span in page.spans:
                            span_info = {
                                "text": self._safe_get_content(span),
                                "confidence": self._safe_get_attribute(span, 'confidence', 0.0)
                            }
                            page_info["spans"].append(span_info)
                    
                    content["pages"].append(page_info)
            
            # 添加表格信息
            if hasattr(result, 'tables') and result.tables:
                for table in result.tables:
                    table_info = {
                        "row_count": self._safe_get_attribute(table, 'row_count', 0),
                        "column_count": self._safe_get_attribute(table, 'column_count', 0),
                        "cells": []
                    }
                    
                    if hasattr(table, 'cells'):
                        for cell in table.cells:
                            cell_info = {
                                "text": self._safe_get_content(cell),
                                "row_index": self._safe_get_attribute(cell, 'row_index', 0),
                                "column_index": self._safe_get_attribute(cell, 'column_index', 0)
                            }
                            table_info["cells"].append(cell_info)
                    
                    content["tables"].append(table_info)
            
            # 添加段落信息
            if hasattr(result, 'paragraphs'):
                for para in result.paragraphs:
                    para_info = {
                        "content": self._safe_get_content(para),
                        "role": self._safe_get_attribute(para, 'role')
                    }
                    content["paragraphs"].append(para_info)
            
            blob = json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')
        elif output_format == "markdown":
            filename += ".md"
            mime_type = "text/markdown"
            blob = result.content.encode('utf-8')
        else:  # text format
            filename += ".txt"
            mime_type = "text/plain"
            blob = result.content.encode('utf-8')
            
        # 创建文件元数据，添加下载相关信息
        meta = {
            "name": filename,
            "mime_type": mime_type,
            "download": True,
            "disposition": "attachment",
            "save_as": filename
        }
        
        # 返回文件数据
        return {
            "text": "文档已解析完成，请点击下方的文件进行下载。",
            "blob": blob,
            "meta": meta
        }

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        try:
            # 获取参数
            file_path = tool_parameters.get('file_path')
            output_format = tool_parameters.get('output_format', 'markdown')
            
            if not file_path:
                yield self.create_text_message("错误：未提供文档路径")
                return
                
            if not os.path.exists(file_path):
                yield self.create_text_message(f"错误：文件不存在 - {file_path}")
                return
                
            # 检查文件类型
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                yield self.create_text_message(
                    f"错误：不支持的文件类型 {file_ext}，支持的类型包括：{', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
                )
                return

            endpoint = os.getenv("AZURE_ENDPOINT")
            key = os.getenv("AZURE_KEY")
            
            if not endpoint or not key:
                yield self.create_text_message("错误：未配置Azure Document Intelligence凭证")
                return

            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=endpoint, 
                credential=AzureKeyCredential(key)
            )

            # 获取文档页数
            total_pages = 1
            if file_ext == '.pdf':
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    total_pages = len(pdf_reader.pages)

            azure_output_format = output_format if output_format in ['markdown', 'json', 'text'] else 'text'
            
            # 分析文档
            with open(file_path, "rb") as f:
                try:
                    if file_ext == '.pdf':
                        combined_content = ""
                        for start_page in range(0, total_pages, 2):
                            end_page = min(start_page + 2, total_pages)
                            poller = document_intelligence_client.begin_analyze_document(
                                "prebuilt-layout", 
                                body=f,
                                pages=f"{start_page+1}-{end_page}",
                                output_content_format=azure_output_format
                            )
                            result: AnalyzeResult = poller.result()
                            combined_content += result.content + "\n"
                            f.seek(0)

                        result = AnalyzeResult._from_generated({
                            "content": combined_content,
                            "pages": [],
                            "tables": [],
                            "paragraphs": []
                        })
                    else:
                        # 对于其他文件类型，直接处理
                        poller = document_intelligence_client.begin_analyze_document(
                            "prebuilt-layout", 
                            body=f,
                            output_content_format=azure_output_format
                        )
                        result: AnalyzeResult = poller.result()
                        
                except HttpResponseError as e:
                    if e.status_code == 401:
                        yield self.create_text_message("错误：Azure Document Intelligence凭证无效")
                        return
                    elif e.status_code == 404:
                        yield self.create_text_message("错误：Azure Document Intelligence服务不可用")
                        return
                    else:
                        yield self.create_text_message(f"错误：Azure Document Intelligence服务错误 - {str(e)}")
                        return

            output = self._convert_to_output_format(result, output_format)
            
            # 返回结果
            yield self.create_text_message(output["text"])
            yield self.create_blob_message(output["blob"], output["meta"])
                
        except Exception as e:
            yield self.create_text_message(f"错误：{str(e)}")
