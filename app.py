import streamlit as st
import pandas as pd
from src.modules.ui_components import load_css, display_header, card_container

# Configure Page
st.set_page_config(
    page_title="AI 도입 솔루션 대시보드",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
load_css('assets/css/style.css')

# --- SIDEBAR (Dark Theme) ---
with st.sidebar:
    st.markdown("#### 기업 프로필")
    company_name = st.text_input("기업명 (Company Name)", placeholder="예: (주)테크코퍼레이션")
    industry = st.selectbox("산업군 (Industry)", ["금융 (Finance)", "헬스케어 (Healthcare)", "유통/커머스 (Retail)", "제조 (Manufacturing)", "IT/테크 (IT/Tech)", "교육 (Education)", "기타 서비스"])
    company_size = st.select_slider("기업 규모 (Size)", options=["스타트업 (<50명)", "중소기업 (50-200명)", "중견기업 (200-1000명)", "대기업 (1000명+)"])
    
    
    st.markdown("#### 페인 포인트 (Pain Points)")
    st.info("현재 겪고 있는 업무상 어려움이나 AI로 해결하고 싶은 과제를 구체적으로 적어주세요.")
    pain_point = st.text_area(
        "Pain Points Input", 
        height=150, 
        placeholder="예시: 고객 센터의 단순 반복 문의가 너무 많아서 상담원 업무 효율이 떨어집니다. 24시간 자동 응대 시스템을 도입하고 싶지만, 우리 회사 데이터 보안이 걱정됩니다.",
        label_visibility="collapsed"
    )
    
    analyze_btn = st.button("AI 솔루션 & 로드맵 생성", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("Powered by GPT-4o & Streamlit\nVer 1.1.0 Platinum KR")

# --- MAIN CONTENT ---
# Compact Header
st.markdown("<div style='margin-bottom: 0px;'></div>", unsafe_allow_html=True) 
display_header("KPC 기업 맞춤형 AX 인사이트 (Insight)", "AS-IS 정밀 진단부터 TO-BE 실행 로드맵까지, 원스톱 솔루션")

if not analyze_btn:
    # Initial State (Empty State)
    st.info("👈 좌측 사이드바에 기업 정보를 입력하고 '솔루션 생성' 버튼을 눌러주세요.")
    
    # Dashboard Overview (Dummy Stats for Visual)
    st.markdown("### 📊 실시간 AI 솔루션 데이터베이스 현황")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="등록된 AI 솔루션", value="50+", delta="Live DB")
    with col2:
        st.metric(label="매칭 알고리즘", value="GPT-4o", delta="Active")
    with col3:
        st.metric(label="평균 도입 기간", value="4.2주", delta="-12% (YoY)")
    with col4:
        st.metric(label="예상 업무 효율", value="+35%", delta="업계 평균 상회")

    # Preview of Tools - Height restricted for one-page view (Adjusted)
    st.markdown("<div class='section-subheader'>사용 가능한 솔루션 리스트 (미리보기)</div>", unsafe_allow_html=True)
    try:
        df = pd.read_csv("data/tools_db.csv")
        
        # UI Tweak: Convert 'Complexity' text to Discrete Visual Bars (Wide & Colored)
        def get_complexity_bars(level):
            if level == '하': return "█" 
            elif level == '중': return "█ █" 
            elif level == '상': return "█ █ █" 
            return level
            
        df['난이도'] = df['Complexity'].apply(get_complexity_bars)
        
        # Select and Reorder columns for display
        display_df = df[['Tool Name', 'Category', 'Description', 'Pricing Model', '난이도']]
        
        # Apply Styling (Blue Color for Complexity)
        styled_df = display_df.style.applymap(
            lambda x: 'color: #2563EB; font-weight: bold;', 
            subset=['난이도']
        )
        
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True, 
            height=350,
            column_config={
                "난이도": st.column_config.TextColumn("구축 난이도"),
                "Pricing Model": st.column_config.TextColumn("가격 모델"),
                "Tool Name": st.column_config.TextColumn("솔루션명"),
                "Category": st.column_config.TextColumn("카테고리"),
                "Description": st.column_config.TextColumn("설명"),
            }
        )
    except FileNotFoundError:
        st.error("데이터베이스 파일을 찾을 수 없습니다.")

else:
    # --- Step 3: Agent Execution Logic ---
    from src.modules.llm_logic import run_diagnosis_agent, find_matching_solutions, generate_roadmap
    import time
    
    # 1. Diagnosis Section
    st.markdown("<div class='section-subheader'>1. 기업 AI 도입 역량 진단 (Diagnosis)</div>", unsafe_allow_html=True)
    
    diagnosis_placeholder = st.empty()
    with diagnosis_placeholder.container():
        with card_container():
            st.write("🔄 **AI 에이전트가 기업 프로필과 페인 포인트를 분석 중입니다...**")
            st.progress(30)
            
    # Run Diagnosis Agent
    diagnosis_result = run_diagnosis_agent(industry, company_size, pain_point)
    
    if diagnosis_result:
        with diagnosis_placeholder.container():
            with card_container():
                st.markdown(f"#### 🩺 진단 요약 (Urgency: {diagnosis_result.urgency})")
                st.info(f"**핵심 문제**: {diagnosis_result.problem_summary}")
                st.write(f"**추출된 키워드**: {', '.join(diagnosis_result.key_keywords)}")
    
    # 2. Recommended Solutions
    st.markdown("<div class='section-subheader'>2. 맞춤형 솔루션 추천 (Best Fit Solutions)</div>", unsafe_allow_html=True)
    
    tools_placeholder = st.empty()
    with tools_placeholder.container():
        st.write("🔍 **데이터베이스에서 최적의 솔루션을 매칭하고 있습니다...**")
    
    # Run Matching Logic
    try:
        df = pd.read_csv("data/tools_db.csv")
        recommended_tools = find_matching_solutions(df, diagnosis_result.key_keywords if diagnosis_result else [])
    except Exception as e:
        st.error(f"DB Error: {e}")
        recommended_tools = []

    if recommended_tools:
        tools_placeholder.empty()
        cols = st.columns(len(recommended_tools))
        
        for i, tool in enumerate(recommended_tools):
            with cols[i]:
                with card_container():
                    st.markdown(f"#### {'🥇' if i==0 else '🥈'} {tool['Tool Name']}")
                    st.caption(f"Category: {tool['Category']}")
                    st.markdown(f"**{tool['Description']}**")
                    st.markdown(f"비용 모델: {tool['Pricing Model']}")
                    st.success(f"매칭 점수: {tool.get('match_score', 0)}점")
                    
    # 3. Education Roadmap
    st.markdown("<div class='section-subheader'>3. 단계별 도입 및 교육 로드맵 (Action Plan)</div>", unsafe_allow_html=True)
    
    roadmap_placeholder = st.empty()
    with roadmap_placeholder.container():
        with card_container():
            st.write("📅 **상세 로드맵 보고서를 생성 중입니다 (GPT-4o Generating)...**")
            st.spinner("Thinking...")
            
    # Run Roadmap Agent
    if recommended_tools:
        roadmap_markdown = generate_roadmap(industry, pain_point, recommended_tools)
        
        with roadmap_placeholder.container():
            with card_container():
                st.markdown(roadmap_markdown)
    else:
         with roadmap_placeholder.container():
            st.warning("추천된 솔루션이 없어 로드맵을 생성할 수 없습니다.")
