# -*- coding: utf-8 -*-
"""
补充对 src/core/safe_query.py 的单元测试，覆盖各种异常分支与正常分支。
目标函数：safe_ident, safe_order_by, safe_query, bulk_query
"""

import pytest
import importlib

# 明确以模块方式导入，避免 package-level 导出造成的歧义
sq = importlib.import_module("core.safe_query")


# -------------------------
# safe_ident
# -------------------------
def test_safe_ident_valid():
    assert sq.safe_ident("name") == "name"
    assert sq.safe_ident("a1_b2") == "a1_b2"


def test_safe_ident_invalid_type():
    with pytest.raises(ValueError):
        sq.safe_ident(123)


def test_safe_ident_invalid_name():
    with pytest.raises(ValueError):
        sq.safe_ident("1abc")
    with pytest.raises(ValueError):
        sq.safe_ident("has-dash")


# -------------------------
# safe_order_by
# -------------------------
def test_safe_order_by_valid():
    assert sq.safe_order_by("col") == "col"
    assert sq.safe_order_by("col ASC") == "col ASC"
    assert sq.safe_order_by("col desc") == "col desc"


def test_safe_order_by_invalid_type():
    with pytest.raises(ValueError):
        sq.safe_order_by(None)


def test_safe_order_by_invalid_expr():
    with pytest.raises(ValueError):
        sq.safe_order_by("col1, col2")
    with pytest.raises(ValueError):
        sq.safe_order_by("col; DROP TABLE users")


# -------------------------
# safe_query
# -------------------------
def test_safe_query_valid():
    sql = "SELECT * FROM t WHERE id = :id AND name = :name"
    params = {"id": 1, "name": "x"}
    out_sql, out_params = sq.safe_query(sql, params)
    assert out_sql == sql
    assert out_params == params


def test_safe_query_sql_not_string():
    with pytest.raises(ValueError):
        sq.safe_query(None, {})


def test_safe_query_params_not_dict():
    with pytest.raises(ValueError):
        sq.safe_query("SELECT 1", None)
    with pytest.raises(ValueError):
        sq.safe_query("SELECT 1", ["not", "dict"])


def test_safe_query_semicolon_in_sql():
    with pytest.raises(ValueError):
        sq.safe_query("SELECT * FROM t; DROP TABLE t", {"a": 1})


def test_safe_query_missing_params():
    sql = "SELECT :a, :b"
    with pytest.raises(KeyError):
        sq.safe_query(sql, {"a": 1})


# -------------------------
# bulk_query
# -------------------------
def test_bulk_query_valid():
    sql = "INSERT INTO t (a, b) VALUES (:a, :b)"
    items = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    out_sql, out_items = sq.bulk_query(sql, items)
    assert out_sql == sql
    assert out_items == items


def test_bulk_query_sql_not_string():
    with pytest.raises(ValueError):
        sq.bulk_query(None, [{"a": 1}])


def test_bulk_query_items_not_list():
    with pytest.raises(ValueError):
        sq.bulk_query("INSERT :a", None)
    with pytest.raises(ValueError):
        sq.bulk_query("INSERT :a", "not-a-list")


def test_bulk_query_items_empty():
    with pytest.raises(ValueError):
        sq.bulk_query("INSERT :a", [])


def test_bulk_query_item_not_dict():
    with pytest.raises(ValueError):
        sq.bulk_query("INSERT :a", [123])


def test_bulk_query_item_missing_params():
    sql = "INSERT INTO t (a, b) VALUES (:a, :b)"
    items = [{"a": 1}, {"a": 2, "b": 3}]
    with pytest.raises(KeyError):
        sq.bulk_query(sql, items)
