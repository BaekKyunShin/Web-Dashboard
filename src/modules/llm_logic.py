import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

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
    problem_summary: str = Field(description="Summary of the company's pain points in 1 sentence.")
    key_keywords: List[str] = Field(description="List of 3-5 technical keywords related to AI solutions for these pain points.")
    urgency: str = Field(description="Urgency level: 'High', 'Medium', or 'Low'.")

def run_diagnosis_agent(industry, company_size, pain_points):
    llm = get_llm()
    if not llm: return None

    parser = PydanticOutputParser(pydantic_object=DiagnosisOutput)

    prompt = PromptTemplate(
        template="""
        You are an Enterprise AI Architect. Analyze the following company profile and pain points.
        
        Company Profile:
        - Industry: {industry}
        - Size: {company_size}
        
        Pain Points:
        {pain_points}
        
        Your Goal:
        1. Summarize the core problem concisely in Korean.
        2. Identify 3-5 key technical keywords (e.g., 'NLP', 'Chatbot', 'Predictive Maintenance', 'RAG') that would solve these problems.
        3. Determine the urgency of AI adoption.
        
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

# --- 2. Matching Logic (Rule-based + Semantic implementation possibility) ---
def find_matching_solutions(df, keywords: List[str]):
    """
    Simple keyword matching against the CSV tools database.
    In a real-world scenario, vector search (Embeddings) would be better.
    """
    if df is None or df.empty:
        return []
    
    # Normalize keywords
    keywords = [k.lower() for k in keywords]
    
    # Score each row based on keyword overlap in 'Category', 'Tool Name', 'Description'
    def calculate_score(row):
        score = 0
        text_content = f"{row['Category']} {row['Tool Name']} {row['Description']}".lower()
        for k in keywords:
            if k in text_content:
                score += 1
        return score

    df['match_score'] = df.apply(calculate_score, axis=1)
    
    # Sort by score and return top 2
    top_results = df.sort_values(by='match_score', ascending=False).head(2)
    
    # Convert to list of dicts for easier consumption
    return top_results.to_dict('records')

# --- 3. Roadmap Agent ---
def generate_roadmap(industry, pain_points, recommended_tools):
    llm = get_llm()
    if not llm: return "API Key Missing"

    tools_str = "\n".join([f"- {t['Tool Name']} ({t['Category']}): {t['Description']}" for t in recommended_tools])

    prompt = PromptTemplate(
        template="""
        As a Senior AI Consultant, generate a structured implementation roadmap for the client.
        
        Context:
        - Scalability: {industry}
        - Problem: {pain_points}
        
        Recommended Solutions:
        {tools_str}
        
        Generate a Markdown report in Korean with the following sections:
        
        ## 1. 🚀 도입 전략 (Strategy)
        Explain why these tools are the best fit.
        
        ## 2. 📅 단계별 실행 계획 (Action Plan)
        - **Phase 1: Pilot (1-3 months)**: What to test?
        - **Phase 2: Expansion (3-6 months)**: How to scale?
        - **Phase 3: Transformation (6+ months)**: Long-term value.
        
        ## 3. 💰 예상 예산 및 ROI
        Provide a rough estimation logic (qualitative).
        
        Make it professional, confident, and actionable for C-Level executives.
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
