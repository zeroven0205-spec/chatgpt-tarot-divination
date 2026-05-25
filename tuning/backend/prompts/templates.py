"""
Prompt registry snapshot for tuning scripts.

The source of truth lives in `src.divination.prompt_registry`.
"""

from src.divination.prompt_registry import export_prompt_registry


PROMPTS = export_prompt_registry()
