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
def generate_faces(prompt_text, pm_options, api_key, deployment_id, widht, height, batch_size=4):
    overrides = {        
        "10": {"inputs": {"text": prompt_text}},
        "11": {"inputs": {
              "gender": pm_options.get("Man","Woman"),
              "nationality_1":pm_options.get("Chinese","Japanese","Korean","South Korean","Indian","Saudi","British","French","German","Italian","Spanish","American","Canadian","Brazilian","Mexican","Argentine","Egyptian","South African","Nigerian","Kenyan","Moroccan","Australian","New Zealander","Fijian","Samoan","Tongan"),
              "body_type": pm_options.get("Chubby","Curvy","Fat","Fit","Hefty","Large","Lanky","Muscular","Obese","Overweight","Petite","Plump","Short","Skinny","Slight","Slim","Small","Stout","Stocky","Tall","Thick","Tiny","Underweight","Well-built"]),
              "eyes_color": pm_options.get("Albino", "Amber", "Blue", "Brown", "Green", "Gray", "Hazel", "Heterochromia", "Red", "Violet"),
              "eyes_shape": pm_options.get("Almond Eyes Shape","Asian Eyes Shape","Close-Set Eyes Shape","Deep Set Eyes Shape","Downturned Eyes Shape","Double Eyelid Eyes Shape","Hooded Eyes Shape","Monolid Eyes Shape","Oval Eyes Shape","Protruding Eyes Shape","Round Eyes Shape","Upturned Eyes Shape"),
              "lips_color": pm_options.get("Berry Lips","Black Lips","Blue Lips","Brown Lips","Burgundy Lips","Coral Lips","Glossy Red Lips","Mauve Lips","Orange Lips","Peach Lips","Pink Lips","Plum Lips","Purple Lips","Red Lips","Yellow Lips"),
              "lips_shape": pm_options.get("Full Lips","Thin Lips","Plump Lips","Small Lips","Large Lips","Wide Lips","Round Lips","Heart-shaped Lips","Cupid's Bow Lips"),
              "face_shape": pm_options.get("Oval","Round","Square","Heart","Diamond","Triangle","Inverted Triangle","Pear","Rectangle","Oblong","Long"),
              "hair_style": pm_options.get("Bald","Buzz","Crew","Pixie","Bob","Long bob","Long straight","Wavy","Curly","Afro","Faded afro","Braided","Box braids","Cornrows","Dreadlocks","Pigtails","Ponytail","High ponytail","Bangs","Curtain bangs","Side-swept bangs","Mohawk","Faux hawk","Undercut","Pompadour","Quiff","Top Knot","Bun","Updo"),
              "hair_color": pm_options.get("Black","Jet Black","Blonde","Platinum","Brown","Chestnut","Auburn","Red","Strawberry","Gray","Silver","White","Salt and pepper"),
              "hair_length": pm_options.get("Short","Medium","Long"),
              "beard": pm_options.get("Stubble Beard","Goatee","Full Beard","Van Dyke Beard","Circle Beard","Balbo Beard","Ducktail Beard","Chinstrap Beard","Chevron Mustache","Handlebar Mustache","Horseshoe Mustache","Pencil Mustache"),
              "beard_color": pm_options.get("Black","Jet Black","Blonde","Platinum","Brown","Chestnut","Auburn","Red","Strawberry","Gray","Silver","White","Salt and pepper")}},
        "24" : {"inputs":{"width": widht,"height": height, "batch_size": batch_size}},
        "47": {"inputs": {"steps": 1}},
        "27": {"inputs": {"steps": 25}},
        "85": {"inputs": {"image": DUMMY_IMAGE_BASE64}} 
        }
    return _run_inference(overrides, api_key, deployment_id)

def generate_full_body(face_image_url, outfit_prompt, api_key, deployment_id):
    overrides = {
        "47": {"inputs": {"steps": 25}}, 
        "27": {"inputs": {"steps": 1}}, 
        "85": {"inputs": {"image": face_image_url}}, 
        "55": {"inputs": {"text": outfit_prompt}}
    }
    return _run_inference(overrides, api_key, deployment_id)
