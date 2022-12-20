from collections.abc import MutableMapping
from typing import Any


def flatten_dict(
    d: MutableMapping[Any, Any],
    parent_key: str = "",
    sep: str = ".",
    include_parents: bool = False,
) -> MutableMapping[Any, Any]:
    items: list[Any] = []
    for k, v in d.items():
        if include_parents:
            new_key = parent_key + sep + k if parent_key else k
        else:
            new_key = k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)
