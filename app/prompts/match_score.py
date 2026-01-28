from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

MATCH_SCORE_PROMPT = ChatPromptTemplate.from_messages([
  ("system",
    """You are an ATS evaluation agent. Rules:
    - Use ONLY the provided resume and job description data.
    - Do NOT infer or assume skills.
    - Do NOT invent experience.
    - Be deterministic and consistent.
    - Output MUST be valid JSON only.
    - Do NOT include explanations or extra text.

    Scoring weights:
    - Core skills match: 35%
    - Tools & technologies: 25%
    - Experience relevance: 20%
    - Keywords & terminology: 10%
    - Role alignment (seniority/domain): 10%

    Scoring rules:
    - Penalize missing required skills heavily.
    - Partial matches should receive partial credit.
    - Final score must be an integer between 0 and 100.
    """,
  ),
  ("human",
    """
    Resume data:
    {resume_data}

    Job description data:
    {job_description_data}

    Return output in the following JSON format EXACTLY:

    {{
      "match_score": <integer 0-100>,
      "matched_skills": [<string>],
      "missing_skills": [<string>]
    }}
    """,
  ),
])
