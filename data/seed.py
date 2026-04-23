"""数据库初始化脚本。

将 mock_data.py 中的数据导入到 SQLite 数据库。

使用方式：
    python -m data.seed
    # 或
    python data/seed.py
"""

import json
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.database import init_db, get_session, Order, Product, FAQ
from data.mock_data import MOCK_ORDERS, MOCK_PRODUCTS, FAQ_DATABASE


def seed_orders(session) -> int:
    """导入订单数据。"""
    count = 0
    for order_id, info in MOCK_ORDERS.items():
        exists = session.query(Order).filter(Order.order_id == order_id).first()
        if exists:
            continue
        order = Order(
            order_id=order_id,
            status=info["status"],
            product=info["product"],
            price=info["price"],
            shipping=info["shipping"],
            tracking=info.get("tracking"),
            estimated_delivery=info.get("estimated_delivery", ""),
        )
        session.add(order)
        count += 1
    return count


def seed_products(session) -> int:
    """导入产品数据。"""
    count = 0
    for name, info in MOCK_PRODUCTS.items():
        exists = session.query(Product).filter(Product.name == name).first()
        if exists:
            continue
        product = Product(
            name=name,
            price=info["price"],
            features=json.dumps(info["features"], ensure_ascii=False),
            stock=info["stock"],
            rating=info["rating"],
        )
        session.add(product)
        count += 1
    return count


def seed_faqs(session) -> int:
    """导入 FAQ 数据。"""
    count = 0
    for keyword, answer in FAQ_DATABASE.items():
        exists = session.query(FAQ).filter(FAQ.keyword == keyword).first()
        if exists:
            continue
        faq = FAQ(keyword=keyword, answer=answer)
        session.add(faq)
        count += 1
    return count


def run_seed() -> None:
    """执行完整的数据初始化。"""
    print("📦 初始化数据库...")
    init_db()

    with get_session() as session:
        n_orders = seed_orders(session)
        n_products = seed_products(session)
        n_faqs = seed_faqs(session)
        session.commit()

    print(f"✅ 数据初始化完成:")
    print(f"   - 订单: {n_orders} 条")
    print(f"   - 产品: {n_products} 条")
    print(f"   - FAQ:  {n_faqs} 条")


if __name__ == "__main__":
    run_seed()
