"""多Agent智能客服系统 —— Streamlit Web UI。

启动方式：
    streamlit run app.py
"""

import streamlit as st

from data.seed import run_seed
from system import CustomerServiceSystem
from utils.tracer import format_trace_for_ui


# ==================== 初始化 ====================

@st.cache_resource
def get_system() -> CustomerServiceSystem:
    """初始化并缓存客服系统实例。"""
    run_seed()
    return CustomerServiceSystem()


def init_session_state():
    """初始化 session state。"""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = "web_user_001"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "results" not in st.session_state:
        st.session_state.results = []


# ==================== 页面配置 ====================

st.set_page_config(
    page_title="多Agent智能客服",
    page_icon="🤖",
    layout="wide",
)

init_session_state()
system = get_system()

# ==================== 侧边栏 ====================

with st.sidebar:
    st.header("⚙️ 会话设置")

    # Thread ID 管理
    thread_id = st.text_input(
        "会话 ID (thread_id)",
        value=st.session_state.thread_id,
        help="相同的会话 ID 会共享用户画像",
    )
    if thread_id != st.session_state.thread_id:
        st.session_state.thread_id = thread_id
        st.session_state.messages = []
        st.session_state.results = []
        st.rerun()

    # 新建会话
    if st.button("🆕 新建会话"):
        import time
        st.session_state.thread_id = f"web_user_{int(time.time())}"
        st.session_state.messages = []
        st.session_state.results = []
        st.rerun()

    st.divider()

    # 用户画像展示
    st.header("👤 用户画像")
    profile = system.get_profile(st.session_state.thread_id)
    if profile:
        if profile.get("budget"):
            st.metric("预算", f"¥{profile['budget']}")
        if profile.get("preferences"):
            st.write("**偏好:**", ", ".join(profile["preferences"]))
        if profile.get("interested_products"):
            st.write("**感兴趣产品:**", ", ".join(profile["interested_products"]))
        if profile.get("mentioned_orders"):
            st.write("**提到的订单:**", ", ".join(profile["mentioned_orders"]))
        if profile.get("language"):
            st.write("**语言:**", profile["language"])
    else:
        st.info("暂无画像数据，开始对话后自动累积")

    st.divider()

    # 最近一次处理的元信息
    if st.session_state.results:
        st.header("📊 处理信息")
        last = st.session_state.results[-1]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("意图", last.get("intent", "—"))
            st.metric("质量", f"{last.get('quality_score', 0):.2f}")
        with col2:
            st.metric("置信度", f"{last.get('confidence', 0):.2f}")
            st.metric("升级", "是" if last.get("escalated") else "否")

        # 节点耗时
        metadata = last.get("metadata", {})
        timings = metadata.get("node_timings", {})
        if timings:
            st.header("⏱️ 节点耗时")
            for node, ms in timings.items():
                st.write(f"- {node}: {ms}ms")

        # 调用链追踪
        trace = format_trace_for_ui(metadata)
        if trace:
            st.header("📋 调用链追踪")
            for i, entry in enumerate(trace, 1):
                status_icon = "✅" if entry.get("status") == "ok" else "❌"
                node = entry.get("node", "?")
                dur = entry.get("duration_ms", 0)
                summary = entry.get("summary", "")
                line = f"{i}. {status_icon} **{node}** ({dur:.1f}ms)"
                if summary:
                    line += f"  \n   {summary}"
                st.markdown(line)

# ==================== 主聊天区 ====================

st.title("🤖 多Agent智能客服系统")
st.caption("基于 LangChain 1.0 + LangGraph | 支持意图分类、画像累积、质量检查、Agent Hand-off")

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用系统处理
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            result = system.handle_message(
                prompt,
                thread_id=st.session_state.thread_id,
            )

        response = result["response"]
        st.markdown(response)

        # 显示处理摘要
        with st.expander("📊 查看处理详情", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("意图", result.get("intent", "—"))
            col2.metric("置信度", f"{result.get('confidence', 0):.2f}")
            col3.metric("质量评分", f"{result.get('quality_score', 0):.2f}")
            col4.metric("升级", "是" if result.get("escalated") else "否")

            # 展示 trace
            trace_data = format_trace_for_ui(result.get("metadata", {}))
            if trace_data:
                st.markdown("---")
                st.markdown("**📋 调用链追踪:**")
                for i, entry in enumerate(trace_data, 1):
                    status_icon = "✅" if entry.get("status") == "ok" else "❌"
                    node = entry.get("node", "?")
                    dur = entry.get("duration_ms", 0)
                    st.markdown(f"{i}. {status_icon} **{node}** ({dur:.1f}ms)")

    # 保存到历史
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.results.append(result)

    # 刷新侧边栏画像
    st.rerun()
