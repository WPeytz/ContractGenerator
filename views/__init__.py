from dataclasses import dataclass
from typing import Callable, Dict

from . import fratraedelse, termination_memo


@dataclass(frozen=True)
class ViewEntry:
    key: str
    label: str
    render: Callable[[], None]


VIEW_REGISTRY: Dict[str, ViewEntry] = {
    "fratraedelse": ViewEntry(
        key="fratraedelse",
        label="Fratrædelsesaftale",
        render=fratraedelse.render,
    ),
    "termination_memo": ViewEntry(
        key="termination_memo",
        label="Termination Memo",
        render=termination_memo.render,
    ),
}
