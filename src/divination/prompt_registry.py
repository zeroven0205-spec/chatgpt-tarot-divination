from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Union


@dataclass(frozen=True)
class PromptVariant:
    id: str
    system_prompt: str
    temperature: float
    max_tokens: int
    tags: List[str] = field(default_factory=list)
    note: str = ""


@dataclass(frozen=True)
class PromptEntry:
    divination_type: str
    active_variant: str
    variants: Dict[str, PromptVariant]
    evaluation_fixtures: List[Dict[str, Any]] = field(default_factory=list)


PROMPT_REGISTRY: Dict[str, PromptEntry] = {
    "tarot": PromptEntry(
        divination_type="tarot",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任塔罗占卜师的角色。 "
                    "您将接受我的问题并使用虚拟塔罗牌进行塔罗牌阅读。 "
                    "不要忘记洗牌并介绍您在本套牌中使用的套牌。 "
                    "请帮我抽3张随机卡。 "
                    "拿到卡片后，请您仔细说明它们的意义，"
                    "解释哪张卡片属于未来或现在或过去，结合我的问题来解释它们，"
                    "并给我有用的建议或我现在应该做的事情."
                ),
                temperature=0.9,
                max_tokens=1500,
                tags=["tarot", "three-card", "guidance"],
                note="三张牌，占卜问题最长 40 字符。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "我最近工作不顺利，想知道接下来该如何突破"},
            {"prompt": "我的财务状况如何"},
        ],
    ),
    "dream": PromptEntry(
        divination_type="dream",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任中国传统的周公解梦师的角色。"
                    "我将会给你我的梦境，请你解释我的梦境，"
                    "并为其提供相应的指导和建议。"
                ),
                temperature=0.9,
                max_tokens=1200,
                tags=["dream", "interpretation", "guidance"],
                note="梦境描述最长 40 字符。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "梦见大蛇追我"},
            {"prompt": "梦见自己在考试"},
        ],
    ),
    "plum_flower": PromptEntry(
        divination_type="plum_flower",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任中国传统的梅花易数占卜师的角色。"
                    "我会随意说出两个数，第一个数取为上卦，第二个数取为下卦。"
                    "请你直接以数起卦, 并向我解释结果"
                ),
                temperature=0.9,
                max_tokens=1000,
                tags=["plum-flower", "yi-jing"],
                note="两个数字起卦。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "测试梅花易数", "plum_flower": {"num1": 8, "num2": 3}},
            {"prompt": "看看今天运势", "plum_flower": {"num1": 6, "num2": 9}},
        ],
    ),
    "birthday": PromptEntry(
        divination_type="birthday",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任中国传统的生辰八字算命的角色。"
                    "我将会给你我的生日，请你根据我的生日推算命盘，"
                    "分析五行属性、吉凶祸福、财运、婚姻、健康、事业等方面的情况，"
                    "并为其提供相应的指导和建议。"
                ),
                temperature=0.85,
                max_tokens=2000,
                tags=["birthday", "bazi", "five-elements"],
                note="生日格式为 YYYY-MM-DD HH:MM:SS。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "想了解我的人生运势", "birthday": "1990-01-01 08:00:00"},
            {"prompt": "事业和健康怎么样", "birthday": "1988-08-08 12:30:00"},
        ],
    ),
    "new_name": PromptEntry(
        divination_type="new_name",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任起名师的角色，"
                    "我将会给你我的姓氏、生日、性别等，"
                    "请返回你认为最适合我的名字，"
                    "请注意姓氏在前，名字在后。"
                ),
                temperature=0.85,
                max_tokens=1500,
                tags=["name", "baby-name", "five-elements"],
                note="宝宝取名，附加要求最长 20 字符。",
            )
        },
        evaluation_fixtures=[
            {
                "prompt": "想给宝宝取个好名字",
                "new_name": {
                    "surname": "王",
                    "sex": "男",
                    "birthday": "2024-01-01 08:00:00",
                    "new_name_prompt": "希望名字带水",
                },
            },
            {
                "prompt": "想要温和有书卷气的名字",
                "new_name": {
                    "surname": "李",
                    "sex": "女",
                    "birthday": "2023-05-20 09:30:00",
                    "new_name_prompt": "温和雅致",
                },
            },
        ],
    ),
    "name": PromptEntry(
        divination_type="name",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "我请求你担任中国传统的姓名五格算命师的角色。"
                    "我将会给你我的名字，请你根据我的名字推算，"
                    "分析姓氏格、名字格、和自己格。"
                    "并为其提供相应的指导和建议。"
                ),
                temperature=0.8,
                max_tokens=800,
                tags=["name", "five-grid"],
                note="姓名长度 1-20 字符。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "李明"},
            {"prompt": "欧阳娜娜"},
        ],
    ),
    "fate": PromptEntry(
        divination_type="fate",
        active_variant="v1.0",
        variants={
            "v1.0": PromptVariant(
                id="v1.0",
                system_prompt=(
                    "你是一个姻缘助手，我给你发两个人的名字，用逗号隔开，"
                    "你来随机说一下，这两个人之间的缘分如何？"
                    " 不需要很真实，只需要娱乐化的说一下即可，"
                    "你可以根据人名先判断一下这个人名的真实性，"
                    "如果输入是一些类似张三李四之类的，就返回不合适，"
                    "或者如果两个人的名字性别，都是同性，也最好返回不合适。"
                    "然后基本主要围绕, 90%的概率 说二人很合适, 然后10%的概率，"
                    "说对方不合适，并列出为啥这样的原因。"
                ),
                temperature=0.8,
                max_tokens=800,
                tags=["fate", "relationship", "entertainment"],
                note="娱乐化姻缘匹配。",
            )
        },
        evaluation_fixtures=[
            {"prompt": "我和她的姻缘如何", "fate": {"name1": "李明", "name2": "王芳"}},
            {"prompt": "看看缘分", "fate": {"name1": "郭靖", "name2": "黄蓉"}},
        ],
    ),
}

PROVIDER_PROFILES: Dict[str, Dict[str, Any]] = {
    "openai": {
        "api_style": "chat_completions",
        "supports_stream": True,
        "default_base_url": "https://api.openai.com/v1",
        "notes": "Default OpenAI-compatible provider profile.",
    },
    "minimax": {
        "api_style": "chat_completions_compatible",
        "supports_stream": True,
        "default_base_url": "https://api.minimax.chat/v1",
        "notes": "MiniMax can be used through custom OpenAI-compatible settings.",
    },
    "custom": {
        "api_style": "chat_completions_compatible",
        "supports_stream": True,
        "default_base_url": "",
        "notes": "User-provided API base URL, API key, and model.",
    },
}


def get_prompt_entry(divination_type: str) -> PromptEntry:
    try:
        return PROMPT_REGISTRY[divination_type]
    except KeyError as exc:
        raise KeyError(f"Prompt type '{divination_type}' is not registered") from exc


def get_prompt_variant(divination_type: str, variant_id: Union[str, None] = None) -> PromptVariant:
    entry = get_prompt_entry(divination_type)
    active_variant_id = variant_id or entry.active_variant
    try:
        return entry.variants[active_variant_id]
    except KeyError as exc:
        raise KeyError(
            f"Prompt variant '{active_variant_id}' is not registered for '{divination_type}'"
        ) from exc


def get_system_prompt(divination_type: str, variant_id: Union[str, None] = None) -> str:
    return get_prompt_variant(divination_type, variant_id).system_prompt


def get_params(divination_type: str, variant_id: Union[str, None] = None) -> Dict[str, Union[float, int]]:
    variant = get_prompt_variant(divination_type, variant_id)
    return {
        "temperature": variant.temperature,
        "max_tokens": variant.max_tokens,
    }


def get_evaluation_fixtures(divination_type: Union[str, None] = None) -> Dict[str, List[Dict[str, Any]]]:
    if divination_type:
        entry = get_prompt_entry(divination_type)
        return {divination_type: list(entry.evaluation_fixtures)}
    return {
        key: list(entry.evaluation_fixtures)
        for key, entry in PROMPT_REGISTRY.items()
    }


def get_provider_profile(provider: str) -> Dict[str, Any]:
    try:
        return dict(PROVIDER_PROFILES[provider])
    except KeyError as exc:
        raise KeyError(f"Provider profile '{provider}' is not registered") from exc


def export_prompt_registry() -> Dict[str, Any]:
    return {
        key: {
            **asdict(entry),
            "variants": {
                variant_key: asdict(variant)
                for variant_key, variant in entry.variants.items()
            },
        }
        for key, entry in PROMPT_REGISTRY.items()
    }
