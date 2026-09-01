"""ktools-json -- official JSON node pack (OC-001).

Exposes the JSON split capability's public direct API, its workflow nodes and
its error taxonomy.
"""

from .api import (
    InvalidJsonDocumentError,
    JsonSourceError,
    read_json_document,
    split_json,
)
from .capability import (
    EmptyMainListError,
    InvalidModeError,
    InvalidPartsError,
    InvalidTargetSizeError,
    JsonSplitError,
    NoMainListError,
    SplitOptions,
    SplitPlan,
    find_largest_list,
    json_path_label,
    make_options,
    replace_at_path,
    split_json_document,
    split_evenly,
)
from .node import register_nodes
from .writer import (
    OutputCollisionError,
    SplitResult,
    JsonPart,
    split_and_write,
)

__all__ = [
    # capability (single owner)
    "EmptyMainListError",
    "InvalidModeError",
    "InvalidPartsError",
    "InvalidTargetSizeError",
    "JsonSplitError",
    "NoMainListError",
    "SplitOptions",
    "SplitPlan",
    "find_largest_list",
    "json_path_label",
    "make_options",
    "replace_at_path",
    "split_json_document",
    "split_evenly",
    # writer (shared orchestration)
    "JsonPart",
    "OutputCollisionError",
    "SplitResult",
    "split_and_write",
    # direct API
    "InvalidJsonDocumentError",
    "JsonSourceError",
    "read_json_document",
    "split_json",
    # node pack registration
    "register_nodes",
]