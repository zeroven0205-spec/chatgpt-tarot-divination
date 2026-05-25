from typing import Tuple
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt


class Fate(DivinationFactory):

    divination_type = "fate"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        fate = divination_body.fate
        if not fate or not fate.name1 or not fate.name2:
            raise HTTPException(status_code=400, detail="姻缘预测需要提供两个人的姓名 (name1 和 name2)")
        if len(fate.name1) > 40 or len(fate.name2) > 40:
            raise HTTPException(status_code=400, detail="Prompt too long")
        # 基本转义：去除可能干扰 prompt 的特殊字符，限制长度
        def sanitize(s: str) -> str:
            return ''.join(c for c in s if c.isalnum() or c in (' ', '-', '_'))[:40]
        prompt = f'{sanitize(fate.name1)}, {sanitize(fate.name2)}'
        return prompt, get_system_prompt(self.divination_type)
