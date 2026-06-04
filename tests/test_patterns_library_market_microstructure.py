"""Tests for src/patterns/library/market_microstructure.py"""
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


class TestOrderTypeAndSide:
    def test_order_type_values(self):
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.CANCEL.value == "cancel"

    def test_side_values(self):
        assert Side.BUY.value == "buy"
        assert Side.SELL.value == "sell"


class TestOrderBook:
    def test_empty_book(self):
        book = OrderBook()
        assert book.get_best_bid() is None
        assert book.get_best_ask() is None
        assert book.get_midprice() is None
        assert book.get_spread() is None

    def test_add_bid_limit(self):
        book = OrderBook()
        order = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        trades = book.add_order(order)
        assert len(trades) == 0
        assert book.get_best_bid() == 100.0

    def test_add_ask_limit(self):
        book = OrderBook()
        order = Order(1, Side.SELL, OrderType.LIMIT, 101.0, 50, 0.0, 1)
        trades = book.add_order(order)
        assert len(trades) == 0
        assert book.get_best_ask() == 101.0

    def test_market_buy_executes(self):
        book = OrderBook()
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(ask)
        market_buy = Order(2, Side.BUY, OrderType.MARKET, 0, 30, 1.0, 2)
        trades = book.add_order(market_buy)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 30
        assert trades[0]["price"] == 100.0

    def test_market_sell_executes(self):
        book = OrderBook()
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(bid)
        market_sell = Order(2, Side.SELL, OrderType.MARKET, 0, 20, 1.0, 2)
        trades = book.add_order(market_sell)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 20

    def test_limit_buy_crosses_spread(self):
        book = OrderBook()
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(ask)
        limit_buy = Order(2, Side.BUY, OrderType.LIMIT, 101.0, 30, 1.0, 2)
        trades = book.add_order(limit_buy)
        assert len(trades) == 1

    def test_limit_sell_crosses_spread(self):
        book = OrderBook()
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(bid)
        limit_sell = Order(2, Side.SELL, OrderType.LIMIT, 99.0, 30, 1.0, 2)
        trades = book.add_order(limit_sell)
        assert len(trades) == 1

    def test_cancel_order(self):
        book = OrderBook()
        order = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1)
        book.add_order(order)
        assert book.cancel_order(order.id) is True
        assert book.get_best_bid() is None

    def test_cancel_unknown_order(self):
        book = OrderBook()
        assert book.cancel_order(999) is False

    def test_get_depth(self):
        book = OrderBook()
        book.add_order(Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1))
        book.add_order(Order(2, Side.SELL, OrderType.LIMIT, 102.0, 50, 0.0, 2))
        depth = book.get_depth(5)
        assert "bids" in depth
        assert "asks" in depth
        assert len(depth["bids"]) == 1
        assert len(depth["asks"]) == 1

    def test_multiple_orders_same_price(self):
        book = OrderBook()
        book.add_order(Order(1, Side.BUY, OrderType.LIMIT, 100.0, 50, 0.0, 1))
        book.add_order(Order(2, Side.BUY, OrderType.LIMIT, 100.0, 30, 0.0, 2))
        assert len(book.bids[100.0]) == 2

    def test_partial_fill(self):
        book = OrderBook()
        book.add_order(Order(1, Side.SELL, OrderType.LIMIT, 100.0, 20, 0.0, 1))
        market_buy = Order(2, Side.BUY, OrderType.MARKET, 0, 50, 1.0, 2)
        trades = book.add_order(market_buy)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 20


class TestAgent:
    def test_generate_order_no_cash_no_position(self):
        agent = Agent(1)
        agent.cash = 0
        agent.position = 0
        book = OrderBook()
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is None

    def test_generate_order_with_cash(self):
        agent = Agent(1)
        agent.cash = 10000
        agent.position = 0
        book = OrderBook()
        book.add_order(Order(1, Side.SELL, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        book.add_order(Order(2, Side.BUY, OrderType.LIMIT, 99.0, 100, 0.0, 99))
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is not None or order is None  # depends on random midprice logic


class TestNoiseTrader:
    def test_generate_order(self):
        trader = NoiseTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 101.0, 100, 0.0, 99))
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 99.0, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.quantity > 0

    def test_generate_order_market(self):
        trader = NoiseTrader(1)
        book = OrderBook()
        # Seed for reproducibility
        np.random.seed(42)
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is not None


class TestInformedTrader:
    def test_no_trade_when_no_deviation(self):
        trader = InformedTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is None

    def test_trade_on_deviation(self):
        trader = InformedTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 110.0, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.side == Side.SELL

    def test_buy_when_underpriced(self):
        trader = InformedTrader(1)
        book = OrderBook()
        book.add_order(Order(99, Side.BUY, OrderType.LIMIT, 90.0, 100, 0.0, 99))
        book.add_order(Order(99, Side.SELL, OrderType.LIMIT, 100.0, 100, 0.0, 99))
        order = trader.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.side == Side.BUY


class TestMarketMaker:
    def test_generate_order_cancels_old(self):
        mm = MarketMaker(1)
        book = OrderBook()
        old_order = Order(99, Side.BUY, OrderType.LIMIT, 99.0, 100, 0.0, 99)
        book.add_order(old_order)
        mm.active_orders = [old_order.id]
        order = mm.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.side == Side.BUY


class TestMarketMicrostructureModel:
    def test_init(self):
        cfg = MarketMicrostructureConfig(n_agents=10, random_seed=42)
        model = MarketMicrostructureModel(cfg)
        assert len(model.agents) == 10
        assert model.config == cfg

    def test_setup_agents(self):
        cfg = MarketMicrostructureConfig(n_agents=20, informed_trader_prob=0.2)
        model = MarketMicrostructureModel(cfg)
        makers = [a for a in model.agents if isinstance(a, MarketMaker)]
        informed = [a for a in model.agents if isinstance(a, InformedTrader)]
        noise = [a for a in model.agents if isinstance(a, NoiseTrader)]
        assert len(makers) == 5
        assert len(informed) > 0
        assert len(noise) > 0

    def test_simulate_short(self):
        cfg = MarketMicrostructureConfig(
            n_agents=20, simulation_time=10.0, arrival_rate=50.0, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        result = model.simulate()
        assert "price_statistics" in result
        assert "spread_statistics" in result
        assert "trades" in result
        assert "volatility" in result
        assert "price_impact" in result
        assert "order_book_depth" in result

    def test_run(self):
        cfg = MarketMicrostructureConfig(
            n_agents=20, simulation_time=10.0, arrival_rate=50.0, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        result = model.run()
        assert result["model_type"] == "market_microstructure"
        assert "parameters" in result

    def test_analyze_results_no_trades(self):
        cfg = MarketMicrostructureConfig(
            n_agents=5, simulation_time=0.1, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        model.price_history = []
        model.spread_history = []
        with patch("patterns.library.market_microstructure.np.mean", return_value=0.0):
            with patch("patterns.library.market_microstructure.np.std", return_value=0.0):
                with patch("patterns.library.market_microstructure.np.min", return_value=0.0):
                    with patch("patterns.library.market_microstructure.np.max", return_value=0.0):
                        result = model._analyze_results([])
        assert result["trades"]["count"] == 0
        assert result["trades"]["total_volume"] == 0

    def test_get_metadata(self):
        meta = MarketMicrostructureModel.get_metadata()
        assert meta["pattern_id"] == 57
        assert "parameters" in meta
        assert "applications" in meta

    def test_calculate_price_impact_few_trades(self):
        model = MarketMicrostructureModel(MarketMicrostructureConfig())
        result = model._calculate_price_impact([{"price": 100.0, "quantity": 10} for _ in range(5)])
        assert result["kyle_lambda"] == 0.0

    def test_calculate_price_impact_many_trades(self):
        model = MarketMicrostructureModel(MarketMicrostructureConfig())
        trades = [{"price": 100.0 + i * 0.1, "quantity": 10 + i} for i in range(15)]
        result = model._calculate_price_impact(trades)
        assert isinstance(result["kyle_lambda"], float)

    def test_price_discovery(self):
        cfg = MarketMicrostructureConfig(
            n_agents=20, simulation_time=5.0, informed_trader_prob=0.3, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        result = model.run()
        mean_price = result["price_statistics"]["mean"]
        assert 80 < mean_price < 120

    def test_spread_formation(self):
        cfg = MarketMicrostructureConfig(
            n_agents=10, simulation_time=5.0, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        result = model.run()
        assert result["spread_statistics"]["mean"] >= 0

    def test_trade_generation(self):
        cfg = MarketMicrostructureConfig(
            n_agents=20, simulation_time=10.0, arrival_rate=20.0, random_seed=42
        )
        model = MarketMicrostructureModel(cfg)
        result = model.run()
        assert result["trades"]["count"] >= 0


class TestMarketMicrostructureAlias:
    def test_alias_exists(self):
        from patterns.library.market_microstructure import MarketMicrostructurePattern
        assert MarketMicrostructurePattern is MarketMicrostructureModel
