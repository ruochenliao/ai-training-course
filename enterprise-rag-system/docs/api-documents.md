# 文档管理模块 API 文档

## 📋 模块概述

文档管理模块提供文档的上传、处理、查询、下载等功能，支持多种文件格式的智能解析和向量化处理。

**基础路径**: `/api/v1/documents`

## 📄 支持的文件格式

- **文档类型**: PDF, DOC, DOCX, TXT, MD
- **表格类型**: XLS, XLSX, CSV
- **演示文稿**: PPT, PPTX
- **图片类型**: PNG, JPG, JPEG（OCR识别）
- **其他格式**: HTML, XML, JSON

## 📚 接口列表

### 1. 获取文档列表

**接口名称**: 获取文档列表  
**功能描述**: 获取指定知识库中的文档列表  
**接口地址**: `/api/v1/documents/`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| page | int | 否 | 页码（默认1） | 1 |
| size | int | 否 | 每页数量（默认20，最大100） | 20 |
| knowledge_base_id | int | 否 | 知识库ID过滤 | 1 |
| processing_status | string | 否 | 处理状态过滤 | completed |
| file_type | string | 否 | 文件类型过滤 | pdf |
| search | string | 否 | 搜索关键词（文件名） | 技术文档 |

#### 响应参数
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "技术文档.pdf",
      "original_filename": "技术文档.pdf",
      "file_size": 1024000,
      "file_type": "pdf",
      "knowledge_base_id": 1,
      "processing_status": "completed",
      "upload_time": "2024-01-01T12:00:00Z",
      "processed_time": "2024-01-01T12:05:00Z",
      "chunk_count": 25,
      "metadata": {
        "pages": 10,
        "language": "zh"
      }
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| documents | array | 文档列表 | 见文档对象 |
| total | int | 总数量 | 50 |
| page | int | 当前页码 | 1 |
| size | int | 每页数量 | 20 |
| pages | int | 总页数 | 3 |

#### 文档对象字段说明
| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 文档ID | 1 |
| filename | string | 存储文件名 | 技术文档.pdf |
| original_filename | string | 原始文件名 | 技术文档.pdf |
| file_size | int | 文件大小（字节） | 1024000 |
| file_type | string | 文件类型 | pdf |
| knowledge_base_id | int | 所属知识库ID | 1 |
| processing_status | string | 处理状态 | completed |
| upload_time | string | 上传时间 | 2024-01-01T12:00:00Z |
| processed_time | string | 处理完成时间 | 2024-01-01T12:05:00Z |
| chunk_count | int | 分块数量 | 25 |
| metadata | object | 文档元数据 | 见元数据对象 |

#### 处理状态说明
- `pending`: 等待处理
- `processing`: 正在处理
- `completed`: 处理完成
- `failed`: 处理失败

---

### 2. 上传文档

**接口名称**: 上传文档  
**功能描述**: 上传文档到指定知识库并进行处理  
**接口地址**: `/api/v1/documents/upload`  
**请求方式**: POST  
**认证**: 需要Bearer Token  
**Content-Type**: multipart/form-data

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| file | file | 是 | 上传的文件 | 文档.pdf |
| knowledge_base_id | int | 是 | 知识库ID | 1 |
| description | string | 否 | 文档描述 | 技术文档说明 |
| language | string | 否 | 文档语言（默认zh） | zh |
| chunk_strategy | string | 否 | 分块策略（默认semantic） | semantic |

#### 分块策略说明
- `semantic`: 语义分块（推荐）
- `fixed`: 固定长度分块
- `paragraph`: 段落分块
- `sentence`: 句子分块

#### 响应参数
```json
{
  "id": 1,
  "filename": "技术文档.pdf",
  "original_filename": "技术文档.pdf",
  "file_size": 1024000,
  "file_type": "pdf",
  "knowledge_base_id": 1,
  "processing_status": "pending",
  "upload_time": "2024-01-01T12:00:00Z",
  "task_id": "task_123456",
  "message": "文档上传成功，正在处理中"
}
```

| 参数名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| id | int | 文档ID | 1 |
| filename | string | 存储文件名 | 技术文档.pdf |
| original_filename | string | 原始文件名 | 技术文档.pdf |
| file_size | int | 文件大小（字节） | 1024000 |
| file_type | string | 文件类型 | pdf |
| knowledge_base_id | int | 所属知识库ID | 1 |
| processing_status | string | 处理状态 | pending |
| upload_time | string | 上传时间 | 2024-01-01T12:00:00Z |
| task_id | string | 处理任务ID | task_123456 |
| message | string | 响应消息 | 文档上传成功，正在处理中 |

#### 错误码
- `400`: 文件格式不支持 / 文件大小超限 / 参数错误
- `403`: 无权访问指定知识库
- `404`: 知识库不存在
- `413`: 文件过大

---

### 3. 获取文档详情

**接口名称**: 获取文档详情  
**功能描述**: 获取指定文档的详细信息  
**接口地址**: `/api/v1/documents/{doc_id}`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| doc_id | int | 是 | 文档ID（路径参数） | 1 |

#### 响应参数
```json
{
  "id": 1,
  "filename": "技术文档.pdf",
  "original_filename": "技术文档.pdf",
  "file_size": 1024000,
  "file_type": "pdf",
  "knowledge_base_id": 1,
  "processing_status": "completed",
  "upload_time": "2024-01-01T12:00:00Z",
  "processed_time": "2024-01-01T12:05:00Z",
  "chunk_count": 25,
  "metadata": {
    "pages": 10,
    "paragraphs": 50,
    "tables": 3,
    "images": 5,
    "language": "zh",
    "processing_method": "marker",
    "extraction_time": "2024-01-01T12:05:00Z"
  },
  "processing_result": {
    "success": true,
    "content_length": 15000,
    "chunks": 25,
    "tables": 3,
    "images": 5,
    "error": null
  }
}
```

#### 错误码
- `404`: 文档不存在
- `403`: 无权访问此文档

---

### 4. 下载文档

**接口名称**: 下载文档  
**功能描述**: 下载指定的文档文件  
**接口地址**: `/api/v1/documents/{doc_id}/download`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| doc_id | int | 是 | 文档ID（路径参数） | 1 |

#### 响应参数
返回文件流，浏览器会自动下载文件。

#### 错误码
- `404`: 文档不存在或文件已删除
- `403`: 无权下载此文档

---

### 5. 删除文档

**接口名称**: 删除文档  
**功能描述**: 删除指定的文档及其相关数据  
**接口地址**: `/api/v1/documents/{doc_id}`  
**请求方式**: DELETE  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| doc_id | int | 是 | 文档ID（路径参数） | 1 |

#### 响应参数
```json
{
  "message": "文档已删除"
}
```

#### 错误码
- `404`: 文档不存在
- `403`: 无权删除此文档

---

### 6. 重新处理文档

**接口名称**: 重新处理文档  
**功能描述**: 重新处理已上传的文档  
**接口地址**: `/api/v1/documents/{doc_id}/reprocess`  
**请求方式**: POST  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| doc_id | int | 是 | 文档ID（路径参数） | 1 |
| chunk_strategy | string | 否 | 分块策略 | semantic |

#### 响应参数
```json
{
  "message": "文档重新处理已开始",
  "task_id": "task_789012",
  "status": "processing"
}
```

---

### 7. 获取处理状态

**接口名称**: 获取处理状态  
**功能描述**: 获取文档处理任务的状态  
**接口地址**: `/api/v1/documents/{doc_id}/status`  
**请求方式**: GET  
**认证**: 需要Bearer Token

#### 请求参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|-------|------|-----|------|--------|
| doc_id | int | 是 | 文档ID（路径参数） | 1 |

#### 响应参数
```json
{
  "document_id": 1,
  "processing_status": "completed",
  "progress": 100,
  "current_step": "向量化完成",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:05:00Z",
  "error_message": null,
  "result": {
    "chunks_created": 25,
    "vectors_created": 25,
    "tables_extracted": 3,
    "images_extracted": 5
  }
}
```

## 🔧 使用示例

### 完整文档管理流程
```bash
# 1. 上传文档
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf" \
  -F "knowledge_base_id=1" \
  -F "description=技术文档" \
  -F "language=zh" \
  -F "chunk_strategy=semantic"

# 2. 查看处理状态
curl -X GET "http://localhost:8000/api/v1/documents/1/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 3. 获取文档列表
curl -X GET "http://localhost:8000/api/v1/documents/?knowledge_base_id=1&page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. 获取文档详情
curl -X GET "http://localhost:8000/api/v1/documents/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 5. 下载文档
curl -X GET "http://localhost:8000/api/v1/documents/1/download" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o downloaded_document.pdf

# 6. 重新处理文档
curl -X POST "http://localhost:8000/api/v1/documents/1/reprocess" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chunk_strategy": "paragraph"}'

# 7. 删除文档
curl -X DELETE "http://localhost:8000/api/v1/documents/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚨 注意事项

1. **文件大小限制**: 单个文件最大支持100MB
2. **并发处理**: 系统支持多文档并发处理
3. **处理时间**: 处理时间取决于文件大小和复杂度
4. **存储管理**: 文档文件和向量数据分别存储
5. **权限控制**: 只能访问有权限的知识库中的文档
6. **格式支持**: 持续扩展支持的文件格式
7. **错误重试**: 处理失败的文档可以重新处理
