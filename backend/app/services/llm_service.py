"""
LLM provider abstraction for AI report generation (Step 11).

Uses OpenAI-compatible API. Config via OPENAI_API_KEY, LLM_MODEL, optional LLM_BASE_URL.
"""

from app.core.config import get_settings


def generate_text(prompt: str, *, system_instruction: str | None = None) -> str:
    """
    Generate text using the configured LLM.
    Raises ValueError with a readable message if the API key is missing or the call fails.
    """
    settings = get_settings()
    if not (settings.openai_api_key or "").strip():
        raise ValueError("AI generation is not configured. Set OPENAI_API_KEY.")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ValueError("OpenAI client is not installed. Install the openai package.") from e
    client_kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url
    client = OpenAI(**client_kwargs)
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        msg = str(e).strip() or "Unknown error"
        if "api_key" in msg.lower() or "auth" in msg.lower():
            raise ValueError("AI generation failed: invalid or missing API key.") from e
        if "rate" in msg.lower() or "limit" in msg.lower():
            raise ValueError("AI generation failed: rate limit exceeded. Please try again.") from e
        raise ValueError("AI generation failed. Please try again.") from e
    choice = response.choices[0] if response.choices else None
    if not choice or not getattr(choice, "message", None):
        raise ValueError("AI generation failed: empty response.")
    content = getattr(choice.message, "content", None) or ""
    return content.strip()
