"""Knowledge source adapters — lazily imported to avoid breaking on missing modules."""
from __future__ import annotations


class BaseSearchAdapter:
    """Base class for all search adapters."""
    pass


class CoreAdapter(BaseSearchAdapter):
    """Core search adapter."""
    pass


def _safe_import(module_name: str, class_name: str):
    try:
        import importlib
        mod = importlib.import_module(f"src.knowledge.sources.{module_name}")
        return getattr(mod, class_name)
    except (ImportError, AttributeError):
        return None


# All adapters — some are stub files, handled by _safe_import returning None
ArxivAdapter = _safe_import("arxiv", "ArxivAdapter")
from .bibsonomy import BibsonomyAdapter


BraveAdapter = _safe_import("brave", "BraveAdapter")
CoreSearchAdapter = _safe_import("core", "CoreSearchAdapter") or CoreAdapter
CrossrefAdapter = _safe_import("crossref", "CrossrefAdapter")
DataciteAdapter = _safe_import("datacite", "DataciteAdapter")
DoajAdapter = _safe_import("doaj", "DoajAdapter")
DblpAdapter = _safe_import("dblp", "DblpAdapter")
EuropePmcAdapter = _safe_import("europe_pmc", "EuropePmcAdapter")
FigshareAdapter = _safe_import("figshare", "FigshareAdapter")
InspireHepAdapter = _safe_import("inspire_hep", "InspireHepAdapter")
LensOrgAdapter = _safe_import("lens_org", "LensOrgAdapter")
OaMgAdapter = _safe_import("oa_mg", "OaMgAdapter")
OpenAlexAdapter = _safe_import("openalex", "OpenAlexAdapter")
PubmedAdapter = _safe_import("pubmed", "PubmedAdapter")
ScimaticAdapter = _safe_import("scimatic", "ScimaticAdapter")
SemanticScholarAdapter = _safe_import("semantic_scholar", "SemanticScholarAdapter")
TavilyAdapter = _safe_import("tavily", "TavilyAdapter")
UnpaywallAdapter = _safe_import("unpaywall", "UnpaywallAdapter")
WikidataAdapter = _safe_import("wikidata", "WikidataAdapter")
ZenodoAdapter = _safe_import("zenodo", "ZenodoAdapter")

# P6 scientific data sources (direct clients, not BaseSourceAdapter-based)
from .base_p6 import BaseP6Client
from .ncbi_eutils import NCBIEUtilsClient
from .pubchem import PubChemClient
from .chembl import ChEMBLClient
from .materials_project import MaterialsProjectClient
from .noaa import NOAAClient
from .gtex import GTExClient
from .uniprot import UniProtClient
from .kaggle import KaggleClient
from .drugbank import DrugBankClient
