from typing import Tuple
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt


class TarotFactory(DivinationFactory):

    divination_type = "tarot"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        if len(divination_body.prompt) > 40:
            raise HTTPException(status_code=400, detail="Prompt too long")
        return divination_body.prompt, get_system_prompt(self.divination_type)
