from pydantic_ai import Agent
from scraper.ai.prompts import CHARACTER_TAGGING_PROMPT, CharacterTags


CHARACTER_TAGGING_AGENT = Agent(
    "openrouter:x-ai/grok-4-fast",
    output_type=CharacterTags,
    system_prompt=CHARACTER_TAGGING_PROMPT,
)
