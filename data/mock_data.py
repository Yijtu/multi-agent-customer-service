"""Mock 数据层。

真实项目中，这里的数据应该来自数据库（MySQL / MongoDB）或外部 API。
我们在演示阶段用硬编码的字典模拟，未来替换时只需修改这一个文件。
"""

MOCK_ORDERS = {
    "ORD001": {
        "status": "已发货",
        "product": "智能手表 Pro",
        "price": 1299,
        "shipping": "顺丰快递",
        "tracking": "SF1234567890",
        "estimated_delivery": "2024-12-20",
    },
    "ORD002": {
        "status": "处理中",
        "product": "无线耳机 Max",
        "price": 899,
        "shipping": "待发货",
        "tracking": None,
        "estimated_delivery": "2024-12-22",
    },
    "ORD003": {
        "status": "已完成",
        "product": "便携充电宝",
        "price": 199,
        "shipping": "已签收",
        "tracking": "YT9876543210",
        "estimated_delivery": "2024-12-15",
    },
}

MOCK_PRODUCTS = {
    "智能手表 Pro": {
        "price": 1299,
        "features": ["心率监测", "GPS定位", "防水50米", "7天续航"],
        "stock": 50,
        "rating": 4.8,
    },
    "无线耳机 Max": {
        "price": 899,
        "features": ["主动降噪", "40小时续航", "蓝牙5.3", "通话降噪"],
        "stock": 120,
        "rating": 4.6,
    },
    "便携充电宝": {
        "price": 199,
        "features": ["20000mAh", "快充支持", "双USB输出", "LED显示"],
        "stock": 200,
        "rating": 4.5,
    },
    "智能音箱": {
        "price": 499,
        "features": ["语音控制", "多房间音频", "智能家居联动", "Hi-Fi音质"],
        "stock": 80,
        "rating": 4.7,
    },
}

FAQ_DATABASE = {
    "连接问题": "请尝试以下步骤：1) 重启设备 2) 检查蓝牙是否开启 3) 删除配对记录后重新配对 4) 确保设备电量充足",
    "充电问题": "建议使用原装充电器，检查充电线是否损坏。如果问题持续，可能需要更换电池或送修。",
    "软件更新": "打开设备对应的APP，进入设置-关于-检查更新，按提示操作即可完成更新。",
    "退货政策": "我们支持7天无理由退货，30天内有质量问题可换货。请保留好购买凭证和完整包装。",
}
