from typing import Tuple
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt


class PlumFlowerFactory(DivinationFactory):

    divination_type = "plum_flower"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        if not divination_body.plum_flower:
            raise HTTPException(status_code=400, detail="No plum_flower")
        prompt = f"我选择的数字是: {divination_body.plum_flower.num1} 和 {divination_body.plum_flower.num2}"
        return prompt, get_system_prompt(self.divination_type)
