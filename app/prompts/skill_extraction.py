from langchain.prompts import ChatPromptTemplate


SKILL_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a resume and job description skill extraction agent.

Rules:
- Extract ONLY explicitly mentioned skills.
- Do NOT infer skills from context.
- Do NOT add skills that are implied or commonly associated.
- Normalize skill names (e.g., "PyTorch" not "pytorch framework").
- Group skills logically.
- Output MUST be valid JSON only.
- No explanations.
""",
        ),
        (
            "human",
            """
Resume text:
{resume_text}

Job description text:
{job_description_text}

Return output EXACTLY in this JSON format:

{
  "resume_skills": {
    "core_skills": [],
    "tools_and_technologies": [],
    "soft_skills": []
  },
  "job_description_skills": {
    "required_skills": [],
    "preferred_skills": [],
    "tools_and_technologies": []
  }
}
""",
        ),
    ]
)
