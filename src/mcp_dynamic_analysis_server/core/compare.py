from __future__ import annotations

from typing import Dict, List, Tuple

from ..models.findings import Finding


def compare_findings(
    base: List[Finding],
    new: List[Finding],
) -> Tuple[List[Finding], List[Finding], List[Finding]]:
    base_map: Dict[str, Finding] = {f.signature: f for f in base}
    new_map: Dict[str, Finding] = {f.signature: f for f in new}

    fixed = [base_map[sig] for sig in base_map.keys() - new_map.keys()]
    added = [new_map[sig] for sig in new_map.keys() - base_map.keys()]
    persistent = [new_map[sig] for sig in new_map.keys() & base_map.keys()]

    return fixed, added, persistent
