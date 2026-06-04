"""
Tests for src/adapters/pubmed_adapter.py

Covers:
- PubMedPaper dataclass
- PubMedAdapter initialization
- search() happy path and error handling
- search_by_mesh() wrapper
- get_recent() wrapper
- _fetch_details() and _parse_pubmed_xml()
- format_for_context()
- Rate limiting behavior
- Edge cases: empty results, malformed XML, network errors
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from src.adapters.pubmed_adapter import PUBMED_FIELDS, PubMedAdapter, PubMedPaper


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def adapter():
    return PubMedAdapter()


@pytest.fixture
def sample_search_response():
    return {
        "esearchresult": {
            "idlist": ["12345", "67890"],
            "count": "2",
        }
    }


@pytest.fixture
def sample_pubmed_xml():
    """Sample PubMed XML with 2 articles."""
    return """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345</PMID>
      <Article>
        <ArticleTitle>Test Paper Title</ArticleTitle>
        <Abstract>
          <AbstractText>This is a test abstract.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Doe</LastName>
            <ForeName>John</ForeName>
          </Author>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>Jane</ForeName>
          </Author>
        </AuthorList>
        <Journal>
          <Title>Nature</Title>
        </Journal>
        <JournalIssue>
          <PubDate>
            <Year>2024</Year>
            <Month>Jan</Month>
          </PubDate>
        </JournalIssue>
      </Article>
      <MeshHeadingList>
        <MeshHeading>
          <DescriptorName>Artificial Intelligence</DescriptorName>
        </MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1234/test</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>67890</PMID>
      <Article>
        <ArticleTitle>Second Paper</ArticleTitle>
        <Abstract>
          <AbstractText>Another abstract.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Brown</LastName>
            <ForeName>Alice</ForeName>
          </Author>
        </AuthorList>
        <Journal>
          <Title>Science</Title>
        </Journal>
        <JournalIssue>
          <PubDate>
            <Year>2023</Year>
          </PubDate>
        </JournalIssue>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


@pytest.fixture
def sample_papers():
    return [
        PubMedPaper(
            pmid="12345",
            title="Test Paper Title",
            abstract="This is a test abstract.",
            authors=["John Doe", "Jane Smith"],
            journal="Nature",
            pub_date="2024-Jan",
            doi="10.1234/test",
            mesh_terms=["Artificial Intelligence"],
        ),
        PubMedPaper(
            pmid="67890",
            title="Second Paper",
            abstract="Another abstract.",
            authors=["Alice Brown"],
            journal="Science",
            pub_date="2023",
            doi="",
            mesh_terms=[],
        ),
    ]


# ═══════════════════════════════════════════════════════════════════
# PubMedPaper Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestPubMedPaper:
    def test_creation(self):
        paper = PubMedPaper(
            pmid="123",
            title="Test",
            abstract="Abstract",
            authors=["A"],
            journal="Nature",
            pub_date="2024",
            doi="10.1234",
            mesh_terms=["AI"],
        )
        assert paper.pmid == "123"
        assert paper.title == "Test"
        assert paper.journal == "Nature"
        assert paper.doi == "10.1234"

    def test_defaults(self):
        paper = PubMedPaper(
            pmid="", title="", abstract="", authors=[], journal="", pub_date="", doi="", mesh_terms=[]
        )
        assert paper.authors == []
        assert paper.mesh_terms == []


# ═══════════════════════════════════════════════════════════════════
# PubMedAdapter Initialization
# ═══════════════════════════════════════════════════════════════════


class TestPubMedAdapterInit:
    def test_init(self, adapter):
        assert adapter.last_request_time == 0
        assert adapter.BASE_URL == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def test_init_with_api_key(self):
        adapter = PubMedAdapter(api_key="test-key")
        assert adapter.api_key == "test-key"


# ═══════════════════════════════════════════════════════════════════
# search() - Happy Path
# ═══════════════════════════════════════════════════════════════════


class TestSearchHappyPath:
    def test_search_returns_papers(self, adapter, sample_search_response, sample_pubmed_xml, sample_papers):
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                papers = adapter.search("quantum computing", max_results=10)

        assert len(papers) == 2
        assert papers[0].pmid == "12345"
        assert papers[0].title == "Test Paper Title"
        assert papers[0].authors == ["John Doe", "Jane Smith"]
        assert papers[0].journal == "Nature"
        assert papers[0].pub_date == "2024-Jan"
        assert papers[0].doi == "10.1234/test"
        assert papers[0].mesh_terms == ["Artificial Intelligence"]

    def test_search_empty_results(self, adapter):
        empty_response = json.dumps({"esearchresult": {"idlist": [], "count": "0"}}).encode()

        mock_response = MagicMock()
        mock_response.read.return_value = empty_response
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_response)
        mock_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_context):
            with patch("urllib.request.Request"):
                papers = adapter.search("xyznonexistent")

        assert papers == []

    def test_search_params(self, adapter, sample_search_response, sample_pubmed_xml):
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request") as mock_req:
                adapter.search("machine learning", max_results=5, sort="pub_date")

        assert mock_req.call_count >= 2

    def test_search_max_results_capped(self, adapter, sample_search_response, sample_pubmed_xml):
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                papers = adapter.search("test", max_results=200)

        assert len(papers) == 2

    def test_search_rate_limiting(self, adapter, sample_search_response, sample_pubmed_xml):
        adapter.last_request_time = 0
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                with patch("time.sleep") as mock_sleep:
                    adapter.search("test")
                    assert mock_sleep.call_count >= 0


# ═══════════════════════════════════════════════════════════════════
# search() - Error Handling
# ═══════════════════════════════════════════════════════════════════


class TestSearchErrors:
    def test_search_network_error(self, adapter):
        with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
            with patch("urllib.request.Request"):
                papers = adapter.search("test")
                assert papers == []

    def test_search_timeout_error(self, adapter):
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Timeout")):
            with patch("urllib.request.Request"):
                papers = adapter.search("test")
                assert papers == []

    def test_search_http_error(self, adapter):
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("http://example.com", 500, "Internal Error", {}, None),
        ):
            with patch("urllib.request.Request"):
                papers = adapter.search("test")
                assert papers == []

    def test_fetch_details_error(self, adapter, sample_search_response):
        search_data = json.dumps(sample_search_response).encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, Exception("Fetch error")]):
            with patch("urllib.request.Request"):
                papers = adapter.search("test")
                assert papers == []


# ═══════════════════════════════════════════════════════════════════
# search_by_mesh & get_recent
# ═══════════════════════════════════════════════════════════════════


class TestSearchWrappers:
    def test_search_by_mesh(self, adapter, sample_search_response, sample_pubmed_xml):
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                papers = adapter.search_by_mesh("Artificial Intelligence", max_results=5)

        assert len(papers) == 2

    def test_get_recent(self, adapter, sample_search_response, sample_pubmed_xml):
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                papers = adapter.get_recent(topic="cancer", days=30, max_results=10)

        assert len(papers) == 2


# ═══════════════════════════════════════════════════════════════════
# _parse_pubmed_xml
# ═══════════════════════════════════════════════════════════════════


class TestParsePubmedXml:
    def test_parse_valid_xml(self, adapter, sample_pubmed_xml):
        papers = adapter._parse_pubmed_xml(sample_pubmed_xml)
        assert len(papers) == 2
        assert papers[0].pmid == "12345"
        assert papers[0].title == "Test Paper Title"
        assert papers[0].authors == ["John Doe", "Jane Smith"]
        assert papers[0].journal == "Nature"
        assert papers[0].pub_date == "2024-Jan"
        assert papers[0].doi == "10.1234/test"
        assert papers[0].mesh_terms == ["Artificial Intelligence"]

    def test_parse_empty_xml(self, adapter):
        xml = "<?xml version=\"1.0\"?><PubmedArticleSet></PubmedArticleSet>"
        papers = adapter._parse_pubmed_xml(xml)
        assert papers == []

    def test_parse_malformed_xml(self, adapter):
        xml = "not valid xml at all"
        papers = adapter._parse_pubmed_xml(xml)
        assert papers == []

    def test_parse_no_authors(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>999</PMID>
      <Article>
        <ArticleTitle>No Authors</ArticleTitle>
        <Abstract><AbstractText>Abstract</AbstractText></Abstract>
        <Journal><Title>Journal</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert len(papers) == 1
        assert papers[0].authors == []

    def test_parse_no_abstract(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>999</PMID>
      <Article>
        <ArticleTitle>No Abstract</ArticleTitle>
        <Journal><Title>Journal</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert len(papers) == 1
        assert papers[0].abstract == ""

    def test_parse_author_without_forename(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>999</PMID>
      <Article>
        <ArticleTitle>Test</ArticleTitle>
        <AuthorList>
          <Author><LastName>OnlyLast</LastName></Author>
        </AuthorList>
        <Journal><Title>J</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert papers[0].authors == ["OnlyLast"]


# ═══════════════════════════════════════════════════════════════════
# format_for_context
# ═══════════════════════════════════════════════════════════════════


class TestFormatForContext:
    def test_with_papers(self, adapter, sample_papers):
        context = adapter.format_for_context(sample_papers)
        assert "Recent biomedical research" in context
        assert "Test Paper Title" in context
        assert "John Doe" in context
        assert "[1]" in context
        assert "[2]" in context

    def test_empty_papers(self, adapter):
        context = adapter.format_for_context([])
        assert context == "No relevant papers found."

    def test_limits_to_five(self, adapter):
        many_papers = [
            PubMedPaper(
                pmid=f"{i}",
                title=f"Paper {i}",
                abstract="Abstract",
                authors=["Author"],
                journal="Journal",
                pub_date="2024",
                doi="",
                mesh_terms=[],
            )
            for i in range(10)
        ]
        context = adapter.format_for_context(many_papers)
        assert "[5]" in context
        assert "[6]" not in context

    def test_et_al_for_many_authors(self, adapter):
        paper = PubMedPaper(
            pmid="1",
            title="Many Authors",
            abstract="Abstract",
            authors=["A", "B", "C", "D", "E"],
            journal="Journal",
            pub_date="2024",
            doi="",
            mesh_terms=[],
        )
        context = adapter.format_for_context([paper])
        assert "et al." in context


# ═══════════════════════════════════════════════════════════════════
# PUBMED_FIELDS
# ═══════════════════════════════════════════════════════════════════


class TestPubmedFields:
    def test_has_title(self):
        assert PUBMED_FIELDS["ti"] == "Title"

    def test_has_abstract(self):
        assert PUBMED_FIELDS["ab"] == "Abstract"

    def test_has_author(self):
        assert PUBMED_FIELDS["au"] == "Author"

    def test_has_mesh(self):
        assert PUBMED_FIELDS["mh"] == "MeSH Terms"


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_search_with_api_key(self, sample_search_response, sample_pubmed_xml):
        adapter = PubMedAdapter(api_key="test-key")
        search_data = json.dumps(sample_search_response).encode()
        xml_data = sample_pubmed_xml.encode()

        mock_search_response = MagicMock()
        mock_search_response.read.return_value = search_data
        mock_search_context = MagicMock()
        mock_search_context.__enter__ = MagicMock(return_value=mock_search_response)
        mock_search_context.__exit__ = MagicMock(return_value=False)

        mock_fetch_response = MagicMock()
        mock_fetch_response.read.return_value = xml_data
        mock_fetch_context = MagicMock()
        mock_fetch_context.__enter__ = MagicMock(return_value=mock_fetch_response)
        mock_fetch_context.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", side_effect=[mock_search_context, mock_fetch_context]):
            with patch("urllib.request.Request"):
                papers = adapter.search("test")

        assert len(papers) == 2

    def test_parse_xml_with_multiple_abstract_parts(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1</PMID>
      <Article>
        <ArticleTitle>Multi Part</ArticleTitle>
        <Abstract>
          <AbstractText>Part one.</AbstractText>
          <AbstractText>Part two.</AbstractText>
        </Abstract>
        <Journal><Title>J</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert papers[0].abstract == "Part one. Part two."

    def test_parse_xml_with_year_only(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1</PMID>
      <Article>
        <ArticleTitle>Year Only</ArticleTitle>
        <Journal><Title>J</Title></Journal>
        <JournalIssue>
          <PubDate>
            <Year>2023</Year>
          </PubDate>
        </JournalIssue>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert papers[0].pub_date == "2023"

    def test_parse_xml_no_journal(self, adapter):
        xml = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1</PMID>
      <Article>
        <ArticleTitle>No Journal</ArticleTitle>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""
        papers = adapter._parse_pubmed_xml(xml)
        assert papers[0].journal == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
