# PaddleOCR 文本识别 - SageMaker Serverless Inference

## 部署步骤

### 1. 准备环境
```bash
# 安装依赖
pip install -r requirements.txt

# 确保Docker已安装并运行
docker --version
```

### 2. 创建IAM角色
创建名为 `SageMakerExecutionRole` 的IAM角色，附加以下策略：
- AmazonSageMakerFullAccess
- AmazonEC2ContainerRegistryFullAccess

### 3. 部署模型
```bash
python deploy.py
```

### 4. 测试端点
```bash
# 修改 test_endpoint.py 中的端点名称和测试图片路径
python test_endpoint.py
```

## API 使用

### 输入格式
```json
{
  "image": "base64_encoded_image_data"
}
```

### 输出格式
```json
{
  "detections": [
    {
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "text": "识别的文字内容",
      "confidence": 0.95
    }
  ],
  "count": 1
}
```

## 配置说明

- **内存**: 2048MB (可在deploy.py中调整)
- **最大并发**: 5 (可调整)
- **支持格式**: JPG, PNG等常见图片格式
- **检测语言**: 中文 (可在inference.py中修改lang参数)
- **功能**: 文本检测 + 文字识别
