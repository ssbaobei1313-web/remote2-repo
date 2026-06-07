import re
from typing import Tuple, Dict, List, Any

_ident_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_order_by_re = re.compile(
    r'^[A-Za-z_][A-Za-z0-9_]*(?:\s+(?:ASC|DESC))?$', re.IGNORECASE
)

def safe_ident(name: str) -> str:
    if not isinstance(name, str) or not _ident_re.match(name):
        raise ValueError("invalid identifier")
    return name

def safe_order_by(expr: str) -> str:
    if not isinstance(expr, str):
        raise ValueError("order by must be a string")
    expr = expr.strip()
    if not _order_by_re.match(expr):
        raise ValueError("invalid order by")
    return expr

def safe_query(sql: str, params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    if not isinstance(sql, str):
        raise ValueError("sql must be a string")
    if not isinstance(params, dict):
        raise ValueError("params must be a dict")
    if ';' in sql:
        raise ValueError("possible injection in sql")
    keys = set(re.findall(r':([A-Za-z_][A-Za-z0-9_]*)', sql))
    missing = keys - set(params.keys())
    if missing:
        raise KeyError(f"missing params: {missing}")
    return sql, params

def bulk_query(sql: str, items: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    if not isinstance(sql, str):
        raise ValueError("sql must be a string")
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    if not items:
        raise ValueError("items list is empty")
    keys = set(re.findall(r':([A-Za-z_][A-Za-z0-9_]*)', sql))
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise ValueError("each item must be a dict")
        missing = keys - set(it.keys())
        if missing:
            raise KeyError(f"item {i} missing params: {missing}")
    return sql, items
