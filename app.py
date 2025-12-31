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
    with st.form("analysis_form"):
        st.markdown("#### 기업 프로필")
        company_name = st.text_input("기업명 (Company Name)", placeholder="예: (주)테크코퍼레이션")
        industry = st.selectbox("산업군 (Industry)", [
            "제조 (Manufacturing)", 
            "IT/소프트웨어 (IT/Software)",
            "금융/핀테크 (Finance/Fintech)", 
            "유통/커머스 (Retail/Commerce)", 
            "헬스케어/바이오 (Healthcare/Bio)", 
            "물류/운송 (Logistics/Transport)",
            "건설/부동산 (Construction/Real Estate)",
            "에너지/화학 (Energy/Chemical)",
            "미디어/콘텐츠 (Media/Content)",
            "교육 (Education)", 
            "공공/행정 (Public/Government)",
            "관광/레저 (Tourism/Leisure)",
            "법률/전문서비스 (Legal/Services)",
            "기타 서비스"
        ])
        company_size = st.select_slider("기업 규모 (Size)", options=["스타트업 (<50명)", "중소기업 (50-200명)", "중견기업 (200-1000명)", "대기업 (1000명+)"])
        
        st.markdown("#### 페인 포인트 (Pain Points)")
        st.info("현재 겪고 있는 업무상 어려움이나 AI로 해결하고 싶은 과제를 구체적으로 적어주세요.")
        pain_point = st.text_area(
            "Pain Points Input", 
            height=150, 
            placeholder="예시: 고객 센터의 단순 반복 문의가 너무 많아서 상담원 업무 효율이 떨어집니다. 24시간 자동 응대 시스템을 도입하고 싶지만, 우리 회사 데이터 보안이 걱정됩니다.",
            label_visibility="collapsed"
        )
        
        # Callback to handle form submission reliably
        def on_analyze_submit():
            st.session_state['analysis_done'] = False
            st.session_state['trigger_analysis'] = True

        analyze_submitted = st.form_submit_button("AI 솔루션 & 로드맵 생성", type="primary", use_container_width=True, on_click=on_analyze_submit)
    
    st.markdown("---")
    st.caption("Powered by GPT-4o & Streamlit\nVer 1.1.0 Platinum KR")

# --- MAIN CONTENT ---
# Compact Header
st.markdown("<div style='margin-bottom: 0px;'></div>", unsafe_allow_html=True) 
display_header("KPC 기업 맞춤형 AX 인사이트 (Insight)", "AS-IS 정밀 진단부터 TO-BE 실행 로드맵까지, 원스톱 솔루션")

# --- Session State Initialization ---
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
if 'trigger_analysis' not in st.session_state:
    st.session_state['trigger_analysis'] = False
if 'diagnosis_result' not in st.session_state:
    st.session_state['diagnosis_result'] = None
if 'recommended_tools' not in st.session_state:
    st.session_state['recommended_tools'] = []
if 'roadmap_markdown' not in st.session_state:
    st.session_state['roadmap_markdown'] = ""

if not st.session_state['analysis_done'] and not st.session_state['trigger_analysis']:
    # Initial State (Empty State)
    st.info("👈 좌측 사이드바에 기업 정보를 입력하고 '솔루션 생성' 버튼을 눌러주세요.")
    
    # Dashboard Overview (Dummy Stats for Visual)
    st.markdown("### 실시간 AI 솔루션 데이터베이스 현황")
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
    # --- Step 3: Agent Execution Logic (Triggered by Form Submit) ---
    if st.session_state['trigger_analysis']:
        # Reset Trigger immediately to prevent re-runs without click
        st.session_state['trigger_analysis'] = False
        from src.modules.llm_logic import run_diagnosis_agent, find_matching_solutions, generate_roadmap
        
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
        st.session_state['diagnosis_result'] = diagnosis_result
        
        # 2. Matching Solutions
        try:
            df = pd.read_csv("data/tools_db.csv")
            recommended_tools = find_matching_solutions(df, diagnosis_result.key_keywords if diagnosis_result else [])
        except Exception as e:
            recommended_tools = []
        st.session_state['recommended_tools'] = recommended_tools
            
        # 3. Roadmap Generation
        if recommended_tools:
            roadmap_markdown = generate_roadmap(industry, pain_point, recommended_tools)
        else:
            roadmap_markdown = ""
        st.session_state['roadmap_markdown'] = roadmap_markdown
            
        # --- PROCESSING COMPLETE: REMOVE OVERLAY ---
        loading_placeholder.empty()
        
        # Set Flag
        st.session_state['analysis_done'] = True
        
    # --- RENDER RESULTS (From Session State) ---
    if st.session_state['analysis_done']:
        diagnosis_result = st.session_state['diagnosis_result']
        recommended_tools = st.session_state['recommended_tools']
        roadmap_markdown = st.session_state['roadmap_markdown']
    
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
        
        # Benefit Text Generator (Matched with Reference Image Style)
        def get_benefit_text(tool_name, category):
            tool = tool_name.lower()
            cat = category.lower()
            
            # Specific Data Mapping for Demo/Visual consistency
            if "zapier" in tool: return "업무 프로세스 자동화를 통해 수작업 시간을 최소화하고, 30% 이상의 업무 효율성을 기대할 수 있습니다."
            if "notion" in tool: return "프로젝트 문서화 및 팀 협업 개선을 통해 작업 혼란을 40% 이상 감소시킬 수 있습니다."
            if "fireflies" in tool: return "자동화된 회의록과 요약 기능으로 정보 전달 시간을 50% 이상 줄일 수 있습니다."
            if "chatgpt" in tool: return "엔터프라이즈급 보안 환경에서 임직원의 업무 질문 및 문서 초안 작성을 즉각 지원합니다."
            if "jasper" in tool: return "브랜드 보이스에 맞는 고품질 마케팅 콘텐츠를 10배 빠르게 제작할 수 있습니다."
            if "midjourney" in tool: return "생성형 AI 디자인 프로세스를 도입하여 시안 제작 비용을 획기적으로 절감할 수 있습니다."
            
            # Fallback based on category
            if "마케팅" in cat: return "마케팅 캠페인 자동화 및 콘텐츠 생성 효율을 40% 이상 높일 수 있습니다."
            if "영업" in cat: return "고객 데이터 분석을 통한 잠재 고객 발굴 및 계약 성사율 증대가 기대됩니다."
            if "생산성" in cat or "자동화" in cat: return "반복 업무 자동화를 통해 수작업 시간을 최소화하고 업무 효율성을 극대화합니다."
            if "분석" in cat: return "데이터 기반의 신속한 의사결정으로 비즈니스 인사이트 도출 시간을 단축합니다."
            return "AI 도입을 통해 기존 업무 방식의 혁신적인 효율화와 생산성 향상을 기대할 수 있습니다."

        # Use columns(3) for 3 items
        cols = st.columns(3)
        for i, tool in enumerate(recommended_tools):
            with cols[i]:
                benefit_text = get_benefit_text(tool['Tool Name'], tool['Category'])
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
