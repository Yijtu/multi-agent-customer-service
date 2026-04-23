"""系统配置中心。

集中管理：
1. 环境变量加载（API Key）
2. LLM 模型初始化
3. 业务阈值常量
4. 持久化路径
"""

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# ==================== 环境变量 ====================

# load_dotenv() 会读取项目根目录（或任何上层目录）的 .env 文件
# 把里面的 KEY=VALUE 注入到 os.environ
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
    raise ValueError(
        "\n请先在 .env 文件中设置有效的 DEEPSEEK_API_KEY\n"
        "访问 https://console.deepseek.com/keys 获取免费密钥"
    )

# ==================== LLM 模型 ====================

# 所有 Agent 共享同一个模型实例，避免重复创建
model = init_chat_model("deepseek:deepseek-chat", api_key=DEEPSEEK_API_KEY)

# ==================== 业务阈值 ====================

# 意图识别置信度下限：低于此值直接转人工
MIN_INTENT_CONFIDENCE = 0.6

# 回复质量评分下限：低于此值触发升级
MIN_QUALITY_SCORE = 0.6

# ==================== 持久化 ====================

# Checkpointer 数据库路径（SQLite）
CHECKPOINT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "data", "checkpoints.db"
)

# 业务数据库路径（SQLite）
BUSINESS_DB_PATH = os.path.join(
    os.path.dirname(__file__), "data", "business.db"
)

# ==================== 多语言 ====================

# 支持的语言列表
SUPPORTED_LANGUAGES = ["zh", "en", "ja", "ko"]

# 默认回复语言
DEFAULT_LANGUAGE = "zh"
