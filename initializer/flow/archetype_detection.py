def detect_archetype(prompt: str):

    text = prompt.lower()

    if "cms" in text or "editorial" in text:
        return "editorial-cms"

    if "api" in text:
        return "api-service"

    if "saas" in text:
        return "saas-app"

    return "editorial-cms"