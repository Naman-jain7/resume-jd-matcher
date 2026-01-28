from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import START, StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser

from app.prompts.skill_extraction import SKILL_EXTRACTION_PROMPT
from app.prompts.resume_rewrite import REWRITE_SUGGESTIONS_PROMPT
from app.prompts.match_score import MATCH_SCORE_PROMPT

llm = ChatOllama(model="llama3.2")
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


async def extract_skills_node(state: MatcherState) -> MatcherState:
    chain = SKILL_EXTRACTION_PROMPT | llm | parser
    result = await chain.ainvoke({
        'resume_text': state['resume_text'],
        'job_description_text': state['job_description_text']
    })
    return {**state, 'resume_skills':result['resume_skills'],
        'jd_skills':result['job_description_skills']
    }

async def match_score_node(state: MatcherState) -> MatcherState:
    chain = MATCH_SCORE_PROMPT | llm | parser

    result = await chain.ainvoke({
        'resume_data':state['resume_skills'],
        'job_description_data': state['jd_skills']
    })
    parsed = result
    return {
        **state,
        "match_score": parsed["match_score"],
        "matched_skills": parsed["matched_skills"],
        "missing_skills": parsed["missing_skills"],
    }

async def rewrite_suggestions_node(state: MatcherState) -> MatcherState:
    chain = REWRITE_SUGGESTIONS_PROMPT | llm | parser

    result = await chain.ainvoke({
        "resume_bullets": state["resume_text"],
        "job_keywords": state["jd_skills"],
    })
    parsed = result
    return {
        **state,
        "rewrite_suggestions": parsed["rewrite_suggestions"],
    }

def builder_matcher_graph():
    graph = StateGraph(MatcherState)

    graph.add_node('extract_skills', extract_skills_node)
    graph.add_node("match_score", match_score_node)
    graph.add_node("rewrite_suggestions", rewrite_suggestions_node)

    graph.set_entry_point('extract_skills')

    graph.add_edge("extract_skills", "match_score")
    graph.add_edge("match_score", "rewrite_suggestions")
    graph.add_edge("rewrite_suggestions", END)

    return graph.compile()

matcher_graph = builder_matcher_graph()

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
