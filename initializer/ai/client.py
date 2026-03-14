import os
from openai import OpenAI

client = OpenAI(api_key="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")

def ask_llm(prompt, model="gpt-4.1-mini"):

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a senior software architect."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content