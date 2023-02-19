from hamilton import node
from hamilton.function_modifiers.metadata import base, tag


def should_cache(n: node.Node) -> bool:
    """Whether this node has been decorated with caching

    :param n: Node to cache
    :return: Whetehr or not the node has been decorated with `@checkpoint`
    """
    return n.tags.get(checkpoint.CHECKPOINT_TAG, False)


class checkpoint(tag):
    CHECKPOINT_TAG = "hamilton.checkpoint"

    def __init__(self, target: base.TargetType = None):
        """Initializes a checkpoint decorator. All this does is decorate the node with
        a tag saying that we'll checkpoint it.

        :param target: Which node outputted by this to target. By default (None), this
        will checkpoint any "non-final" node (sinks) in the set of nodes produced by this function.

        """
        super(checkpoint, self).__init__(
            target_=target, is_internal_user_=True, **{checkpoint.CHECKPOINT_TAG: True}
        )
