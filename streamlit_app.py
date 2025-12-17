import streamlit as st
import json
import random
import requests
import time

# ==========================================
# 1. RunComfy Serverless API 함수 (사용자 코드 기반 수정)
# ==========================================
BASE_URL = "https://api.runcomfy.net/prod/v1"

def runcomfy_generate_image(
    api_key: str,
    deployment_id: str,
    overrides: dict,  # ★ 핵심 수정: 고정된 payload 대신 외부에서 주입받음
    poll_interval: int = 2,
):
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    # Payload 구성
    payload = {
        "overrides": overrides
    }

    # 1) Submit
    try:
        submit_res = requests.post(
            f"{BASE_URL}/deployments/{deployment_id}/inference",
            headers=headers,
            json=payload,
            timeout=60,
        )
        submit_res.raise_for_status()
        request_id = submit_res.json()["request_id"]
    except Exception as e:
        st.error(f"API 요청 실패: {e}")
        return None, None

    # 2) Poll
    while True:
        try:
            st_res = requests.get(
                f"{BASE_URL}/deployments/{deployment_id}/requests/{request_id}/status",
                headers=headers,
                timeout=60,
            )
            st_res.raise_for_status()
            status_data = st_res.json()
            status = (status_data.get("status") or "").lower()

            if status in ("succeeded", "completed"):
                break
            if status in ("failed", "error"):
                raise RuntimeError(f"Run failed: {status_data}")
            
            time.sleep(poll_interval)
        except Exception as e:
            st.error(f"상태 확인 중 오류: {e}")
            return None, None

    # 3) Result
    result_res = requests.get(
        f"{BASE_URL}/deployments/{deployment_id}/requests/{request_id}/result",
        headers=headers,
        timeout=60,
    )
    result_res.raise_for_status()
    result_data = result_res.json()

    # 4) Parse Outputs (모든 이미지 수집)
    # 특정 노드만 찾는 게 아니라, 출력된 모든 이미지를 리스트로 반환
    outputs = result_data.get("outputs", {})
    image_urls = []

    if isinstance(outputs, dict):
        for node_id, content in outputs.items():
            imgs = content.get("images", [])
            for img in imgs:
                image_urls.append(img.get("url"))

    return request_id, image_urls


# ==========================================
# 2. Streamlit 앱 설정
# ==========================================
st.set_page_config(page_title="Storyboard Generator", layout="wide")

# Secrets에서 키 가져오기 (없으면 UI에서 입력)
api_key = st.sidebar.text_input("RunComfy API Key", value=st.secrets.get("RUNCOMFY_API_KEY", ""), type="password")
deployment_id = st.sidebar.text_input("Deployment ID", value=st.secrets.get("RUNCOMFY_DEPLOYMENT_ID", ""))

if not api_key or not deployment_id:
    st.warning("좌측 사이드바에 API Key와 Deployment ID를 입력해주세요.")
    st.stop()

# 상태 초기화
if "step" not in st.session_state: st.session_state.step = 1
if "face_candidates" not in st.session_state: st.session_state.face_candidates = []
if "selected_face_url" not in st.session_state: st.session_state.selected_face_url = None
if "final_scene_url" not in st.session_state: st.session_state.final_scene_url = None


st.title("🎬 Storyboard Generator (Serverless)")
st.markdown("RunComfy Serverless API를 사용하여 주인공을 캐스팅하고 씬을 생성합니다.")

# ==========================================
# [STEP 1] 주인공 오디션 (얼굴 생성)
# ==========================================
if st.session_state.step == 1:
    st.header("Step 1. 주인공 캐스팅")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("AI가 4명의 배우 후보를 생성합니다.")
        if st.button("📸 오디션 시작", type="primary"):
            
            # [Step 1 Payload]
            # Muter(Node 78): Group 1 ON ("yes"), Group 2 OFF ("no")
            # Face Seed(Node 2): Random
            seed = random.randint(1, 2**31 - 1)
            
            overrides = {
                "78": {
                    "inputs": {
                        "match_1": "yes",
                        "match_2": "no"
                    }
                },
                "2": {
                    "inputs": {
                        "seed": seed
                    }
                }
            }

            with st.spinner("배우 섭외 중..."):
                req_id, img_urls = runcomfy_generate_image(api_key, deployment_id, overrides)
                
                if img_urls:
                    st.session_state.face_candidates = img_urls
                    st.rerun()

    # 결과 표시 및 선택
    if st.session_state.face_candidates:
        st.divider()
        cols = st.columns(4)
        for idx, url in enumerate(st.session_state.face_candidates):
            with cols[idx]:
                st.image(url, use_container_width=True)
                if st.button(f"✅ {idx+1}번 배우 선택", key=f"sel_{idx}"):
                    st.session_state.selected_face_url = url
                    st.session_state.step = 2
                    st.rerun()

# ==========================================
# [STEP 2] 전신 촬영 (스토리보드 생성)
# ==========================================
elif st.session_state.step == 2:
    st.header("Step 2. 씬(Scene) 생성")
    
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.image(st.session_state.selected_face_url, caption="선택된 주인공", width=200)
        if st.button("⬅️ 다시 뽑기"):
            st.session_state.step = 1
            st.rerun()
            
    with col_r:
        prompt = st.text_area("촬영 프롬프트", value="white t-shirt, black pants, running in the rain, cyberpunk city background")
        
        if st.button("🎬 촬영 시작", type="primary"):
            
            # [Step 2 Payload]
            # Muter(Node 78): Group 1 OFF ("no"), Group 2 ON ("yes")
            # Image Input(Node 83): 선택된 이미지 URL 주입
            # Text Input(Node 55): 프롬프트 입력
            # Body Seed(Node 47): Random
            
            seed = random.randint(1, 2**31 - 1)
            
            overrides = {
                "78": {
                    "inputs": {
                        "match_1": "no",
                        "match_2": "yes"
                    }
                },
                "83": {
                    "inputs": {
                        # Serverless 환경에서는 URL로 이미지를 전달하는 것이 가장 안전합니다.
                        # Node 83이 LoadImage라면 URL 처리가 안될 수 있으므로, 
                        # 워크플로우에서 LoadImageFromURL 같은 노드를 쓰거나 
                        # RunComfy가 지원하는 이미지 입력 방식을 확인해야 합니다.
                        # 여기서는 사용자가 제공한 방식대로 'image' input에 URL을 넣습니다.
                        "image": st.session_state.selected_face_url
                    }
                },
                "55": {
                    "inputs": {
                        "text": prompt
                    }
                },
                "47": {
                    "inputs": {
                        "seed": seed
                    }
                }
            }

            with st.spinner("촬영 진행 중..."):
                req_id, img_urls = runcomfy_generate_image(api_key, deployment_id, overrides)
                
                if img_urls:
                    # 결과 중 마지막 이미지(전신)를 선택
                    st.session_state.final_scene_url = img_urls[0] 
    
    if st.session_state.final_scene_url:
        st.divider()
        st.success("촬영 완료!")
        st.image(st.session_state.final_scene_url, caption="Generated Scene", use_container_width=True)
