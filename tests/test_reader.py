import inspect
from pathlib import Path

import pytest

from w1_lab.reader import iter_lines

@pytest.fixture
def sample_file(tmp_path:Path) -> Path:

    f =tmp_path /"sample.log"
    f.write_text("l1\n\nl2\n \nl3\n",encoding="utf-8")
    return f

def test_iter_lines_skips_blank(sample_file:Path) ->None:
    assert list(iter_lines(sample_file))==["l1","l2","l3"]

def test_iter_lines_returns_generator(sample_file:Path)->None:
    assert inspect.isgenerator(iter_lines(sample_file))

def test_iter_lines_empty_file(tmp_path:Path)->None:
    f = tmp_path / "empty.log"
    f.write_text("",encoding="utf-8")
    assert list(iter_lines(f))==[]