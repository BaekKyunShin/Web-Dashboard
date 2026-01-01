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
if 'recommendation_reasons' not in st.session_state:
    st.session_state['recommendation_reasons'] = []


# --- MAIN CONTENT LOGIC ---
# STEP 1: Handle form submission FIRST (before any rendering)
if analyze_submitted:
    from src.modules.llm_logic import run_diagnosis_agent, find_matching_solutions, generate_roadmap, generate_recommendation_reasons
    
    # Loading Overlay Injection
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
        <div class='loading-overlay'>
            <div class='spinner'></div>
            <div class='loading-text'>AI 솔루션 및 로드맵 생성 중...</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Check API Key
    if "OPENAI_API_KEY" not in st.secrets:
        loading_placeholder.empty()
        st.error("🚨 OpenAI API Key가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
        st.stop()
        
    # 1. Diagnosis
    diagnosis_result = run_diagnosis_agent(industry, company_size, pain_point)
    st.session_state['diagnosis_result'] = diagnosis_result
    
    # 2. Matching Solutions (Semantic Search)
    try:
        df = pd.read_csv("data/tools_db.csv")
        recommended_tools = find_matching_solutions(
            df, 
            pain_point,
            diagnosis_result.key_keywords if diagnosis_result else []
        )
    except Exception as e:
        recommended_tools = []
    st.session_state['recommended_tools'] = recommended_tools
    
    # 3. Generate Dynamic Recommendation Reasons
    if recommended_tools:
        dynamic_reasons = generate_recommendation_reasons(pain_point, industry, recommended_tools)
        st.session_state['recommendation_reasons'] = dynamic_reasons
    else:
        st.session_state['recommendation_reasons'] = []
        
    # 4. Roadmap Generation
    if recommended_tools:
        raw_roadmap = generate_roadmap(industry, pain_point, recommended_tools)
        cleaned_roadmap = raw_roadmap.replace("```markdown", "").replace("```", "").strip()
        st.session_state['roadmap_markdown'] = cleaned_roadmap
    else:
        st.session_state['roadmap_markdown'] = ""
        
    # Processing Complete
    loading_placeholder.empty()
    st.session_state['analysis_done'] = True

# STEP 2: Render UI based on state (AFTER processing is complete)
if st.session_state['analysis_done']:
    # --- RENDER RESULTS (From Session State) ---
    diagnosis_result = st.session_state['diagnosis_result']
    recommended_tools = st.session_state['recommended_tools']
    roadmap_markdown = st.session_state['roadmap_markdown']
    recommendation_reasons = st.session_state.get('recommendation_reasons', [])
    
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
        def get_tool_intro(tool_name, category=""):
            tool = tool_name.lower()
            cat = category.lower() if category else ""
            # Specific tool mappings
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
            # Additional specific tools
            if "intercom" in tool: return "AI 기반 고객 서비스 챗봇 플랫폼입니다. 24시간 자동 응대로 고객 문의를 즉시 처리하고 상담원 업무 부담을 줄입니다."
            if "elevenlabs" in tool or "eleven labs" in tool: return "최첨단 AI 음성 합성 플랫폼입니다. 자연스러운 음성을 다국어로 생성하여 콘텐츠 제작, 더빙, 접근성 향상에 활용합니다."
            if "zendesk" in tool: return "AI 기반 통합 고객 서비스 플랫폼입니다. 티켓 관리, 지식 베이스, 자동 응답 기능으로 고객 지원 품질을 높입니다."
            if "synthesia" in tool: return "AI 아바타 기반 비디오 생성 플랫폼입니다. 텍스트만으로 전문 발표자가 등장하는 교육·마케팅 영상을 제작합니다."
            if "heygen" in tool: return "AI 아바타 비디오 제작 도구입니다. 다양한 언어와 스타일의 영상을 빠르게 생성하여 글로벌 콘텐츠 제작을 지원합니다."
            if "runway" in tool: return "AI 기반 비디오 편집 및 생성 플랫폼입니다. 텍스트 프롬프트로 영상을 생성하고 고급 편집 작업을 자동화합니다."
            if "descript" in tool: return "텍스트 기반 오디오·비디오 편집 도구입니다. 문서 편집하듯 미디어를 편집하고 AI로 더빙, 자막을 생성합니다."
            if "murf" in tool: return "전문 내레이션을 위한 AI 음성 생성기입니다. 120개 이상의 음성으로 교육, 광고, 프레젠테이션 나레이션을 제작합니다."
            if "krisp" in tool: return "AI 노이즈 캔슬링 앱입니다. 통화와 회의 중 배경 소음을 실시간으로 제거하여 깨끗한 음성 품질을 보장합니다."
            if "miro" in tool: return "AI 기능을 갖춘 협업 화이트보드 플랫폼입니다. 아이디어 정리, 마인드맵, 워크숍을 온라인에서 효과적으로 진행합니다."
            if "monday" in tool: return "AI 기반 프로젝트 관리 플랫폼입니다. 워크플로우 자동화와 AI 인사이트로 팀 생산성을 극대화합니다."
            if "asana" in tool: return "AI 지원 프로젝트 관리 도구입니다. 업무 할당, 진행 상황 추적, 목표 관리를 스마트하게 지원합니다."
            if "clickup" in tool: return "AI 지식 관리자가 탑재된 올인원 프로젝트 관리 플랫폼입니다. 문서, 태스크, 목표를 통합 관리합니다."
            if "amplitude" in tool: return "AI 인사이트를 제공하는 제품 분석 플랫폼입니다. 사용자 행동 데이터를 분석하여 제품 개선 방향을 도출합니다."
            if "mixpanel" in tool: return "이벤트 기반 제품 분석 도구입니다. 사용자 여정을 추적하고 전환율 개선을 위한 인사이트를 제공합니다."
            if "pendo" in tool: return "AI 기반 제품 경험 플랫폼입니다. 사용자 행동 분석, 인앱 가이드, 피드백 수집을 통합 지원합니다."
            if "drift" in tool: return "대화형 마케팅 및 영업 플랫폼입니다. AI 챗봇으로 웹사이트 방문자를 리드로 전환합니다."
            if "typeform" in tool: return "AI 기반 폼 빌더입니다. 대화형 설문조사와 데이터 수집으로 응답률을 높입니다."
            if "surveymonkey" in tool: return "AI 분석 기능을 갖춘 설문조사 플랫폼입니다. 설문 설계부터 결과 분석까지 스마트하게 지원합니다."
            if "airtable" in tool: return "AI 기능을 갖춘 스마트 스프레드시트 플랫폼입니다. 데이터베이스와 앱을 코딩 없이 구축합니다."
            if "softr" in tool: return "노코드 앱 빌더입니다. Airtable, Google Sheets와 연동하여 고객 포털과 내부 도구를 빠르게 제작합니다."
            if "framer" in tool: return "AI 기반 웹 디자인 도구입니다. 디자인과 퍼블리싱을 원스톱으로 처리하여 빠르게 웹사이트를 제작합니다."
            if "webflow" in tool: return "비주얼 웹 개발 플랫폼입니다. 코딩 없이 전문적인 반응형 웹사이트를 디자인하고 배포합니다."
            if "shopify" in tool: return "이커머스 플랫폼의 AI 도구 모음입니다. 상품 설명 생성, 재고 관리, 마케팅 자동화를 지원합니다."
            if "adcreative" in tool: return "AI 광고 크리에이티브 생성 도구입니다. 고전환율 광고 이미지와 배너를 자동으로 제작합니다."
            if "feedhive" in tool: return "AI 소셜 미디어 관리 도구입니다. 콘텐츠 스케줄링, 자동 게시, 성과 분석을 통합 지원합니다."
            if "surfer" in tool: return "AI 기반 SEO 최적화 도구입니다. 콘텐츠 분석과 키워드 추천으로 검색 순위를 높입니다."
            if "github copilot" in tool or "copilot" in tool: return "AI 페어 프로그래머입니다. 코드 자동 완성과 함수 제안으로 개발 속도를 높입니다."
            if "claude" in tool: return "Anthropic의 안전하고 유용한 AI 어시스턴트입니다. 복잡한 분석, 글쓰기, 코딩 작업을 지원합니다."
            if "perplexity" in tool: return "AI 기반 대화형 검색 엔진입니다. 복잡한 질문에 출처와 함께 정확한 답변을 제공합니다."
            if "loom" in tool: return "AI 요약 기능을 갖춘 비디오 메시징 도구입니다. 화면 녹화로 비동기 커뮤니케이션을 효율화합니다."
            if "gamma" in tool: return "AI 기반 프레젠테이션 도구입니다. 아이디어를 입력하면 디자인된 슬라이드를 자동 생성합니다."
            if "tome" in tool: return "AI 스토리텔링 플랫폼입니다. 프롬프트로 시각적으로 풍부한 프레젠테이션을 만듭니다."
            if "beautiful.ai" in tool or "beautiful ai" in tool: return "생성형 AI 프레젠테이션 도구입니다. 콘텐츠를 추가하면 자동으로 레이아웃을 디자인합니다."
            if "gong" in tool: return "영업 인텔리전스 플랫폼입니다. 고객 대화를 AI로 분석하여 영업 성과를 높입니다."
            if "lavender" in tool: return "AI 이메일 비서입니다. 영업 이메일의 톤과 효과를 분석하여 응답률을 높입니다."
            if "hubspot" in tool: return "마케팅, 영업, 서비스를 통합하는 CRM 플랫폼입니다. AI로 콘텐츠 생성과 고객 관리를 자동화합니다."
            if "canva" in tool: return "AI 디자인 도구 모음입니다. 템플릿과 AI 기능으로 누구나 전문적인 디자인을 제작합니다."
            if "writer" in tool: return "엔터프라이즈급 생성형 AI 플랫폼입니다. 브랜드 가이드에 맞는 콘텐츠를 일관되게 생성합니다."
            # Inventory/ERP/Manufacturing tools
            if "fishbowl" in tool: return "중소 제조업체를 위한 AI 재고 추적 및 창고 관리 시스템입니다. 실시간 재고 현황 파악과 자동 재주문 기능으로 재고 관리를 최적화합니다."
            if "zoho inventory" in tool or "zoho" in tool: return "다채널 판매 환경을 위한 AI 재고 관리 플랫폼입니다. 자동 재주문 시스템으로 재고 부족과 과잉을 방지하고 주문 처리를 간소화합니다."
            if "oracle" in tool or "netsuite" in tool: return "클라우드 기반 ERP 솔루션으로 재고 추적과 수요 예측을 자동화합니다. 제조업체가 수요 변동에 빠르게 대응할 수 있도록 지원합니다."
            if "sap" in tool or "ibp" in tool: return "AI 기반 수요 예측 및 재고 최적화 플랫폼입니다. 공급망 전체를 통합 관리하여 재고 비용을 절감하고 서비스 수준을 높입니다."
            if "cin7" in tool: return "옴니채널 재고 관리 및 주문 처리 자동화 플랫폼입니다. 오프라인 매장과 온라인 채널의 재고를 실시간으로 동기화합니다."
            if "katana" in tool: return "AI 기반 제조 자원 계획(MRP) 및 실시간 재고 관리 도구입니다. 생산 계획과 재고 수준을 최적화하여 제조 효율을 높입니다."
            if "landing ai" in tool or "landing" in tool: return "제조업 불량 검출을 위한 컴퓨터 비전 AI 플랫폼입니다. 품질 검사를 자동화하여 불량률을 크게 낮추고 검사 속도를 높입니다."
            if "cognex" in tool or "vidi" in tool: return "딥러닝 기반 산업용 비전 AI로 제품 결함을 자동 탐지합니다. 복잡한 품질 검사 작업을 자동화하여 품질 관리 비용을 절감합니다."
            if "minitab" in tool: return "AI 기반 통계적 품질관리(SPC) 및 공정 분석 도구입니다. 품질 불량의 근본 원인을 분석하고 공정을 개선하여 제품 품질을 높입니다."
            # Category-based fallbacks (more specific)
            if "재고" in cat or "erp" in cat: return "AI 기반 재고 관리 솔루션으로, 실시간 재고 추적과 수요 예측으로 재고 최적화를 지원합니다."
            if "품질" in cat or "제조" in cat: return "AI 기반 품질 관리 솔루션으로, 불량 검출과 공정 분석을 자동화하여 제품 품질을 높입니다."
            if "공급망" in cat: return "AI 기반 공급망 관리 솔루션으로, 수요 예측과 재고 최적화로 공급망 효율을 높입니다."
            if "고객 지원" in cat or "고객지원" in cat: return "AI 기반 고객 서비스 솔루션으로, 고객 문의를 자동 분류하고 빠른 응대를 지원하여 고객 만족도를 높입니다."
            if "오디오" in cat: return "AI 오디오 기술 솔루션으로, 음성 합성, 녹음, 편집 등 오디오 관련 작업을 자동화하고 품질을 높입니다."
            if "비디오" in cat: return "AI 비디오 제작 도구로, 영상 편집, 자막 생성, 콘텐츠 자동화로 미디어 제작 효율을 높입니다."
            if "분석" in cat or "데이터" in cat: return "AI 데이터 분석 솔루션으로, 복잡한 데이터에서 인사이트를 도출하고 의사결정을 지원합니다."
            if "프로젝트" in cat: return "AI 기반 프로젝트 관리 도구로, 업무 자동화와 진행 상황 추적으로 팀 생산성을 높입니다."
            if "마케팅" in cat: return "AI 마케팅 도구로, 콘텐츠 생성과 캠페인 최적화를 자동화하여 마케팅 효율을 높입니다."
            if "영업" in cat or "crm" in cat: return "AI 영업 지원 솔루션으로, 고객 관계 관리와 영업 프로세스를 최적화합니다."
            if "디자인" in cat: return "AI 디자인 도구로, 이미지 생성과 편집을 자동화하여 크리에이티브 작업 속도를 높입니다."
            if "생산성" in cat: return "AI 생산성 도구로, 반복 업무를 자동화하고 협업을 강화하여 업무 효율을 높입니다."
            if "자동화" in cat: return "워크플로우 자동화 플랫폼으로, 수작업을 줄이고 프로세스를 표준화하여 생산성을 높입니다."
            if "회의" in cat: return "AI 회의 지원 도구로, 녹취, 요약, 액션 아이템 추출을 자동화하여 회의 효율을 높입니다."
            if "커뮤니케이션" in cat: return "AI 커뮤니케이션 도구로, 작문, 번역, 메시징을 지원하여 소통 품질을 높입니다."
            if "프레젠테이션" in cat: return "AI 프레젠테이션 도구로, 슬라이드 디자인과 콘텐츠 생성을 자동화하여 발표 준비 시간을 단축합니다."
            if "개발" in cat: return "AI 개발 도구로, 코드 자동 완성과 버그 탐지로 개발 생산성을 높입니다."
            if "검색" in cat: return "AI 검색 도구로, 정확한 정보 검색과 요약으로 리서치 시간을 단축합니다."
            if "노코드" in cat or "로우코드" in cat: return "노코드/로우코드 플랫폼으로, 프로그래밍 없이 앱과 자동화를 구축할 수 있습니다."
            if "설문" in cat: return "AI 설문조사 도구로, 설문 설계와 결과 분석을 자동화하여 인사이트를 빠르게 도출합니다."
            if "이커머스" in cat or "커머스" in cat: return "AI 이커머스 도구로, 상품 관리, 마케팅, 고객 응대를 자동화합니다."
            if "seo" in cat: return "AI SEO 도구로, 콘텐츠 최적화와 키워드 분석으로 검색 노출을 높입니다."
            if "소셜" in cat: return "AI 소셜 미디어 관리 도구로, 콘텐츠 스케줄링과 성과 분석을 자동화합니다."
            if "웹" in cat: return "AI 웹 개발 도구로, 디자인과 퍼블리싱을 효율화하여 웹사이트 제작 속도를 높입니다."
            if "제품" in cat: return "AI 제품 관리 도구로, 사용자 분석과 피드백 수집으로 제품 개선을 지원합니다."
            if "일반" in cat or "ai" in cat: return "범용 AI 어시스턴트로, 글쓰기, 분석, 코딩 등 다양한 업무를 지원합니다."
            # Default fallback (should rarely be used now)
            return "AI 기반 업무 효율화 솔루션으로, 기존 워크플로우에 쉽게 통합하여 생산성을 높일 수 있습니다."
        
        # Note: Recommendation reasons are now dynamically generated by LLM (see llm_logic.py)
        
        # Benefit Text (Expected outcome)
        def get_benefit_text(tool_name, category):
            tool = tool_name.lower()
            cat = category.lower()
            # Specific tool mappings
            if "zapier" in tool: return "예상 효과: 수작업 시간 30% 이상 절감"
            if "notion" in tool: return "예상 효과: 팀 협업 효율 40% 향상"
            if "fireflies" in tool: return "예상 효과: 회의록 작성 시간 50% 단축"
            if "chatgpt" in tool: return "예상 효과: 문서 초안 작성 시간 60% 절감"
            if "jasper" in tool: return "예상 효과: 콘텐츠 생산 속도 10배 향상"
            if "midjourney" in tool: return "예상 효과: 디자인 시안 비용 70% 절감"
            # Additional specific tools
            if "intercom" in tool: return "예상 효과: 고객 응대 시간 67% 단축"
            if "elevenlabs" in tool or "eleven labs" in tool: return "예상 효과: 음성 콘텐츠 제작 비용 80% 절감"
            if "zendesk" in tool: return "예상 효과: 티켓 처리 시간 40% 단축"
            if "synthesia" in tool: return "예상 효과: 교육 영상 제작 비용 80% 절감"
            if "heygen" in tool: return "예상 효과: 영상 제작 시간 90% 단축"
            if "runway" in tool: return "예상 효과: 영상 편집 시간 70% 단축"
            if "descript" in tool: return "예상 효과: 미디어 편집 시간 50% 단축"
            if "murf" in tool: return "예상 효과: 내레이션 비용 90% 절감"
            if "krisp" in tool: return "예상 효과: 통화 품질 문제 95% 해결"
            if "miro" in tool: return "예상 효과: 팀 아이디어 공유 속도 50% 향상"
            if "monday" in tool: return "예상 효과: 프로젝트 가시성 60% 향상"
            if "asana" in tool: return "예상 효과: 업무 완료율 25% 향상"
            if "clickup" in tool: return "예상 효과: 팀 협업 효율 45% 향상"
            if "amplitude" in tool: return "예상 효과: 제품 인사이트 발굴 3배 증가"
            if "mixpanel" in tool: return "예상 효과: 전환율 개선 속도 40% 향상"
            if "pendo" in tool: return "예상 효과: 사용자 온보딩 완료율 30% 향상"
            if "drift" in tool: return "예상 효과: 리드 전환율 40% 향상"
            if "typeform" in tool: return "예상 효과: 설문 응답률 50% 향상"
            if "surveymonkey" in tool: return "예상 효과: 인사이트 도출 시간 60% 단축"
            if "airtable" in tool: return "예상 효과: 데이터 관리 효율 50% 향상"
            if "softr" in tool: return "예상 효과: 앱 개발 시간 80% 단축"
            if "framer" in tool: return "예상 효과: 웹사이트 제작 시간 70% 단축"
            if "webflow" in tool: return "예상 효과: 웹 개발 비용 60% 절감"
            if "shopify" in tool: return "예상 효과: 이커머스 운영 효율 35% 향상"
            if "adcreative" in tool: return "예상 효과: 광고 제작 시간 80% 단축"
            if "feedhive" in tool: return "예상 효과: SNS 관리 시간 60% 절감"
            if "surfer" in tool: return "예상 효과: 검색 순위 2배 향상"
            if "github copilot" in tool or "copilot" in tool: return "예상 효과: 코딩 속도 55% 향상"
            if "claude" in tool: return "예상 효과: 분석 및 작문 효율 50% 향상"
            if "perplexity" in tool: return "예상 효과: 리서치 시간 70% 단축"
            if "loom" in tool: return "예상 효과: 회의 시간 30% 절감"
            if "gamma" in tool: return "예상 효과: 프레젠테이션 제작 시간 80% 단축"
            if "tome" in tool: return "예상 효과: 발표 자료 품질 50% 향상"
            if "beautiful.ai" in tool or "beautiful ai" in tool: return "예상 효과: 슬라이드 디자인 시간 70% 단축"
            if "gong" in tool: return "예상 효과: 영업 성사율 30% 향상"
            if "lavender" in tool: return "예상 효과: 이메일 응답률 45% 향상"
            if "hubspot" in tool: return "예상 효과: 마케팅 ROI 40% 향상"
            if "canva" in tool: return "예상 효과: 디자인 제작 시간 75% 단축"
            if "writer" in tool: return "예상 효과: 콘텐츠 일관성 90% 유지"
            if "copy.ai" in tool: return "예상 효과: 카피라이팅 시간 80% 단축"
            if "otter" in tool: return "예상 효과: 회의 기록 정확도 95% 달성"
            if "grammarly" in tool: return "예상 효과: 영문 오류 90% 감소"
            if "tableau" in tool: return "예상 효과: 데이터 인사이트 도출 3배 향상"
            if "salesforce" in tool: return "예상 효과: 영업 효율 35% 향상"
            # Category-based fallbacks (more specific)
            if "고객 지원" in cat or "고객지원" in cat: return "예상 효과: 고객 응대 만족도 40% 향상"
            if "오디오" in cat: return "예상 효과: 오디오 제작 시간 70% 단축"
            if "비디오" in cat: return "예상 효과: 영상 제작 비용 60% 절감"
            if "분석" in cat or "데이터" in cat: return "예상 효과: 데이터 분석 속도 50% 향상"
            if "프로젝트" in cat: return "예상 효과: 프로젝트 완료율 30% 향상"
            if "마케팅" in cat: return "예상 효과: 콘텐츠 생성 효율 40% 향상"
            if "영업" in cat or "crm" in cat: return "예상 효과: 영업 생산성 35% 향상"
            if "디자인" in cat: return "예상 효과: 디자인 제작 시간 60% 단축"
            if "생산성" in cat: return "예상 효과: 업무 효율 30% 이상 향상"
            if "자동화" in cat: return "예상 효과: 수작업 시간 40% 절감"
            if "회의" in cat: return "예상 효과: 회의 후속 조치 속도 50% 향상"
            if "커뮤니케이션" in cat: return "예상 효과: 커뮤니케이션 품질 40% 향상"
            if "프레젠테이션" in cat: return "예상 효과: 발표 준비 시간 60% 단축"
            if "개발" in cat: return "예상 효과: 개발 속도 40% 향상"
            if "검색" in cat: return "예상 효과: 정보 검색 시간 60% 단축"
            if "노코드" in cat or "로우코드" in cat: return "예상 효과: 개발 의존도 70% 감소"
            if "설문" in cat: return "예상 효과: 응답률 및 인사이트 40% 향상"
            if "이커머스" in cat or "커머스" in cat: return "예상 효과: 운영 효율 35% 향상"
            if "seo" in cat: return "예상 효과: 오가닉 트래픽 50% 증가"
            if "소셜" in cat: return "예상 효과: SNS 운영 효율 50% 향상"
            if "웹" in cat: return "예상 효과: 웹 제작 시간 60% 단축"
            if "제품" in cat: return "예상 효과: 제품 개선 속도 40% 향상"
            if "일반" in cat or "ai" in cat: return "예상 효과: 전반적 생산성 35% 향상"
            # Default fallback
            return "예상 효과: 업무 생산성 향상"

        # Render all 3 cards in a single HTML flex container for equal heights
        cards_html = '<div class="solution-cards-container">'
        for i, tool in enumerate(recommended_tools):
            tool_intro = get_tool_intro(tool['Tool Name'], tool['Category'])
            # Use dynamic recommendation reason from LLM, with fallback
            rec_reason = recommendation_reasons[i] if i < len(recommendation_reasons) else "이 도구는 귀사의 업무 효율화에 도움이 됩니다."
            benefit_text = get_benefit_text(tool['Tool Name'], tool['Category'])
            cards_html += f'''<div class="solution-card">
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
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

    # [3] Curriculum
    st.markdown("<div class='section-subheader'>3. 교육 커리큘럼 (Curriculum)</div>", unsafe_allow_html=True)
    
    if roadmap_markdown:
        # LLM now generates only the table directly, just clean and render
        cleaned_content = roadmap_markdown.replace("```markdown", "").replace("```", "").strip()
        st.markdown(cleaned_content)
    else:
         st.warning("추천된 솔루션이 없어 커리큘럼을 생성할 수 없습니다.")

else:
    # --- INITIAL STATE (Empty State - Show preview) ---
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

    # Preview of Tools - Height restricted for one-page view
    st.markdown("<div class='section-subheader'>사용 가능한 솔루션 리스트 (미리보기)</div>", unsafe_allow_html=True)
    try:
        df = pd.read_csv("data/tools_db.csv")
        
        # UI Tweak: Convert 'Complexity' text to Discrete Visual Bars
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
