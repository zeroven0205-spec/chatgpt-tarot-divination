from typing import Tuple
import datetime
import logging
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory
from .prompt_registry import get_system_prompt

_logger = logging.getLogger(__name__)


class BirthdayFactory(DivinationFactory):

    divination_type = "birthday"

    def build_prompt(self, divination_body: DivinationBody) -> Tuple[str, str]:
        return self.internal_build_prompt(divination_body.birthday)

    def internal_build_prompt(self, birthday: str) -> Tuple[str, str]:
        try:
            birthday_dt = datetime.datetime.strptime(
                birthday, '%Y-%m-%d %H:%M:%S'
            )
        except (ValueError, TypeError):
            _logger.warning(f"Invalid birthday format: {birthday}")
            raise HTTPException(
                status_code=400,
                detail="生日格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式"
            )
        prompt = f"我的生日是{birthday_dt.year}年{birthday_dt.month}月{birthday_dt.day}日{birthday_dt.hour}时{birthday_dt.minute}分{birthday_dt.second}秒"
        return prompt, get_system_prompt(self.divination_type)
