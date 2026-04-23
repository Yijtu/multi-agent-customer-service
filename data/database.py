"""业务数据库层。

使用 SQLAlchemy ORM 封装 SQLite 数据库操作，
替代 mock_data.py 中的硬编码字典。

表结构：
- orders: 订单表
- products: 产品表
- faqs: FAQ 表
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, Column, Integer, Float, String, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config import BUSINESS_DB_PATH

Base = declarative_base()

# ==================== 模型定义 ====================


class Order(Base):
    """订单表。"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False)
    product = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    shipping = Column(String(50), default="")
    tracking = Column(String(50), nullable=True)
    estimated_delivery = Column(String(20), default="")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "product": self.product,
            "price": self.price,
            "shipping": self.shipping,
            "tracking": self.tracking,
            "estimated_delivery": self.estimated_delivery,
        }


class Product(Base):
    """产品表。"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    features = Column(Text, default="[]")  # JSON 数组
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "price": self.price,
            "features": json.loads(self.features) if self.features else [],
            "stock": self.stock,
            "rating": self.rating,
        }


class FAQ(Base):
    """FAQ 表。"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(50), unique=True, nullable=False, index=True)
    answer = Column(Text, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "answer": self.answer,
        }


# ==================== 数据库引擎 ====================

_engine = create_engine(f"sqlite:///{BUSINESS_DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=_engine)


def init_db() -> None:
    """创建所有表（如果不存在）。"""
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    """获取一个数据库会话。"""
    return SessionLocal()


# ==================== 查询函数 ====================


def query_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """根据订单号查询订单。"""
    with get_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id.upper()).first()
        return order.to_dict() if order else None


def track_shipping_by_number(tracking_number: str) -> Optional[str]:
    """根据物流单号查询物流信息。"""
    with get_session() as session:
        order = session.query(Order).filter(Order.tracking == tracking_number).first()
        if order:
            return f"{order.shipping} {tracking_number}: 订单 {order.order_id} - {order.status}"
        return None


def search_products_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    """按关键词搜索产品。"""
    with get_session() as session:
        products = session.query(Product).filter(
            Product.name.ilike(f"%{keyword}%")
        ).all()
        return [p.to_dict() for p in products]


def get_products_by_budget(budget: int, limit: int = 3) -> List[Dict[str, Any]]:
    """根据预算推荐产品（按评分降序）。"""
    with get_session() as session:
        products = (
            session.query(Product)
            .filter(Product.price <= budget)
            .order_by(Product.rating.desc())
            .limit(limit)
            .all()
        )
        return [p.to_dict() for p in products]


def search_faq_by_keyword(problem_type: str) -> Optional[Dict[str, str]]:
    """搜索 FAQ。"""
    with get_session() as session:
        # 精确匹配
        faq = session.query(FAQ).filter(FAQ.keyword == problem_type).first()
        if faq:
            return {"keyword": faq.keyword, "answer": faq.answer}
        # 模糊匹配
        faq = session.query(FAQ).filter(
            FAQ.keyword.ilike(f"%{problem_type}%")
        ).first()
        if faq:
            return {"keyword": faq.keyword, "answer": faq.answer}
        # 反向匹配：problem_type 包含 keyword
        faqs = session.query(FAQ).all()
        for f in faqs:
            if f.keyword in problem_type:
                return {"keyword": f.keyword, "answer": f.answer}
        return None
