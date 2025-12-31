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
        
        
        # Simple submit button (Reset to standard behavior for reliability)
        analyze_submitted = st.form_submit_button("AI 솔루션 & 로드맵 생성", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("Powered by GPT-4o & Streamlit\nVer 1.1.0 Platinum KR")

# --- MAIN CONTENT ---
# Compact Header
st.markdown("<div style='margin-bottom: 0px;'></div>", unsafe_allow_html=True) 
display_header("KPC 기업 맞춤형 AX 인사이트 (Insight)")

# --- Session State Initialization ---
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
# Removed trigger_analysis flag to simplify logic
if 'diagnosis_result' not in st.session_state:
    st.session_state['diagnosis_result'] = None
if 'recommended_tools' not in st.session_state:
    st.session_state['recommended_tools'] = []
if 'roadmap_markdown' not in st.session_state:
    st.session_state['roadmap_markdown'] = ""

if not st.session_state['analysis_done'] and not analyze_submitted:
    # Initial State (Empty State)
    st.info("AS-IS 정밀 진단부터 TO-BE 실행 로드맵까지, 원스톱 솔루션")
    
    # Dashboard Overview (Dummy Stats for Visual)
    st.markdown("<div class='section-subheader'>AI 솔루션 도입 효율성 및 기대 효과</div>", unsafe_allow_html=True)
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
    if analyze_submitted:
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
            raw_roadmap = generate_roadmap(industry, pain_point, recommended_tools)
            # Clean Markdown artifacts
            cleaned_roadmap = raw_roadmap.replace("```markdown", "").replace("```", "").strip()
            st.session_state['roadmap_markdown'] = cleaned_roadmap
        else:
            st.session_state['roadmap_markdown'] = ""
            
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
            st.markdown("#### 진단 요약")
            st.info(f"**핵심 문제**: {diagnosis_result.problem_summary}")
            st.write(f"**추출된 키워드**: {', '.join(diagnosis_result.key_keywords)}")
    
    # [2] Solutions
    st.markdown("<div class='section-subheader'>2. 맞춤형 솔루션 추천 (Best Fit Solutions)</div>", unsafe_allow_html=True)
    
    if recommended_tools:
        # Layout: Grid of 3 columns (User requested 3 items)
        
        # Tool Introduction (What is this tool?)
        def get_tool_intro(tool_name):
            tool = tool_name.lower()
            if "zapier" in tool: return "5,000개 이상의 앱을 연결하는 노코드 자동화 플랫폼입니다. 코딩 없이 다양한 서비스 간 데이터 흐름을 자동화하여 반복 업무를 제거합니다."
            if "notion" in tool: return "AI 기반 올인원 협업 및 문서 관리 도구입니다. 프로젝트 관리, 위키, 데이터베이스를 하나의 워크스페이스에서 통합 관리할 수 있습니다."
            if "fireflies" in tool: return "AI 회의 녹음 및 자동 요약 서비스입니다. 화상회의를 자동 녹취하고, 핵심 액션 아이템과 결정사항을 추출해 공유합니다."
            if "chatgpt" in tool: return "OpenAI의 기업용 대화형 AI 솔루션입니다. SSO, 데이터 보안, 관리자 콘솔 등 엔터프라이즈급 기능을 제공합니다."
            if "jasper" in tool: return "AI 기반 마케팅 콘텐츠 생성 플랫폼입니다. 블로그, 소셜미디어, 광고 카피 등 다양한 마케팅 콘텐츠를 브랜드 톤에 맞게 생성합니다."
            if "midjourney" in tool: return "프롬프트 기반 고품질 AI 이미지 생성 도구입니다. 마케팅 소재, 제품 컨셉 이미지, 프레젠테이션 비주얼을 빠르게 제작할 수 있습니다."
            if "copy.ai" in tool: return "AI 카피라이팅 및 콘텐츠 자동 생성 도구입니다. 광고 문구, 이메일, 블로그 등 다양한 형식의 텍스트를 자동 생성합니다."
            if "otter" in tool: return "실시간 음성 인식 및 회의록 자동화 서비스입니다. 회의 내용을 실시간으로 텍스트로 변환하고 검색 가능한 형태로 저장합니다."
            if "grammarly" in tool: return "AI 기반 영문 교정 및 작문 보조 도구입니다. 문법 오류 수정부터 톤 조절, 명확성 개선까지 전문적인 영문 작성을 지원합니다."
            if "tableau" in tool: return "인터랙티브 데이터 시각화 및 분석 플랫폼입니다. 대량의 데이터를 직관적인 대시보드와 차트로 변환하여 인사이트를 도출합니다."
            if "power bi" in tool: return "Microsoft의 비즈니스 인텔리전스 도구입니다. Excel, Azure 등 MS 생태계와 완벽하게 통합되어 데이터 분석을 지원합니다."
            if "salesforce" in tool: return "AI 탑재 CRM 및 영업 자동화 플랫폼입니다. 고객 관계 관리부터 영업 예측, 마케팅 자동화까지 통합 솔루션을 제공합니다."
            return "AI 기반 업무 효율화 솔루션으로, 기존 워크플로우에 쉽게 통합하여 생산성을 높일 수 있습니다."
        
        # Recommendation Reason (2-3 lines, more detailed)
        def get_recommendation_reason(tool_name, category):
            tool = tool_name.lower()
            cat = category.lower()
            if "zapier" in tool: return "귀사의 반복적인 수작업 프로세스를 자동화하여 인적 오류를 줄이고 업무 효율을 극대화할 수 있습니다. 다양한 툴 간 데이터 연동으로 사일로 현상을 해결합니다."
            if "notion" in tool: return "분산된 팀 협업 도구를 하나로 통합하여 정보 검색 시간을 단축하고 지식 공유를 활성화합니다. AI Q&A 기능으로 문서 내 정보를 즉시 찾을 수 있습니다."
            if "fireflies" in tool: return "회의록 작성에 소요되는 시간을 제거하고, 중요 결정사항과 액션 아이템을 자동 추출합니다. 팀원 간 정보 공유 속도가 크게 향상됩니다."
            if "chatgpt" in tool: return "임직원들이 업무 중 발생하는 질문에 즉시 답변을 받고, 문서 초안 작성, 데이터 분석 등 다양한 태스크를 AI로 가속화할 수 있습니다."
            if "jasper" in tool: return "마케팅팀의 콘텐츠 생산 속도를 획기적으로 높이고, 일관된 브랜드 보이스를 유지하면서 다양한 채널용 콘텐츠를 생성할 수 있습니다."
            if "midjourney" in tool: return "디자이너 리소스 없이도 고품질 시각 자료를 빠르게 생성하여 마케팅 및 제안서 작성 시간을 단축합니다. 아이데이션 단계에서 특히 유용합니다."
            # Fallback based on category
            if "마케팅" in cat: return "마케팅 콘텐츠 생성과 캠페인 운영을 자동화하여 팀의 창의적 업무에 집중할 시간을 확보합니다. ROI 측정과 최적화도 지원합니다."
            if "영업" in cat: return "고객 데이터를 체계적으로 관리하고 영업 파이프라인을 시각화하여 성사율을 높입니다. AI 기반 고객 인사이트도 제공합니다."
            if "생산성" in cat or "자동화" in cat: return "반복적인 수작업을 자동화하여 직원들이 고부가가치 업무에 집중할 수 있게 합니다. 평균 30% 이상의 시간 절감 효과가 있습니다."
            if "분석" in cat: return "복잡한 데이터를 직관적으로 시각화하여 빠른 의사결정을 지원합니다. 실시간 대시보드로 핵심 KPI를 모니터링할 수 있습니다."
            return "AI 기술을 활용하여 기존 업무 방식을 혁신하고 전반적인 생산성과 품질을 향상시킬 수 있습니다."
        
        # Benefit Text (Expected outcome)
        def get_benefit_text(tool_name, category):
            tool = tool_name.lower()
            cat = category.lower()
            if "zapier" in tool: return "예상 효과: 수작업 시간 30% 이상 절감"
            if "notion" in tool: return "예상 효과: 팀 협업 효율 40% 향상"
            if "fireflies" in tool: return "예상 효과: 회의록 작성 시간 50% 단축"
            if "chatgpt" in tool: return "예상 효과: 문서 초안 작성 시간 60% 절감"
            if "jasper" in tool: return "예상 효과: 콘텐츠 생산 속도 10배 향상"
            if "midjourney" in tool: return "예상 효과: 디자인 시안 비용 70% 절감"
            # Fallback
            if "마케팅" in cat: return "예상 효과: 콘텐츠 생성 효율 40% 향상"
            if "영업" in cat: return "예상 효과: 영업 생산성 35% 향상"
            if "생산성" in cat or "자동화" in cat: return "예상 효과: 업무 효율 30% 이상 향상"
            return "예상 효과: 업무 생산성 향상"

        # Use columns(3) for 3 items
        cols = st.columns(3)
        for i, tool in enumerate(recommended_tools):
            with cols[i]:
                tool_intro = get_tool_intro(tool['Tool Name'])
                rec_reason = get_recommendation_reason(tool['Tool Name'], tool['Category'])
                benefit_text = get_benefit_text(tool['Tool Name'], tool['Category'])
                html_content = f'''<div class="solution-card">
<div class="solution-header">
<h3 class="solution-title">{tool['Tool Name']}</h3>
</div>
<span class="solution-badge">{tool['Category']}</span>
<div class="solution-intro">{tool_intro}</div>
<div class="solution-section-label">추천 이유</div>
<div class="solution-description">{rec_reason}</div>
<div class="solution-benefit-box">
<span>{benefit_text}</span>
</div>
</div>'''
                st.markdown(html_content, unsafe_allow_html=True)

    # [3] Curriculum
    st.markdown("<div class='section-subheader'>3. 교육 커리큘럼 (Curriculum)</div>", unsafe_allow_html=True)
    
    if roadmap_markdown:
        # LLM now generates only the table directly, just clean and render
        cleaned_content = roadmap_markdown.replace("```markdown", "").replace("```", "").strip()
        st.markdown(cleaned_content)
    else:
         st.warning("추천된 솔루션이 없어 커리큘럼을 생성할 수 없습니다.")
