"""
当前各占卜类型的 System Prompt 模板快照

此文件为只读参考，用于：
  - 对比不同版本的 prompt 改动了什么
  - 记录 prompt 调优历史
  - 在修改前做备份

如需修改实际 prompt，请编辑对应的 src/divination/*.py 文件。
"""

PROMPTS = {
    "tarot": {
        "file": "src/divination/tarot.py",
        "var": "TAROT_PROMPT",
        "content": (
            "我请求你担任塔罗占卜师的角色。"
            "您将接受我的问题并使用虚拟塔罗牌进行塔罗牌阅读。"
            "不要忘记洗牌并介绍您在本套牌中使用的套牌。"
            "请帮我抽3张随机卡。"
            "拿到卡片后，请您仔细说明它们的意义，"
            "解释哪张卡片属于未来或现在或过去，结合我的问题来解释它们，"
            "并给我有用的建议或我现在应该做的事情."
        ),
        "note": "无聊天历史记忆，每轮独立，prompt 最大 40 字符",
    },
    "dream": {
        "file": "src/divination/dream.py",
        "var": "DREAM_PROMPT",
        "content": (
            "我请求你担任中国传统的周公解梦师的角色。"
            "我将会给你我的梦境，请你解释我的梦境，"
            "并为其提供相应的指导和建议。"
        ),
        "note": "无聊天历史记忆，每轮独立，prompt 最大 40 字符",
    },
    "birthday": {
        "file": "src/divination/birthday.py",
        "note": "birthday 类型待补充",
    },
    "name": {
        "file": "src/divination/name.py",
        "note": "name 类型待补充",
    },
    "new_name": {
        "file": "src/divination/new_name.py",
        "note": "new_name 类型待补充",
    },
    "plum_flower": {
        "file": "src/divination/plum_flower.py",
        "note": "plum_flower 类型待补充",
    },
    "fate": {
        "file": "src/divination/fate.py",
        "note": "fate 类型待补充",
    },
}
