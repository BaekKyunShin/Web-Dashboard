import streamlit as st
import pandas as pd
import numpy as np
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Configuration ---
def get_llm():
    """
    Initialize and return the LLM instance.
    Handles missing API Key gracefully.
    """
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        return ChatOpenAI(
            model="gpt-4o", 
            temperature=0.7, 
            openai_api_key=api_key
        )
    except Exception as e:
        st.error("🚨 OpenAI API Key가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
        return None

# --- 1. Diagnosis Agent ---
class DiagnosisOutput(BaseModel):
    problem_summary: str = Field(description="Detailed analysis of the company's core problem in 2-3 sentences, including root cause and business impact.")
    key_keywords: List[str] = Field(description="List of 5-7 technical keywords related to AI solutions for these pain points.")
    urgency: str = Field(description="Urgency level: 'High', 'Medium', or 'Low'.")

@st.cache_data(show_spinner=False)
def run_diagnosis_agent(industry, company_size, pain_points):
    llm = get_llm()
    if not llm: return None

    parser = PydanticOutputParser(pydantic_object=DiagnosisOutput)

    prompt = PromptTemplate(
        template="""
        You are an Enterprise AI Architect with 15+ years of experience. Analyze the following company profile and pain points in depth.
        
        Company Profile:
        - Industry: {industry}
        - Size: {company_size}
        
        Pain Points:
        {pain_points}
        
        Your Goal:
        1. Provide a DETAILED problem analysis in Korean (2-3 sentences):
           - Identify the ROOT CAUSE of the problem (not just restate the symptom)
           - Explain the BUSINESS IMPACT (productivity loss, cost increase, customer satisfaction decline, etc.)
           - Suggest the TYPE of AI solution needed (automation, analytics, AI assistant, etc.)
           Format: "귀사의 핵심 문제는 [root cause]로 인한 [specific problem]입니다. 이로 인해 [business impact]가 발생하고 있으며, [AI solution type]을 통해 해결할 수 있습니다."
        
        2. Identify 5-7 specific technical keywords (e.g., 'NLP', 'Chatbot', 'RPA', 'RAG', 'Predictive Analytics', 'Computer Vision', 'Workflow Automation')
        
        3. Determine the urgency based on business impact severity.
        
        {format_instructions}
        """,
        input_variables=["industry", "company_size", "pain_points"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "industry": industry,
            "company_size": company_size,
            "pain_points": pain_points
        })
        return result
    except Exception as e:
        st.error(f"Diagnosis Failed: {e}")
        return None

# --- 2. Semantic Matching Logic (Embedding-based) ---
def get_embeddings():
    """Initialize and return the Embeddings instance."""
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        return OpenAIEmbeddings(openai_api_key=api_key, model="text-embedding-3-small")
    except Exception as e:
        st.error("🚨 OpenAI API Key가 설정되지 않았습니다.")
        return None

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@st.cache_data(show_spinner=False)
def find_matching_solutions(df, pain_points: str, keywords: List[str]):
    """
    Semantic matching using OpenAI embeddings.
    Combines pain point text with extracted keywords for better matching.
    """
    if df is None or df.empty:
        return []
    
    embeddings = get_embeddings()
    if not embeddings:
        return []
    
    # Create query text from pain points and keywords
    query_text = f"{pain_points} {' '.join(keywords)}"
    
    try:
        # Get embedding for the query
        query_embedding = embeddings.embed_query(query_text)
        
        # Get embeddings for each tool (combine category + description)
        tool_texts = [f"{row['Category']} {row['Tool Name']} {row['Description']}" for _, row in df.iterrows()]
        tool_embeddings = embeddings.embed_documents(tool_texts)
        
        # Calculate similarity scores
        similarities = [cosine_similarity(query_embedding, te) for te in tool_embeddings]
        df = df.copy()
        df['similarity_score'] = similarities
        
        # Sort by similarity and return top 3
        top_results = df.sort_values(by='similarity_score', ascending=False).head(3)
        
        return top_results.to_dict('records')
    except Exception as e:
        st.error(f"매칭 실패: {e}")
        # Fallback to keyword matching
        keywords_lower = [k.lower() for k in keywords]
        def calculate_score(row):
            text_content = f"{row['Category']} {row['Tool Name']} {row['Description']}".lower()
            return sum(1 for k in keywords_lower if k in text_content)
        df = df.copy()
        df['match_score'] = df.apply(calculate_score, axis=1)
        top_results = df.sort_values(by='match_score', ascending=False).head(3)
        return top_results.to_dict('records')

# --- 3. Dynamic Recommendation Reason Generator ---
class RecommendationReasons(BaseModel):
    reasons: List[str] = Field(description="List of recommendation reasons for each tool, in Korean")

@st.cache_data(show_spinner=False)
def generate_recommendation_reasons(pain_points: str, industry: str, recommended_tools: list):
    """
    Generate dynamic, context-aware recommendation reasons for each tool.
    """
    llm = get_llm()
    if not llm:
        return ["AI 기반 업무 효율화 솔루션입니다."] * len(recommended_tools)
    
    parser = PydanticOutputParser(pydantic_object=RecommendationReasons)
    
    tools_info = "\n".join([f"- {t['Tool Name']} ({t['Category']}): {t['Description']}" for t in recommended_tools])
    
    prompt = PromptTemplate(
        template="""
        You are an Enterprise AI Consultant. Generate specific, personalized recommendation reasons for each AI tool below.
        
        Context:
        - Industry: {industry}
        - Pain Points: {pain_points}
        
        Recommended Tools:
        {tools_info}
        
        For EACH tool (in order), write a compelling 2-sentence recommendation reason in Korean that:
        1. Directly addresses the specific pain point mentioned (e.g., if "재고관리가 어렵다", explain how this tool solves inventory issues)
        2. Explains the concrete benefit for this specific company context
        
        Important: Each reason must be SPECIFIC to the pain point, NOT generic marketing copy.
        
        {format_instructions}
        """,
        input_variables=["industry", "pain_points", "tools_info"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({
            "industry": industry,
            "pain_points": pain_points,
            "tools_info": tools_info
        })
        return result.reasons
    except Exception as e:
        return [f"이 도구는 귀사의 {pain_points} 문제 해결에 도움이 됩니다."] * len(recommended_tools)


# --- 3. Roadmap Agent ---
# @st.cache_data(show_spinner=False)  # Temporarily disabled for testing
def generate_roadmap(industry, pain_points, recommended_tools):
    llm = get_llm()
    if not llm: return "API Key Missing"

    # Convert dicts to hashable tuple for caching if needed, but streamlit handles dicts in cache_data usually fine as/if they are JSON serializable. 
    # Actually, recommended_tools is a list of dicts. 
    tools_str = "\n".join([f"- {t['Tool Name']} ({t['Category']}): {t['Description']}" for t in recommended_tools])

    prompt = PromptTemplate(
        template="""
        As a Senior AI Consultant with extensive corporate training experience, generate a comprehensive education curriculum for the client's AI adoption.
        
        Context:
        - Industry: {industry}
        - Problem: {pain_points}
        
        Recommended Solutions:
        {tools_str}
        
        Generate ONLY a Markdown table in Korean for the education curriculum.
        Use exactly these columns: [단계 | 교육 과정 | 주요 내용 | 시간 | 산출물]
        
        Requirements:
        - Create exactly 10 rows of curriculum content for a comprehensive training program
        - 단계 distribution: 초급(3), 중급(4), 고급(3)
        - Each row must reference specific tool names from the recommended solutions
        - 교육 과정 should be specific course titles (e.g., "Zapier 기초 자동화 설계", "Notion AI 팀 협업 워크플로우")
        - 주요 내용 MUST be between 45-55 characters (including spaces). This is CRITICAL.
          * IMPORTANT: Count characters carefully. Each cell must have 45-55 characters.
          * Too short examples (BAD): "AI 기본 대화 흐름 학습" (14자) - NOT ACCEPTABLE
          * Good examples (45-55 characters):
            - "AI 챗봇의 대화 흐름 설계 원리를 학습하고 실제 FAQ 기반 자동 응답 시나리오를 구축" (48자)
            - "고객 지원 AI 챗봇의 기본 설정과 자동 응답 시나리오 설계 및 테스트 실습 진행" (46자)
            - "음성 합성 기술의 기본 원리 이해 및 다양한 톤과 억양의 음성 생성 실습" (43자)
        - 시간 should be realistic (4시간, 6시간, 8시간, 10시간, 12시간, 16시간, 20시간)
        - 산출물 should be specific, tangible deliverables (e.g., "자동화 워크플로우 구축", "팀 협업 템플릿", "고객 응대 시나리오")
        
        Output ONLY the markdown table, no headers, no introduction, no explanation:
        """,
        input_variables=["industry", "pain_points", "tools_str"]
    )

    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "industry": industry,
            "pain_points": pain_points,
            "tools_str": tools_str
        })
        return response.content
    except Exception as e:
        return f"Roadmap Generation Failed: {e}"
