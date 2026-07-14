from __future__ import annotations

import asyncio

from src.pipeline.provider_coordinator import ProviderSlot
from src.pipeline.smart_scheduler import SchedulerConfig, SmartScheduler


class TestSchedulerConfig:
    def test_defaults(self):
        cfg = SchedulerConfig()
        assert cfg.max_concurrent == 2
        assert cfg.min_call_interval == 3.0
        assert cfg.max_retries == 3
        assert cfg.backoff_base == 2.0
        assert cfg.rate_limit_window == 60
        assert cfg.max_calls_per_window == 20


class TestSmartScheduler:
    def test_initializes(self):
        sched = SmartScheduler()
        assert sched._active == 0
        assert sched._completed == 0
        assert sched._total == 0
        assert sched.cfg.max_concurrent == 2

    def test_initializes_with_custom_config(self):
        cfg = SchedulerConfig(max_concurrent=5, min_call_interval=1.0)
        sched = SmartScheduler(config=cfg)
        assert sched.cfg.max_concurrent == 5
        assert sched.cfg.min_call_interval == 1.0

    def test_schedule_empty(self):
        async def run():
            sched = SmartScheduler()
            results = await sched.schedule([])
            assert results == []
            assert sched._completed == 0

        asyncio.run(run())

    def test_schedule_single_task(self):
        async def run():
            sched = SmartScheduler()
            async def task():
                return 42

            results = await sched.schedule([task])
            assert len(results) == 1
            assert results[0] == 42
            assert sched._completed == 1

        asyncio.run(run())

    def test_schedule_multiple_tasks(self):
        async def run():
            sched = SmartScheduler(SchedulerConfig(max_concurrent=10, min_call_interval=0.0))

            def make_task(n):
                async def _inner():
                    return n * 10
                return _inner

            tasks = [make_task(i) for i in range(5)]
            results = await sched.schedule(tasks)

            assert sorted(results) == [0, 10, 20, 30, 40]
            assert sched._completed == 5

        asyncio.run(run())

    def test_schedule_with_progress(self):
        progress_calls = []

        async def run():
            sched = SmartScheduler(SchedulerConfig(max_concurrent=10, min_call_interval=0.0))

            async def task():
                return "done"

            def on_progress(completed, total, msg):
                progress_calls.append((completed, total, msg))

            await sched.schedule([task, task], on_progress=on_progress)
            assert len(progress_calls) >= 4  # start + done for each

        asyncio.run(run())


class TestProviderSlot:
    def test_can_accept_returns_bool(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=8,
            cost_per_1k=0.0,
        )
        assert isinstance(slot.can_accept(), bool)

    def test_can_accept_when_available(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=8,
            cost_per_1k=0.0,
        )
        assert slot.can_accept() is True

    def test_cannot_accept_when_unavailable(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=8,
            cost_per_1k=0.0,
            available=False,
        )
        assert slot.can_accept() is False

    def test_cannot_accept_when_active_limit_reached(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=1,
            cost_per_1k=0.0,
            active_pipelines=1,
        )
        assert slot.can_accept() is False

    def test_acquire_and_release(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=2,
            cost_per_1k=0.0,
        )
        assert slot.active_pipelines == 0
        slot.acquire()
        assert slot.active_pipelines == 1
        slot.acquire()
        assert slot.active_pipelines == 2
        slot.release()
        assert slot.active_pipelines == 1
        slot.release()
        assert slot.active_pipelines == 0
        slot.release()
        assert slot.active_pipelines == 0

    def test_load_pct(self):
        slot = ProviderSlot(
            name="test",
            url="http://localhost:8080",
            api_key="",
            tier="local",
            rate_limit_per_min=999,
            concurrent_limit=4,
            cost_per_1k=0.0,
        )
        assert slot.load_pct == 0.0
        slot.active_pipelines = 2
        assert slot.load_pct == 0.5
