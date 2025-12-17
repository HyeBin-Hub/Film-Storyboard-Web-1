import streamlit as st
import backend # 위에서 만든 backend.py 임포트

# --- 페이지 설정 ---
st.set_page_config(page_title="Movie Character Creator", layout="wide")

# --- 🔑 API Key 관리 로직 ---
# st.sidebar.title("🔐 API 설정")

# 1. secrets.toml 파일에서 먼저 찾아봄
if "RUNCOMFY_API_KEY" in st.secrets:
    api_key = st.secrets["RUNCOMFY_API_KEY"]
    deployment_id = st.secrets["DEPLOYMENT_ID"]
    # st.sidebar.success("API Key가 로드되었습니다! ✅")
else:
    # 2. 파일이 없으면 입력창 표시
    api_key = st.sidebar.text_input("RunComfy API Key", type="password")
    deployment_id = st.sidebar.text_input("Deployment ID")
    if not api_key or not deployment_id:
        st.sidebar.warning("API Key와 Deployment ID를 입력해주세요.")
        st.stop() # 키가 없으면 앱 실행 중단
        
st.title("🎬 영화 주인공 캐릭터 생성기")
st.markdown("ComfyUI & Flux 기반 스토리보드 캐릭터 제작 도구")

# --- 세션 상태 초기화 (데이터 저장소) ---
if "step" not in st.session_state:
    st.session_state.step = 1 # 1: 얼굴생성, 2: 얼굴선택, 3: 의상생성
if "generated_faces" not in st.session_state:
    st.session_state.generated_faces = []
if "selected_face_url" not in st.session_state:
    st.session_state.selected_face_url = None

# --- 사이드바: Portrait Master 옵션 ---
st.sidebar.header("⚙️ 캐릭터 세부 설정 (Portrait Master)")

           "gender": pm_options.get("Man","Woman"),
              "nationality_1":pm_options.get("Chinese","Japanese","Korean","South Korean","Indian","Saudi","British","French","German","Italian","Spanish","American","Canadian","Brazilian","Mexican","Argentine","Egyptian","South African","Nigerian","Kenyan","Moroccan","Australian","New Zealander","Fijian","Samoan","Tongan"),
              "body_type": :pm_options.get(]),
              "eyes_color": pm_options.get(,
              "eyes_shape": pm_options.get("),
              "lips_color": pm_options.get(),
              "lips_shape": pm_options.get(),
              "face_shape": pm_options.get(),
              "hair_style": pm_options.get(),
              "hair_color": pm_options.get("Black","Jet Black","Blonde","Platinum","Brown","Chestnut","Auburn","Red","Strawberry","Gray","Silver","White","Salt and pepper"),
              "hair_length": pm_options.get(),
              "beard": pm_options.get(),
              "beard_color": pm_options.get(),},


pm_options = {}
pm_options["gender"] = st.sidebar.selectbox("Gender", ["Man","Woman"])
pm_options["nationality"] = st.sidebar.selectbox("Nationality", ["Chinese","Japanese","Korean","South Korean","Indian","Saudi","British","French","German","Italian","Spanish","American","Canadian","Brazilian","Mexican","Argentine","Egyptian","South African","Nigerian","Kenyan","Moroccan","Australian","New Zealander","Fijian","Samoan","Tongan"])
pm_options["body_type"] = st.sidebar.selectbox("Body Type", ["Chubby","Curvy","Fat","Fit","Hefty","Large","Lanky","Muscular","Obese","Overweight","Petite","Plump","Short","Skinny","Slight","Slim","Small","Stout","Stocky","Tall","Thick","Tiny","Underweight","Well-built"])
pm_options["eyes_color"] = st.sidebar.selectbox("Eyes Color", ["Albino", "Amber", "Blue", "Brown", "Green", "Gray", "Hazel", "Heterochromia", "Red", "Violet")])
pm_options["eyes_shape"] = st.sidebar.selectbox("Eyes Shape", ["Almond Eyes Shape","Asian Eyes Shape","Close-Set Eyes Shape","Deep Set Eyes Shape","Downturned Eyes Shape","Double Eyelid Eyes Shape","Hooded Eyes Shape","Monolid Eyes Shape","Oval Eyes Shape","Protruding Eyes Shape","Round Eyes Shape","Upturned Eyes Shape"])
pm_options["lips_color"] = st.sidebar.selectbox("Lips Color", ["Berry Lips","Black Lips","Blue Lips","Brown Lips","Burgundy Lips","Coral Lips","Glossy Red Lips","Mauve Lips","Orange Lips","Peach Lips","Pink Lips","Plum Lips","Purple Lips","Red Lips","Yellow Lips"])
pm_options["lips_shape"] = st.sidebar.selectbox("Lips Shape", ["Full Lips","Thin Lips","Plump Lips","Small Lips","Large Lips","Wide Lips","Round Lips","Heart-shaped Lips","Cupid's Bow Lips"])
pm_options["face_shape"] = st.sidebar.selectbox("Face Shape", ["Oval","Round","Square","Heart","Diamond","Triangle","Inverted Triangle","Pear","Rectangle","Oblong","Long"])
pm_options["hair_style"] = st.sidebar.selectbox("Hair Style", ["Bald","Buzz","Crew","Pixie","Bob","Long bob","Long straight","Wavy","Curly","Afro","Faded afro","Braided","Box braids","Cornrows","Dreadlocks","Pigtails","Ponytail","High ponytail","Bangs","Curtain bangs","Side-swept bangs","Mohawk","Faux hawk","Undercut","Pompadour","Quiff","Top Knot","Bun","Updo"])
pm_options["hair_color"] = st.sidebar.selectbox("Hair Color", ["Black","Jet Black","Blonde","Platinum","Brown","Chestnut","Auburn","Red","Strawberry","Gray","Silver","White","Salt and pepper"])
pm_options["hair_length"] = st.sidebar.selectbox("Hair Length", ["Short","Medium","Long"])
pm_options["beard"] = st.sidebar.selectbox("Beard", ["Stubble Beard","Goatee","Full Beard","Van Dyke Beard","Circle Beard","Balbo Beard","Ducktail Beard","Chinstrap Beard","Chevron Mustache","Handlebar Mustache","Horseshoe Mustache","Pencil Mustache"])
pm_options["beard_color"] = st.sidebar.selectbox("Beard Color", ["Black","Jet Black","Blonde","Platinum","Brown","Chestnut","Auburn","Red","Strawberry","Gray","Silver","White","Salt and pepper"])

# 필요하다면 조명 등 더 추가 가능

# =================================================================
# STEP 1: 기본 정보 입력 및 얼굴 생성
# =================================================================
if st.session_state.step == 1:
    st.subheader("Step 1: 캐릭터 기본 정보 입력")

    # --- 비율 선택 UI 추가 ---
    col_ratio, col_num = st.columns(2)
    
    with col_ratio:
        ratio_option = st.selectbox(
            "이미지 비율 (Aspect Ratio)",
            ["세로형 (9:16) - 인물 중심", "가로형 (16:9) - 영화 느낌", "정사각형 (1:1) - SNS"]
        )
        
        # 선택에 따라 실제 픽셀값 할당 (Flux 모델 권장 해상도 기준)
        if "세로형" in ratio_option:
            width, height = 896, 1152
        elif "가로형" in ratio_option:
            width, height = 1152, 896
        else:
            width, height = 1024, 1024

    with col_num:
        num_images = st.number_input("생성할 장수", min_value=1, max_value=4, value=2)

    # --- 프롬프트 입력 ---
    base_prompt = st.text_input("기본 프롬프트", value="12-year-old Korean boy, white t-shirt, Buzz cut hair")
    
    # col1, col2 = st.columns([3, 1])
    # with col1:
    #     base_prompt = st.text_input("기본 프롬프트 (예: 12-year-old boy, buzz cut hair)", 
    #                                 value="12-year-old Korean boy, white t-shirt, Buzz cut hair")

        
    # with col2:
    #     num_images = st.number_input("생성할 장수", min_value=1, max_value=4, value=2)

    if st.button("🚀 캐릭터 얼굴 생성 시작", use_container_width=True):
        with st.spinner("ComfyUI가 열심히 그림을 그리고 있습니다... (약 20~40초 소요)"):
            # 백엔드 호출
            images = backend.generate_faces(base_prompt, 
                                            pm_options, 
                                            api_key,       
                                            deployment_id, 
                                            batch_size=num_images)
            
            if images:
                st.session_state.generated_faces = images
                st.session_state.step = 2 # 다음 단계로 이동
                st.rerun() # 화면 새로고침
            else:
                st.error("이미지 생성에 실패했습니다. 백엔드 로그를 확인해주세요.")

# =================================================================
# STEP 2: 마음에 드는 얼굴 선택
# =================================================================
elif st.session_state.step == 2:
    st.subheader("Step 2: 마음에 드는 배우(캐릭터)를 선택하세요")
    
    if st.button("⬅️ 다시 생성하기"):
        st.session_state.step = 1
        st.rerun()

    # 이미지 그리드 표시
    cols = st.columns(len(st.session_state.generated_faces))
    
    for idx, img_url in enumerate(st.session_state.generated_faces):
        with cols[idx]:
            st.image(img_url, use_container_width=True)
            # 버튼마다 고유 키(key)를 줘야 에러가 안 남
            if st.button(f"이 얼굴 선택 (#{idx+1})", key=f"btn_{idx}"):
                st.session_state.selected_face_url = img_url
                st.session_state.step = 3
                st.rerun()

# =================================================================
# STEP 3: 의상 입히기 (전신 생성)
# =================================================================
elif st.session_state.step == 3:
    st.subheader("Step 3: 캐릭터 의상 디자인")
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.info("선택된 얼굴")
        st.image(st.session_state.selected_face_url, width=200)
        if st.button("⬅️ 얼굴 다시 선택"):
            st.session_state.step = 2
            st.rerun()
            
    with col_right:
        outfit_prompt = st.text_area("의상 프롬프트 (예: yellow hoodie, baggy jeans, sneakers)", height=150)
        
        if st.button("✨ 최종 캐릭터 완성하기", type="primary", use_container_width=True):
            if not outfit_prompt:
                st.warning("의상 내용을 입력해주세요!")
            else:
                with st.spinner("얼굴을 유지하면서 의상을 입히는 중입니다..."):
                    # 백엔드 호출
                    final_images = backend.generate_full_body(
                        st.session_state.selected_face_url, 
                        outfit_prompt,api_key,       
                        deployment_id  
                    )
                    
                    if final_images:
                        st.success("완성!")
                        # 결과는 보통 마지막 이미지가 최종본
                        st.image(final_images[-1], caption="최종 결과물")
                    else:
                        st.error("생성 실패.")
