# tests/test_proxy_pool_extra.py
import pytest
from src.proxy_pool.proxy_pool import ProxyPool

def test_add_none_and_empty_string():
    pool = ProxyPool()
    # 添加 None 和 空字符串（实现允许任意可哈希对象）
    pool.add(None)
    pool.add("")
    assert pool.size() == 2
    # get 应该轮询返回 None 和 ""（顺序与添加顺序一致）
    first = pool.get()
    second = pool.get()
    assert {first, second} == {None, ""}

def test_get_single_proxy_cycles():
    pool = ProxyPool()
    pool.add("http://1.1.1.1:1")
    assert pool.size() == 1
    # 多次 get 都应返回同一个代理（轮询但只有一个元素）
    assert pool.get() == "http://1.1.1.1:1"
    assert pool.get() == "http://1.1.1.1:1"

def test_mark_bad_then_remove_then_add():
    pool = ProxyPool(["p1", "p2", "p3"])
    # 标记 p2 为 bad，会从队列移除
    pool.mark_bad("p2")
    assert "p2" not in pool.all_proxies()
    # 再 remove 一个不存在的代理（不应抛出）
    pool.remove("nonexistent")
    # 重新添加 p2，应当出现在队列末尾
    pool.add("p2")
    assert pool.all_proxies()[-1] == "p2"

def test_duplicate_after_mark_bad_unmarks_and_places_at_end():
    pool = ProxyPool(["a", "b"])
    pool.mark_bad("a")
    assert "a" not in pool.all_proxies()
    # 再次 add 相同代理，应当取消 bad 标记并加入队列末尾
    pool.add("a")
    assert "a" in pool.all_proxies()
    assert pool.all_proxies()[-1] == "a"

def test_remove_clears_bad_flag():
    pool = ProxyPool(["x", "y"])
    pool.mark_bad("x")
    # x 被标记为 bad 并移除
    assert "x" not in pool.all_proxies()
    # remove 应该清除 bad 标记（即使不在队列中）
    pool.remove("x")
    # 重新 add 应该成功并出现在末尾
    pool.add("x")
    assert pool.all_proxies()[-1] == "x"
