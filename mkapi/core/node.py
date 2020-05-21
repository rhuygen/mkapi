import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, List, Optional

import mkapi.core.markdown
from mkapi.core.docstring import Docstring, parse_docstring
from mkapi.core.signature import Signature

ISFUNCTIONS = {}
for x in dir(inspect):
    if x.startswith("is"):
        name = x[2:]
        if name not in ["routine", "builtin", "code"]:
            ISFUNCTIONS[name] = getattr(inspect, x)


def get_kind(kinds: List[str]) -> str:
    if "generatorfunction" in kinds:
        return "generator"
    return kinds[-1]


@dataclass
class Node:
    obj: Any = field(repr=False)
    name: str
    depth: int
    prefix: str
    kinds: List[str]
    lineno: int
    signature: Optional[Signature]
    docstring: Docstring
    members: List["Node"]

    def __post_init__(self):
        self.kind = get_kind(self.kinds)
        if self.name.startswith("__"):
            self.type = "special"
        elif self.name.startswith("_"):
            self.type = "private"
        else:
            self.type = "normal"

    def __iter__(self):
        yield from self.docstring
        for member in self.members:
            yield from member

    def get_markdown(self):
        markdowns = []
        for x in self:
            markdowns.append(mkapi.core.markdown.convert(x.markdown))
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str):
        for x, html in zip(self, html.split("<!-- mkapi:sep -->")):
            x.set_html(html.strip())


def get_kinds(obj) -> List[str]:
    kinds = []
    if hasattr(obj, "__dataclass_fields__"):
        return ["dataclass"]
    for kind, func in ISFUNCTIONS.items():
        if func(obj):
            kinds.append(kind)
    if "function" in kinds and "generatorfunction" not in kinds:
        if "self" in inspect.signature(obj).parameters:
            kinds = ["method"]
    if isinstance(obj, property):
        if obj.fset:
            kinds.append("readwrite_property")
        else:
            kinds.append("readonly_property")
    return kinds


def get_lineno(obj) -> int:
    if isinstance(obj, property):
        obj = obj.fget
    return inspect.getsourcelines(obj)[1]


def filter(obj) -> bool:
    if not get_kinds(obj):
        return False
    try:
        get_lineno(obj)
    except TypeError:
        return False
    else:
        return True


def walk(name, obj, prefix="", depth=0) -> Node:
    kinds = get_kinds(obj)
    lineno = get_lineno(obj)
    docstring = parse_docstring(obj)
    if prefix:
        next_prefix = ".".join([prefix, name])
    else:
        next_prefix = name
    members = []
    if not isinstance(obj, property):
        for x in inspect.getmembers(obj, filter):
            member = walk(*x, prefix=next_prefix, depth=depth + 1)
            if member.type == "normal" or member.docstring:
                members.append(member)
        members.sort(key=lambda x: x.lineno)
    if callable(obj):
        signature = Signature(obj)
    else:
        signature = None  # type:ignore
    node = Node(obj, name, depth, prefix, kinds, lineno, signature, docstring, members)
    if isinstance(obj, property):
        if docstring.sections:
            node.type = docstring.sections[0].type
        else:
            node.type = ""
    return node


def get_attr(path: str):
    module_path, _, name = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, name)


def get_object(name: str):
    try:
        return get_attr(name)
    except (ModuleNotFoundError, AttributeError):
        return importlib.import_module(name)


def get_node(name: str) -> Node:
    obj = get_object(name)
    node = walk(name, obj)
    return node
