from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

REWRITE_SUGGESTIONS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
"""
You are an expert Resume Optimization Agent. Your goal is to analyze provided resume content and suggest improvements that enhance professional impact, clarity, and ATS compatibility.

Guidelines:
- Use ONLY the provided resume bullets.
- Do NOT invent skills, tools, metrics, or experience.
- Use strong action verbs.
- Ensure professional tone and concise ATS-friendly language.
- Output ONLY valid JSON. Do not include any conversational filler or explanations outside the JSON.
- No explanations or commentary.
""",
        ),
        (
            "human",
"""
Resume bullets:
{resume_bullets}

Relevant job description keywords:
{job_keywords}

Return output EXACTLY in this JSON format:

{
  "rewrite_suggestions": [
    {
      "before": "<original bullet>",
      "after": "<optimized bullet>"
    }
  ]
}
""",
        ),
    ]
)
