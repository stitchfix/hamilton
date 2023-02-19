import pandas as pd

from hamilton import function_modifiers
from hamilton.function_modifiers import extract_columns


@extract_columns("a", "b")
@function_modifiers.checkpoint(target="slow_loading_data")
def slow_loading_data() -> pd.DataFrame:
    """Data that takes a while to load"""
    import time

    # Expensive
    time.sleep(10)
    return pd.DataFrame.from_records({"a": [1], "b": [2]})


def a_plus_b(a: pd.Series, b: pd.Series) -> int:
    return a + b


def slow_computation(a_plus_b: pd.Series) -> pd.Series:
    import time

    # Expensive
    time.sleep(10)
    return a_plus_b + 1


def computation_that_could_break(a_plus_b: pd.Series) -> pd.Series:
    return a_plus_b + 1
