import streamlit as st
import json
import random
import requests
import time

# ==========================================
# 1. RunComfy Serverless API 함수
# ==========================================
BASE_URL = "https://api.runcomfy.net/prod/v1"

def runcomfy_generate_image(
    api_key: str,
    deployment_id: str,
    overrides: dict,
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
        st.error(f"❌ API 요청 실패: {e}")
        return None, {}

    # 2) Poll (대기)
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
            st.error(f"❌ 상태 확인 중 오류: {e}")
            return None, {}

    # 3) Result (결과 확보)
    result_res = requests.get(
        f"{BASE_URL}/deployments/{deployment_id}/requests/{request_id}/result",
        headers=headers,
        timeout=60,
    )
    result_res.raise_for_status()
    result_data = result_res.json()

    # 4) Parse Outputs
    outputs = result_data.get("outputs", {})
    parsed_images = {} 

    if isinstance(outputs, dict):
        for node_id, content in outputs.items():
            imgs = content.get("images", [])
            urls = [img.get("url") for img in imgs if img.get("url")]
            if urls:
                parsed_images[node_id] = urls

    return request_id, parsed_images


# ==========================================
# 2. Streamlit 앱 설정
# ==========================================
st.set_page_config(page_title="Storyboard Generator V3", layout="wide")

# Secrets 또는 사이드바 입력
api_key = st.sidebar.text_input("RunComfy API Key", value=st.secrets.get("RUNCOMFY_API_KEY", ""), type="password")
deployment_id = st.sidebar.text_input("Deployment ID", value=st.secrets.get("RUNCOMFY_DEPLOYMENT_ID", ""))

if not api_key or not deployment_id:
    st.warning("👈 사이드바에 API Key와 Deployment ID를 입력해주세요.")
    st.stop()

# 상태 초기화
if "step" not in st.session_state: st.session_state.step = 1
if "face_candidates" not in st.session_state: st.session_state.face_candidates = []
if "selected_face_url" not in st.session_state: st.session_state.selected_face_url = None
if "final_scene_url" not in st.session_state: st.session_state.final_scene_url = None


st.title("🎬 Storyboard Generator (Muter Control)")
st.caption("Using Fast Groups Muter (Node 78) for Control")

# ==========================================
# [STEP 1] 주인공 오디션 (얼굴 생성)
# ==========================================
if st.session_state.step == 1:
    st.header("Step 1. 주인공 캐스팅")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("AI가 4명의 배우 후보를 생성합니다.")
        batch_size = st.slider("생성할 후보 수", 1, 4, 4)

        if st.button("📸 오디션 시작", type="primary"):
            
            # [Step 1 전략]
            # Node 78 (Muter): match_1(Face)=YES, match_2(Body)=NO
            
            seed = random.randint(1, 2**31 - 1)
            
            overrides = {
                "78": {
                    "inputs": {
                        "match_1": "yes",  # Group 1 (Face) 켜기
                        "match_2": "no"    # Group 2 (Body) 끄기
                    }
                },
                "2": { "inputs": { "seed": seed } },      # Face Seed
                "24": { "inputs": { "batch_size": batch_size } }
            }

            with st.spinner("배우 섭외 중..."):
                req_id, outputs = runcomfy_generate_image(api_key, deployment_id, overrides)
                
                # Node 84 (Face SaveImage) 결과 확인
                if outputs and "84" in outputs:
                    st.session_state.face_candidates = outputs["84"]
                    st.rerun()
                elif outputs:
                    st.error(f"결과를 찾을 수 없습니다. (Node 84). 반환된 노드: {outputs.keys()}")

    if st.session_state.face_candidates:
        st.divider()
        st.subheader("마음에 드는 배우를 선택하세요")
        cols = st.columns(4)
        for idx, url in enumerate(st.session_state.face_candidates):
            with cols[idx % 4]:
                st.image(url, use_container_width=True)
                if st.button(f"✅ 선택 ({idx+1})", key=f"sel_{idx}"):
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
        prompt = st.text_area("촬영 프롬프트", 
                            value="white t-shirt, black pants, yellow sneakers, running in the park")
        
        if st.button("🎬 촬영 시작", type="primary"):
            
            # [Step 2 전략]
            # Node 78 (Muter): match_1(Face)=NO, match_2(Body)=YES
            # Node 85 (LoadImage): URL 주입
            
            seed = random.randint(1, 2**31 - 1)
            
            overrides = {
                "78": {
                    "inputs": {
                        "match_1": "no",   # Group 1 끄기
                        "match_2": "yes"   # Group 2 켜기
                    }
                },
                "47": { "inputs": { "seed": seed } },        # Body Seed
                "55": { "inputs": { "text": prompt } },      # Body Prompt
                "85": { 
                    "inputs": { 
                        "image": st.session_state.selected_face_url 
                    } 
                }
            }

            with st.spinner("촬영 진행 중..."):
                req_id, outputs = runcomfy_generate_image(api_key, deployment_id, overrides)
                
                # Node 54 (Body SaveImage) 결과 확인
                if outputs and "54" in outputs:
                    st.session_state.final_scene_url = outputs["54"][0]
                elif outputs:
                    st.error(f"결과를 찾을 수 없습니다 (Node 54). 반환된 노드: {outputs.keys()}")
    
    if st.session_state.final_scene_url:
        st.divider()
        st.success("촬영 완료!")
        st.image(st.session_state.final_scene_url, caption="Generated Scene", use_container_width=True)
