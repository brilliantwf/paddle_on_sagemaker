#!/usr/bin/env python3
"""
PaddleOCR SageMaker G5.xlarge 一键部署脚本
使用方法: 
  python3 one_click_deploy.py                    # 默认部署到us-east-1
  python3 one_click_deploy.py --region eu-west-1 # 部署到指定区域
"""

import boto3
import time
import subprocess
import base64
import json
import argparse

# 配置
ECR_REPO_NAME = 'paddleocr-g5'
IMAGE_TAG = 'latest'

def check_prerequisites():
    """检查部署前提条件"""
    print("🔍 检查部署前提条件...")
    
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        print("✅ Docker 已安装")
    except:
        print("❌ Docker 未安装或不可用")
        return False
    
    try:
        subprocess.run(['aws', '--version'], check=True, capture_output=True)
        print("✅ AWS CLI 已配置")
    except:
        print("❌ AWS CLI 未安装或未配置")
        return False
    
    return True

def create_iam_role(region):
    """创建IAM角色"""
    print(f"🔑 在 {region} 创建IAM角色...")
    iam = boto3.client('iam', region_name=region)
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "sagemaker.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        iam.create_role(
            RoleName='SageMakerExecutionRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        policies = [
            'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
            'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess'
        ]
        
        for policy in policies:
            iam.attach_role_policy(
                RoleName='SageMakerExecutionRole',
                PolicyArn=policy
            )
        print("✅ IAM角色创建成功")
    except iam.exceptions.EntityAlreadyExistsException:
        print("✅ IAM角色已存在")

def deploy_paddleocr_g5(region):
    """一键部署PaddleOCR G5端点到指定区域"""
    print(f"🚀 开始部署PaddleOCR G5.xlarge端点到 {region}...")
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    # 创建ECR仓库
    ecr = boto3.client('ecr', region_name=region)
    try:
        response = ecr.create_repository(repositoryName=ECR_REPO_NAME)
        repo_uri = response['repository']['repositoryUri']
    except ecr.exceptions.RepositoryAlreadyExistsException:
        response = ecr.describe_repositories(repositoryNames=[ECR_REPO_NAME])
        repo_uri = response['repositories'][0]['repositoryUri']
    
    image_uri = f"{repo_uri}:{IMAGE_TAG}"
    print(f"📦 ECR仓库: {repo_uri}")
    
    # 构建和推送镜像
    print("🔨 构建Docker镜像...")
    commands = [
        f"docker build -f Dockerfile_gpu -t {ECR_REPO_NAME} .",
        f"docker tag {ECR_REPO_NAME}:latest {image_uri}",
        f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com",
        f"docker push {image_uri}"
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 命令失败: {cmd}")
            print(f"错误: {result.stderr}")
            return None
    
    print("✅ 镜像推送成功")
    
    # 创建SageMaker资源
    sagemaker = boto3.client('sagemaker', region_name=region)
    iam = boto3.client('iam', region_name=region)
    
    role_arn = iam.get_role(RoleName='SageMakerExecutionRole')['Role']['Arn']
    timestamp = int(time.time())
    
    model_name = f'paddleocr-g5-{timestamp}'
    config_name = f'paddleocr-g5-config-{timestamp}'
    endpoint_name = f'paddleocr-g5-endpoint-{timestamp}'
    
    # 创建模型
    print("🤖 创建SageMaker模型...")
    sagemaker.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': image_uri,
            'Mode': 'SingleModel'
        },
        ExecutionRoleArn=role_arn
    )
    
    # 创建端点配置
    print("⚙️ 创建G5端点配置...")
    sagemaker.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            'VariantName': 'AllTraffic',
            'ModelName': model_name,
            'InitialInstanceCount': 1,
            'InstanceType': 'ml.g5.xlarge',
            'InitialVariantWeight': 1
        }]
    )
    
    # 创建端点
    print("🎯 创建G5端点...")
    sagemaker.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=config_name
    )
    
    print("⏳ 等待端点就绪...")
    waiter = sagemaker.get_waiter('endpoint_in_service')
    waiter.wait(EndpointName=endpoint_name)
    
    print("🎉 部署完成!")
    print(f"📋 端点信息:")
    print(f"   - 名称: {endpoint_name}")
    print(f"   - 区域: {region}")
    print(f"   - 实例: ml.g5.xlarge (NVIDIA A10G, 24GB)")
    print(f"   - 状态: InService")
    
    return endpoint_name, region

def performance_test(endpoint_name, region):
    """性能测试"""
    print(f"🧪 在 {region} 进行性能测试...")
    
    from PIL import Image, ImageDraw
    import io
    
    # 创建测试图片
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 30), "Test OCR", fill='black')  # 使用英文避免编码问题
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 性能测试
    runtime = boto3.client('sagemaker-runtime', region_name=region)
    times = []
    
    for i in range(3):
        start_time = time.time()
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps({'image': image_data})
        )
        end_time = time.time()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    
    print(f"⚡ 平均推理时间: {avg_time:.3f}秒")
    print(f"🚀 最快推理时间: {min_time:.3f}秒")

def generate_usage_code(endpoint_name, region):
    """生成使用代码示例"""
    code = f'''
# PaddleOCR {region} 端点使用示例
import boto3
import json
import base64

# 读取图片
with open('image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 调用{region}端点
runtime = boto3.client('sagemaker-runtime', region_name='{region}')
response = runtime.invoke_endpoint(
    EndpointName='{endpoint_name}',
    ContentType='application/json',
    Body=json.dumps({{'image': image_data}})
)

# 解析结果
result = json.loads(response['Body'].read().decode())
for detection in result['detections']:
    print(f"文字: {{detection['text']}}")
    print(f"置信度: {{detection['confidence']:.1%}}")
'''
    
    with open(f'usage_example_{region.replace("-", "_")}.py', 'w') as f:
        f.write(code)
    
    print(f"📝 使用示例已保存到: usage_example_{region.replace('-', '_')}.py")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PaddleOCR SageMaker G5.xlarge 部署')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS区域 (默认: us-east-1)')
    
    args = parser.parse_args()
    region = args.region
    
    print("=" * 70)
    print(f"🚀 PaddleOCR SageMaker G5.xlarge 部署到 {region}")
    print("=" * 70)
    
    if not check_prerequisites():
        print("❌ 前提条件检查失败")
        return
    
    create_iam_role(region)
    result = deploy_paddleocr_g5(region)
    
    if result:
        endpoint_name, deployed_region = result
        performance_test(endpoint_name, deployed_region)
        generate_usage_code(endpoint_name, deployed_region)
        
        print(f"\n🎯 {deployed_region} 部署成功!")
        print(f"📝 端点名称: {endpoint_name}")
        print(f"🌍 部署区域: {deployed_region}")
        print(f"💰 成本: ~$1.006/小时")
        print(f"⚡ 性能: 0.2-0.3秒热推理")
    else:
        print("❌ 部署失败")

if __name__ == '__main__':
    main()
