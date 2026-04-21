"""多代理客服系统 —— 启动入口。

运行方式：
    cd 02_multi_agent_support
    python main.py
"""

from system import CustomerServiceSystem


TEST_CASES = [
    {
        "category": "技术支持",
        "messages": [
            "我的蓝牙耳机连接不上手机怎么办？",
            "手表充电很慢，是不是坏了？",
        ],
    },
    {
        "category": "订单服务",
        "messages": [
            "帮我查一下订单 ORD001 的物流状态",
            "我的订单什么时候能到？订单号是 ORD002",
        ],
    },
    {
        "category": "产品咨询",
        "messages": [
            "你们有什么智能手表推荐吗？预算1500左右",
            "无线耳机有什么功能？",
        ],
    },
    {
        "category": "人工升级",
        "messages": [
            "我要投诉！这是第三次出问题了！",
            "我想和你们经理谈谈",
        ],
    },
]


# 多轮对话场景：同一 thread_id 内连续对话，观察 profile 如何累积
MULTI_TURN_DEMO = {
    "thread_id": "demo_user_001",
    "messages": [
        "你好，我预算1500左右",
        "我比较看重降噪和长续航",
        "根据我的需求推荐几个智能手表",
        "那之前 ORD001 的订单现在到哪了？",
    ],
}


def print_result(result: dict) -> None:
    """格式化打印单次处理结果。"""
    print("\n🤖 客服回复:")
    print(result["response"])
    print("\n📊 处理信息:")
    print(f"   - 意图: {result['intent']}")
    print(f"   - 置信度: {result['confidence']:.2f}")
    print(f"   - 质量评分: {result['quality_score']:.2f}")
    print(f"   - 是否升级: {'是' if result['escalated'] else '否'}")
    if result.get("profile"):
        print(f"   - 当前画像: {result['profile']}")
    print("-" * 60)


def run_test_cases(system: CustomerServiceSystem) -> None:
    """跑预设的无状态测试用例。每个消息用独立 thread_id 保证互不干扰。"""
    print("\n" + "=" * 60)
    print("📋 单轮测试用例（各自独立 thread）")
    print("=" * 60)

    for test in TEST_CASES:
        print(f"\n{'=' * 60}")
        print(f"📝 测试类别: {test['category']}")
        print("=" * 60)
        for i, message in enumerate(test["messages"]):
            thread = f"{test['category']}_{i}"
            result = system.handle_message(message, thread_id=thread)
            print_result(result)


def run_multi_turn_demo(system: CustomerServiceSystem) -> None:
    """多轮对话演示 —— 同一 thread_id，观察 profile 累积效果。"""
    print("\n" + "=" * 60)
    print("🎯 多轮对话演示（同一 thread_id，观察画像累积）")
    print("=" * 60)
    print(f"thread_id = {MULTI_TURN_DEMO['thread_id']}")

    for turn, message in enumerate(MULTI_TURN_DEMO["messages"], start=1):
        print(f"\n--- 第 {turn} 轮 ---")
        result = system.handle_message(
            message,
            thread_id=MULTI_TURN_DEMO["thread_id"],
        )
        print_result(result)

    print("\n" + "=" * 60)
    print("🧬 最终累积的用户画像:")
    print(system.get_profile(MULTI_TURN_DEMO["thread_id"]))
    print("=" * 60)


def run_interactive(system: CustomerServiceSystem) -> None:
    """交互式对话循环 —— 整个 session 共用一个 thread_id。"""
    print("\n" + "=" * 60)
    print("💬 交互式对话演示")
    print("=" * 60)
    print("提示: 输入 'quit' 退出，输入 'profile' 查看当前画像")

    thread_id = "interactive_session"
    while True:
        user_input = input("\n👤 您: ").strip()
        if user_input.lower() == "quit":
            print("\n感谢使用智能客服系统，再见！👋")
            break
        if user_input.lower() == "profile":
            print(f"📋 当前画像: {system.get_profile(thread_id)}")
            continue
        if not user_input:
            continue

        result = system.handle_message(user_input, thread_id=thread_id)
        print(f"\n🤖 客服: {result['response']}")


def main() -> None:
    """程序入口。"""
    print("=" * 60)
    print("🤖 多代理智能客服系统演示（含用户画像）")
    print("=" * 60)

    print("\n📦 初始化客服系统...")
    system = CustomerServiceSystem()
    print("✅ 系统初始化完成！")

    run_multi_turn_demo(system)   # 先演示多轮画像累积（最精彩）
    run_test_cases(system)         # 再跑单轮用例
    run_interactive(system)        # 最后进入交互


if __name__ == "__main__":
    main()
