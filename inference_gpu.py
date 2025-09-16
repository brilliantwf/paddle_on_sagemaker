import os
import json
import base64
import io
from flask import Flask, request, jsonify
from PIL import Image
import numpy as np
import cv2

app = Flask(__name__)

# Global OCR instance
ocr = None

def init_ocr():
    """Initialize PaddleOCR with GPU"""
    global ocr
    if ocr is None:
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(
                use_angle_cls=True, 
                lang='ch', 
                det=True, 
                rec=True, 
                use_gpu=True,
                show_log=False
            )
            print("PaddleOCR initialized successfully with GPU")
        except Exception as e:
            print(f"Failed to initialize PaddleOCR: {e}")
            ocr = None
    return ocr

@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return '', 200

@app.route('/invocations', methods=['POST'])
def predict():
    """Main inference endpoint"""
    try:
        # Initialize OCR if needed
        ocr_instance = init_ocr()
        if ocr_instance is None:
            return jsonify({'error': 'PaddleOCR not available'}), 500
        
        # Input validation and size limits
        MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB limit
        
        # Parse input
        if request.content_type == 'application/json':
            data = request.get_json()
            if not data or 'image' not in data:
                return jsonify({'error': 'No image provided'}), 400
            
            try:
                image_data = base64.b64decode(data['image'])
                if len(image_data) > MAX_IMAGE_SIZE:
                    return jsonify({'error': 'Image too large (max 10MB)'}), 400
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                return jsonify({'error': 'Invalid image data'}), 400
        else:
            image_data = request.data
            if len(image_data) > MAX_IMAGE_SIZE:
                return jsonify({'error': 'Image too large (max 10MB)'}), 400
            try:
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                return jsonify({'error': 'Invalid image format'}), 400
        
        # Validate image dimensions
        if image.size[0] > 4096 or image.size[1] > 4096:
            return jsonify({'error': 'Image dimensions too large (max 4096x4096)'}), 400
        
        # Convert PIL to numpy array safely
        img_array = np.array(image)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        elif len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        else:
            return jsonify({'error': 'Unsupported image format'}), 400
        
        # Run OCR
        result = ocr_instance.ocr(img_array, det=True, rec=True)
        
        # Format results
        detections = []
        if result and result[0]:
            for detection in result[0]:
                bbox = detection[0]
                text_info = detection[1]
                text = text_info[0] if text_info else ""
                confidence = text_info[1] if text_info else 0.0
                
                detections.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence
                })
        
        return jsonify({
            'detections': detections,
            'count': len(detections),
            'status': 'success',
            'gpu_enabled': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Pre-initialize OCR
    init_ocr()
    app.run(host='0.0.0.0', port=8080)
