"""
Transaction Management for TURBO-CDI v8.4 Application Layer
Ensures data consistency across operations and proper rollback on failure.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

from turbo_cdi.domain.entities import CorpusId


# Transaction Context
@dataclass
class TransactionContext:
    """Context information for a transaction"""

    transaction_id: str
    start_time: float
    operations: List[Dict[str, Any]]
    isolation_level: str = "serializable"  # "read_committed", "repeatable_read", "serializable"
    timeout: int = 300  # seconds
    user: Optional[str] = None


# Transaction Result
@dataclass
class TransactionResult:
    """Result of a transaction execution"""

    success: bool
    transaction_id: str
    duration: float
    operations_completed: int
    operations_failed: int
    errors: List[str]
    rollback_performed: bool


# Transaction Manager Interface
class TransactionManager(ABC):
    """Abstract base for transaction managers"""

    @abstractmethod
    async def begin_transaction(
        self, isolation_level: str = "serializable", timeout: int = 300, user: Optional[str] = None
    ) -> TransactionContext:
        """Begin a new transaction"""
        pass

    @abstractmethod
    async def commit_transaction(self, context: TransactionContext) -> None:
        """Commit a transaction"""
        pass

    @abstractmethod
    async def rollback_transaction(self, context: TransactionContext) -> None:
        """Rollback a transaction"""
        pass

    @abstractmethod
    async def execute_in_transaction(
        self, operations: List[callable], isolation_level: str = "serializable"
    ) -> TransactionResult:
        """Execute multiple operations in a transaction"""
        pass


# Database Transaction Manager
class DatabaseTransactionManager(TransactionManager):
    """
    Transaction manager that coordinates database operations.
    Handles multi-repository transactions with proper rollback.
    """

    def __init__(self, repositories: Dict[str, Any]):
        self.repositories = repositories
        self.logger = logging.getLogger("transaction_manager")
        self.active_transactions: Dict[str, TransactionContext] = {}

    async def begin_transaction(
        self, isolation_level: str = "serializable", timeout: int = 300, user: Optional[str] = None
    ) -> TransactionContext:
        """Begin a new database transaction"""
        transaction_id = f"tx_{int(asyncio.get_event_loop().time() * 1000000)}"

        context = TransactionContext(
            transaction_id=transaction_id,
            start_time=asyncio.get_event_loop().time(),
            operations=[],
            isolation_level=isolation_level,
            timeout=timeout,
            user=user,
        )

        self.active_transactions[transaction_id] = context

        # Set transaction isolation level on repositories
        for repo_name, repo in self.repositories.items():
            if hasattr(repo, "set_transaction_isolation"):
                await repo.set_transaction_isolation(isolation_level)

        self.logger.info(f"Began transaction {transaction_id} (isolation: {isolation_level})")
        return context

    async def commit_transaction(self, context: TransactionContext) -> None:
        """Commit a database transaction"""
        try:
            # Commit on all repositories
            for repo_name, repo in self.repositories.items():
                if hasattr(repo, "commit_transaction"):
                    await repo.commit_transaction(context.transaction_id)

            duration = asyncio.get_event_loop().time() - context.start_time
            self.logger.info(
                f"Committed transaction {context.transaction_id} "
                f"({len(context.operations)} operations in {duration:.3f}s)"
            )

        except Exception as e:
            self.logger.error(f"Failed to commit transaction {context.transaction_id}: {e}")
            raise

        finally:
            self.active_transactions.pop(context.transaction_id, None)

    async def rollback_transaction(self, context: TransactionContext) -> None:
        """Rollback a database transaction"""
        try:
            # Rollback on all repositories
            for repo_name, repo in self.repositories.items():
                if hasattr(repo, "rollback_transaction"):
                    await repo.rollback_transaction(context.transaction_id)

            duration = asyncio.get_event_loop().time() - context.start_time
            failed_ops = sum(1 for op in context.operations if op.get("status") == "failed")

            self.logger.warning(
                f"Rolled back transaction {context.transaction_id} "
                f"({len(context.operations)} operations, {failed_ops} failed in {duration:.3f}s)"
            )

        except Exception as e:
            self.logger.error(f"Failed to rollback transaction {context.transaction_id}: {e}")
            raise

        finally:
            self.active_transactions.pop(context.transaction_id, None)

    async def execute_in_transaction(
        self, operations: List[callable], isolation_level: str = "serializable"
    ) -> TransactionResult:
        """
        Execute multiple operations in a single transaction
        Automatically handles rollback on failure
        """
        context = await self.begin_transaction(isolation_level)
        result = TransactionResult(
            success=True,
            transaction_id=context.transaction_id,
            duration=0.0,
            operations_completed=0,
            operations_failed=0,
            errors=[],
            rollback_performed=False,
        )

        try:
            for i, operation in enumerate(operations):
                try:
                    await operation()
                    context.operations.append(
                        {
                            "index": i,
                            "status": "completed",
                            "operation": operation.__name__
                            if hasattr(operation, "__name__")
                            else str(operation),
                        }
                    )
                    result.operations_completed += 1

                except Exception as e:
                    context.operations.append(
                        {
                            "index": i,
                            "status": "failed",
                            "error": str(e),
                            "operation": operation.__name__
                            if hasattr(operation, "__name__")
                            else str(operation),
                        }
                    )
                    result.operations_failed += 1
                    result.errors.append(f"Operation {i} failed: {str(e)}")
                    result.success = False

            if result.success:
                await self.commit_transaction(context)
            else:
                await self.rollback_transaction(context)
                result.rollback_performed = True

        except Exception as e:
            result.success = False
            result.errors.append(f"Transaction execution failed: {str(e)}")
            await self.rollback_transaction(context)
            result.rollback_performed = True

        finally:
            result.duration = asyncio.get_event_loop().time() - context.start_time

        return result


# Transaction Scope Context Manager
@asynccontextmanager
async def transaction_scope(
    transaction_manager: TransactionManager, isolation_level: str = "serializable"
):
    """
    Context manager for handling transactions with automatic rollback.
    Usage:
        async with transaction_scope(tx_manager):
            await some_operation()
            await another_operation()
    """
    context = await transaction_manager.begin_transaction(isolation_level)

    try:
        yield context
        await transaction_manager.commit_transaction(context)
    except Exception as e:
        await transaction_manager.rollback_transaction(context)
        raise e


# Saga Pattern for Long-Running Transactions
class SagaCoordinator:
    """
    Coordinator for saga pattern - useful for long-running, multi-step operations
    that span multiple services and might need compensation.
    """

    def __init__(self, name: str):
        self.name = name
        self.steps: List[SagaStep] = []
        self.logger = logging.getLogger(f"saga_{name}")

    def add_step(
        self, action: callable, compensation: Optional[callable] = None, name: Optional[str] = None
    ) -> None:
        """Add a step to the saga"""
        step = SagaStep(
            action=action, compensation=compensation, name=name or f"step_{len(self.steps)}"
        )
        self.steps.append(step)

    async def execute(self) -> SagaResult:
        """Execute the entire saga"""
        executed_steps: List[SagaStep] = []
        start_time = asyncio.get_event_loop().time()

        for step in self.steps:
            try:
                self.logger.info(f"Executing saga step: {step.name}")
                await step.action()
                executed_steps.append(step)

            except Exception as e:
                self.logger.error(f"Saga step {step.name} failed: {e}")

                # Compensate executed steps in reverse order
                await self._compensate_steps(reversed(executed_steps))

                return SagaResult(
                    success=False,
                    steps_completed=len(executed_steps),
                    compensation_performed=True,
                    error=str(e),
                    duration=asyncio.get_event_loop().time() - start_time,
                )

        return SagaResult(
            success=True,
            steps_completed=len(self.steps),
            compensation_performed=False,
            duration=asyncio.get_event_loop().time() - start_time,
        )

    async def _compensate_steps(self, steps: List[SagaStep]) -> None:
        """Execute compensation actions for steps"""
        for step in steps:
            if step.compensation:
                try:
                    self.logger.info(f"Compensating saga step: {step.name}")
                    await step.compensation()
                except Exception as e:
                    self.logger.error(f"Compensation failed for {step.name}: {e}")


@dataclass
class SagaStep:
    """A step in a saga"""

    action: callable  # The action to execute
    compensation: Optional[callable] = None  # Action to undo the step
    name: str = ""  # Step name for logging


@dataclass
class SagaResult:
    """Result of saga execution"""

    success: bool
    steps_completed: int
    compensation_performed: bool
    error: Optional[str] = None
    duration: float = 0.0


# Transaction Monitoring
class TransactionMonitor:
    """Monitor and report on transaction performance and health"""

    def __init__(self):
        self.metrics = {
            "transactions_started": 0,
            "transactions_committed": 0,
            "transactions_rolled_back": 0,
            "average_duration": 0.0,
            "long_running_transactions": 0,
        }
        self.logger = logging.getLogger("transaction_monitor")

    async def record_transaction_start(self, context: TransactionContext) -> None:
        """Record that a transaction started"""
        self.metrics["transactions_started"] += 1

    async def record_transaction_commit(self, context: TransactionContext) -> None:
        """Record that a transaction committed"""
        self.metrics["transactions_committed"] += 1
        self._update_average_duration(context)

        if context.start_time and asyncio.get_event_loop().time() - context.start_time > 60:
            self.metrics["long_running_transactions"] += 1

    async def record_transaction_rollback(self, context: TransactionContext) -> None:
        """Record that a transaction rolled back"""
        self.metrics["transactions_rolled_back"] += 1
        self.logger.warning(f"Transaction rolled back: {context.transaction_id}")

    def get_health_report(self) -> Dict[str, Any]:
        """Get a health report on transactions"""
        if self.metrics["transactions_started"] == 0:
            return {"status": "no_activity"}

        rollback_rate = (
            self.metrics["transactions_rolled_back"] / self.metrics["transactions_started"]
        )

        status = "healthy"
        if rollback_rate > 0.1:  # More than 10% rollbacks
            status = "warning"
        if rollback_rate > 0.25:  # More than 25% rollbacks
            status = "unhealthy"

        return {
            "status": status,
            "transactions_started": self.metrics["transactions_started"],
            "rollback_rate": rollback_rate,
            "average_duration": self.metrics["average_duration"],
            "long_running_count": self.metrics["long_running_transactions"],
        }

    def _update_average_duration(self, context: TransactionContext) -> None:
        """Update the average transaction duration"""
        if not context.start_time:
            return

        duration = asyncio.get_event_loop().time() - context.start_time

        # Running average calculation
        n = self.metrics["transactions_committed"]
        current_avg = self.metrics["average_duration"]
        self.metrics["average_duration"] = (current_avg * (n - 1) + duration) / n


# Global Transaction Monitor
transaction_monitor = TransactionMonitor()
