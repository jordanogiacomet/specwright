import os
from openai import OpenAI

client = OpenAI(api_key="")

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