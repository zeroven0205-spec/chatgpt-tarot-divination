import datetime
import logging
from fastapi import HTTPException
from src.models import DivinationBody
from .base import DivinationFactory

_logger = logging.getLogger(__name__)

BIRTHDAY_PROMPT = "我请求你担任中国传统的生辰八字算命的角色。" \
    "我将会给你我的生日，请你根据我的生日推算命盘，" \
    "分析五行属性、吉凶祸福、财运、婚姻、健康、事业等方面的情况，" \
    "并为其提供相应的指导和建议。"


class BirthdayFactory(DivinationFactory):

    divination_type = "birthday"

    def build_prompt(self, divination_body: DivinationBody) -> tuple[str, str]:
        return self.internal_build_prompt(divination_body.birthday)

    def internal_build_prompt(self, birthday: str) -> tuple[str, str]:
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
        return prompt, BIRTHDAY_PROMPT
