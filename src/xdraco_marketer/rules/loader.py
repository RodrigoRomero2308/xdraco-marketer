from __future__ import annotations

from typing import Any

import yaml
from pydantic import TypeAdapter

from xdraco_marketer.rules.ast import RuleExpr

_rule_adapter = TypeAdapter(RuleExpr)


def load_rule_from_dict(data: dict[str, Any]) -> RuleExpr:
    return _rule_adapter.validate_python(data)


def load_rule_from_yaml_text(text: str) -> RuleExpr:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError("La regla YAML debe ser un objeto en la raíz")
    return load_rule_from_dict(raw)
