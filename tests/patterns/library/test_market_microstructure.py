"""Tests for market_microstructure pattern module."""

import numpy as np
import pytest

from src.patterns.library.market_microstructure import (
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


class TestEnums:
    def test_order_type_values(self):
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.CANCEL.value == "cancel"

    def test_side_values(self):
        assert Side.BUY.value == "buy"
        assert Side.SELL.value == "sell"


class TestOrder:
    def test_order_creation(self):
        order = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        assert order.id == 1
        assert order.side == Side.BUY
        assert order.price == 100.0
        assert order.quantity == 10


class TestOrderBook:
    @pytest.fixture
    def book(self):
        return OrderBook(tick_size=0.01)

    def test_init(self, book):
        assert book.get_best_bid() is None
        assert book.get_best_ask() is None
        assert book.get_midprice() is None
        assert book.get_spread() is None

    def test_add_limit_bid(self, book):
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        book.add_order(bid)
        assert book.get_best_bid() == 100.0

    def test_add_limit_ask(self, book):
        ask = Order(1, Side.SELL, OrderType.LIMIT, 101.0, 10, 0.0, 1)
        book.add_order(ask)
        assert book.get_best_ask() == 101.0

    def test_spread_calculation(self, book):
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        ask = Order(2, Side.SELL, OrderType.LIMIT, 101.0, 10, 0.0, 2)
        book.add_order(bid)
        book.add_order(ask)
        assert book.get_spread() == 1.0
        assert book.get_midprice() == 100.5

    def test_market_order_buy(self, book):
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        book.add_order(ask)
        market_buy = Order(2, Side.BUY, OrderType.MARKET, 0, 5, 1.0, 2)
        trades = book.add_order(market_buy)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 5
        assert trades[0]["price"] == 100.0

    def test_market_order_sell(self, book):
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        book.add_order(bid)
        market_sell = Order(2, Side.SELL, OrderType.MARKET, 0, 5, 1.0, 2)
        trades = book.add_order(market_sell)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 5

    def test_partial_fill(self, book):
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 5, 0.0, 1)
        book.add_order(ask)
        market_buy = Order(2, Side.BUY, OrderType.MARKET, 0, 10, 1.0, 2)
        trades = book.add_order(market_buy)
        assert len(trades) == 1
        assert trades[0]["quantity"] == 5

    def test_cancel_order(self, book):
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        book.add_order(bid)
        assert book.cancel_order(1) is True
        assert book.get_best_bid() is None
        assert book.cancel_order(999) is False

    def test_limit_order_crossing(self, book):
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 10, 0.0, 1)
        book.add_order(ask)
        crossing_bid = Order(2, Side.BUY, OrderType.LIMIT, 101.0, 5, 1.0, 2)
        trades = book.add_order(crossing_bid)
        assert len(trades) > 0

    def test_get_depth(self, book):
        for i in range(3):
            bid = Order(i, Side.BUY, OrderType.LIMIT, 100.0 - i, 10, 0.0, 1)
            ask = Order(i + 10, Side.SELL, OrderType.LIMIT, 101.0 + i, 10, 0.0, 1)
            book.add_order(bid)
            book.add_order(ask)
        depth = book.get_depth(5)
        assert len(depth["bids"]) == 3
        assert len(depth["asks"]) == 3


class TestAgents:
    def test_noise_trader(self):
        book = OrderBook()
        agent = NoiseTrader(1, volatility=0.02)
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.side in [Side.BUY, Side.SELL]
        assert order.order_type in [OrderType.MARKET, OrderType.LIMIT]

    def test_informed_trader_deviation(self):
        book = OrderBook()
        book.add_order(Order(1, Side.BUY, OrderType.LIMIT, 99.0, 10, 0.0, 1))
        book.add_order(Order(2, Side.SELL, OrderType.LIMIT, 102.0, 10, 0.0, 2))
        agent = InformedTrader(1, conviction=0.5)
        order = agent.generate_order(book, 100.0, 0.0)
        # Mid = 100.5, fundamental = 100, deviation ≈ 0.005 > 0.001 → should trade
        assert order is not None

    def test_informed_trader_no_deviation(self):
        book = OrderBook()
        book.add_order(Order(1, Side.BUY, OrderType.LIMIT, 99.9, 10, 0.0, 1))
        book.add_order(Order(2, Side.SELL, OrderType.LIMIT, 100.1, 10, 0.0, 2))
        agent = InformedTrader(1, conviction=0.5)
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is None

    def test_market_maker(self):
        book = OrderBook()
        agent = MarketMaker(1, spread_target=0.02)
        order = agent.generate_order(book, 100.0, 0.0)
        assert order is not None
        assert order.order_type == OrderType.LIMIT


class TestMarketMicrostructureModel:
    @pytest.fixture
    def config(self):
        return MarketMicrostructureConfig(n_agents=20, simulation_time=10.0, random_seed=42)

    @pytest.fixture
    def model(self, config):
        return MarketMicrostructureModel(config)

    def test_init(self, model, config):
        assert model.config == config
        assert len(model.agents) == config.n_agents
        assert model.fundamental == config.initial_price

    def test_setup_agents(self, model):
        assert len(model.agents) == 20

    def test_simulate(self, model):
        result = model.simulate()
        assert "price_statistics" in result
        assert "spread_statistics" in result
        assert "volatility" in result
        assert "trades" in result
        assert "price_impact" in result
        assert result["trades"]["count"] >= 0

    def test_price_discovery(self):
        config = MarketMicrostructureConfig(
            n_agents=20, simulation_time=20.0, informed_trader_prob=0.3, random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.simulate()
        mean_price = result["price_statistics"]["mean"]
        assert 80 < mean_price < 120

    def test_trade_generation(self):
        config = MarketMicrostructureConfig(
            n_agents=50, simulation_time=50.0, arrival_rate=20.0, random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.simulate()
        assert result["trades"]["count"] > 0
        assert result["trades"]["total_volume"] > 0

    def test_price_impact(self):
        config = MarketMicrostructureConfig(n_agents=30, simulation_time=30.0, random_seed=42)
        model = MarketMicrostructureModel(config)
        result = model.simulate()
        assert "kyle_lambda" in result["price_impact"]

    def test_run(self, model):
        result = model.run()
        assert result["model_type"] == "market_microstructure"
        assert "parameters" in result

    def test_get_metadata(self):
        metadata = MarketMicrostructureModel.get_metadata()
        assert metadata["pattern_id"] == 57
        assert "parameters" in metadata
