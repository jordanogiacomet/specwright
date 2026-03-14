from initializer.ai.client import ask_llm


def review_prd(prd_text):

    prompt = f"""
Review this product requirements document.

Identify:

- missing requirements
- scalability concerns
- unclear specifications
- architectural risks

PRD:

{prd_text}
"""

    return ask_llm(prompt)