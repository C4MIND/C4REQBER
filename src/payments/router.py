"""Payment gateway integrations."""


class PaymentRouter:
    """PaymentRouter."""
    GATEWAYS = {
        "rub_card": {
            "provider": "CloudPayments",
            "currencies": ["RUB"],
            "commission": "2.6%",
            "methods": ["visa", "mc", "mir", "sberpay", "sbp"],
            "subscription": True,
        },
        "crypto": {
            "provider": "NOWPayments",
            "currencies": ["BTC", "ETH", "USDT", "+345"],
            "commission": "0.5%",
            "auto_convert": "RUB",
        },
    }

    PRICING = {
        "free": {"price": 0, "features": ["cpu", "community", "agpl"]},
        "pro": {"price": 10, "features": ["gpu", "nvidia", "support"]},
        "team": {"price": 19, "features": ["5_users", "collab", "dash"]},
        "enterprise": {"price": 49, "features": ["unlimited", "private", "sla"]},
    }
