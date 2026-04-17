import os
from typing import List, Tuple


DEFAULT_MODEL = "gemini:gemini-3-flash-preview"


def map_ai_key(ai_key: str, model_name: str):
    """
    Maps the universal CLEAN_WORKSPACE_AI_KEY to the provider-specific environment variable name.
    """
    provider = model_name.split(":")[0]

    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "google-gla": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "cohere": "CO_API_KEY",
    }
    if provider in mapping and mapping[provider] not in os.environ:
        os.environ[mapping[provider]] = ai_key


def update_env_variables():
    # Primary prefix for this project
    prefix = "CLEAN_WORKSPACE_"

    for key in list(os.environ.keys()):
        if key.startswith(prefix):
            base_key = key[len(prefix) :]
            os.environ[base_key] = os.environ[key]

    # Universal key mapping
    ai_key = os.environ.get("CLEAN_WORKSPACE_AI_KEY")
    if ai_key:
        model_name = os.environ.get("CLEAN_WORKSPACE_MODEL", DEFAULT_MODEL)
        map_ai_key(ai_key, model_name)


update_env_variables()


# This will raise ImportError if pydantic-ai is not installed
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError  # noqa: E402


MODEL_NAME = os.environ.get("MODEL") or os.environ.get("CLEAN_WORKSPACE_MODEL") or DEFAULT_MODEL
PROMPT_CUTOFF = 10000


def summarize_links(links: List[Tuple[str, str]]) -> str:
    """
    Summarizes the provided links into a 3-7 word summary using pydantic-ai.
    Returns an empty string if no API key is configured or on error.
    """
    # Check if an API key is available
    if not os.environ.get("CLEAN_WORKSPACE_AI_KEY") and not any(k.endswith("_API_KEY") for k in os.environ.keys()):
        return ""

    prompt = "You are a helpful assistant. Please provide a 3-7 word summary of the following links of the day."

    # Catching generic Exceptions during Agent creation allows us to handle
    # missing provider-specific dependencies (e.g., if the user specified a Google model
    # but the `google-genai` package is missing) without breaking the core archiving flow.
    try:
        agent = Agent(MODEL_NAME, system_prompt=prompt)
    except Exception as e:
        print(f"AI Agent creation error (perhaps missing provider dependency?): {e}")
        return ""

    links_text = "\n".join([f"{name}: {url}" for url, name in links])

    if len(links_text) > PROMPT_CUTOFF:
        links_text = links_text[:PROMPT_CUTOFF]

    model_settings = None
    try:
        from pydantic_ai.models.google import GoogleModel

        if isinstance(agent.model, GoogleModel):
            from google.genai.types import ThinkingLevel
            from pydantic_ai.models.google import GoogleModelSettings

            model_settings = GoogleModelSettings(
                google_thinking_config={
                    "include_thoughts": True,
                    "thinking_level": ThinkingLevel.MINIMAL,
                }
            )
    except ImportError:
        pass

    # Network operations are inherently flaky, and APIs can experience rate limits or outages.
    # Catching HTTP/API errors guarantees that if the AI generation fails for any reason,
    # it safely returns an empty string and the script will still archive the URLs to Todoist.
    try:
        result = agent.run_sync(links_text, model_settings=model_settings)
        return result.output.strip() if result.output else ""
    except (ModelHTTPError, ModelAPIError) as e:
        print(f"AI API error: {e}. Falling back to no summary.")
        return ""
    except Exception as e:
        print(f"Unexpected AI error: {e}. Falling back to no summary.")
        return ""
