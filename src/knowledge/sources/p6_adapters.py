"""
c4reqber: P6 Source Adapters

Wraps BaseP6Client-based sources (NCBI, PubChem, ChEMBL, Materials Project,
Kaggle, AFLOW, UCI ML, Harvard Dataverse, re3data) into BaseSourceAdapter.
"""
from __future__ import annotations

import logging
from typing import Any

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class _P6Adapter(BaseSourceAdapter):
    """Generic adapter for a P6 client with a ``search_*`` method."""

    _client_cls: type
    _search_method: str
    _source_name: str
    _needs_key: bool = False
    _api_key_env: str = ""

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)
        kwargs: dict[str, Any] = {}
        if self._needs_key and api_key:
            kwargs["api_key"] = api_key
        self._client = self._client_cls(**kwargs)

    @property
    def source_id(self) -> str:
        return self._source_name

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            method = getattr(self._client, self._search_method)
            results = await method(query, limit=limit)
            for r in results:
                r["source"] = self._source_name
            return results
        except Exception as e:
            logger.warning("%s search error: %s", self._source_name, e)
            return []


class NcbiEutilsAdapter(_P6Adapter):
    """NCBI E-utilities — biomedical literature and data."""

    _source_name = "ncbi_eutils"
    _search_method = "search"
    _needs_key = True
    _api_key_env = "NCBI_API_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        from .ncbi_eutils import NCBIEUtilsClient
        self._client_cls = NCBIEUtilsClient
        super().__init__(api_key)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            results = await self._client.search("pubmed", query, retmax=limit)
            for r in results:
                r["source"] = self._source_name
            return results
        except Exception as e:
            logger.warning("%s search error: %s", self._source_name, e)
            return []


class PubchemAdapter(_P6Adapter):
    """PubChem — chemical structures and bioactivity."""

    _source_name = "pubchem"
    _search_method = "search_compound"

    def __init__(self, api_key: str | None = None) -> None:
        from .pubchem import PubChemClient
        self._client_cls = PubChemClient
        super().__init__(api_key)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            results = await self._client.search_compound(query)
            for r in results:
                r["source"] = self._source_name
            return results
        except Exception as e:
            logger.warning("%s search error: %s", self._source_name, e)
            return []


class ChemblAdapter(_P6Adapter):
    """ChEMBL — bioactive molecules and SAR data."""

    _source_name = "chembl"
    _search_method = "search_molecule"

    def __init__(self, api_key: str | None = None) -> None:
        from .chembl import ChEMBLClient
        self._client_cls = ChEMBLClient
        super().__init__(api_key)


class MaterialsProjectAdapter(_P6Adapter):
    """Materials Project — DFT-calculated materials."""

    _source_name = "materials_project"
    _search_method = "search_materials"
    _needs_key = True
    _api_key_env = "MATERIALS_PROJECT_API_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        from .materials_project import MaterialsProjectClient
        self._client_cls = MaterialsProjectClient
        super().__init__(api_key)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Skip text search — Materials Project only supports element-based search."""
        logger.debug("%s: text search not supported (use element search)", self._source_name)
        return []


class KaggleAdapter(_P6Adapter):
    """Kaggle — datasets and notebooks."""

    _source_name = "kaggle"
    _search_method = "search_datasets"
    _needs_key = True
    _api_key_env = "KAGGLE_USERNAME"

    def __init__(self, api_key: str | None = None) -> None:
        from .kaggle import KaggleClient
        self._client_cls = KaggleClient
        super().__init__(api_key)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            results = await self._client.search_datasets(query)
            for r in results:
                r["source"] = self._source_name
            return results
        except Exception as e:
            logger.warning("%s search error: %s", self._source_name, e)
            return []


class AflowAdapter(_P6Adapter):
    """AFLOW — computational materials data."""

    _source_name = "aflow"
    _search_method = "search_materials"

    def __init__(self, api_key: str | None = None) -> None:
        from .aflow import AflowClient
        self._client_cls = AflowClient
        super().__init__(api_key)


class UciMlAdapter(_P6Adapter):
    """UCI ML Repository — classic ML datasets."""

    _source_name = "uci_ml"
    _search_method = "search_datasets"

    def __init__(self, api_key: str | None = None) -> None:
        from .uci_ml import UciMlClient
        self._client_cls = UciMlClient
        super().__init__(api_key)


class HarvardDataverseAdapter(_P6Adapter):
    """Harvard Dataverse — research datasets."""

    _source_name = "harvard_dataverse"
    _search_method = "search_datasets"
    _needs_key = True
    _api_key_env = "HARVARD_DATAVERSE_API_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        from .harvard_dataverse import HarvardDataverseClient
        self._client_cls = HarvardDataverseClient
        super().__init__(api_key)


class Re3dataAdapter(_P6Adapter):
    """re3data — registry of research data repositories."""

    _source_name = "re3data"
    _search_method = "search_repositories"

    def __init__(self, api_key: str | None = None) -> None:
        from .re3data import Re3dataClient
        self._client_cls = Re3dataClient
        super().__init__(api_key)


# ─── NEW ADAPTERS (2026-05-31 batch) ─────────────────────────────────────────

class StringDbAdapter(_P6Adapter):
    """STRING DB — protein-protein interaction networks."""

    _source_name = "string_db"
    _search_method = "search_proteins"

    def __init__(self, api_key: str | None = None) -> None:
        from .string_db import StringDbClient
        self._client_cls = StringDbClient
        super().__init__(api_key)


class ClinicalTrialsAdapter(_P6Adapter):
    """ClinicalTrials.gov — clinical trial registry."""

    _source_name = "clinicaltrials"
    _search_method = "search_studies"

    def __init__(self, api_key: str | None = None) -> None:
        from .clinicaltrials import ClinicalTrialsClient
        self._client_cls = ClinicalTrialsClient
        super().__init__(api_key)


class GbifAdapter(_P6Adapter):
    """GBIF — Global Biodiversity Information Facility."""

    _source_name = "gbif"
    _search_method = "search_occurrences"

    def __init__(self, api_key: str | None = None) -> None:
        from .gbif import GbifClient
        self._client_cls = GbifClient
        super().__init__(api_key)


class AllenBrainAdapter(_P6Adapter):
    """Allen Brain Atlas — neuroanatomy and gene expression."""

    _source_name = "allen_brain"
    _search_method = "search_genes"

    def __init__(self, api_key: str | None = None) -> None:
        from .allen_brain import AllenBrainClient
        self._client_cls = AllenBrainClient
        super().__init__(api_key)


class UsgsAdapter(_P6Adapter):
    """USGS — earthquakes and geology."""

    _source_name = "usgs"
    _search_method = "search_earthquakes"

    def __init__(self, api_key: str | None = None) -> None:
        from .usgs import UsgsClient
        self._client_cls = UsgsClient
        super().__init__(api_key)


class OrcidAdapter(_P6Adapter):
    """ORCID — researcher profiles and works."""

    _source_name = "orcid"
    _search_method = "search_orcid"

    def __init__(self, api_key: str | None = None) -> None:
        from .orcid import OrcidClient
        self._client_cls = OrcidClient
        # OrcidClient reads credentials from env directly; pass no api_key
        super(_P6Adapter, self).__init__(api_key)
        self._client = self._client_cls()


class NoaaAdapter(_P6Adapter):
    """NOAA — climate and weather data."""

    _source_name = "noaa"
    _search_method = "search_stations"
    _needs_key = True
    _api_key_env = "NOAA_API_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        from .noaa import NOAAClient
        self._client_cls = NOAAClient
        super().__init__(api_key)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search weather stations by location query."""
        try:
            results = await self._client.search_stations(
                location=query, limit=limit
            )
            for r in results:
                r["source"] = self._source_name
            return results
        except Exception as e:
            logger.warning("%s search error: %s", self._source_name, e)
            return []


class CernOpenDataAdapter(_P6Adapter):
    """CERN Open Data — LHC experiment data."""

    _source_name = "cern_opendata"
    _search_method = "search_records"

    def __init__(self, api_key: str | None = None) -> None:
        from .cern_opendata import CernOpenDataClient
        self._client_cls = CernOpenDataClient
        super().__init__(api_key)


class OeisAdapter(_P6Adapter):
    """OEIS — integer sequences."""

    _source_name = "oeis"
    _search_method = "search_sequences"

    def __init__(self, api_key: str | None = None) -> None:
        from .oeis import OeisClient
        self._client_cls = OeisClient
        super().__init__(api_key)


class ConceptNetAdapter(_P6Adapter):
    """ConceptNet — semantic network."""

    _source_name = "conceptnet"
    _search_method = "search_concepts"

    def __init__(self, api_key: str | None = None) -> None:
        from .conceptnet import ConceptNetClient
        self._client_cls = ConceptNetClient
        super().__init__(api_key)


class UsptoPatentsviewAdapter(_P6Adapter):
    """USPTO PatentsView — US patents."""

    _source_name = "uspto_patentsview"
    _search_method = "search_patents"

    def __init__(self, api_key: str | None = None) -> None:
        from .uspto_patentsview import UsptoPatentsviewClient
        self._client_cls = UsptoPatentsviewClient
        super().__init__(api_key)


class HuggingFaceDatasetsAdapter(_P6Adapter):
    """HuggingFace Datasets Hub."""

    _source_name = "huggingface_datasets"
    _search_method = "search_datasets"

    def __init__(self, api_key: str | None = None) -> None:
        from .huggingface_datasets import HuggingFaceDatasetsClient
        self._client_cls = HuggingFaceDatasetsClient
        super().__init__(api_key)


class OpenReviewAdapter(_P6Adapter):
    """OpenReview — ML/AI conference papers."""

    _source_name = "openreview"
    _search_method = "search_notes"

    def __init__(self, api_key: str | None = None) -> None:
        from .openreview import OpenReviewClient
        self._client_cls = OpenReviewClient
        super().__init__(api_key)


class OpenFdaAdapter(_P6Adapter):
    """OpenFDA — adverse events and drug labels."""

    _source_name = "openfda"
    _search_method = "search_adverse_events"
    _needs_key = True
    _api_key_env = "OPENFDA_API_KEY"

    def __init__(self, api_key: str | None = None) -> None:
        from .openfda import OpenFdaClient
        self._client_cls = OpenFdaClient
        super().__init__(api_key)


class NasaEarthdataAdapter(_P6Adapter):
    """NASA Earthdata — satellite data via CMR."""

    _source_name = "nasa_earthdata"
    _search_method = "search_collections"
    _needs_key = True
    _api_key_env = "NASA_EARTHDATA_TOKEN"

    def __init__(self, api_key: str | None = None) -> None:
        from .nasa_earthdata import NasaEarthdataClient
        self._client_cls = NasaEarthdataClient
        super().__init__(api_key)


class CyberLeninkaAdapter(_P6Adapter):
    """CyberLeninka — Russian open-access journals."""

    _source_name = "cyberleninka"
    _search_method = "search_articles"

    def __init__(self, api_key: str | None = None) -> None:
        from .cyberleninka import CyberLeninkaClient
        self._client_cls = CyberLeninkaClient
        super().__init__(api_key)


class MathNetRuAdapter(_P6Adapter):
    """Math-Net.Ru — Russian mathematical portal."""

    _source_name = "mathnet_ru"
    _search_method = "search_articles"

    def __init__(self, api_key: str | None = None) -> None:
        from .mathnet_ru import MathNetRuClient
        self._client_cls = MathNetRuClient
        super().__init__(api_key)
