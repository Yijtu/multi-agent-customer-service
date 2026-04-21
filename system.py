"""多代理客服系统主类。

使用 LangGraph 编排：意图分类 → 画像提取 → 业务代理 → 质量检查 → 响应 / 升级。

通过 InMemorySaver 为每个 thread_id 持久化 state，
实现跨轮次的 user_profile 累积。
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

from agents.classifier import IntentClassifier
from agents.order_service import OrderServiceAgent
from agents.product_consult import ProductConsultAgent
from agents.profile_extractor import ProfileExtractor
from agents.quality_checker import QualityChecker
from agents.tech_support import TechSupportAgent
from config import MIN_INTENT_CONFIDENCE, MIN_QUALITY_SCORE
from state import CustomerServiceState


class CustomerServiceSystem:
    """多代理客服系统。"""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.profile_extractor = ProfileExtractor()
        self.tech_agent = TechSupportAgent()
        self.order_agent = OrderServiceAgent()
        self.product_agent = ProductConsultAgent()
        self.quality_checker = QualityChecker()

        # Checkpointer: 按 thread_id 跨轮次保存 state
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    # ==================== 节点函数 ====================

    def _classify_intent(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：意图分类。"""
        print("🔍 分析用户意图...")
        result = self.classifier.classify(state["user_message"])
        state["intent"] = result.get("intent", "escalate")
        state["confidence"] = result.get("confidence", 0.5)
        print(f"   意图: {state['intent']} (置信度: {state['confidence']:.2f})")
        return state

    def _extract_profile(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：从当前消息中提取画像，合并到已有 profile。"""
        print("👤 提取用户画像...")
        current = state.get("user_profile") or {}
        updated = self.profile_extractor.extract(state["user_message"], current)
        state["user_profile"] = updated
        print(f"   当前画像: {updated}")
        return state

    def _tech_support_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：技术支持处理。"""
        print("🔧 技术支持代理处理中...")
        state["agent_response"] = self.tech_agent.handle(
            state["user_message"],
            profile=state.get("user_profile"),
        )
        return state

    def _order_service_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：订单服务处理。"""
        print("📦 订单服务代理处理中...")
        state["agent_response"] = self.order_agent.handle(
            state["user_message"],
            profile=state.get("user_profile"),
        )
        return state

    def _product_consult_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点:产品咨询处理。"""
        print("🛍️ 产品咨询代理处理中...")
        state["agent_response"] = self.product_agent.handle(
            state["user_message"],
            profile=state.get("user_profile"),
        )
        return state

    def _escalate_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：直接升级（分类阶段就决定转人工）。"""
        print("👤 升级到人工客服...")
        state["needs_escalation"] = True
        state["escalation_reason"] = "意图识别置信度低或用户要求人工服务"
        state["agent_response"] = """非常抱歉，您的问题需要人工客服来处理。

我已经为您转接人工客服，请稍候...

在等待期间，您也可以：
1. 拨打客服热线：400-xxx-xxxx
2. 发送邮件至：support@example.com
3. 工作日 9:00-18:00 在线客服响应更快

感谢您的耐心等待！"""
        return state

    def _quality_check(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：回复质量检查。"""
        print("✅ 执行质量检查...")
        result = self.quality_checker.check(
            state["user_message"],
            state["agent_response"],
        )
        state["quality_score"] = result.get("total_score", 0) / 100

        if result.get("needs_escalation", False) or state["quality_score"] < MIN_QUALITY_SCORE:
            state["needs_escalation"] = True
            state["escalation_reason"] = result.get("reason", "质量检查未通过")

        print(f"   质量评分: {state['quality_score']:.2f}")
        return state

    def _final_escalate(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：质量检查后的升级——保留原回复，附加人工客服提示。"""
        original = state["agent_response"]
        state["agent_response"] = f"""{original}

---
⚠️ 系统提示：由于此问题可能需要更专业的处理，我们建议您联系人工客服以获得更好的服务。"""
        return state

    # ==================== 路由函数 ====================

    def _route_to_agent(
        self, state: CustomerServiceState
    ) -> Literal["tech_support", "order_service", "product_consult", "escalate"]:
        """条件路由：根据 intent 和 confidence 决定走哪个代理。"""
        if state["confidence"] < MIN_INTENT_CONFIDENCE:
            return "escalate"

        intent = state["intent"]
        if intent in ("tech_support", "order_service", "product_consult"):
            return intent
        return "escalate"

    def _should_escalate(
        self, state: CustomerServiceState
    ) -> Literal["escalate_final", "respond"]:
        """条件路由：质量检查后决定是否升级。"""
        if state.get("needs_escalation", False):
            return "escalate_final"
        return "respond"

    # ==================== 图构建 ====================

    def _build_graph(self):
        """构建并编译 LangGraph 工作流。"""
        graph = StateGraph(CustomerServiceState)

        graph.add_node("classify", self._classify_intent)
        graph.add_node("extract_profile", self._extract_profile)
        graph.add_node("tech_support", self._tech_support_handler)
        graph.add_node("order_service", self._order_service_handler)
        graph.add_node("product_consult", self._product_consult_handler)
        graph.add_node("escalate", self._escalate_handler)
        graph.add_node("quality_check", self._quality_check)
        graph.add_node("escalate_final", self._final_escalate)

        # 起点 → 分类 → 画像提取 → 路由
        graph.add_edge(START, "classify")
        graph.add_edge("classify", "extract_profile")

        graph.add_conditional_edges(
            "extract_profile",
            self._route_to_agent,
            {
                "tech_support": "tech_support",
                "order_service": "order_service",
                "product_consult": "product_consult",
                "escalate": "escalate",
            },
        )

        graph.add_edge("tech_support", "quality_check")
        graph.add_edge("order_service", "quality_check")
        graph.add_edge("product_consult", "quality_check")
        graph.add_edge("escalate", END)

        graph.add_conditional_edges(
            "quality_check",
            self._should_escalate,
            {
                "escalate_final": "escalate_final",
                "respond": END,
            },
        )

        graph.add_edge("escalate_final", END)

        # 编译时传入 checkpointer, 自动按 thread_id 保存/恢复 state
        return graph.compile(checkpointer=self.checkpointer)

    # ==================== 对外 API ====================

    def handle_message(
        self,
        message: str,
        thread_id: str = "default",
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """处理一条用户消息。

        Args:
            message: 用户输入。
            thread_id: 会话标识；相同 thread_id 的多次调用共享 state（含 user_profile）。
            chat_history: 历史对话（未接入，留作扩展）。

        Returns:
            本轮处理结果字典。
        """
        print(f"\n{'=' * 60}")
        print(f"💬 [{thread_id}] 用户: {message}")
        print("=" * 60)

        # 每轮都重置"请求级"字段（intent/quality_score/needs_escalation 等）。
        # 不要包含 user_profile —— 它需要跨轮累积，由 Checkpointer 恢复。
        turn_input: Dict[str, Any] = {
            "user_message": message,
            "chat_history": chat_history or [],
            "intent": "",
            "confidence": 0.0,
            "agent_response": "",
            "needs_escalation": False,
            "escalation_reason": "",
            "quality_score": 0.0,
            "metadata": {"timestamp": datetime.now().isoformat()},
        }

        # thread_id 通过 configurable 传递给 Checkpointer
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(turn_input, config=config)

        return {
            "response": result["agent_response"],
            "intent": result["intent"],
            "confidence": result["confidence"],
            "quality_score": result["quality_score"],
            "escalated": result["needs_escalation"],
            "profile": result.get("user_profile", {}),
        }

    def get_profile(self, thread_id: str) -> Dict[str, Any]:
        """查询指定 thread 当前累积的用户画像。"""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.graph.get_state(config)
        return snapshot.values.get("user_profile", {}) if snapshot else {}
