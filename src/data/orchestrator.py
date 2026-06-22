"""
c4reqber: DataOrchestrator — automatic tabular data retrieval for causal discovery.

Searches ALL relevant data sources (37+) before falling back to toy models.
Domain-aware routing maps hypothesis domains to the best tabular data sources.
"""
from __future__ import annotations

import asyncio
import io
import logging
from typing import Any

import pandas as pd


logger = logging.getLogger("c4reqber.data.orchestrator")

# ---------------------------------------------------------------------------
# Domain → preferred tabular-data sources (data-oriented subset of 37+)
# ---------------------------------------------------------------------------
DOMAIN_DATA_SOURCES: dict[str, list[str]] = {
    "biomedical": ["chembl", "pubchem", "gtex", "drugbank", "string_db", "openfda", "clinicaltrials", "kaggle", "uci_ml", "harvard_dataverse"],
    "medicine": ["chembl", "pubchem", "gtex", "drugbank", "string_db", "openfda", "clinicaltrials", "kaggle", "uci_ml", "harvard_dataverse"],
    "neuroscience": ["gtex", "pubchem", "allen_brain", "string_db", "kaggle", "uci_ml", "harvard_dataverse"],
    "biology": ["chembl", "pubchem", "gtex", "string_db", "gbif", "kaggle", "uci_ml", "harvard_dataverse"],
    "materials": ["materials_project", "aflow", "pubchem", "kaggle", "uci_ml", "uspto_patentsview"],
    "physics": ["materials_project", "aflow", "pubchem", "cern_opendata", "kaggle", "uci_ml", "uspto_patentsview"],
    "chemistry": ["materials_project", "aflow", "pubchem", "chembl", "kaggle", "uci_ml"],
    "math": ["oeis", "mathnet_ru", "kaggle", "uci_ml"],
    "cs": ["kaggle", "uci_ml", "harvard_dataverse", "huggingface_datasets", "openreview", "uspto_patentsview"],
    "ml": ["kaggle", "uci_ml", "harvard_dataverse", "huggingface_datasets", "openreview"],
    "ai": ["kaggle", "uci_ml", "huggingface_datasets", "openreview", "conceptnet"],
    "software": ["kaggle", "uci_ml", "huggingface_datasets"],
    "social_science": ["harvard_dataverse", "re3data", "cyberleninka", "kaggle", "uci_ml"],
    "economics": ["harvard_dataverse", "re3data", "cyberleninka", "kaggle", "uci_ml"],
    "psychology": ["harvard_dataverse", "kaggle", "uci_ml"],
    "geoscience": ["noaa", "usgs", "nasa_earthdata", "harvard_dataverse", "kaggle", "uci_ml"],
    "environment": ["noaa", "usgs", "nasa_earthdata", "gbif", "harvard_dataverse", "kaggle", "uci_ml"],
    "ecology": ["gbif", "noaa", "usgs", "kaggle", "uci_ml"],
    "engineering": ["uspto_patentsview", "kaggle", "uci_ml", "harvard_dataverse"],
    "patents": ["uspto_patentsview", "kaggle", "uci_ml"],
    "astronomy": ["cern_opendata", "kaggle", "uci_ml"],
    "general": ["kaggle", "uci_ml", "harvard_dataverse", "re3data", "pubchem", "conceptnet", "cyberleninka", "oeis"],
    "science": ["kaggle", "uci_ml", "harvard_dataverse", "pubchem", "materials_project", "chembl", "cern_opendata", "cyberleninka", "mathnet_ru"],
}

# Sources that can yield structured records directly (no file download needed)
STRUCTURED_SOURCES: set[str] = {
    "materials_project", "aflow", "chembl", "pubchem", "gtex", "drugbank", "noaa",
    "string_db", "clinicaltrials", "gbif", "allen_brain", "usgs",
    "openfda", "nasa_earthdata", "oeis", "conceptnet",
    "cyberleninka", "mathnet_ru",
}

# Sources that require CSV/TSV download from dataset metadata
DATASET_SOURCES: set[str] = {"kaggle", "uci_ml", "harvard_dataverse", "huggingface_datasets"}

# Registry / metadata-only sources (no direct data extraction)
REGISTRY_SOURCES: set[str] = {"re3data", "uspto_patentsview", "openreview", "cern_opendata"}


class DataOrchestrator:
    """Search all relevant data sources and return the best DataFrame for causal discovery."""

    MIN_ROWS = 100
    MAX_ROWS = 100_000
    TIMEOUT = 30.0

    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}
        self._search_report: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_dataframe_for_hypothesis(
        self, problem: str, domain: str
    ) -> tuple[pd.DataFrame | None, dict[str, Any]]:
        """Main entry: search → extract → return best DataFrame + metadata."""
        sources = self._resolve_sources(domain, problem)
        results = await self._search_all_sources(problem, sources)
        df, meta = await self._extract_best_dataframe(results, problem)

        report = {
            "sources_searched": sources,
            "sources_count": len(sources),
            "results_found": sum(len(r.get("items", [])) for r in results),
            "dataframe_extracted": df is not None,
            **meta,
        }
        return df, report

    # ------------------------------------------------------------------
    # Domain resolution
    # ------------------------------------------------------------------
    def _resolve_sources(self, domain: str, problem: str) -> list[str]:
        """Pick data-oriented sources based on domain + problem keywords."""
        domain_lower = domain.lower().replace(" ", "_")
        candidates = list(DOMAIN_DATA_SOURCES.get(domain_lower, DOMAIN_DATA_SOURCES["science"]))

        # Keyword boost: scan problem for domain-specific terms
        problem_lower = problem.lower()
        keyword_boost: dict[str, list[str]] = {
            "materials_project": ["band gap", "fermi energy", "elastic modulus", "bulk modulus", "dielectric", "crystal", "lattice", "perovskite", "oxide"],
            "aflow": ["aflow", "icsd", "space group", "wyckoff", "enthalpy"],
            "chembl": ["ic50", "ec50", "bioactivity", "assay", "inhibitor", "agonist", "antagonist"],
            "pubchem": ["cid", "smiles", "molecular weight", "logp", "compound", "synthetic"],
            "gtex": ["gene expression", "tissue", "rna-seq", "transcriptome", "eqtl"],
            "drugbank": ["drug", "pharmacology", "therapeutic", "indication", "drug interaction"],
            "noaa": ["temperature", "precipitation", "climate", "weather station", "sea level"],
            "kaggle": ["dataset", "competition", "csv", "tabular"],
            "uci_ml": ["benchmark", "classification", "regression", "dataset"],
            "harvard_dataverse": ["survey", "census", "social", "policy", "longitudinal"],
        }
        boosted: set[str] = set(candidates)
        for source, keywords in keyword_boost.items():
            if any(kw in problem_lower for kw in keywords):
                boosted.add(source)

        # Remove registry-only sources from primary extraction list
        # (re3data is useful for finding *other* repos, but doesn't host data)
        final = [s for s in boosted if s not in REGISTRY_SOURCES]
        # Keep re3data at the tail as a last-ditch repo finder
        if "re3data" in boosted and "re3data" not in final:
            final.append("re3data")

        return final

    # ------------------------------------------------------------------
    # Parallel search
    # ------------------------------------------------------------------
    async def _search_all_sources(
        self, problem: str, sources: list[str]
    ) -> list[dict[str, Any]]:
        """Fire parallel searches across all resolved sources."""
        coros = [self._search_one(problem, src) for src in sources]
        results = await asyncio.gather(*coros, return_exceptions=True)
        out: list[dict[str, Any]] = []
        for src, res in zip(sources, results):
            if isinstance(res, Exception):
                logger.warning("Data search error for %s: %s", src, res)
                out.append({"source": src, "items": [], "error": str(res)})
            else:
                out.append({"source": src, "items": res or [], "error": None})
        return out

    async def _search_one(self, problem: str, source: str) -> list[dict[str, Any]]:
        """Route search to the correct P6 client / adapter."""
        try:
            client = self._get_client(source)
        except Exception as exc:
            logger.debug("Client init failed for %s: %s", source, exc)
            return []

        method_name = self._search_method_for(source)
        method = getattr(client, method_name, None)
        if method is None:
            return []

        try:
            # Some clients expect list[str] (e.g. materials_project elements)
            if source == "materials_project":
                # Heuristic: split problem into element-like words
                words = [w for w in problem.split() if w[0].isupper() and len(w) <= 2]
                if not words:
                    words = ["Fe", "O"]  # fallback demo query
                return await method(words, limit=20)
            elif source == "aflow":
                return await method(problem, limit=20)
            elif source == "noaa":
                return await method(query=problem, limit=20)
            elif source in ("gtex", "drugbank"):
                # These have search_gene / search_drugs etc.
                return await method(query=problem, limit=20)
            else:
                return await method(query=problem, limit=20)
        except Exception as exc:
            logger.warning("Search error %s: %s", source, exc)
            return []

    def _get_client(self, source: str) -> Any:
        """Lazy-init P6 client for a source."""
        if source in self._clients:
            return self._clients[source]

        # Map source name → client module/class
        mapping: dict[str, tuple[str, str]] = {
            "kaggle": ("src.knowledge.sources.kaggle", "KaggleClient"),
            "uci_ml": ("src.knowledge.sources.uci_ml", "UciMlClient"),
            "harvard_dataverse": ("src.knowledge.sources.harvard_dataverse", "HarvardDataverseClient"),
            "materials_project": ("src.knowledge.sources.materials_project", "MaterialsProjectClient"),
            "aflow": ("src.knowledge.sources.aflow", "AflowClient"),
            "chembl": ("src.knowledge.sources.chembl", "ChEMBLClient"),
            "pubchem": ("src.knowledge.sources.pubchem", "PubChemClient"),
            "gtex": ("src.knowledge.sources.gtex", "GTExClient"),
            "drugbank": ("src.knowledge.sources.drugbank", "DrugBankClient"),
            "noaa": ("src.knowledge.sources.noaa", "NOAAClient"),
            "re3data": ("src.knowledge.sources.re3data", "Re3dataClient"),
            "string_db": ("src.knowledge.sources.string_db", "StringDbClient"),
            "clinicaltrials": ("src.knowledge.sources.clinicaltrials", "ClinicalTrialsClient"),
            "gbif": ("src.knowledge.sources.gbif", "GbifClient"),
            "allen_brain": ("src.knowledge.sources.allen_brain", "AllenBrainClient"),
            "usgs": ("src.knowledge.sources.usgs", "UsgsClient"),
            "openfda": ("src.knowledge.sources.openfda", "OpenFdaClient"),
            "nasa_earthdata": ("src.knowledge.sources.nasa_earthdata", "NasaEarthdataClient"),
            "oeis": ("src.knowledge.sources.oeis", "OeisClient"),
            "conceptnet": ("src.knowledge.sources.conceptnet", "ConceptNetClient"),
            "cyberleninka": ("src.knowledge.sources.cyberleninka", "CyberLeninkaClient"),
            "mathnet_ru": ("src.knowledge.sources.mathnet_ru", "MathNetRuClient"),
            "huggingface_datasets": ("src.knowledge.sources.huggingface_datasets", "HuggingFaceDatasetsClient"),
        }
        mod_path, cls_name = mapping.get(source, ("", ""))
        if not mod_path:
            raise RuntimeError(f"Unknown data source: {source}")
        mod = __import__(mod_path, fromlist=[cls_name])
        cls = getattr(mod, cls_name)
        client = cls()
        self._clients[source] = client
        return client

    def _search_method_for(self, source: str) -> str:
        """Return the primary search method name for a source."""
        return {
            "kaggle": "search_datasets",
            "uci_ml": "search_datasets",
            "harvard_dataverse": "search_datasets",
            "materials_project": "search_materials",
            "aflow": "search_materials",
            "chembl": "search_molecule",
            "pubchem": "search_compound",
            "gtex": "search_gene",
            "drugbank": "search_drugs",
            "noaa": "search_stations",
            "re3data": "search_repositories",
            "string_db": "search_proteins",
            "clinicaltrials": "search_studies",
            "gbif": "search_occurrences",
            "allen_brain": "search_genes",
            "usgs": "search_earthquakes",
            "openfda": "search_adverse_events",
            "nasa_earthdata": "search_collections",
            "oeis": "search_sequences",
            "conceptnet": "search_concepts",
            "cyberleninka": "search_articles",
            "mathnet_ru": "search_articles",
            "huggingface_datasets": "search_datasets",
        }.get(source, "search")

    # ------------------------------------------------------------------
    # DataFrame extraction
    # ------------------------------------------------------------------
    async def _extract_best_dataframe(
        self, results: list[dict[str, Any]], problem: str
    ) -> tuple[pd.DataFrame | None, dict[str, Any]]:
        """Try to build a DataFrame from every non-empty result."""
        meta: dict[str, Any] = {"attempts": [], "best_source": None}
        best_df: pd.DataFrame | None = None
        best_score = -1.0

        for result in results:
            source = result["source"]
            items = result.get("items", [])
            if not items:
                meta["attempts"].append({"source": source, "status": "no_results"})
                continue

            df: pd.DataFrame | None = None
            try:
                if source in STRUCTURED_SOURCES:
                    df = await self._extract_structured(source, items, problem)
                elif source in DATASET_SOURCES:
                    df = await self._extract_dataset(source, items, problem)
                elif source in REGISTRY_SOURCES:
                    meta["attempts"].append({"source": source, "status": "registry_skipped"})
                    continue
            except Exception as exc:
                logger.debug("Extraction error for %s: %s", source, exc)
                meta["attempts"].append({"source": source, "status": f"extraction_error: {exc}"})
                continue

            if df is None or len(df) < self.MIN_ROWS or len(df) > self.MAX_ROWS:
                status = "too_small" if (df is not None and len(df) < self.MIN_ROWS) else (
                    "too_large" if (df is not None and len(df) > self.MAX_ROWS) else "extraction_failed"
                )
                meta["attempts"].append({"source": source, "status": status, "rows": len(df) if df is not None else 0})
                continue

            score = self._score_dataframe(df, problem)
            meta["attempts"].append({"source": source, "status": "success", "rows": len(df), "columns": list(df.columns), "score": round(score, 4)})
            if score > best_score:
                best_score = score
                best_df = df
                meta["best_source"] = source

        return best_df, meta

    def _score_dataframe(self, df: pd.DataFrame, problem: str) -> float:
        """Heuristic: more numeric columns + keyword match = better for causal discovery."""
        numeric_cols = df.select_dtypes(include="number").columns
        score = len(numeric_cols) * 2.0 + min(len(df.columns), 20)
        problem_words = set(problem.lower().split())
        for col in df.columns:
            if any(w in col.lower() for w in problem_words):
                score += 3.0
        return score

    # ------------------------------------------------------------------
    # Structured-source extraction (no download needed)
    # ------------------------------------------------------------------
    async def _extract_structured(
        self, source: str, items: list[dict[str, Any]], problem: str
    ) -> pd.DataFrame | None:
        if source == "materials_project":
            return await self._mp_to_dataframe(items)
        if source == "aflow":
            return await self._aflow_to_dataframe(items)
        if source == "chembl":
            return await self._chembl_to_dataframe(items)
        if source == "pubchem":
            return await self._pubchem_to_dataframe(items)
        if source == "gtex":
            return await self._gtex_to_dataframe(items)
        if source == "drugbank":
            return await self._drugbank_to_dataframe(items)
        if source == "noaa":
            return await self._noaa_to_dataframe(items)
        if source == "string_db":
            return await self._string_db_to_dataframe(items)
        if source == "clinicaltrials":
            return pd.DataFrame(items) if items else None
        if source == "gbif":
            return pd.DataFrame(items) if items else None
        if source == "allen_brain":
            return pd.DataFrame(items) if items else None
        if source == "usgs":
            return pd.DataFrame(items) if items else None
        if source == "openfda":
            return pd.DataFrame(items) if items else None
        if source == "nasa_earthdata":
            return pd.DataFrame(items) if items else None
        if source == "oeis":
            return pd.DataFrame(items) if items else None
        if source == "conceptnet":
            return pd.DataFrame(items) if items else None
        if source == "cyberleninka":
            return pd.DataFrame(items) if items else None
        if source == "mathnet_ru":
            return pd.DataFrame(items) if items else None
        return None

    async def _mp_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("materials_project")
        rows: list[dict[str, Any]] = []
        for item in items[:50]:  # cap to avoid rate limits
            mid = item.get("material_id")
            if not mid:
                continue
            try:
                props = await client.get_properties(mid)
                if isinstance(props, dict):
                    flat = {"material_id": mid, "formula": item.get("formula", "")}
                    flat.update(self._flatten_dict(props, prefix="prop"))
                    rows.append(flat)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _aflow_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("aflow")
        rows: list[dict[str, Any]] = []
        for item in items[:50]:
            aurl = item.get("aurl")
            if not aurl:
                continue
            try:
                props = await client.get_properties(aurl)
                if isinstance(props, dict):
                    flat = {"auid": item.get("auid", ""), "species": item.get("species", "")}
                    flat.update(self._flatten_dict(props, prefix="prop"))
                    rows.append(flat)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _chembl_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("chembl")
        rows: list[dict[str, Any]] = []
        for item in items[:20]:
            cid = item.get("chembl_id")
            if not cid:
                continue
            try:
                acts = await client.get_bioactivities(cid, limit=50)
                if isinstance(acts, list):
                    for act in acts:
                        if isinstance(act, dict):
                            act["query_molecule_chembl_id"] = cid
                            rows.append(act)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _pubchem_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("pubchem")
        rows: list[dict[str, Any]] = []
        for item in items[:20]:
            cid = item.get("cid")
            if not cid:
                continue
            try:
                props = await client.get_properties(cid)
                if isinstance(props, dict):
                    props["query_cid"] = cid
                    rows.append(props)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _gtex_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("gtex")
        rows: list[dict[str, Any]] = []
        for item in items[:20]:
            gene = item.get("gene_id") or item.get("symbol")
            if not gene:
                continue
            try:
                expr = await client.get_expression(gene)
                if isinstance(expr, list):
                    rows.extend(expr)
                elif isinstance(expr, dict):
                    rows.append(expr)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _drugbank_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("drugbank")
        rows: list[dict[str, Any]] = []
        for item in items[:20]:
            dbid = item.get("drugbank_id")
            if not dbid:
                continue
            try:
                targets = await client.get_targets(dbid)
                if isinstance(targets, list):
                    for t in targets:
                        t["drugbank_id"] = dbid
                        rows.append(t)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _noaa_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("noaa")
        rows: list[dict[str, Any]] = []
        for item in items[:10]:
            sid = item.get("id")
            if not sid:
                continue
            try:
                data = await client.get_daily_data(sid)
                if isinstance(data, list):
                    rows.extend(data)
                elif isinstance(data, dict):
                    rows.append(data)
            except Exception:
                continue
        return pd.DataFrame(rows) if rows else None

    async def _string_db_to_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("string_db")
        rows: list[dict[str, Any]] = []
        identifiers = [item.get("string_id") or item.get("preferred_name") for item in items[:20] if item]
        identifiers = [i for i in identifiers if i]
        if not identifiers:
            return None
        try:
            network = await client.get_network(identifiers[:10])
            return pd.DataFrame(network) if network else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Dataset-repository extraction (may require CSV download)
    # ------------------------------------------------------------------
    async def _extract_dataset(
        self, source: str, items: list[dict[str, Any]], problem: str
    ) -> pd.DataFrame | None:
        if source == "uci_ml":
            return await self._uci_ml_dataframe(items)
        if source == "kaggle":
            return await self._kaggle_dataframe(items)
        if source == "harvard_dataverse":
            return await self._harvard_dataverse_dataframe(items)
        if source == "huggingface_datasets":
            return await self._huggingface_datasets_dataframe(items)
        return None

    async def _uci_ml_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("uci_ml")
        for item in items[:5]:
            dsid = item.get("id")
            if not dsid:
                continue
            try:
                meta = await client.get_dataset(dsid)
                if not isinstance(meta, dict):
                    continue
                # UCI ML API returns metadata; try to find CSV URL in the response
                csv_url = self._find_csv_url_in_dict(meta)
                if csv_url:
                    df = await self._download_csv(csv_url)
                    if df is not None and len(df) >= self.MIN_ROWS:
                        return df
            except Exception:
                continue
        return None

    async def _kaggle_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("kaggle")
        for item in items[:3]:
            ref = item.get("ref") or item.get("datasetRef")
            if not ref or "/" not in ref:
                continue
            owner, dataset = ref.split("/", 1)
            try:
                files = await client.list_files(owner, dataset)
                if not isinstance(files, list):
                    continue
                for f in files:
                    fname = f.get("name", "")
                    if fname.endswith(".csv"):
                        url = await client.download_link(owner, dataset, fname)
                        if url:
                            df = await self._download_csv(url, auth=client._client.auth if hasattr(client, "_client") else None)
                            if df is not None and len(df) >= self.MIN_ROWS:
                                return df
            except Exception:
                continue
        return None

    async def _harvard_dataverse_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("harvard_dataverse")
        for item in items[:3]:
            pid = item.get("global_id")
            if not pid:
                continue
            try:
                meta = await client.get_dataset_metadata(pid)
                if not isinstance(meta, dict):
                    continue
                files = meta.get("data", {}).get("latestVersion", {}).get("files", [])
                for f in files:
                    fname = f.get("dataFile", {}).get("filename", "")
                    if fname.endswith(".csv") or fname.endswith(".tsv") or fname.endswith(".tab"):
                        # Construct download URL
                        file_id = f.get("dataFile", {}).get("id")
                        if file_id:
                            url = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}"
                            df = await self._download_csv(url)
                            if df is not None and len(df) >= self.MIN_ROWS:
                                return df
            except Exception:
                continue
        return None

    async def _huggingface_datasets_dataframe(self, items: list[dict[str, Any]]) -> pd.DataFrame | None:
        client = self._get_client("huggingface_datasets")
        for item in items[:3]:
            ds_id = item.get("id")
            if not ds_id:
                continue
            try:
                info = await client.get_dataset_info(ds_id)
                if not isinstance(info, dict):
                    continue
                features = info.get("features", [])
                rows = info.get("rows", [])
                if rows and len(rows) >= self.MIN_ROWS:
                    return pd.DataFrame(rows)
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _download_csv(
        self, url: str, auth: Any = None, sep: str | None = None
    ) -> pd.DataFrame | None:
        """Download a CSV/TSV from URL and return a DataFrame."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.TIMEOUT, follow_redirects=True) as client:
                response = await client.get(url, auth=auth)
                response.raise_for_status()
                content = response.content
                if not content:
                    return None
                # Detect separator
                if sep is None:
                    first_line = content.split(b"\n")[0].decode("utf-8", errors="replace")
                    sep = "\t" if "\t" in first_line else ","
                return pd.read_csv(io.BytesIO(content), sep=sep, low_memory=False)
        except Exception as exc:
            logger.debug("CSV download failed for %s: %s", url, exc)
            return None

    def _find_csv_url_in_dict(self, d: dict[str, Any]) -> str | None:
        """Recursively scan a dict for anything that looks like a CSV URL."""
        for k, v in d.items():
            if isinstance(v, str) and v.endswith(".csv") and v.startswith("http"):
                return v
            if isinstance(v, dict):
                found = self._find_csv_url_in_dict(v)
                if found:
                    return found
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        found = self._find_csv_url_in_dict(item)
                        if found:
                            return found
        return None

    def _flatten_dict(self, d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten nested dicts for DataFrame rows."""
        out: dict[str, Any] = {}
        for k, v in d.items():
            key = f"{prefix}_{k}" if prefix else k
            if isinstance(v, dict):
                out.update(self._flatten_dict(v, prefix=key))
            elif not isinstance(v, (list, dict)):
                out[key] = v
        return out


# ---------------------------------------------------------------------------
# Convenience sync wrapper for non-async callers
# ---------------------------------------------------------------------------

def get_dataframe_for_hypothesis(
    problem: str, domain: str
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Sync wrapper around DataOrchestrator."""
    orch = DataOrchestrator()
    try:
        loop = asyncio.get_running_loop()
        # If already in an async context, schedule it
        future = asyncio.ensure_future(orch.get_dataframe_for_hypothesis(problem, domain))
        # We can't block; return None with a note
        if not future.done():
            return None, {"note": "async_context_cannot_block", "sources_searched": []}
        return future.result()
    except RuntimeError:
        # No running loop — safe to use run_until_complete
        return asyncio.run(orch.get_dataframe_for_hypothesis(problem, domain))
