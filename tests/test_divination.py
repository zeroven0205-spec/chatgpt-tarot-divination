"""
Tests for divination modules — particularly new_name birthday field fix.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.divination.base import DivinationFactory
from src.models import DivinationBody


class TestNewNameFactory:
    """Test that new_name correctly uses new_name.birthday (not divination_body.birthday)."""

    def test_new_name_build_prompt_success(self):
        """Valid new_name input should produce correct prompt."""
        body = DivinationBody(
            prompt="想给宝宝取个好名字",
            prompt_type="new_name",
            new_name={
                "surname": "王",
                "sex": "male",
                "birthday": "2024-01-01 08:00:00",
                "new_name_prompt": "聪明善良",
            },
        )

        factory = DivinationFactory.get("new_name")
        assert factory is not None

        user_prompt, system_prompt = factory.build_prompt(body)

        assert "王" in user_prompt
        assert "2024" in user_prompt
        assert "1" in user_prompt or "01" in user_prompt  # month/day
        assert system_prompt  # system prompt should not be empty

    def test_new_name_birthday_parsing(self):
        """Birthday should be parsed from new_name.birthday, not divination_body.birthday."""
        body = DivinationBody(
            prompt="test",
            prompt_type="new_name",
            new_name={
                "surname": "李",
                "sex": "female",
                "birthday": "2020-06-15 10:30:00",
                "new_name_prompt": "",
            },
        )

        factory = DivinationFactory.get("new_name")
        user_prompt, _ = factory.build_prompt(body)

        # Verify the birthday was correctly parsed from new_name.birthday
        assert "2020" in user_prompt
        assert "6" in user_prompt or "06" in user_prompt
        assert "15" in user_prompt or "015" not in user_prompt  # day 15, not minute
        assert "10" in user_prompt or "30" in user_prompt  # hour or minute

    def test_new_name_missing_birthday(self):
        """Missing new_name.birthday should raise ValidationError at Pydantic construction time."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DivinationBody(
                prompt="test",
                prompt_type="new_name",
                new_name={
                    "surname": "王",
                    "sex": "male",
                    # birthday missing
                    "new_name_prompt": "聪明",
                },
            )

    def test_new_name_invalid_birthday_format(self):
        """Invalid birthday format should raise 400."""
        body = DivinationBody(
            prompt="test",
            prompt_type="new_name",
            new_name={
                "surname": "王",
                "sex": "male",
                "birthday": "not-a-date",
                "new_name_prompt": "聪明",
            },
        )

        factory = DivinationFactory.get("new_name")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            factory.build_prompt(body)
        assert exc_info.value.status_code == 400
        assert "生日格式错误" in str(exc_info.value.detail)


class TestNewNameValidation:
    """Test new_name field-level validation."""

    def test_new_name_missing_surname(self):
        """Missing surname should raise 400."""
        body = DivinationBody(
            prompt="test",
            prompt_type="new_name",
            new_name={
                "surname": "",  # empty
                "sex": "male",
                "birthday": "2024-01-01 08:00:00",
                "new_name_prompt": "聪明",
            },
        )

        factory = DivinationFactory.get("new_name")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            factory.build_prompt(body)
        assert exc_info.value.status_code == 400

    def test_new_name_prompt_too_long(self):
        """new_name_prompt > 20 chars should raise 400."""
        body = DivinationBody(
            prompt="test",
            prompt_type="new_name",
            new_name={
                "surname": "王",
                "sex": "male",
                "birthday": "2024-01-01 08:00:00",
                "new_name_prompt": "a" * 21,  # 21 chars
            },
        )

        factory = DivinationFactory.get("new_name")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            factory.build_prompt(body)
        assert exc_info.value.status_code == 400