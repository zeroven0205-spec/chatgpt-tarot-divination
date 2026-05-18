
from src.models import DivinationBody
from typing import Optional


# 按占卜类型配置的 LLM 参数
DIVINATION_PARAMS: dict[str, dict] = {
    "tarot":       {"temperature": 0.9, "max_tokens": 1500},
    "dream":       {"temperature": 0.9, "max_tokens": 1200},
    "plum_flower": {"temperature": 0.9, "max_tokens": 1000},
    "birthday":    {"temperature": 0.85, "max_tokens": 2000},
    "new_name":    {"temperature": 0.85, "max_tokens": 1500},
    "name":        {"temperature": 0.8, "max_tokens": 800},
    "fate":        {"temperature": 0.8, "max_tokens": 800},   # 娱乐化降低 temperature
}


class MetaDivination(type):

    divination_map = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if hasattr(cls, 'divination_type'):
            MetaDivination.divination_map[cls.divination_type] = cls


class DivinationFactory(metaclass=MetaDivination):

    @staticmethod
    def get(divination_type: str) -> Optional["DivinationFactory"]:
        cls = MetaDivination.divination_map.get(divination_type)
        if cls is None:
            return
        return cls()

    def build_prompt(self, divination_body: DivinationBody) -> tuple[str, str]:
        return '', ''

    @classmethod
    def get_params(cls, divination_type: str) -> dict:
        """返回指定类型的 LLM 参数（temperature, max_tokens）"""
        return DIVINATION_PARAMS.get(divination_type, {"temperature": 0.9, "max_tokens": 1000})
