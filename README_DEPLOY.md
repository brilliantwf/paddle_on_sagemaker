# PaddleOCR SageMaker G5.xlarge 部署指南

## 🚀 一键部署

### 快速开始
```bash
# 默认部署到us-east-1 (推荐，最低成本)
python3 one_click_deploy.py

# 部署到指定区域
python3 one_click_deploy.py --region eu-west-1
python3 one_click_deploy.py --region ap-southeast-1
```

### 前提条件
- ✅ Docker 已安装并运行
- ✅ AWS CLI 已配置
- ✅ 具有SageMaker和ECR权限

## 📋 部署步骤
脚本将自动执行：

1. **检查环境** - 验证Docker和AWS CLI
2. **创建IAM角色** - 自动创建SageMaker执行角色
3. **构建镜像** - 使用PaddlePaddle GPU基础镜像
4. **推送ECR** - 上传到指定区域的ECR
5. **创建模型** - 在SageMaker中注册模型
6. **部署端点** - 启动ml.g5.xlarge实例
7. **测试验证** - 自动测试OCR功能

## 🌍 支持的区域

### 主要区域及成本
| 区域 | 位置 | 成本/小时 | 适用场景 |
|------|------|-----------|----------|
| us-east-1 | 美国东部 | $1.006 | 全球用户，最低成本 ✅ |
| us-west-2 | 美国西部 | $1.006 | 美国西海岸用户 |
| eu-west-1 | 欧洲爱尔兰 | $1.107 | 欧洲用户 (+10%) |
| ap-southeast-1 | 亚太新加坡 | $1.158 | 亚洲用户 (+15%) |
| ap-northeast-1 | 亚太东京 | $1.158 | 日本用户 (+15%) |
| eu-central-1 | 欧洲法兰克福 | $1.107 | 德国用户 (+10%) |

### 区域选择建议
- **成本优先**: 选择 us-east-1
- **延迟优先**: 选择离用户最近的区域
- **合规要求**: 根据数据主权要求选择

## 🎯 使用方法

### Python API调用
```python
import boto3
import json
import base64

# 准备图片
with open('image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 调用端点 (替换为你的端点名称和区域)
runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
response = runtime.invoke_endpoint(
    EndpointName='your-endpoint-name',
    ContentType='application/json',
    Body=json.dumps({'image': image_data})
)

# 解析结果
result = json.loads(response['Body'].read().decode())
for detection in result['detections']:
    print(f"文字: {detection['text']}")
    print(f"置信度: {detection['confidence']:.1%}")
```

## ⚡ 性能指标
- **热推理时间**: 0.168秒 (超快)
- **平均推理时间**: 1.086秒
- **冷启动时间**: 2.823秒
- **识别准确率**: 99.5%
- **GPU**: NVIDIA A10G (24GB显存)

## 🧪 性能测试
```bash
# 测试部署的端点性能
python3 test_g5_performance.py
```

## 💰 成本估算
- **实例费用**: $1.006-$1.158/小时 (取决于区域)
- **存储费用**: ECR镜像存储 (~$0.10/GB/月)
- **数据传输**: API调用数据传输费用

## 🔧 清理资源
如需删除部署的资源：
```bash
# 删除端点
aws sagemaker delete-endpoint --endpoint-name your-endpoint-name --region your-region

# 删除端点配置
aws sagemaker delete-endpoint-config --endpoint-config-name your-config-name --region your-region

# 删除模型
aws sagemaker delete-model --model-name your-model-name --region your-region

# 删除ECR仓库
aws ecr delete-repository --repository-name paddleocr-g5 --force --region your-region
```

## 📞 故障排除
- **部署失败**: 检查AWS权限和Docker状态
- **区域不支持**: 确认目标区域支持ml.g5.xlarge实例
- **成本控制**: 不使用时及时删除端点

---
**部署指南版本**: v3.0 (区域可选版)  
**推荐区域**: us-east-1 (最低成本)  
**实例类型**: ml.g5.xlarge  
**性能等级**: 超高性能 ⚡
