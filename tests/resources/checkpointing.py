from hamilton import function_modifiers

op_count_for_testing = 0


@function_modifiers.checkpoint()
def op_to_checkpoint() -> int:
    return 1


def op_to_forget(op_to_checkpoint: int) -> int:
    return op_to_checkpoint + 1


@function_modifiers.checkpoint()
def second_op_to_checkpoint() -> int:
    global op_count_for_testing
    op_count_for_testing += 1
    return 10


@function_modifiers.config.when_not(broken=True)
def second_op_to_forget(op_to_checkpoint: int) -> int:
    return op_to_checkpoint + 1


@function_modifiers.config.when(broken=True)
def second_op_to_forget__broken(op_to_checkpoint: int) -> int:
    raise Exception("broken")


@function_modifiers.checkpoint()
def third_op_to_checkpoint(second_op_to_checkpoint: int) -> int:
    return second_op_to_checkpoint + 1
