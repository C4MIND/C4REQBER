"""
Pattern 57: Market Microstructure Model
Implements agent-based order book dynamics with limit order markets,
price impact analysis, and bid-ask spread formation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class OrderType(Enum):
    """OrderType."""
    MARKET = "market"
    LIMIT = "limit"
    CANCEL = "cancel"


class Side(Enum):
    """Side."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Represents a single order."""
    id: int
    side: Side
    order_type: OrderType
    price: float
    quantity: int
    timestamp: float
    agent_id: int


@dataclass
class MarketMicrostructureConfig:
    """Configuration for market microstructure simulation."""
    n_agents: int = 100
    initial_price: float = 100.0
    tick_size: float = 0.01
    lot_size: int = 100
    initial_spread: float = 0.05
    max_depth: int = 10
    arrival_rate: float = 10.0  # Orders per second
    fundamental_volatility: float = 0.001
    informed_trader_prob: float = 0.1
    noise_trader_volatility: float = 0.02
    simulation_time: float = 100.0
    random_seed: int = 42


class OrderBook:
    """
    Limit order book with price-time priority matching.
    """

    def __init__(self, tick_size: float = 0.01) -> None:
        self.tick_size = tick_size
        self.bids: dict[float, list[Order]] = {}  # price -> list of orders
        self.asks: dict[float, list[Order]] = {}  # price -> list of orders
        self.order_id_map: dict[int, Order] = {}
        self.next_order_id = 0
        self.trades: list[dict] = []

    def get_best_bid(self) -> float | None:
        """Get highest bid price."""
        if not self.bids:
            return None
        return max(self.bids.keys())

    def get_best_ask(self) -> float | None:
        """Get lowest ask price."""
        if not self.asks:
            return None
        return min(self.asks.keys())

    def get_midprice(self) -> float | None:
        """Get mid price."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2

    def get_spread(self) -> float | None:
        """Get bid-ask spread."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid

    def add_order(self, order: Order) -> list[dict]:
        """
        Add order to book and return any trades.
        """
        self.next_order_id += 1
        order.id = self.next_order_id
        self.order_id_map[order.id] = order

        executed_trades = []

        if order.order_type == OrderType.MARKET:
            executed_trades = self._execute_market_order(order)
        elif order.order_type == OrderType.LIMIT:
            executed_trades = self._execute_limit_order(order)

        return executed_trades

    def _execute_market_order(self, order: Order) -> list[dict]:
        """Execute market order against resting orders."""
        trades = []
        remaining = order.quantity

        if order.side == Side.BUY:
            # Buy at ask prices
            while remaining > 0 and self.asks:
                best_ask = min(self.asks.keys())
                orders_at_price = self.asks[best_ask]

                while remaining > 0 and orders_at_price:
                    resting = orders_at_price[0]
                    trade_qty = min(remaining, resting.quantity)

                    trades.append({
                        'price': best_ask,
                        'quantity': trade_qty,
                        'buyer': order.agent_id,
                        'seller': resting.agent_id,
                        'timestamp': order.timestamp
                    })

                    remaining -= trade_qty
                    resting.quantity -= trade_qty

                    if resting.quantity == 0:
                        orders_at_price.pop(0)
                        del self.order_id_map[resting.id]

                if not orders_at_price:
                    del self.asks[best_ask]
        else:
            # Sell at bid prices
            while remaining > 0 and self.bids:
                best_bid = max(self.bids.keys())
                orders_at_price = self.bids[best_bid]

                while remaining > 0 and orders_at_price:
                    resting = orders_at_price[0]
                    trade_qty = min(remaining, resting.quantity)

                    trades.append({
                        'price': best_bid,
                        'quantity': trade_qty,
                        'buyer': resting.agent_id,
                        'seller': order.agent_id,
                        'timestamp': order.timestamp
                    })

                    remaining -= trade_qty
                    resting.quantity -= trade_qty

                    if resting.quantity == 0:
                        orders_at_price.pop(0)
                        del self.order_id_map[resting.id]

                if not orders_at_price:
                    del self.bids[best_bid]

        return trades

    def _execute_limit_order(self, order: Order) -> list[dict]:
        """Execute or add limit order."""
        # Check for immediate execution
        trades = []

        if order.side == Side.BUY:
            best_ask = self.get_best_ask()
            if best_ask is not None and order.price >= best_ask:
                # Execute as market order
                market_order = Order(
                    id=0, side=Side.BUY, order_type=OrderType.MARKET,
                    price=0, quantity=order.quantity, timestamp=order.timestamp,
                    agent_id=order.agent_id
                )
                trades = self._execute_market_order(market_order)
                return trades
            # Add to book
            if order.price not in self.bids:
                self.bids[order.price] = []
            self.bids[order.price].append(order)
        else:
            best_bid = self.get_best_bid()
            if best_bid is not None and order.price <= best_bid:
                # Execute as market order
                market_order = Order(
                    id=0, side=Side.SELL, order_type=OrderType.MARKET,
                    price=0, quantity=order.quantity, timestamp=order.timestamp,
                    agent_id=order.agent_id
                )
                trades = self._execute_market_order(market_order)
                return trades
            # Add to book
            if order.price not in self.asks:
                self.asks[order.price] = []
            self.asks[order.price].append(order)

        return trades

    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order."""
        if order_id not in self.order_id_map:
            return False

        order = self.order_id_map[order_id]
        book = self.bids if order.side == Side.BUY else self.asks

        if order.price in book:
            book[order.price] = [o for o in book[order.price] if o.id != order_id]
            if not book[order.price]:
                del book[order.price]

        del self.order_id_map[order_id]
        return True

    def get_depth(self, n_levels: int = 5) -> dict[str, list[tuple[float, int]]]:
        """Get order book depth."""
        bids = sorted(self.bids.items(), reverse=True)[:n_levels]
        asks = sorted(self.asks.items())[:n_levels]

        bid_depth = [(p, sum(o.quantity for o in orders)) for p, orders in bids]
        ask_depth = [(p, sum(o.quantity for o in orders)) for p, orders in asks]

        return {'bids': bid_depth, 'asks': ask_depth}


class Agent:
    """Base class for trading agents."""

    def __init__(self, agent_id: int) -> None:
        self.agent_id = agent_id
        self.position = 0
        self.cash = 0.0

    def generate_order(self, book: OrderBook, fundamental: float, time: float) -> Order | None:
        """Generate a trading order using mean-reversion strategy."""
        bid = book.get_best_bid()
        ask = book.get_best_ask()
        mid = book.get_midprice()

        if bid is None:
            bid = fundamental * 0.99
        if ask is None:
            ask = fundamental * 1.01
        if mid is None:
            mid = fundamental

        if self.cash <= 0 and self.position <= 0:
            return None

        if mid < bid * 1.005:
            qty = min(10, int(self.cash // mid)) if mid > 0 else 0
            if qty > 0:
                self.position += qty
                self.cash -= qty * mid
                return Order(
                    id=0, side=Side.BUY, order_type=OrderType.MARKET,
                    price=0, quantity=qty, timestamp=time, agent_id=self.agent_id,
                )
        elif mid > ask * 0.995 and self.position > 0:
            qty = min(self.position, 10)
            self.position -= qty
            self.cash += qty * mid
            return Order(
                id=0, side=Side.SELL, order_type=OrderType.MARKET,
                price=0, quantity=qty, timestamp=time, agent_id=self.agent_id,
            )

        return None


class NoiseTrader(Agent):
    """Noise trader with random orders."""

    def __init__(self, agent_id: int, volatility: float = 0.02) -> None:
        super().__init__(agent_id)
        self.volatility = volatility

    def generate_order(self, book: OrderBook, fundamental: float, time: float) -> Order | None:
        """Generate order."""
        side = np.random.choice([Side.BUY, Side.SELL])  # type: ignore[arg-type]
        order_type = np.random.choice([OrderType.MARKET, OrderType.LIMIT], p=[0.3, 0.7])  # type: ignore[arg-type]

        mid = book.get_midprice()
        if mid is None:
            mid = fundamental

        if order_type == OrderType.LIMIT:
            # Place limit order around mid
            offset = np.random.normal(0, self.volatility * mid)
            price = mid + offset if side == Side.SELL else mid - offset
            price = round(price / 0.01) * 0.01  # Tick size
            price = max(0.01, price)
        else:
            price = 0

        quantity = np.random.randint(1, 10) * 100

        return Order(
            id=0, side=side, order_type=order_type, price=price,
            quantity=quantity, timestamp=time, agent_id=self.agent_id
        )


class InformedTrader(Agent):
    """Informed trader with knowledge of fundamental value."""

    def __init__(self, agent_id: int, conviction: float = 0.5) -> None:
        super().__init__(agent_id)
        self.conviction = conviction

    def generate_order(self, book: OrderBook, fundamental: float, time: float) -> Order | None:
        """Generate order."""
        mid = book.get_midprice()
        if mid is None:
            return None

        # Trade if price deviates from fundamental
        deviation = (mid - fundamental) / fundamental

        if abs(deviation) < 0.001:
            return None

        side = Side.SELL if mid > fundamental else Side.BUY
        order_type = OrderType.MARKET if abs(deviation) > 0.01 else OrderType.LIMIT

        price = fundamental if order_type == OrderType.LIMIT else 0
        quantity = int(50 * abs(deviation) / 0.01) * 100

        return Order(
            id=0, side=side, order_type=order_type, price=price,
            quantity=quantity, timestamp=time, agent_id=self.agent_id
        )


class MarketMaker(Agent):
    """Market maker providing liquidity."""

    def __init__(self, agent_id: int, spread_target: float = 0.02) -> None:
        super().__init__(agent_id)
        self.spread_target = spread_target
        self.active_orders: list[int] = []

    def generate_order(self, book: OrderBook, fundamental: float, time: float) -> Order | None:
        # Cancel old orders
        """Generate order."""
        for oid in self.active_orders:
            book.cancel_order(oid)
        self.active_orders = []

        # Place new quotes around fundamental
        bid_price = round((fundamental - self.spread_target/2) / 0.01) * 0.01
        ask_price = round((fundamental + self.spread_target/2) / 0.01) * 0.01

        bid_order = Order(
            id=0, side=Side.BUY, order_type=OrderType.LIMIT,
            price=bid_price, quantity=500, timestamp=time, agent_id=self.agent_id
        )
        Order(
            id=0, side=Side.SELL, order_type=OrderType.LIMIT,
            price=ask_price, quantity=500, timestamp=time, agent_id=self.agent_id
        )

        # Return one order at a time (bid first)
        return bid_order


class MarketMicrostructureModel:
    """
    Agent-based model of market microstructure.
    """

    def __init__(self, config: MarketMicrostructureConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or MarketMicrostructureConfig()
        np.random.seed(self.config.random_seed)
        self.book = OrderBook(tick_size=self.config.tick_size)
        self.agents: list[Agent] = []
        self.fundamental = self.config.initial_price
        self.price_history: list[float] = []
        self.spread_history: list[float] = []
        self.time = 0.0
        self._setup_agents()

    def _setup_agents(self) -> None:
        """Initialize trading agents."""
        cfg = self.config

        # Market makers
        for i in range(5):
            self.agents.append(MarketMaker(i, spread_target=0.03))

        # Informed traders
        for i in range(5, 5 + int(cfg.n_agents * cfg.informed_trader_prob)):
            self.agents.append(InformedTrader(i))

        # Noise traders
        for i in range(5 + int(cfg.n_agents * cfg.informed_trader_prob), cfg.n_agents):
            self.agents.append(NoiseTrader(i, cfg.noise_trader_volatility))

    def simulate(self) -> dict[str, Any]:
        """Run market simulation."""
        cfg = self.config

        # Initialize order book
        for i in range(5):  # Market makers place initial quotes
            order = self.agents[i].generate_order(self.book, self.fundamental, 0)
            if order:
                self.book.add_order(order)

        trades = []

        while self.time < cfg.simulation_time:
            # Update fundamental
            self.fundamental *= (1 + np.random.normal(0, cfg.fundamental_volatility))

            # Random agent acts
            agent = np.random.choice(self.agents)  # type: ignore[arg-type]
            order = agent.generate_order(self.book, self.fundamental, self.time)

            if order:
                new_trades = self.book.add_order(order)
                trades.extend(new_trades)

            # Record state
            mid = self.book.get_midprice()
            spread = self.book.get_spread()

            if mid:
                self.price_history.append(mid)
            if spread:
                self.spread_history.append(spread)

            # Advance time
            self.time += np.random.exponential(1.0 / cfg.arrival_rate)

        return self._analyze_results(trades)

    def _analyze_results(self, trades: list[dict]) -> dict[str, Any]:
        """Analyze simulation results."""
        prices = np.array(self.price_history)
        spreads = np.array(self.spread_history)

        # Price impact analysis
        price_impact = self._calculate_price_impact(trades)

        # Volatility
        returns = np.diff(np.log(prices)) if len(prices) > 1 else np.array([0])
        volatility = np.std(returns) * np.sqrt(252 * 24 * 3600) if len(returns) > 0 else 0

        # Order book statistics
        depth = self.book.get_depth(10)

        # Trade statistics
        trade_prices = [t['price'] for t in trades]
        trade_volumes = [t['quantity'] for t in trades]

        return {
            "price_statistics": {
                "mean": float(np.mean(prices)),
                "std": float(np.std(prices)),
                "min": float(np.min(prices)),
                "max": float(np.max(prices))
            },
            "spread_statistics": {
                "mean": float(np.mean(spreads)),
                "std": float(np.std(spreads)),
                "min": float(np.min(spreads)),
                "max": float(np.max(spreads))
            },
            "volatility": {
                "annualized": float(volatility),
                "returns_std": float(np.std(returns))
            },
            "trades": {
                "count": len(trades),
                "total_volume": int(np.sum(trade_volumes)),
                "avg_trade_size": float(np.mean(trade_volumes)) if trade_volumes else 0,
                "avg_price": float(np.mean(trade_prices)) if trade_prices else 0
            },
            "price_impact": price_impact,
            "order_book_depth": depth,
            "final_state": {
                "best_bid": self.book.get_best_bid(),
                "best_ask": self.book.get_best_ask(),
                "mid_price": self.book.get_midprice(),
                "spread": self.book.get_spread()
            },
            "price_history": prices[::max(1, len(prices)//100)].tolist(),
            "spread_history": spreads[::max(1, len(spreads)//100)].tolist()
        }

    def _calculate_price_impact(self, trades: list[dict]) -> dict[str, float]:
        """Calculate Kyle's lambda (price impact coefficient)."""
        if len(trades) < 10:
            return {"kyle_lambda": 0.0, "r_squared": 0.0}

        # Simplified price impact estimation
        # Delta P = lambda * Q + noise
        trade_sizes = np.array([t['quantity'] for t in trades[1:]])
        price_changes = np.array([trades[i]['price'] - trades[i-1]['price']
                                   for i in range(1, len(trades))])

        if len(trade_sizes) > 0 and np.sum(trade_sizes**2) > 0:
            lambda_kyle = np.sum(price_changes * trade_sizes) / np.sum(trade_sizes**2)
        else:
            lambda_kyle = 0

        return {
            "kyle_lambda": float(lambda_kyle),
            "avg_price_impact": float(np.mean(np.abs(price_changes)))
        }

    def run(self) -> dict[str, Any]:
        """Execute market microstructure simulation."""
        results = self.simulate()
        results["model_type"] = "market_microstructure"
        results["parameters"] = {
            "n_agents": self.config.n_agents,
            "arrival_rate": self.config.arrival_rate,
            "informed_trader_prob": self.config.informed_trader_prob
        }
        return results

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 57,
            "name": "Market Microstructure",
            "category": "Financial Markets",
            "description": "Agent-based order book dynamics and price formation",
            "author": "Kyle, Glosten, Milgrom",
            "year": 1985,
            "parameters": ["n_agents", "arrival_rate", "informed_trader_prob"],
            "outputs": ["price_impact", "spread", "volatility", "trades"],
            "applications": ["market_design", "liquidity_analysis", "trading_costs"]
        }


# Unit Tests
import unittest


class TestMarketMicrostructureModel(unittest.TestCase):

    """TestMarketMicrostructureModel."""
    def test_order_book_basic(self) -> None:
        """Test basic order book operations."""
        book = OrderBook(tick_size=0.01)

        # Add bid
        bid = Order(1, Side.BUY, OrderType.LIMIT, 100.0, 100, 0.0, 1)
        book.add_order(bid)

        self.assertEqual(book.get_best_bid(), 100.0)

        # Add ask
        ask = Order(2, Side.SELL, OrderType.LIMIT, 101.0, 100, 0.0, 2)
        book.add_order(ask)

        self.assertEqual(book.get_best_ask(), 101.0)
        self.assertEqual(book.get_spread(), 1.0)

    def test_market_order_execution(self) -> None:
        """Test market order execution."""
        book = OrderBook(tick_size=0.01)

        # Add resting limit orders
        ask = Order(1, Side.SELL, OrderType.LIMIT, 100.0, 100, 0.0, 1)
        book.add_order(ask)

        # Market buy
        market_buy = Order(2, Side.BUY, OrderType.MARKET, 0, 50, 1.0, 2)
        trades = book.add_order(market_buy)

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['quantity'], 50)
        self.assertEqual(trades[0]['price'], 100.0)

    def test_spread_formation(self) -> None:
        """Test that spread forms with market makers."""
        config = MarketMicrostructureConfig(
            n_agents=10,
            simulation_time=10.0,
            random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.run()

        self.assertIn("spread_statistics", result)
        self.assertGreater(result["spread_statistics"]["mean"], 0)

    def test_price_discovery(self) -> None:
        """Test that price tracks fundamental."""
        config = MarketMicrostructureConfig(
            n_agents=20,
            simulation_time=20.0,
            informed_trader_prob=0.3,
            random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.run()

        # Price should be within reasonable range of initial price
        mean_price = result["price_statistics"]["mean"]
        self.assertGreater(mean_price, 80)
        self.assertLess(mean_price, 120)

    def test_trade_generation(self) -> None:
        """Test that trades are generated."""
        config = MarketMicrostructureConfig(
            n_agents=50,
            simulation_time=50.0,
            arrival_rate=20.0,
            random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.run()

        self.assertGreater(result["trades"]["count"], 0)
        self.assertGreater(result["trades"]["total_volume"], 0)

    def test_price_impact(self) -> None:
        """Test price impact calculation."""
        config = MarketMicrostructureConfig(
            n_agents=30,
            simulation_time=30.0,
            random_seed=42
        )
        model = MarketMicrostructureModel(config)
        result = model.run()

        self.assertIn("price_impact", result)
        self.assertIn("kyle_lambda", result["price_impact"])


if __name__ == "__main__":
    # Run demonstration
    config = MarketMicrostructureConfig(
        n_agents=50,
        simulation_time=100.0,
        random_seed=42
    )
    model = MarketMicrostructureModel(config)
    result = model.run()

    print("=" * 60)
    print("MARKET MICROSTRUCTURE MODEL")
    print("=" * 60)
    print("\nPrice Statistics:")
    print(f"  Mean: {result['price_statistics']['mean']:.4f}")
    print(f"  Std: {result['price_statistics']['std']:.4f}")
    print("\nSpread Statistics:")
    print(f"  Mean: {result['spread_statistics']['mean']:.4f}")
    print(f"  Min: {result['spread_statistics']['min']:.4f}")
    print("\nTrading Activity:")
    print(f"  Number of Trades: {result['trades']['count']}")
    print(f"  Total Volume: {result['trades']['total_volume']}")
    print("\nPrice Impact:")
    print(f"  Kyle's Lambda: {result['price_impact']['kyle_lambda']:.8f}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
MarketMicrostructurePattern = MarketMicrostructureModel
