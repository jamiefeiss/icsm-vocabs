from pathlib import Path
from typing import List

import pytest
import pyshacl
from rdflib import Graph

REPO_DIR = Path(__file__).parent.parent.resolve()


@pytest.fixture
def _get_vocpub_graph() -> Graph:
    graph = Graph()
    graph.parse(Path(__file__).parent / "vocpub-4.10.ttl")
    return graph


def _get_vocab_files() -> List[Path]:
    vocab_directories = [
        REPO_DIR / "cadastre",
        # REPO_DIR / "geocoded-addressing",
        # REPO_DIR / "transport",
        # REPO_DIR / "place-names",
    ]
    files = []

    for directory in vocab_directories:
        files += directory.glob("**/*.ttl")

    return files


@pytest.mark.parametrize("vocab_file", _get_vocab_files())
def test_vocabs(vocab_file: List[Path], _get_vocpub_graph: Graph):
    conforms, _, results_text = pyshacl.validate(
        data_graph=Graph().parse(vocab_file),
        shacl_graph=_get_vocpub_graph,
        allow_warnings=True,
    )

    assert conforms, f"{vocab_file} failed:\n{results_text}"
