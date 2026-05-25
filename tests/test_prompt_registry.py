"""
Tests for versioned prompt registry and lightweight evaluation.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.divination.base import DivinationFactory, MetaDivination
from src.divination.prompt_registry import (
    PROVIDER_PROFILES,
    PROMPT_REGISTRY,
    get_evaluation_fixtures,
    get_params,
    get_provider_profile,
    get_prompt_variant,
    get_system_prompt,
)
from src.models import DivinationBody
from tuning.backend.prompt_evaluator import evaluate_output


def build_body(divination_type: str, params: dict) -> DivinationBody:
    return DivinationBody(prompt_type=divination_type, **params)


def test_registry_has_all_registered_divination_types():
    registered_types = set(MetaDivination.divination_map.keys())

    assert registered_types == set(PROMPT_REGISTRY.keys())


def test_each_prompt_type_has_active_variant_params_and_fixtures():
    for divination_type, entry in PROMPT_REGISTRY.items():
        variant = get_prompt_variant(divination_type)

        assert entry.active_variant == variant.id
        assert get_system_prompt(divination_type)
        assert 0 <= variant.temperature <= 2
        assert variant.max_tokens > 0
        assert get_params(divination_type) == {
            "temperature": variant.temperature,
            "max_tokens": variant.max_tokens,
        }
        assert get_evaluation_fixtures(divination_type)[divination_type]


def test_factories_use_registry_system_prompts_and_params():
    fixtures = get_evaluation_fixtures()

    for divination_type, cases in fixtures.items():
        factory = DivinationFactory.get(divination_type)
        body = build_body(divination_type, cases[0])
        _user_prompt, system_prompt = factory.build_prompt(body)

        assert system_prompt == get_system_prompt(divination_type)
        assert DivinationFactory.get_params(divination_type) == get_params(divination_type)


def test_prompt_evaluator_scores_representative_output():
    result = evaluate_output(
        "tarot",
        "我最近工作不顺利，想知道接下来该如何突破",
        "塔罗解析：过去的牌提示你曾经承受压力。现在的牌显示需要调整节奏。未来的牌提醒你保持行动，并给出清晰建议。",
    )

    assert result["divination_type"] == "tarot"
    assert result["overall_score"] > 0.5
    assert set(result["scores"]) == {
        "completeness",
        "relevance",
        "role_consistency",
        "format_quality",
        "fluency",
    }


def test_provider_profiles_are_declared():
    assert {"openai", "minimax", "custom"} <= set(PROVIDER_PROFILES)
    assert get_provider_profile("openai")["supports_stream"] is True
