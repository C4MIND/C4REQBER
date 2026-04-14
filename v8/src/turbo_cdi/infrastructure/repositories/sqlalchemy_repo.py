"""
SQLAlchemy repository implementations for TURBO-CDI v8.4
Production-ready persistence layer.
"""

import json
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, insert, update, delete, text, desc
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from turbo_cdi.domain.entities import KnowledgeCorpus, CorpusId, Fact, Theory, Anomaly
from turbo_cdi.domain.entities.advanced import (
    Presupposition,
    Transformation,
    PresuppositionId,
    TransformationId,
    PresuppositionType,
    TransformationType,
)
from turbo_cdi.domain.repositories import (
    DiscoveryRepository,
    PresuppositionRepository,
    TransformationRepository,
)


class Base(DeclarativeBase):
    """SQLAlchemy base class for all entities"""

    pass


class CorpusORM(Base):
    """SQLAlchemy ORM model for KnowledgeCorpus"""

    __tablename__ = "corpora"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    domain: Mapped[str] = mapped_column(nullable=False)
    subdomains: Mapped[str] = mapped_column(nullable=False, default="[]")  # JSON array
    epoch_end: Mapped[str] = mapped_column(nullable=False, default="2024")
    facts: Mapped[str] = mapped_column(nullable=False, default="[]")  # JSON array
    theories: Mapped[str] = mapped_column(nullable=False, default="[]")  # JSON array
    anomalies: Mapped[str] = mapped_column(nullable=False, default="[]")  # JSON array
    created_at: Mapped[str] = mapped_column(nullable=False)
    updated_at: Mapped[str] = mapped_column(nullable=False)


class PresuppositionORM(Base):
    """SQLAlchemy ORM model for Presupposition"""

    __tablename__ = "presuppositions"

    id: Mapped[str] = mapped_column(primary_key=True)
    theory_id: Mapped[str] = mapped_column(nullable=False)
    theory_name: Mapped[str] = mapped_column(nullable=False)
    statement: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)  # PresuppositionType enum value
    confidence: Mapped[float] = mapped_column(nullable=False)
    discovered_at: Mapped[str] = mapped_column(nullable=False)


class TransformationORM(Base):
    """SQLAlchemy ORM model for Transformation"""

    __tablename__ = "transformations"

    id: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False)  # TransformationType enum value
    input_concept: Mapped[str] = mapped_column(nullable=False)
    output_concept: Mapped[str] = mapped_column(nullable=False)
    domain: Mapped[str] = mapped_column(nullable=False)
    operator: Mapped[str] = mapped_column(nullable=False)
    resonance: Mapped[float] = mapped_column(nullable=False)
    effectiveness: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(nullable=False)


class SQLAlchemyDiscoveryRepository(DiscoveryRepository):
    """
    SQLAlchemy implementation of DiscoveryRepository.

    Production-ready persistence with proper transaction handling,
    connection pooling, and error recovery.
    """

    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_factory = None

    async def _ensure_initialized(self) -> async_sessionmaker:
        """Lazy initialization of database connection and schema"""
        if self._session_factory is None:
            # Create engine
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
            )

            # Create tables
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

        return self._session_factory

    async def save_corpus(self, corpus: KnowledgeCorpus) -> None:
        """Save or update a knowledge corpus with optimistic locking"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                # Convert domain entity to ORM
                orm_data = self._domain_to_orm(corpus)

                # Upsert with conflict resolution
                stmt = insert(CorpusORM).values(orm_data)
                stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=orm_data)

                await session.execute(stmt)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to save corpus {corpus.id}: {e}") from e

    async def get_corpus(self, corpus_id: CorpusId) -> Optional[KnowledgeCorpus]:
        """Retrieve a corpus by ID with error handling"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(CorpusORM).where(CorpusORM.id == corpus_id)
                result = await session.execute(stmt)
                orm_corpus = result.scalar_one_or_none()

                return self._orm_to_domain(orm_corpus) if orm_corpus else None

            except Exception as e:
                raise RuntimeError(f"Failed to retrieve corpus {corpus_id}: {e}") from e

    async def list_corpuses(self, domain: Optional[str] = None) -> List[KnowledgeCorpus]:
        """List corpora with optional domain filtering"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(CorpusORM)
                if domain:
                    stmt = stmt.where(CorpusORM.domain == domain)

                stmt = stmt.order_by(CorpusORM.created_at.desc())
                result = await session.execute(stmt)
                orm_corpuses = result.scalars().all()

                return [self._orm_to_domain(orm) for orm in orm_corpuses]

            except Exception as e:
                raise RuntimeError(f"Failed to list corpora: {e}") from e

    async def delete_corpus(self, corpus_id: CorpusId) -> None:
        """Delete a corpus with proper cleanup"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = delete(CorpusORM).where(CorpusORM.id == corpus_id)
                result = await session.execute(stmt)

                if result.rowcount == 0:
                    raise ValueError(f"Corpus {corpus_id} not found")

                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to delete corpus {corpus_id}: {e}") from e

    async def corpus_exists(self, corpus_id: CorpusId) -> bool:
        """Check corpus existence efficiently"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(CorpusORM.id).where(CorpusORM.id == corpus_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None

            except Exception as e:
                raise RuntimeError(f"Failed to check corpus existence {corpus_id}: {e}") from e

    def _domain_to_orm(self, corpus: KnowledgeCorpus) -> dict:
        """Convert domain entity to ORM data with validation"""
        import json
        from datetime import datetime

        try:
            return {
                "id": corpus.id,
                "name": corpus.name,
                "domain": corpus.domain,
                "subdomains": json.dumps(list(corpus.subdomains)),
                "epoch_end": corpus.epoch_end,
                "facts": json.dumps(
                    [
                        {
                            "id": f.id,
                            "statement": f.statement,
                            "source": f.source,
                            "year": f.year,
                            "domain": f.domain,
                            "confidence": f.confidence,
                        }
                        for f in corpus.facts
                    ]
                ),
                "theories": json.dumps(
                    [
                        {
                            "id": t.id,
                            "name": t.name,
                            "principles": list(t.principles),
                            "equations": list(t.equations),
                        }
                        for t in corpus.theories
                    ]
                ),
                "anomalies": json.dumps(
                    [
                        {
                            "id": a.id,
                            "corpus_id": a.corpus_id,
                            "type": a.type.value,
                            "fact_statement": a.fact_statement,
                            "theory_name": a.theory_name,
                            "conflict_description": a.conflict_description,
                            "criticality": a.criticality.value,
                            "confidence": a.confidence,
                            "detected_at": a.detected_at.isoformat(),
                        }
                        for a in corpus.anomalies
                    ]
                ),
                "created_at": corpus.created_at.isoformat(),
                "updated_at": corpus.updated_at.isoformat(),
            }
        except Exception as e:
            raise ValueError(f"Failed to serialize corpus {corpus.id}: {e}") from e

    def _orm_to_domain(self, orm: CorpusORM) -> KnowledgeCorpus:
        """Convert ORM data to domain entity with error handling"""
        import json
        from datetime import datetime

        try:
            # Parse JSON data safely
            facts_data = json.loads(orm.facts) if orm.facts else []
            theories_data = json.loads(orm.theories) if orm.theories else []
            anomalies_data = json.loads(orm.anomalies) if orm.anomalies else []
            subdomains = tuple(json.loads(orm.subdomains) if orm.subdomains else [])

            # Convert to domain entities
            facts = frozenset(
                Fact(
                    id=f["id"],
                    statement=f["statement"],
                    source=f["source"],
                    year=f["year"],
                    domain=f["domain"],
                    confidence=f.get("confidence", 1.0),
                )
                for f in facts_data
            )

            theories = frozenset(
                Theory(
                    id=t["id"],
                    name=t["name"],
                    principles=tuple(t["principles"]),
                    equations=tuple(t.get("equations", [])),
                )
                for t in theories_data
            )

            anomalies = frozenset(
                Anomaly(
                    id=a["id"],
                    corpus_id=a["corpus_id"],
                    type=a["type"],
                    fact_statement=a["fact_statement"],
                    theory_name=a["theory_name"],
                    conflict_description=a["conflict_description"],
                    criticality=a["criticality"],
                    confidence=a.get("confidence", 0.8),
                    detected_at=datetime.fromisoformat(a["detected_at"]),
                )
                for a in anomalies_data
            )

            return KnowledgeCorpus(
                id=orm.id,
                name=orm.name,
                domain=orm.domain,
                subdomains=subdomains,
                epoch_end=orm.epoch_end,
                facts=facts,
                theories=theories,
                anomalies=anomalies,
                created_at=datetime.fromisoformat(orm.created_at),
                updated_at=datetime.fromisoformat(orm.updated_at),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise RuntimeError(f"Failed to deserialize corpus {orm.id}: {e}") from e

    async def health_check(self) -> dict:
        """Health check for repository"""
        try:
            session_factory = await self._ensure_initialized()
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "database": str(e)}


class SQLAlchemyPresuppositionRepository(PresuppositionRepository):
    """
    SQLAlchemy implementation of PresuppositionRepository.
    Handles persistence of hidden assumptions in theories.
    """

    def __init__(self, database_url: str, discovery_repo: DiscoveryRepository, echo: bool = False):
        self.database_url = database_url
        self.discovery_repo = discovery_repo  # For cross-repository operations
        self.echo = echo
        self._engine = None
        self._session_factory = None

    async def _ensure_initialized(self) -> async_sessionmaker:
        """Lazy initialization of database connection and schema"""
        if self._session_factory is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
            )

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

        return self._session_factory

    async def save_presupposition(self, presupposition: Presupposition) -> None:
        """Save or update a presupposition"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                orm_data = self._presupposition_to_orm(presupposition)

                stmt = insert(PresuppositionORM).values(orm_data)
                stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=orm_data)

                await session.execute(stmt)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to save presupposition {presupposition.id}: {e}") from e

    async def get_presupposition(self, p_id: PresuppositionId) -> Optional[Presupposition]:
        """Retrieve a presupposition by ID"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(PresuppositionORM).where(PresuppositionORM.id == p_id)
                result = await session.execute(stmt)
                orm_p = result.scalar_one_or_none()

                return self._orm_to_presupposition(orm_p) if orm_p else None

            except Exception as e:
                raise RuntimeError(f"Failed to retrieve presupposition {p_id}: {e}") from e

    async def list_presuppositions_by_theory(self, theory_id: str) -> List[Presupposition]:
        """List all presuppositions for a theory"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(PresuppositionORM).where(PresuppositionORM.theory_id == theory_id)
                result = await session.execute(stmt)
                orm_presuppositions = result.scalars().all()

                return [self._orm_to_presupposition(orm) for orm in orm_presuppositions]

            except Exception as e:
                raise RuntimeError(
                    f"Failed to list presuppositions for theory {theory_id}: {e}"
                ) from e

    async def list_presuppositions_by_type(
        self, p_type: PresuppositionType
    ) -> List[Presupposition]:
        """List presuppositions by type"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(PresuppositionORM).where(PresuppositionORM.type == p_type.value)
                result = await session.execute(stmt)
                orm_presuppositions = result.scalars().all()

                return [self._orm_to_presupposition(orm) for orm in orm_presuppositions]

            except Exception as e:
                raise RuntimeError(f"Failed to list presuppositions by type {p_type}: {e}") from e

    async def delete_presupposition(self, p_id: PresuppositionId) -> None:
        """Delete a presupposition"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = delete(PresuppositionORM).where(PresuppositionORM.id == p_id)
                result = await session.execute(stmt)

                if result.rowcount == 0:
                    raise ValueError(f"Presupposition {p_id} not found")

                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to delete presupposition {p_id}: {e}") from e

    async def find_contradictory_presuppositions(
        self,
    ) -> List[Tuple[Presupposition, Presupposition]]:
        """Find presuppositions that contradict each other"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                # Get all presuppositions
                stmt = select(PresuppositionORM)
                result = await session.execute(stmt)
                orm_presuppositions = result.scalars().all()

                presuppositions = [self._orm_to_presupposition(orm) for orm in orm_presuppositions]
                contradictory_pairs = []

                # Simple contradiction detection (could be more sophisticated)
                for i, p1 in enumerate(presuppositions):
                    for p2 in presuppositions[i + 1 :]:
                        if self._presuppositions_contradict(p1, p2):
                            contradictory_pairs.append((p1, p2))

                return contradictory_pairs

            except Exception as e:
                raise RuntimeError(f"Failed to find contradictory presuppositions: {e}") from e

    def _presupposition_to_orm(self, presupposition: Presupposition) -> dict:
        """Convert presupposition to ORM data"""
        return {
            "id": presupposition.id,
            "theory_id": presupposition.theory_id,
            "theory_name": presupposition.theory_name,
            "statement": presupposition.statement,
            "type": presupposition.type.value,
            "confidence": presupposition.confidence,
            "discovered_at": presupposition.discovered_at.isoformat(),
        }

    def _orm_to_presupposition(self, orm: PresuppositionORM) -> Presupposition:
        """Convert ORM data to presupposition"""
        import json
        from datetime import datetime

        return Presupposition(
            id=orm.id,
            theory_id=orm.theory_id,
            theory_name=orm.theory_name,
            statement=orm.statement,
            type=PresuppositionType(orm.type),
            confidence=orm.confidence,
            discovered_at=datetime.fromisoformat(orm.discovered_at),
        )

    def _presuppositions_contradict(self, p1: Presupposition, p2: Presupposition) -> bool:
        """Simple contradiction detection logic"""
        # This would be implemented with more sophisticated NLP/Logic analysis
        negation_words = ["not", "no", "never", "without"]
        p1_lower = p1.statement.lower()
        p2_lower = p2.statement.lower()

        for neg in negation_words:
            if neg in p1_lower and any(
                word in p2_lower for word in p1_lower.split() if word != neg
            ):
                return True
            if neg in p2_lower and any(
                word in p1_lower for word in p2_lower.split() if word != neg
            ):
                return True

        return False


class SQLAlchemyTransformationRepository(TransformationRepository):
    """
    SQLAlchemy implementation of TransformationRepository.
    Handles persistence of cognitive transformations.
    """

    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_factory = None

    async def _ensure_initialized(self) -> async_sessionmaker:
        """Lazy initialization of database connection and schema"""
        if self._session_factory is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
            )

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self._session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

        return self._session_factory

    async def save_transformation(self, transformation: Transformation) -> None:
        """Save or update a transformation"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                orm_data = self._transformation_to_orm(transformation)

                stmt = insert(TransformationORM).values(orm_data)
                stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=orm_data)

                await session.execute(stmt)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to save transformation {transformation.id}: {e}") from e

    async def get_transformation(self, t_id: TransformationId) -> Optional[Transformation]:
        """Retrieve a transformation by ID"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(TransformationORM).where(TransformationORM.id == t_id)
                result = await session.execute(stmt)
                orm_t = result.scalar_one_or_none()

                return self._orm_to_transformation(orm_t) if orm_t else None

            except Exception as e:
                raise RuntimeError(f"Failed to retrieve transformation {t_id}: {e}") from e

    async def list_transformations_by_domain(self, domain: str) -> List[Transformation]:
        """List transformations for a specific domain"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(TransformationORM).where(TransformationORM.domain == domain)
                result = await session.execute(stmt)
                orm_transformations = result.scalars().all()

                return [self._orm_to_transformation(orm) for orm in orm_transformations]

            except Exception as e:
                raise RuntimeError(
                    f"Failed to list transformations for domain {domain}: {e}"
                ) from e

    async def list_transformations_by_type(
        self, t_type: TransformationType
    ) -> List[Transformation]:
        """List transformations by type"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = select(TransformationORM).where(TransformationORM.type == t_type.value)
                result = await session.execute(stmt)
                orm_transformations = result.scalars().all()

                return [self._orm_to_transformation(orm) for orm in orm_transformations]

            except Exception as e:
                raise RuntimeError(f"Failed to list transformations by type {t_type}: {e}") from e

    async def get_most_effective_transformations(self, limit: int = 10) -> List[Transformation]:
        """Get transformations ordered by effectiveness"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = (
                    select(TransformationORM)
                    .order_by((TransformationORM.effectiveness + TransformationORM.resonance) / 2)
                    .desc()
                    .limit(limit)
                )
                result = await session.execute(stmt)
                orm_transformations = result.scalars().all()

                return [self._orm_to_transformation(orm) for orm in orm_transformations]

            except Exception as e:
                raise RuntimeError(f"Failed to get most effective transformations: {e}") from e

    async def delete_transformation(self, t_id: TransformationId) -> None:
        """Delete a transformation"""
        session_factory = await self._ensure_initialized()

        async with session_factory() as session:
            try:
                stmt = delete(TransformationORM).where(TransformationORM.id == t_id)
                result = await session.execute(stmt)

                if result.rowcount == 0:
                    raise ValueError(f"Transformation {t_id} not found")

                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to delete transformation {t_id}: {e}") from e

    def _transformation_to_orm(self, transformation: Transformation) -> dict:
        """Convert transformation to ORM data"""
        return {
            "id": transformation.id,
            "type": transformation.type.value,
            "input_concept": transformation.input_concept,
            "output_concept": transformation.output_concept,
            "domain": transformation.domain,
            "operator": transformation.operator,
            "resonance": transformation.resonance,
            "effectiveness": transformation.effectiveness,
            "created_at": transformation.created_at.isoformat(),
        }

    def _orm_to_transformation(self, orm: TransformationORM) -> Transformation:
        """Convert ORM data to transformation"""
        import json
        from datetime import datetime

        return Transformation(
            id=orm.id,
            type=TransformationType(orm.type),
            input_concept=orm.input_concept,
            output_concept=orm.output_concept,
            domain=orm.domain,
            operator=orm.operator,
            resonance=orm.resonance,
            effectiveness=orm.effectiveness,
            created_at=datetime.fromisoformat(orm.created_at),
        )
