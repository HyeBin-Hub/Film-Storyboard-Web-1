# backend.py
import requests
import time

BASE_URL = "https://api.runcomfy.net/prod/v1"
DUMMY_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# 내부 함수도 api_key와 deployment_id를 인자로 받도록 수정
def _run_inference(overrides, api_key, deployment_id):
    
    if not api_key or not deployment_id:
        print("❌ API Key 또는 Deployment ID가 없습니다.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {"overrides": overrides}
    
    try:
        # 요청 전송
        res = requests.post(
            f"{BASE_URL}/deployments/{deployment_id}/inference",
            headers=headers,
            json=payload
        )
        res.raise_for_status()
        request_id = res.json()["request_id"]
        
        # ... (이하 대기 및 결과 처리 로직은 동일) ...
        # (생략: 위와 동일한 폴링 로직)
        
        # 간략화를 위해 결과 URL 리턴 부분만 남김
        while True:
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/deployments/{deployment_id}/requests/{request_id}/status", headers=headers)
            status = status_res.json().get("status", "").lower()
            
            if status == "completed": 
                break
            elif status in ["failed", "error"]: 
                return None
            
        result_res = requests.get(f"{BASE_URL}/deployments/{deployment_id}/requests/{request_id}/result", headers=headers)
        outputs = result_res.json().get("outputs", {})
        
        image_urls = []
        for node_id, content in outputs.items():
            for img in content.get("images", []):
                if img.get("url"): image_urls.append(img["url"])
        return image_urls

    except Exception as e:
        print(f"API Error: {e}")
        return None

# 외부에서 호출하는 함수들도 키를 인자로 받아야 함
def generate_faces(prompt_text, pm_options, api_key, deployment_id, batch_size=4):
    overrides = {
        "47": {"inputs": {"steps": 25}},
        "24": {"inputs": {"batch_size": batch_size}},
        "27": {"inputs": {"steps": 1}},
        "11": {"inputs": {
            "shot": pm_options.get("shot", "Half-length portrait"),
            "lighting_type": pm_options.get("lighting", "Natural Lighting"),
            "face_shape": pm_options.get("face_shape", "Oval"),
            "eyes_color": pm_options.get("eyes_color", "Brown"),
            "nationality_1": pm_options.get("nationality", "Korean")
        }},
        "10": {"inputs": {"text": prompt_text}},
        "85": {"inputs": {"image": DUMMY_IMAGE_BASE64}} 
    }
    return _run_inference(overrides, api_key, deployment_id)

def generate_full_body(face_image_url, outfit_prompt, api_key, deployment_id):
    overrides = {
        "47": {"inputs": {"steps": 1}}, 
        "27": {"inputs": {"steps": 30}}, 
        "85": {"inputs": {"image": face_image_url}}, 
        "55": {"inputs": {"text": outfit_prompt}}
    }
    return _run_inference(overrides, api_key, deployment_id)
