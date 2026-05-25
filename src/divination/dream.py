from typing import Tuple
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt


class DreamFactory(DivinationFactory):

    divination_type = "dream"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        if len(divination_body.prompt) > 40:
            raise HTTPException(status_code=400, detail="Prompt too long")
        prompt = f"我的梦境是: {divination_body.prompt}"
        return prompt, get_system_prompt(self.divination_type)
