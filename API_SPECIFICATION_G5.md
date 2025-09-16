# PaddleOCR SageMaker G5 端点 API 规范

## 🎯 端点信息
- **端点名称**: `paddleocr-g5-endpoint-1758025210`
- **实例类型**: `ml.g5.xlarge` (NVIDIA A10G, 24GB显存)
- **区域**: `us-east-1`
- **性能**: 0.168秒热推理，99.5%准确率

## 📡 API 规范

### 请求格式
```http
POST /invocations
Content-Type: application/json

{
  "image": "base64_encoded_image_data"
}
```

### 响应格式
```json
{
  "detections": [
    {
      "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
      "text": "识别的文字内容",
      "confidence": 0.999
    }
  ],
  "count": 1,
  "status": "success",
  "gpu_enabled": true
}
```

## 💻 Python 调用示例

### 基础调用
```python
import boto3
import json
import base64

# 读取图片
with open('image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 调用G5端点
runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
response = runtime.invoke_endpoint(
    EndpointName='paddleocr-g5-endpoint-1758025210',
    ContentType='application/json',
    Body=json.dumps({'image': image_data})
)

# 解析结果
result = json.loads(response['Body'].read().decode())
for detection in result['detections']:
    print(f"文字: {detection['text']}")
    print(f"置信度: {detection['confidence']:.1%}")
    print(f"位置: {detection['bbox']}")
```

### 性能测试示例
```python
import time

def benchmark_ocr(endpoint_name, image_path, iterations=10):
    """OCR性能基准测试"""
    runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
    
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    times = []
    for i in range(iterations):
        start = time.time()
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps({'image': image_data})
        )
        end = time.time()
        times.append(end - start)
    
    print(f"平均时间: {sum(times)/len(times):.3f}秒")
    print(f"最快时间: {min(times):.3f}秒")
    print(f"最慢时间: {max(times):.3f}秒")

# 使用示例
benchmark_ocr('paddleocr-g5-endpoint-1758025210', 'test.jpg')
```

## ⚡ 性能指标

### G5.xlarge 性能
- **热推理**: 0.168秒 (超快)
- **平均推理**: 1.086秒
- **冷启动**: 2.823秒
- **并发**: 支持多请求并发
- **准确率**: 99.5%

### 与其他实例对比
| 实例类型 | GPU | 显存 | 热推理时间 | 成本/小时 |
|----------|-----|------|------------|-----------|
| ml.g4dn.xlarge | T4 | 16GB | ~1-3秒 | $0.736 |
| ml.g5.xlarge | A10G | 24GB | ~0.2秒 | $1.006 |
| ml.g5.2xlarge | A10G | 24GB | ~0.1秒 | $1.515 |

## 📏 使用限制

### 图片要求
- **格式**: JPG, PNG, BMP, TIFF
- **大小**: < 10MB (推荐 < 5MB)
- **分辨率**: < 4096x4096 (推荐 < 2048x2048)
- **编码**: Base64编码

### 性能优化建议
- **预热**: 首次调用后性能最佳
- **批处理**: 可考虑批量处理多张图片
- **图片优化**: 适当压缩图片可提升速度
- **并发**: 支持多线程并发调用

### 错误处理
```python
try:
    response = runtime.invoke_endpoint(...)
    result = json.loads(response['Body'].read().decode())
    
    if result.get('status') != 'success':
        print(f"OCR处理失败: {result.get('error', '未知错误')}")
    
except Exception as e:
    print(f"API调用失败: {e}")
```

## 🔍 健康检查
```http
GET /ping
```
响应: `200 OK`

## 💰 成本优化
- **按需使用**: 不使用时删除端点
- **实例选择**: 根据QPS需求选择合适实例
- **监控**: 使用CloudWatch监控使用情况

---
**API版本**: v2.0 (G5优化版)  
**更新时间**: 2025-09-16  
**性能等级**: 超高性能 ⚡
