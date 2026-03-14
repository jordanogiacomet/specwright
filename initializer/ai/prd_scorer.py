import json

from initializer.ai.client import ask_llm


def build_prompt(prd_text):

    return f"""
Evaluate the following Product Requirements Document.

Score the PRD from 1 to 10 for production readiness.

Evaluation criteria:

1. Clarity of requirements
2. Architecture completeness
3. Scalability considerations
4. Technical feasibility
5. Implementation readiness

Return JSON in this format:

{{
  "score": number,
  "strengths": [],
  "weaknesses": [],
  "missing_elements": [],
  "improvement_suggestions": []
}}

PRD:

{prd_text}
"""


def score_prd(prd_text):

    prompt = build_prompt(prd_text)

    result = ask_llm(prompt)

    try:

        data = json.loads(result)

    except Exception:

        return {
            "score": None,
            "raw": result
        }

    return data