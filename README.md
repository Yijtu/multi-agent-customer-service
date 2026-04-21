# 多代理智能客服系统

基于 **LangChain 1.0 + LangGraph** 的多代理客服系统，支持意图分类、动态路由、工具调用、质量检查和**跨轮次用户画像累积**。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangChain](https://img.shields.io/badge/LangChain-1.0-green)
![LangGraph](https://img.shields.io/badge/LangGraph-orange)

---

## 核心特性

- 🧠 **意图分类**：自动识别用户意图（技术支持 / 订单服务 / 产品咨询 / 人工升级）
- 🔧 **多代理协作**：每个业务域由独立 Agent 处理，各自配备专属工具
- 👤 **用户画像累积**：通过 LangGraph Checkpointer 实现跨轮次的偏好、预算、订单记忆
- ✅ **质量检查层**：LLM 自评回复质量，低分自动升级到人工
- 🔀 **条件路由**：基于置信度和分类结果动态决定工作流路径

## 架构图

```mermaid
flowchart TD
    START([START]) --> classify[意图分类]
    classify --> extract[用户画像提取]
    extract -->|tech_support| tech[技术支持代理]
    extract -->|order_service| order[订单服务代理]
    extract -->|product_consult| product[产品咨询代理]
    extract -->|escalate / 置信度低| escalate[直接升级]
    tech --> quality[质量检查]
    order --> quality
    product --> quality
    quality -->|质量达标| END([END])
    quality -->|质量差| final_esc[附加人工提示]
    escalate --> END
    final_esc --> END
```

## 技术栈

| 组件 | 用途 |
|---|---|
| **LangChain 1.0** | LLM 编排、LCEL 管道、`create_agent` |
| **LangGraph** | 工作流编排、状态管理、条件路由 |
| **LangGraph Checkpointer** | 跨轮次状态持久化（InMemorySaver） |
| **DeepSeek** | LLM 后端（国内低成本方案） |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Yijtu/multi-agent-customer-service.git
cd 02_multi_agent_support
```

### 2. 安装依赖

```bash
# 建议创建虚拟环境
python -m venv venv
source venv/bin/activate         # Linux/Mac
venv\Scripts\activate            # Windows

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
# 获取地址：https://console.deepseek.com/keys
```

### 4. 运行

```bash
python main.py
```

## 项目结构

```
02_multi_agent_support/
├── main.py                  # 入口：演示场景 + 交互循环
├── system.py                # LangGraph 工作流编排
├── config.py                # 模型初始化 + 阈值常量
├── state.py                 # CustomerServiceState / UserProfile 定义
│
├── agents/                  # 代理层
│   ├── base.py              # 业务代理基类
│   ├── classifier.py        # 意图分类（LCEL 模式）
│   ├── profile_extractor.py # 用户画像提取
│   ├── tech_support.py      # 技术支持代理
│   ├── order_service.py     # 订单服务代理
│   ├── product_consult.py   # 产品咨询代理
│   └── quality_checker.py   # 回复质量检查
│
├── tools/                   # LangChain @tool 函数
│   ├── order_tools.py       # query_order, track_shipping
│   └── product_tools.py     # search_product, recommendations, FAQ
│
├── data/
│   └── mock_data.py         # Mock 数据（订单/产品/FAQ）
│
└── utils/
    └── json_parser.py       # 容错 JSON 解析
```

## 核心设计

### State 分层

- **请求级字段**：`user_message` / `intent` / `agent_response` / `quality_score` —— 每轮重置
- **会话级字段**：`user_profile` —— 通过 Checkpointer 跨轮次累积

### 两种代理模式

| 模式 | 使用场景 | 示例 |
|---|---|---|
| **LCEL 管道** (`prompt \| llm \| parser`) | 一次性的转换 | `IntentClassifier`, `QualityChecker`, `ProfileExtractor` |
| **`create_agent`** | 需要工具调用循环 | `TechSupportAgent`, `OrderServiceAgent`, `ProductConsultAgent` |

### 用户画像累积

同一 `thread_id` 下的多轮对话会自动合并画像：

```
第1轮 "我预算1500"        → profile: {budget: 1500}
第2轮 "喜欢降噪"          → profile: {budget: 1500, preferences: ['降噪']}
第3轮 "推荐智能手表"      → Agent 知道预算和偏好，直接按 1500 推荐
```

## 多轮对话示例

```python
from system import CustomerServiceSystem

system = CustomerServiceSystem()

# 使用相同 thread_id 会累积画像
system.handle_message("我预算1500左右", thread_id="user_A")
system.handle_message("喜欢降噪和长续航", thread_id="user_A")
result = system.handle_message("推荐几个智能手表", thread_id="user_A")

print(result["response"])  # 产品代理会基于预算和偏好推荐
print(system.get_profile("user_A"))  # 查看累积的画像
```

## 未来可扩展方向

- [ ] 代理间协作（Hand-off / Supervisor 模式）
- [ ] 多语言支持（根据用户语言切换回复）
- [ ] 真实数据库对接（替换 `data/mock_data.py`）
- [ ] 持久化 Checkpointer（SqliteSaver / PostgresSaver）
- [ ] Web UI（Streamlit / Gradio）

## License

MIT
