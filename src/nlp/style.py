from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional
import re

_KEYVAL = re.compile(r"\s*([^:]+)\s*:\s*(.+)\s*$")

def _parse_props(s: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = _KEYVAL.match(chunk)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            props[k] = v
    return props

def _strip_quotes(v: str) -> str:
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        return v[1:-1]
    return v

@dataclass
class Style:
    # Input
    style_string: str

    # Computed fields
    size: int = field(init=False)
    family: Optional[str] = field(init=False, default=None)
    weight: Tuple[str, ...] = field(init=False, default_factory=tuple)

    def __post_init__(self) -> None:
        props = _parse_props(self.style_string)

        # font-size: e.g., "11pt" (tolerate whitespace)
        size_raw = props.get("font-size")
        if not size_raw:
            raise ValueError("font-size missing")
        m = re.search(r"(\d+)\s*pt\b", size_raw)
        if m:
            self.size = int(m.group(1))
        else:
            # fallback if someone passed a bare integer string
            self.size = int(re.search(r"\d+", size_raw).group(0))

        # font-family: e.g., "Times" (possibly quoted)
        fam = props.get("font-family")
        if fam:
            self.family = _strip_quotes(fam)

        # font-style or font-weight: e.g., "bold italic" (often quoted)
        style_or_weight = props.get("font-style") or props.get("font-weight") or ""
        style_or_weight = _strip_quotes(style_or_weight)
        tokens = [t.lower() for t in re.split(r"[\s,]+", style_or_weight) if t]
        self.weight = tuple(tokens)

    # Allow: 'bold' in style
    def __contains__(self, token: str) -> bool:
        return token.lower() in self.weight
