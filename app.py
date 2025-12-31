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
    
    # Loading Overlay Injection
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
        <div class='loading-overlay'>
            <div class='spinner'></div>
            <div class='loading-text'>AI 솔루션 및 로드맵 생성 중...</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 1. Diagnosis Section
    # Check API Key
    if "OPENAI_API_KEY" not in st.secrets:
        loading_placeholder.empty()
        st.error("🚨 OpenAI API Key가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
        st.stop()
        
    diagnosis_result = run_diagnosis_agent(industry, company_size, pain_point)
    
    # 2. Matching Solutions
    try:
        df = pd.read_csv("data/tools_db.csv")
        recommended_tools = find_matching_solutions(df, diagnosis_result.key_keywords if diagnosis_result else [])
    except Exception as e:
        recommended_tools = []
        
    # 3. Roadmap Generation
    if recommended_tools:
        roadmap_markdown = generate_roadmap(industry, pain_point, recommended_tools)
    else:
        roadmap_markdown = ""
        
    # --- PROCESSING COMPLETE: REMOVE OVERLAY ---
    loading_placeholder.empty()
    
    # --- RENDER RESULTS ---
    
    # [1] Diagnosis
    st.markdown("<div class='section-subheader'>1. 기업 AI 도입 역량 진단 (Diagnosis)</div>", unsafe_allow_html=True)
    
    if diagnosis_result:
        with card_container():
            st.markdown(f"#### 🩺 진단 요약 (Urgency: {diagnosis_result.urgency})")
            st.info(f"**핵심 문제**: {diagnosis_result.problem_summary}")
            st.write(f"**추출된 키워드**: {', '.join(diagnosis_result.key_keywords)}")
    
    # [2] Solutions
    st.markdown("<div class='section-subheader'>2. 맞춤형 솔루션 추천 (Best Fit Solutions)</div>", unsafe_allow_html=True)
    
    if recommended_tools:
        # Layout: Grid of 3 columns (User requested 3 items)
        
        # Benefit Text Generator
        def get_benefit_text(category):
            cat = category.lower()
            if "마케팅" in cat: return "콘텐츠 생성 시간 단축 및 품질 향상 기대 (효율 +40%)"
            if "영업" in cat: return "고객 데이터 분석을 통한 영업 기회 포착 및 매출 증대"
            if "생산성" in cat or "업무" in cat: return "반복 업무 자동화를 통해 업무 처리 속도 2배 향상"
            if "분석" in cat: return "데이터 기반 의사결정으로 비즈니스 인사이트 도출 가속화"
            if "디자인" in cat: return "창의적 디자인 시안 생성 시간 90% 단축"
            if "개발" in cat: return "코드 자동 생성 및 디버깅 지원으로 개발 생산성 향상"
            return "AI 도입을 통해 기존 업무 방식의 혁신적인 효율화 기대"

        # Use columns(3) for 3 items
        cols = st.columns(3)
        for i, tool in enumerate(recommended_tools):
            with cols[i]:
                benefit_text = get_benefit_text(tool['Category'])
                # IMPORTANT: No indentation inside the HTML string to prevent Markdown code block interpretation
                html_content = f"""
<div class="solution-card">
    <div class="solution-header">
        <h3 class="solution-title">{tool['Tool Name']}</h3>
    </div>
    <span class="solution-badge">{tool['Category']}</span>
    
    <div class="solution-section-label">추천 이유:</div>
    <div class="solution-description">
        {tool['Description']}
    </div>
    
    <div class="solution-benefit-box">
        <span>{benefit_text}</span>
    </div>
</div>
"""
                st.markdown(html_content, unsafe_allow_html=True)

    # [3] Roadmap
    st.markdown("<div class='section-subheader'>3. 단계별 도입 및 교육 로드맵 (Action Plan)</div>", unsafe_allow_html=True)
    
    if roadmap_markdown:
        # Simple splitting by headers for UI
        # Roadmap is Markdown. Let's just render it nicely or split.
        # Splitting by '## '
        sections = roadmap_markdown.split('## ')
        
        # Section 0 is usually introductory empty or title.
        # Section 1: Strategy
        # Section 2: Action Plan
        # Section 3: Budget
        
        for section in sections:
            if not section.strip(): continue
            
            lines = section.split('\n')
            header = lines[0].strip()
            content = "\n".join(lines[1:])
            
            if "도입 전략" in header or "Strategy" in header:
                with st.container():
                     st.markdown(f"### {header}")
                     st.markdown(content)
            elif "실행 계획" in header or "Action Plan" in header:
                with st.expander(f"📌 {header} (클릭하여 상세 보기)", expanded=True):
                    st.markdown(content)
            elif "예산" in header or "ROI" in header:
                with st.container():
                    st.success(f"### {header}\n{content}")
            else:
                # Fallback
                st.markdown(f"## {section}")
    else:
         st.warning("추천된 솔루션이 없어 로드맵을 생성할 수 없습니다.")
