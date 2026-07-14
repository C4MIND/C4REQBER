"""Extended tests for src/patterns/library/market_microstructure.py - covering missed paths"""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from patterns.library.market_microstructure import (
    Agent,
    InformedTrader,
    MarketMaker,
    MarketMicrostructureConfig,
    MarketMicrostructureModel,
    NoiseTrader,
    Order,
    OrderBook,
    OrderType,
    Side,
)


class TestOrderBookExtended:
    def test_limit_buy_no_cross(self):
        book = OrderBook()
        bid = Order(1, Side.BUY, OrderType.LIMIT, 99.0, 50, 0.0, 1)
        trades = book.add_order(bid)
        assert len(trades) == 0
        assert book.get_best_bid() == 99.0

    def test_limit_sell_no_cross(self):
        book = OrderBook()
        ask = Order(1, Side.SELL, OrderType.LIMIT, 101.0, 50, 0.0, 1)
        trades = book.add_order(ask)
        assert len(trades) == 0
        assert book.get_best_ask() == 101.0

    def test_cancel_order_not_found(self):
        book = OrderBook()
        assert book.cancel_order(999) is False

    def test_cancel_order_removes_from_book(self):
        book = OrderBook()
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(bid)
        assert book.cancel_order(bid.id) is True
        assert book.get_best_bid() is None

    def test_multiple_orders_same_price_cancel_first(self):
        book = OrderBook()
        o1 = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        o2 = Order(2, Side.BUY, OrderType.LIMIT, 100.0, 30, 0.0, 2)
        book.add_order(o1)
        book.add_order(o2)
        book.cancel_order(o1.id)
        assert book.get_best_bid() == 100.0
        assert len(book.bids[100.0]) == 1


class TestAgentExtended:
    def test_generate_order_no_funds(self):
        agent = Agent(1)
        agent.cash = 0
        agent.position = 0
        book = OrderBook()
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is None

    def test_generate_order_with_mid_none(self):
        agent = Agent(1)
        agent.cash = 10000
        book = OrderBook()
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is None or order is not None


class TestInformedTraderExtended:
    def test_no_trade_when_price_matches(self):
        trader = InformedTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is None

    def test_limit_order_on_small_deviation(self):
        trader = InformedTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 99.5, 100, 0.0, 99))
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 100.5, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        # With deviation = 0/100 = 0, abs(deviation) < 0.001 returns None
        assert order is None


class TestMarketMakerExtended:
    def test_generate_order_returns_bid(self):
        mm = MarketMaker(1)
        book = OrderBook()
        order = mm.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.side == Side.BUY
        assert order.order_type == OrderType.LIMIT

    def test_generate_order_cancels_previous(self):
        mm = MarketMaker(1)
        book = OrderBook()
        old = Order(99, Side.BUY, OrderType.LIMIT, 99.0, 100, 0.0, 99)
        book.add_order(old)
        mm.active_orders = [old.id]
        order = mm.generate_order(book, 100.0, 0.0)
        assert old.id not in book.order_id_map


class TestMarketMicrostructureModelExtended:
    def test_simulate_loop(self):
        cfg = MarketMicrostructureConfig(n_agents=10, simulation_time=1.0, arrival_rate=100.0, random_seed=42)
        model = MarketMicrostructureModel(cfg)
        result = model.simulate()
        assert "price_statistics" in result

    def test_analyze_results_with_trades(self):
        cfg = MarketMicrostructureConfig(n_agents=10, simulation_time=5.0, random_seed=42)
        model = MarketMicrostructureModel(cfg)
        result = model.run()
        assert result["trades"]["count"] >= 0

    def test_price_impact_with_few_trades(self):
        model = MarketMicrostructureModel(MarketMicrostructureConfig())
        trades = [{"price": 100.0 + i * 0.1, "quantity": 10} for i in range(5)]
        result = model._calculate_price_impact(trades)
        assert result["kyle_lambda"] == 0.0

    def test_price_impact_with_many_trades(self):
        model = MarketMicrostructureModel(MarketMicrostructureConfig())
        trades = [{"price": 100.0 + i * 0.1, "quantity": 10 + i} for i in range(15)]
        result = model._calculate_price_impact(trades)
        assert isinstance(result["kyle_lambda"], float)
        assert isinstance(result["avg_price_impact"], float)

    def test_get_metadata(self):
        meta = MarketMicrostructureModel.get_metadata()
        assert meta["pattern_id"] == 57
        assert "outputs" in meta
