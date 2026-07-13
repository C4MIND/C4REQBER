"""Tests for new data source clients (P6)."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.knowledge.sources.aflow import AflowClient
from src.knowledge.sources.chembl import ChEMBLClient
from src.knowledge.sources.drugbank import DrugBankClient
from src.knowledge.sources.gtex import GTExClient
from src.knowledge.sources.harvard_dataverse import HarvardDataverseClient
from src.knowledge.sources.kaggle import KaggleClient
from src.knowledge.sources.materials_project import MaterialsProjectClient
from src.knowledge.sources.ncbi_eutils import NCBIEUtilsClient
from src.knowledge.sources.noaa import NOAAClient
from src.knowledge.sources.pubchem import PubChemClient
from src.knowledge.sources.re3data import Re3dataClient
from src.knowledge.sources.uci_ml import UciMlClient
from src.knowledge.sources.uniprot import UniProtClient


class TestNCBIEUtilsClient:
    def test_uses_email(self) -> None:
        client = NCBIEUtilsClient(api_key="test_key", email="test@example.com")
        assert client.email == "test@example.com"

    @pytest.mark.anyio(backend="asyncio")
    async def test_search_returns_results(self) -> None:
        client = NCBIEUtilsClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {"esearchresult": {"idlist": ["123", "456"]}}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search("pubmed", "cancer")

        assert len(result) == 2
        assert result[0]["uid"] == "123"

    @pytest.mark.anyio(backend="asyncio")
    async def test_summary_returns_docs(self) -> None:
        client = NCBIEUtilsClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "uids": ["123"],
                "123": {"title": "Test Paper"},
            }
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.summary("pubmed", ["123"])

        assert len(result) == 1
        assert result[0]["title"] == "Test Paper"


class TestPubChemClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_compound(self) -> None:
        client = PubChemClient()
        mock_response = Mock()
        mock_response.json.return_value = {"PC_Compounds": [{"id": {"id": [{"cid": 123}]}}]}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_compound("aspirin")

        assert len(result) == 1
        assert result[0]["cid"] == 123

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_properties(self) -> None:
        client = PubChemClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "PropertyTable": {"Properties": [{"MolecularFormula": "C9H8O4"}]}
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_properties(123)

        assert result.get("MolecularFormula") == "C9H8O4"


class TestChEMBLClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_molecule(self) -> None:
        client = ChEMBLClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "molecules": [{"molecule_chembl_id": "CHEMBL123", "pref_name": "Test"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_molecule("aspirin")

        assert len(result) == 1
        assert result[0]["chembl_id"] == "CHEMBL123"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_bioactivities(self) -> None:
        client = ChEMBLClient()
        mock_response = Mock()
        mock_response.json.return_value = {"activities": [{"activity_id": 1, "value": 10.0}]}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_bioactivities("CHEMBL123")

        assert len(result) == 1


class TestMaterialsProjectClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_requires_key(self) -> None:
        client = MaterialsProjectClient(api_key="")
        result = await client.search_materials(["Fe", "O"])
        assert result == []

    @pytest.mark.anyio(backend="asyncio")
    async def test_search_with_key(self) -> None:
        client = MaterialsProjectClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"material_id": "mp-123", "formula_pretty": "Fe2O3"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_materials(["Fe", "O"])

        assert len(result) == 1
        assert result[0]["formula"] == "Fe2O3"


class TestNOAAClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_requires_key(self) -> None:
        client = NOAAClient(api_key="")
        result = await client.search_stations()
        assert result == []

    @pytest.mark.anyio(backend="asyncio")
    async def test_search_stations(self) -> None:
        client = NOAAClient(api_key="test_token")
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [{"id": "USW00094728", "name": "NY Central Park"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_stations(location="FIPS:36")

        assert len(result) == 1
        assert result[0]["id"] == "USW00094728"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_daily_data(self) -> None:
        client = NOAAClient(api_key="test_token")
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"date": "2024-01-01", "value": 5.2}]}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_daily_data("USW00094728", "2024-01-01", "2024-01-02")

        assert len(result) == 1


class TestGTExClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_gene(self) -> None:
        client = GTExClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"geneSymbol": "BRCA1", "gencodeId": "ENSG00000012048"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_gene("BRCA1")

        assert len(result) == 1
        assert result[0]["geneSymbol"] == "BRCA1"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_expression(self) -> None:
        client = GTExClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"tissueSiteDetailId": "Liver", "median": 12.5}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_expression("ENSG00000012048")

        assert len(result) == 1

    @pytest.mark.anyio(backend="asyncio")
    async def test_list_tissues(self) -> None:
        client = GTExClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"tissueSiteDetailId": "Brain_Cortex", "tissueSite": "Brain - Cortex"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.list_tissues()

        assert len(result) == 1


class TestUniProtClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search(self) -> None:
        client = UniProtClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [{"primaryAccession": "P04637", "uniProtkbId": "P53_HUMAN"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search("gene:BRCA1")

        assert len(result) == 1
        assert result[0]["primaryAccession"] == "P04637"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_entry(self) -> None:
        client = UniProtClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "primaryAccession": "P04637",
            "proteinDescription": {"recommendedName": {"fullName": "Cellular tumor antigen p53"}},
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_entry("P04637")

        assert result["primaryAccession"] == "P04637"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_sequence(self) -> None:
        client = UniProtClient()
        mock_response = Mock()
        mock_response.text = ">sp|P04637|P53_HUMAN\nMEEPQSDPSI"
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_sequence("P04637")

        assert "MEEPQSDPSI" in result


class TestKaggleClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_requires_credentials(self) -> None:
        client = KaggleClient(username="", api_key="")
        result = await client.search_datasets("healthcare")
        assert result == []

    @pytest.mark.anyio(backend="asyncio")
    async def test_search_datasets(self) -> None:
        client = KaggleClient(username="testuser", api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = [
            {"ref": "testuser/healthcare-data", "title": "Healthcare Dataset"}
        ]
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_datasets("healthcare")

        assert len(result) == 1
        assert result[0]["title"] == "Healthcare Dataset"


class TestDrugBankClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_not_available_without_key(self) -> None:
        client = DrugBankClient(api_key="")
        assert not client.available
        result = await client.search_drugs("aspirin")
        assert result == []

    def test_available_with_key(self) -> None:
        client = DrugBankClient(api_key="test_key")
        assert client.available

    @pytest.mark.anyio(backend="asyncio")
    async def test_search_drugs(self) -> None:
        client = DrugBankClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {"drugs": [{"drugbank_id": "DB00945", "name": "Aspirin"}]}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_drugs("aspirin")

        assert len(result) == 1
        assert result[0]["drugbank_id"] == "DB00945"


class TestAflowClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_materials(self) -> None:
        client = AflowClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "entries": [{"auid": "aflow:123", "aurl": "test/auid/123", "species": "Al,O"}]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_materials("AlO")

        assert len(result) == 1
        assert result[0]["auid"] == "aflow:123"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_properties(self) -> None:
        client = AflowClient()
        mock_response = Mock()
        mock_response.json.return_value = {"band_gap": 1.2}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_properties("test/auid/123")

        assert result.get("band_gap") == 1.2


class TestUciMlClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_datasets(self) -> None:
        client = UciMlClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "datasets": [
                {
                    "id": 53,
                    "name": "Iris",
                    "abstract": "Classic classification dataset",
                    "area": "biology",
                }
            ]
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_datasets("iris")

        assert len(result) == 1
        assert result[0]["name"] == "Iris"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_dataset(self) -> None:
        client = UciMlClient()
        mock_response = Mock()
        mock_response.json.return_value = {"id": 53, "name": "Iris"}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_dataset(53)

        assert result["name"] == "Iris"


class TestHarvardDataverseClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_datasets(self) -> None:
        client = HarvardDataverseClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {
                        "global_id": "doi:10.7910/DVN/ABC123",
                        "name": "Test Dataset",
                        "authors": ["Doe, J"],
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_datasets("social science")

        assert len(result) == 1
        assert result[0]["global_id"] == "doi:10.7910/DVN/ABC123"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_dataset_metadata(self) -> None:
        client = HarvardDataverseClient(api_key="test_key")
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"title": "Test Dataset"}}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_dataset_metadata("doi:10.7910/DVN/ABC123")

        assert result.get("data", {}).get("title") == "Test Dataset"


class TestRe3dataClient:
    @pytest.mark.anyio(backend="asyncio")
    async def test_search_repositories(self) -> None:
        client = Re3dataClient()
        mock_response = Mock()
        mock_response.json.return_value = {
            "re3data": {"repository": [{"id": "r3d100000001", "name": "Zenodo", "type": "general"}]}
        }
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.search_repositories("zenodo")

        assert len(result) == 1
        assert result[0]["name"] == "Zenodo"

    @pytest.mark.anyio(backend="asyncio")
    async def test_get_repository(self) -> None:
        client = Re3dataClient()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "r3d100000001", "name": "Zenodo"}
        mock_response.raise_for_status = Mock(return_value=None)

        with patch.object(client._client, "get", return_value=mock_response):
            result = await client.get_repository("r3d100000001")

        assert result["name"] == "Zenodo"
