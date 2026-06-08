# Place at tests/test_proxy_pool.py

import pytest
from src.proxy_pool.proxy_pool import ProxyPool


@pytest.fixture
def sample_proxies():
    return [
        "http://10.0.0.1:8000",
        "http://10.0.0.2:8000",
        "http://10.0.0.3:8000",
    ]


def test_add_and_size(sample_proxies):
    pool = ProxyPool()
    assert pool.size() == 0
    pool.add(sample_proxies[0])
    assert pool.size() == 1
    pool.add(sample_proxies[0])  # duplicate add should not increase size
    assert pool.size() == 1
    pool.add(sample_proxies[1])
    assert pool.size() == 2
    assert sample_proxies[0] in pool.all_proxies()
    assert sample_proxies[1] in pool.all_proxies()


def test_round_robin_order(sample_proxies):
    pool = ProxyPool(sample_proxies)
    # first three gets should cycle through proxies in order
    first = pool.get()
    second = pool.get()
    third = pool.get()
    assert [first, second, third] == sample_proxies
    # next get should return the first again (round-robin)
    fourth = pool.get()
    assert fourth == sample_proxies[0]


def test_mark_bad_removes_from_rotation(sample_proxies):
    pool = ProxyPool(sample_proxies)
    assert pool.size() == 3
    pool.mark_bad(sample_proxies[1])
    assert pool.size() == 2
    assert sample_proxies[1] not in pool.all_proxies()
    # ensure round-robin still works with remaining proxies
    got = [pool.get(), pool.get()]
    assert set(got) == {sample_proxies[0], sample_proxies[2]}


def test_remove_and_readd(sample_proxies):
    pool = ProxyPool(sample_proxies)
    pool.remove(sample_proxies[0])
    assert pool.size() == 2
    assert sample_proxies[0] not in pool.all_proxies()
    # re-add should put it at the end
    pool.add(sample_proxies[0])
    assert pool.size() == 3
    assert pool.all_proxies()[-1] == sample_proxies[0]


def test_mark_bad_nonexistent_proxy_is_noop(sample_proxies):
    pool = ProxyPool(sample_proxies)
    pool.mark_bad("http://nonexistent:1234")  # should not raise
    assert pool.size() == 3


def test_get_on_empty_pool_returns_none():
    pool = ProxyPool()
    assert pool.get() is None


def test_clear_resets_pool(sample_proxies):
    pool = ProxyPool(sample_proxies)
    pool.clear()
    assert pool.size() == 0
    assert pool.all_proxies() == []


def test_readding_marked_bad_proxy_unmarks_it(sample_proxies):
    pool = ProxyPool(sample_proxies)
    pool.mark_bad(sample_proxies[0])
    assert sample_proxies[0] not in pool.all_proxies()
    pool.add(sample_proxies[0])  # should unmark and re-add
    assert sample_proxies[0] in pool.all_proxies()
    assert pool.size() == 3
