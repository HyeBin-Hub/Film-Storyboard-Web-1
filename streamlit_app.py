# app.py 상단 부분 수정

import streamlit as st
import backend

st.set_page_config(page_title="Movie Character Creator", layout="wide")

# --- 🔑 API Key 관리 로직 ---
st.sidebar.title("🔐 API 설정")

# 1. secrets.toml 파일에서 먼저 찾아봄
if "RUNCOMFY_API_KEY" in st.secrets:
    api_key = st.secrets["RUNCOMFY_API_KEY"]
    deployment_id = st.secrets["DEPLOYMENT_ID"]
    st.sidebar.success("API Key가 로드되었습니다! ✅")
else:
    # 2. 파일이 없으면 입력창 표시
    api_key = st.sidebar.text_input("RunComfy API Key", type="password")
    deployment_id = st.sidebar.text_input("Deployment ID")
    if not api_key or not deployment_id:
        st.sidebar.warning("API Key와 Deployment ID를 입력해주세요.")
        st.stop() # 키가 없으면 앱 실행 중단

# --- (이하 기존 코드와 동일하지만, backend 함수 호출 시 키를 전달해야 함) ---

# ... (중략) ...

if st.button("🚀 캐릭터 얼굴 생성 시작", use_container_width=True):
    # backend 함수에 api_key와 deployment_id 전달
    images = backend.generate_faces(
        prompt_text, 
        pm_options, 
        api_key,       # 추가됨
        deployment_id, # 추가됨
        batch_size=num_images
    )
    # ...

# ... (중략) ...

if st.button("✨ 최종 캐릭터 완성하기", ...):
    final_images = backend.generate_full_body(
        st.session_state.selected_face_url, 
        outfit_prompt,
        api_key,       # 추가됨
        deployment_id  # 추가됨
    )
    # ...
