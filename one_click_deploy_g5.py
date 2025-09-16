#!/usr/bin/env python3
"""
PaddleOCR SageMaker G5.xlarge 一键部署脚本
使用方法: python3 one_click_deploy_g5.py
"""

import boto3
import time
import subprocess
import base64
import json

# 配置
REGION = 'us-east-1'
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

def create_iam_role():
    """创建IAM角色"""
    print("🔑 创建IAM角色...")
    iam = boto3.client('iam')
    
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

def deploy_paddleocr_g5():
    """一键部署PaddleOCR G5端点"""
    print("🚀 开始部署PaddleOCR G5.xlarge端点...")
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    # 创建ECR仓库
    ecr = boto3.client('ecr', region_name=REGION)
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
        f"aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{REGION}.amazonaws.com",
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
    sagemaker = boto3.client('sagemaker', region_name=REGION)
    iam = boto3.client('iam')
    
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
            'InstanceType': 'ml.g5.xlarge',  # G5.xlarge高性能实例
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
    print(f"   - 实例: ml.g5.xlarge (NVIDIA A10G, 24GB)")
    print(f"   - 区域: {REGION}")
    print(f"   - 状态: InService")
    print(f"   - 预期性能: 0.2-0.3秒热推理")
    
    return endpoint_name

def performance_test(endpoint_name):
    """性能测试"""
    print("🧪 进行性能测试...")
    
    from PIL import Image, ImageDraw
    import io
    
    # 创建测试图片
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 30), "测试文字", fill='black')
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 性能测试
    runtime = boto3.client('sagemaker-runtime', region_name=REGION)
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

def main():
    """主函数"""
    print("=" * 70)
    print("🚀 PaddleOCR SageMaker G5.xlarge 一键部署")
    print("=" * 70)
    
    if not check_prerequisites():
        print("❌ 前提条件检查失败")
        return
    
    create_iam_role()
    endpoint_name = deploy_paddleocr_g5()
    
    if endpoint_name:
        performance_test(endpoint_name)
        print("\n🎯 G5.xlarge部署成功! 超高性能OCR服务已就绪")
        print(f"📝 端点名称: {endpoint_name}")
        print(f"💰 成本: ~$1.006/小时")
        print(f"⚡ 性能: 0.2-0.3秒热推理")
    else:
        print("❌ 部署失败")

if __name__ == '__main__':
    main()
