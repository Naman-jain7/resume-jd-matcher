from typing import TypedDict, List, Dict, Any
from langgraph.graph import START, StateGraph, END

class MatcherState(TypedDict):
    resume_text: str
    job_description: str
    resume_skills: Dict[str, Any]
    jd_skills: Dict[str, Any]
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    rewrite_suggestions: List[Dict[str, str]]


def extract_skills_node(state: MatcherState) -> MatcherState:
    # TODO: CALL SKILL_EXTRACTION_PROMPT
    return {**state, 'resume_skills':{}, 'jd_skills':{}}

def match_score_node(state: MatcherState) -> MatcherState:
    # TODO: call MATCH_SCORE_PROMPT
    return {
        **state,
        'match_score':0,
        'matched_skills':[],
        'missing_skills':[],

    }

def rewrite_suggestions_node(state: MatcherState) -> MatcherState:
    # TODO: call REWRITE_SUGGESTIONS_PROMPT
    return {
        **state,
        'rewrite_suggestions':[]
    }

def builder_matcher_graph():
    graph = StateGraph(MatcherState)

    graph.add_node('extract_skills', extract_skills_node)
    graph.add_node("match_score", match_score_node)
    graph.add_node("rewrite_suggestions", rewrite_suggestions_node)

    graph.set_entry_point('extract_skills')

    graph.add_edge("extract_skills", "match_score")
    graph.add_edge("match_score", "rewrite")
    graph.add_edge("rewrite", END)

    return graph.compile()

matcher_graph = builder_matcher_graph()

def run_matcher_graph(resume_text: str, job_description_text: str) -> Dict[str, Any]:
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

    return matcher_graph.invoke(initial_state)