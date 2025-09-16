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
        
        # Parse input
        if request.content_type == 'application/json':
            data = request.get_json()
            if 'image' in data:
                image_data = base64.b64decode(data['image'])
                image = Image.open(io.BytesIO(image_data))
            else:
                return jsonify({'error': 'No image provided'}), 400
        else:
            image_data = request.data
            image = Image.open(io.BytesIO(image_data))
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
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
