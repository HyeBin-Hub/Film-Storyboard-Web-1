import requests
import time
import json
import base64

# =================================================================
# 설정: 본인의 API KEY와 DEPLOYMENT ID로 교체하세요
# =================================================================
BASE_URL = "https://api.runcomfy.net/prod/v1"

# 에러 방지용 1x1 투명 픽셀 (Step 1에서 PuLID 노드가 비어있으면 에러나는 것 방지)
DUMMY_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

def _run_inference(overrides):
    """ComfyUI 서버에 요청을 보내고 결과를 기다리는 내부 함수"""
    headers = {
        "Authorization": f"Bearer {RUNCOMFY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {"overrides": overrides}
    
    try:
        # 1. 요청 전송
        res = requests.post(
            f"{BASE_URL}/deployments/{DEPLOYMENT_ID}/inference",
            headers=headers,
            json=payload
        )
        res.raise_for_status()
        request_id = res.json()["request_id"]
        
        # 2. 대기 (Polling)
        while True:
            time.sleep(2)
            status_res = requests.get(
                f"{BASE_URL}/deployments/{DEPLOYMENT_ID}/requests/{request_id}/status",
                headers=headers
            )
            status = status_res.json().get("status", "").lower()
            
            if status == "completed":
                break
            elif status in ["failed", "error"]:
                print(f"Error Details: {status_res.json()}")
                return None
        
        # 3. 결과 이미지 URL 추출
        result_res = requests.get(
            f"{BASE_URL}/deployments/{DEPLOYMENT_ID}/requests/{request_id}/result",
            headers=headers
        )
        outputs = result_res.json().get("outputs", {})
        
        image_urls = []
        for node_id, content in outputs.items():
            for img in content.get("images", []):
                if img.get("url"):
                    image_urls.append(img["url"])
        
        return image_urls

    except Exception as e:
        print(f"API Error: {e}")
        return None

def generate_faces(prompt_text, pm_options, batch_size=4):
    """
    Step 1: 얼굴 생성 (Node 27 ON, Node 47 OFF)
    """
    overrides = {
        # --- Node 27 (Portrait KSampler) 설정 ---
        "27": {"inputs": {"steps": 25}},  # 활성화
        "24": {"inputs": {"batch_size": batch_size}}, # 몇 장 생성할지
        
        # --- Node 47 (Body KSampler) 끄기 ---
        "47": {"inputs": {"steps": 1}},   # 스킵
        
        # --- Portrait Master (Node 11) 옵션 적용 ---
        "11": {"inputs": {
            "shot": pm_options.get("shot", "Half-length portrait"),
            "lighting_type": pm_options.get("lighting", "Natural Lighting"), # JSON에 없다면 기본값 사용
            "face_shape": pm_options.get("face_shape", "Oval"),
            "eyes_color": pm_options.get("eyes_color", "Brown"),
            "nationality_1": pm_options.get("nationality", "Korean")
        }},
        
        # --- Text Prompt (Node 10) ---
        "10": {"inputs": {"text": prompt_text}},
        
        # --- 에러 방지: Node 85에 더미 이미지 주입 ---
        "85": {"inputs": {"image": DUMMY_IMAGE_BASE64}} 
    }
    
    return _run_inference(overrides)

def generate_full_body(face_image_url, outfit_prompt):
    """
    Step 2: 전신 의상 생성 (Node 27 OFF, Node 47 ON)
    """
    # URL 이미지를 ComfyUI가 읽으려면, 보통 Base64 변환하거나 RunComfy가 URL 처리를 지원해야 함.
    # 여기서는 URL을 직접 넘기는 방식을 시도하되, 만약 에러가 나면 다운로드 후 Base64로 변환하는 로직이 필요할 수 있습니다.
    # RunComfy API는 종종 URL을 'image' 필드에 넣으면 처리해줍니다.
    
    overrides = {
        # --- Node 27 (Portrait KSampler) 끄기 ---
        "27": {"inputs": {"steps": 1}}, 
        
        # --- Node 47 (Body KSampler) 켜기 ---
        "47": {"inputs": {"steps": 30}}, 
        
        # --- Node 85 (Load Image)에 선택한 얼굴 이미지 주입 ---
        # 중요: RunComfy에서 URL 직접 입력을 지원하지 않을 경우, 
        # requests로 이미지를 받아 base64로 변환해서 보내야 합니다.
        "85": {"inputs": {"image": face_image_url}}, 
        
        # --- 의상 프롬프트 (Node 55) ---
        "55": {"inputs": {"text": outfit_prompt}}
    }
    
    return _run_inference(overrides)
