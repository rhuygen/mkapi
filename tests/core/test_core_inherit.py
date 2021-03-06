from dataclasses import dataclass

import pytest

import mkapi
from mkapi.core.inherit import (get_params, inherit, inherit_by_filters,
                                is_complete)


@dataclass
class A:
    """Base class.

    Parameters:
        name: Object name.
        type: Object type

    Attributes:
        name: Object name.
        type: Object type
    """

    name: str
    type: str = ""

    def set_name(self, name: str):
        """Sets name.

        Args:
            name: A New name
        """
        self.name = name


@dataclass
class B(A):
    """Item class.

    Parameters:
        markdown: Object markdown

    Attributes:
        markdown: Object markdown
    """

    markdown: str = ""

    def set_name(self, name: str):
        """Sets name in upper case."""
        self.name = name.upper()


@dataclass
class C(A):
    """Item class.

    Parameters:
        markdown: Object markdown
    """

    markdown: str = ""

    def set_name(self, name: str):
        """Sets name in upper case."""
        self.name = name.upper()


@dataclass
class D(A):
    """Item class.

    Parameters:
        markdown: Object markdown
    """

    markdown: str = ""

    def set_name(self, name: str):
        """Sets name in upper case."""
        self.name = name.upper()


@pytest.fixture()
def a():
    return mkapi.get_node(A)


@pytest.fixture()
def b():
    return mkapi.get_node(B)


@pytest.fixture()
def c():
    return mkapi.get_node(C)


@pytest.fixture()
def d():
    return mkapi.get_node(D)


def test_is_complete(a, b):
    assert is_complete(a)
    assert not is_complete(b)


@pytest.mark.parametrize("name", ["Parameters", "Attributes"])
def test_get_params(a, b, name):
    a_doc_params, a_sig_params = get_params(a, name)
    assert len(a_doc_params) == 2
    assert len(a_sig_params) == 2

    b_doc_params, b_sig_params = get_params(b, name)
    assert len(b_doc_params) == 1 if name == 'Parameters' else 3
    assert len(b_sig_params) == 3


def test_inherit(b):
    inherit(b)
    assert is_complete(b)


@pytest.mark.parametrize("name", ["Parameters", "Attributes"])
def test_get_params_after(b, name):
    b_doc_params, b_sig_params = get_params(b, name)
    assert len(b_doc_params) == 3
    assert len(b_sig_params) == 3


def test_inheritance_members(b):
    item = b.members[0].docstring["Parameters"].items[0]
    assert item.name == "name"
    assert item.type.name == "str"


def test_inheritance_parameters(c):
    doc_params, sig_params = get_params(c, "Attributes")
    assert len(doc_params) == 0
    assert len(sig_params) == 3
    inherit(c, strict=True)
    doc_params, sig_params = get_params(c, "Attributes")
    assert len(doc_params) == 3


def test_inheritance_by_filters(d):
    doc_params, sig_params = get_params(d, "Attributes")
    assert len(doc_params) == 0
    assert len(sig_params) == 3
    inherit_by_filters(d, ['inherit'])
    doc_params, sig_params = get_params(d, "Parameters")
    assert len(doc_params) == 3
    doc_params, sig_params = get_params(d, "Attributes")
    assert len(doc_params) == 2
    inherit_by_filters(d, ['strict'])
    doc_params, sig_params = get_params(d, "Parameters")
    assert len(doc_params) == 3
    doc_params, sig_params = get_params(d, "Attributes")
    assert len(doc_params) == 3
