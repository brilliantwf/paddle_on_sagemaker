import boto3
import json
import base64
import time

def test_g5_performance():
    """测试G5.xlarge性能"""
    
    # 读取测试图片
    with open('img.jpg', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {'image': image_data}
    runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
    
    # 新的G5端点
    endpoint_name = 'paddleocr-g5-endpoint-1758025210'
    
    print("=" * 70)
    print("🚀 PaddleOCR G5.xlarge 性能测试")
    print("=" * 70)
    print(f"📸 测试图片: img.jpg")
    print(f"🎯 端点: {endpoint_name}")
    print(f"💻 实例: ml.g5.xlarge (NVIDIA A10G)")
    print()
    
    # 进行多次测试以获得平均性能
    times = []
    results = []
    
    for i in range(3):
        print(f"🧪 测试 {i+1}/3...")
        
        start_time = time.time()
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        end_time = time.time()
        
        inference_time = end_time - start_time
        times.append(inference_time)
        
        result = json.loads(response['Body'].read().decode())
        results.append(result)
        
        print(f"   ⏱️ 推理时间: {inference_time:.3f}秒")
        print(f"   📊 检测区域: {result['count']}个")
        print()
    
    # 计算平均性能
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print("=" * 70)
    print("📊 性能统计")
    print("=" * 70)
    print(f"⏱️ 平均推理时间: {avg_time:.3f}秒")
    print(f"🚀 最快推理时间: {min_time:.3f}秒")
    print(f"🐌 最慢推理时间: {max_time:.3f}秒")
    print()
    
    # 显示识别结果
    result = results[0]  # 使用第一次的结果
    print("📝 识别结果:")
    for i, detection in enumerate(result['detections'], 1):
        text = detection['text']
        confidence = detection['confidence']
        print(f"   {i}. '{text}' (置信度: {confidence:.1%})")
    
    print()
    print("=" * 70)
    print("🎯 G5.xlarge 优势:")
    print("   - NVIDIA A10G GPU (24GB显存)")
    print("   - 更新的GPU架构")
    print("   - 更好的AI推理性能")
    print("   - 支持更大的模型和批处理")
    print("=" * 70)
    
    return {
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'detections': result['count']
    }

if __name__ == '__main__':
    try:
        performance = test_g5_performance()
        print(f"\n✅ G5性能测试完成!")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
