import wrapt

"""Example to represent metaflow's hello world. 
This is pretty awkward as it relies on side-effects whereas Hamilton is a different computational model.
Hence these nice decorators to demonstrate that we can bake side-effects into the framework as well.

A cleaner way to do this would be a custom executor that prints out everything.
"""


@wrapt.decorator
def _print(wrapped, instance, args, kwargs):
    out = wrapped(*args, **kwargs)
    print(out)
    return out

@_print
def start() -> str:
    return 'HelloFlow is starting'


@_print
def hello(start: str) -> str:
    return 'Hamilton (masquerading as metaflow) says: "Hi!"'


@_print
def end(hello: str) -> str:
    return 'Hamilton running HelloFlow is all done.'
