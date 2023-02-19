import pytest

import tests.resources.checkpointing
from hamilton import driver, graph
from hamilton.storage import caching


def test_retrieve_cache():
    fn_graph = graph.FunctionGraph(tests.resources.checkpointing, config={})
    cache = caching.InMemoryCache(run_id="test_retrieve_cache")
    cache_actualized = cache.retrieve_cache(fn_graph)
    # Nothing in this yet
    assert len(cache_actualized) == 0
    cache.save(fn_graph.nodes["op_to_checkpoint"], 100)
    cache = cache.retrieve_cache(fn_graph)
    assert cache["op_to_checkpoint"] == 100


def test_retrieve_cache_with_filterlist():
    fn_graph = graph.FunctionGraph(tests.resources.checkpointing, config={})
    cache = caching.InMemoryCache(
        run_id="test_retrieve_cache_with_filterlist", filterlist=["op_to_checkpoint"]
    )
    cache_actualized = cache.retrieve_cache(fn_graph)
    # Nothing in this yet
    assert len(cache_actualized) == 0
    cache.save(fn_graph.nodes["op_to_checkpoint"], 100)
    cache = cache.retrieve_cache(fn_graph)
    assert len(cache) == 0


def test_cache_with_driver():
    dr = driver.Driver({}, tests.resources.checkpointing)
    cache = caching.InMemoryCache(run_id="test_cache_with_driver")
    # cache everything once
    op_count = tests.resources.checkpointing.op_count_for_testing
    dr.execute([var.name for var in dr.list_available_variables()], cache=cache)
    assert tests.resources.checkpointing.op_count_for_testing == op_count + 1
    op_count = tests.resources.checkpointing.op_count_for_testing
    cache_actualized = cache.retrieve_cache(dr.graph)
    assert len(cache_actualized) == 3  # One for each checkpointed note
    dr.raw_execute(["third_op_to_checkpoint"], cache=cache)
    # Op count has not been incremented as we used the cache
    assert tests.resources.checkpointing.op_count_for_testing == op_count


def test_cache_with_driver_that_could_break():
    dr = driver.Driver({"broken": True}, tests.resources.checkpointing)
    cache = caching.InMemoryCache(run_id="test_cache_with_driver_that_could_break")
    # cache everything once
    with pytest.raises(Exception):
        dr.execute([var.name for var in dr.list_available_variables()], cache=cache)
    assert "op_to_checkpoint" in cache.retrieve_cache(dr.graph)
