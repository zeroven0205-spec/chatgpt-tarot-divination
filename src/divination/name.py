from typing import Tuple
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt


class NameFactory(DivinationFactory):

    divination_type = "name"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        if len(divination_body.prompt) > 20 or len(divination_body.prompt) < 1:
            raise HTTPException(status_code=400, detail="姓名长度错误")
        prompt = f"我的名字是{divination_body.prompt}"
        return prompt, get_system_prompt(self.divination_type)
