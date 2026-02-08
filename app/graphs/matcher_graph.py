from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import START, StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser

from langsmith import traceable

from app.prompts.skill_extraction import SKILL_EXTRACTION_PROMPT
from app.prompts.resume_rewrite import REWRITE_SUGGESTIONS_PROMPT
from app.prompts.match_score import MATCH_SCORE_PROMPT

matcher_llm = ChatOllama(model="job-description:latest", base_url="http://127.0.0.1:11434")
extractor_suggester_llm = ChatOllama(model="gemma3:1b", base_url="http://127.0.0.1:11434")
parser = JsonOutputParser()
class MatcherState(TypedDict):
    resume_text: str
    job_description_text: str

    resume_skills: Dict[str, Any]
    jd_skills: Dict[str, Any]

    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]

    rewrite_suggestions: List[Dict[str, str]]

@traceable(name='extract_skills_node')
async def extract_skills_node(state: MatcherState) -> Dict[str, Any]:
    chain = SKILL_EXTRACTION_PROMPT | extractor_suggester_llm | parser
    result = await chain.ainvoke({
        'resume_text': state['resume_text'],
        'job_description_text': state['job_description_text']
    })
    
    return {
        'resume_skills':result['resume_skills'],
        'jd_skills':result['job_description_skills']
    }

@traceable(name='match_score_node')
async def match_score_node(state: MatcherState) -> MatcherState:
    chain = MATCH_SCORE_PROMPT | matcher_llm | parser

    result = await chain.ainvoke({
        'resume_data':state['resume_skills'],
        'job_description_data': state['jd_skills']
    })

    return {
        "match_score":  result["match_score"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
    }

@traceable(name='rewrite_suggestions_node')
async def rewrite_suggestions_node(state: MatcherState) -> MatcherState:
    chain = REWRITE_SUGGESTIONS_PROMPT | extractor_suggester_llm | parser

    result = await chain.ainvoke({
        "resume_bullets": state["resume_text"],
        "job_keywords": state["jd_skills"],
    })

    return {
        "rewrite_suggestions": result["rewrite_suggestions"],
    }

def builder_matcher_graph():
    graph = StateGraph(MatcherState)

    graph.add_node('extract_skills', extract_skills_node)
    graph.add_node("match_score", match_score_node)
    graph.add_node("rewrite_suggestions", rewrite_suggestions_node)

    graph.set_entry_point('extract_skills')

    graph.add_edge("extract_skills", "match_score")
    graph.add_edge("extract_skills", "rewrite_suggestions")
    graph.add_edge("match_score", END)
    graph.add_edge("rewrite_suggestions", END)

    return graph.compile()

matcher_graph = builder_matcher_graph()

@traceable(name='run_matcher_graph')
async def run_matcher_graph(resume_text: str, job_description_text: str) -> Dict[str, Any]:
    initial_state: MatcherState = {
        "resume_text": resume_text,
        "job_description_text": job_description_text,
        "resume_skills": {},
        "jd_skills": {},
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "rewrite_suggestions": [],
    }

    return await matcher_graph.ainvoke(initial_state)