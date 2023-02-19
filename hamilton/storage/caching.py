import abc
import collections
import uuid
from typing import Any, Dict, List

from hamilton import graph
from hamilton.base import node
from hamilton.function_modifiers import caching


class Cache(abc.ABC):
    def __init__(self, run_id: str, filterlist: List[str] = None):
        """Creates a checkpoint with a run_id.
        The run_id is used to identify the run that you're running.
        Note that if we're doing smarter caching (E.G. fingerprinting), we may want to
        make the run_id optional, or create a class that does not use it.

        :param run_id: Run ID to
        :param filterlist: Cache items not to retrieve.
        """
        self._run_id = run_id
        self.filterlist = set(filterlist) if filterlist is not None else set()

    @property
    def run_id(self) -> str:
        """Gets the run id.

        :return: The run id.
        """
        return self._run_id

    def generate_run_id(self, prefix: str = None) -> str:
        """Generates a run id for your first time using a run.
        This is a convenience function -- you can pass any run id you want.

        :return:
        """
        return f"{prefix + '-' if prefix else ''}{uuid.uuid4().hex}"

    def should_save(self, node_: node.Node) -> bool:
        """Whether this caching mechanism should cache this node.

        :paramnode_: Node that we're caching
        :return: Whether we should cache this.
        """

        return caching.should_cache(node_)

    def should_load(self, node_: node.Node) -> bool:
        """Whether this caching mechanism should load this node.

        :paramnode_: Node that we're loading
        :return: Whether we should load this from cache.
        """
        return self.should_save(node_) and node_.name not in self.filterlist

    @abc.abstractmethod
    def can_save(self, result: Any, node_: node.Node) -> bool:
        """Whether we can save this result.

        :param result: Result saved by the node
        :param node_: Node saving the result
        :return: True if we can save this result, False otherwise.
        """
        pass

    @abc.abstractmethod
    def is_available(self, node_: node.Node) -> bool:
        """Whether the cache has a key for the node
        :paramnode_: Node to check
        """
        pass

    @abc.abstractmethod
    def save(self, node_: node.Node, result: Any):
        """Writes the result to the cache

        :param node_: Node that produced this result
        :param result: Result to write
        """
        pass

    @abc.abstractmethod
    def load(self, node_: node.Node) -> Any:
        """Loads the result from the cache

        :paramnode_: Node to load
        :return: Result loaded from the cache
        """
        pass

    def save_bulk(self, results: Dict[node.Node, Any]):
        """Saves all cache items in bulk to the cache.
        By default, this is just an iteration, but we override for more
        efficient implementations.

        :param results: Results to save from an execution
        """
        for node_, result in results.items():
            if self.should_save(node_) and self.can_save(result, node_):
                self.save(node_, result)

    def retrieve_cache(self, fn_graph: graph.FunctionGraph) -> Dict[str, Any]:
        """Goes through the graph and loads any nodes that should be loaded from cache.
        Note that this currently loads everything, even if one node is solely upstream of
        another node. We will likely add graph-walking algorithms to only load the specific nodes.

        Furthermore, this is the capability that a more intelligent caching mechanism would use
        to determine whether something should be loaded from cache.
        We may want to update it to take in more runtime parameters (inputs, etc...) to do
        fingerprinting/hashing of the chain of results.

        :param fn_graph:
        :return:
        """
        cache = {}
        for node_name, node_ in fn_graph.nodes.items():
            if self.should_load(node_) and self.is_available(node_):
                cache[node_name] = self.load(node_)
        return cache

    @abc.abstractmethod
    def cleanup(self):
        pass


class NoOpCache(Cache):
    """A checkpoint that does nothing. This is a cheap way to disabling caching."""

    def __init__(self):
        super().__init__("")

    def can_save(self, result: Any, node_: node.Node) -> bool:
        return False

    def is_available(self, node_: node.Node) -> bool:
        return False

    def save(self, node_: node.Node, result: Any):
        pass

    def load(self, node_: node.Node) -> Any:
        return None

    def cleanup(self):
        pass


# Quick trick to get an in memory cache that function globally
# This is more meant for testing, but could easily be used for long-running operations
# E.G. API calls, etc...
in_memory_cache = collections.defaultdict(dict)


class InMemoryCache(Cache):
    def __init__(self, run_id: str, filterlist: List[str] = None):
        super(InMemoryCache, self).__init__(run_id=run_id, filterlist=filterlist)
        global in_memory_cache
        if run_id not in in_memory_cache:
            in_memory_cache[run_id] = {}
        self.cache = in_memory_cache[run_id]

    def can_save(self, result: Any, node_: node.Node) -> bool:
        return True

    def is_available(self, node_: node.Node) -> bool:
        return node_.name in self.cache

    def save(self, node_: node.Node, result: Any):
        self.cache[node_.name] = result

    def load(self, node_: node.Node) -> Any:
        return self.cache[node_.name]

    def cleanup(self):
        del in_memory_cache[self.run_id]
