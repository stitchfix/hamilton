# Decorators

While the 1:1 mapping of column -> function implementation is powerful, we've implemented a few decorators to promote
business-logic reuse. The decorators we've defined are as follows
(source can be found in [function_modifiers](hamilton/function_modifiers.py)):

## @parameterized
Expands a single function into n, each of which corresponds to a function in which the parameter value is replaced by
that *specific value*.
```python
import pandas as pd
from hamilton.function_modifiers import parametrized
import internal_package_with_logic

ONE_OFF_DATES = {
     #output name        # doc string               # input value to function
    ('D_ELECTION_2016', 'US Election 2016 Dummy'): '2016-11-12',
    ('SOME_OUTPUT_NAME', 'Doc string for this thing'): 'value to pass to function',
}
            # parameter matches the name of the argument in the function below
@parametrized(parameter='one_off_date', assigned_output=ONE_OFF_DATES)
def create_one_off_dates(date_index: pd.Series, one_off_date: str) -> pd.Series:
    """Given a date index, produces a series where a 1 is placed at the date index that would contain that event."""
    one_off_dates = internal_package_with_logic.get_business_week(one_off_date)
    return internal_package_with_logic.bool_to_int(date_index.isin([one_off_dates]))
```
We see here that `parameterized` allows you keep your code DRY by reusing the same function to create multiple
distinct outputs. The _parameter_ key word argument has to match one of the arguments in the function. The rest of
the arguments are pulled from outside the DAG. The _assigned_output_ key word argument takes in a dictionary of
tuple(Output Name, Documentation string) -> value.

## @parameterized_inputs
Expands a single function into _n_, each of which corresponds to a function in which the parameters specified are mapped
to the specified inputs. Note this decorator and `@parametrized` are quite similar, except that
the input here is another DAG node(s), i.e. column/input, rather than a specific scalar/static value.

```python
import pandas as pd
from hamilton.function_modifiers import parameterized_inputs


@parameterized_inputs(
    D_ELECTION_2016_shifted=dict(one_off_date='D_ELECTION_2016'),
    SOME_OUTPUT_NAME=dict(one_off_date='SOME_INPUT_NAME')
)
def date_shifter(one_off_date: pd.Series) -> pd.Series:
    """{one_off_date} shifted by 1 to create {output_name}"""
    return one_off_date.shift(1)

```
We see here that `parameterized_inputs` allows you to keep your code DRY by reusing the same function to create multiple
distinct outputs. The key word arguments passed have to have the following structure:
> OUTPUT_NAME = Mapping of function argument to input that should go into it.

So in the example, `D_ELECTION_2016_shifted` is an _output_ that will correspond to replacing `one_off_date` with `D_ELECTION_2016`.
Then similarly `SOME_OUTPUT_NAME` is an _output_ that will correspond to replacing `one_off_date` with `SOME_INPUT_NAME`.
The documentation for both uses the same function doc and will replace values that are templatized with the input
parameter names, and the reserved value `output_name`.

To help visualize what the above is doing, it is equivalent to writing the following two function definitions:

```python
def D_ELECTION_2016_shifted(D_ELECTION_2016: pd.Series) -> pd.Series:
    """D_ELECTION_2016 shifted by 1 to create D_ELECTION_2016_shifted"""
    return D_ELECTION_2016.shift(1)

def SOME_OUTPUT_NAME(SOME_INPUT_NAME: pd.Series) -> pd.Series:
    """SOME_INPUT_NAME shifted by 1 to create SOME_OUTPUT_NAME"""
    return SOME_INPUT_NAME.shift(1)
```

*Note*: that the different input variables must all have compatible types with the original decorated input variable.

## @extract_columns
This works on a function that outputs a dataframe, that we want to extract the columns from and make them individually
available for consumption. So it expands a single function into _n functions_, each of which take in the output dataframe
 and output a specific column as named in the `extract_columns` decorator.
```python
import pandas as pd
from hamilton.function_modifiers import extract_columns

@extract_columns('fiscal_date', 'fiscal_week_name', 'fiscal_month', 'fiscal_quarter', 'fiscal_year')
def fiscal_columns(date_index: pd.Series, fiscal_dates: pd.DataFrame) -> pd.DataFrame:
    """Extracts the fiscal column data.
    We want to ensure that it has the same spine as date_index.
    :param fiscal_dates: the input dataframe to extract.
    :return:
    """
    df = pd.DataFrame({'date_index': date_index}, index=date_index.index)
    merged = df.join(fiscal_dates, how='inner')
    return merged
```
Note: if you have a list of columns to extract, then when you call `@extract_columns` you should call it with an
asterisk like this:
```python
import pandas as pd
from hamilton.function_modifiers import extract_columns

@extract_columns(*my_list_of_column_names)
def my_func(...) -> pd.DataFrame:
   """..."""
```

## @does
`@does` is a decorator that essentially allows you to run a function over all the input parameters. So you can't pass
any old function to `@does`, instead the function passed has to take any amount of inputs and process them all in the same way.
```python
import pandas as pd
from hamilton.function_modifiers import does
import internal_package_with_logic

def sum_series(**series: pd.Series) -> pd.Series:
    """This function takes any number of inputs and sums them all together."""
    ...

@does(sum_series)
def D_XMAS_GC_WEIGHTED_BY_DAY(D_XMAS_GC_WEIGHTED_BY_DAY_1: pd.Series,
                              D_XMAS_GC_WEIGHTED_BY_DAY_2: pd.Series) -> pd.Series:
    """Adds D_XMAS_GC_WEIGHTED_BY_DAY_1 and D_XMAS_GC_WEIGHTED_BY_DAY_2"""
    pass

@does(internal_package_with_logic.identity_function)
def copy_of_x(x: pd.Series) -> pd.Series:
    """Just returns x"""
    pass
```
The example here is a function, that all that it does, is sum all the parameters together. So we can annotate it with
the `@does` decorator and pass it the `sum_series` function.
The `@does` decorator is currently limited to just allow functions that consist only of one argument, a generic `**kwargs`.

## @model
`@model` allows you to abstract a function that is a model. You will need to implement models that make sense for
your business case. Reach out if you need examples.

Under the hood, they're just DAG nodes whose inputs are determined by a configuration parameter. A model takes in
two required parameters:
1. The class it uses to run the model. If external to Stitch Fix you will need to write your own, else internally
   see the internal docs for this. Basically the class defined determines what the function actually does.
2. The configuration key that determines how the model functions. This is just the name of a configuration parameter
   that stores the way the model is run.

The following is an example usage of `@model`:

```python
import pandas as pd
from hamilton.function_modifiers import model
import internal_package_with_logic

@model(internal_package_with_logic.GLM, 'model_p_cancel_manual_res')
# This runs a GLM (Generalized Linear Model)
# The associated configuration parameter is 'model_p_cancel_manual_res',
# which points to the results of loading the model_p_cancel_manual_res table
def prob_cancel_manual_res() -> pd.Series:
    pass
```

`GLM` here is not part of the hamilton framework, and instead a user defined model.

Models (optionally) accept a `output_column` parameter -- this is specifically if the name of the function differs
from the output column that it should represent. E.G. if you use the model result as an intermediate object, and manipulate
it all later. At Stitch Fix this is necessary because various dependent columns that a model queries
(e.g. `MULTIPLIER_...` and `OFFSET_...`) are derived from the model's name.

## @config.when*

`@config.when` allows you to specify different implementations depending on configuration parameters.

The following use cases are supported:
1. A column is present for only one value of a config parameter -- in this case, we define a function only once,
   with a `@config.when`
```python
    import pandas as pd
    from hamilton.function_modifiers import config

    # signups_parent_before_launch is only present in the kids business line
    @config.when(business_line='kids')
    def signups_parent_before_launch(signups_from_existing_womens_tf: pd.Series) -> pd.Series:
        """TODO:
        :param signups_from_existing_womens_tf:
        :return:
        """
        return signups_from_existing_womens_tf
```
2. A column is implemented differently for different business inputs, e.g. in the case of Stitch Fix gender intent.
```python
    import pandas as pd
    from hamilton.function_modifiers import config, model
    import internal_package_with_logic

    # Some 21 day autoship cadence does not exist for kids, so we just return 0s
    @config.when(gender_intent='kids')
    def percent_clients_something__kids(date_index: pd.Series) -> pd.Series:
        return pd.Series(index=date_index.index, data=0.0)

    # In other business lines, we have a model for it
    @config.when_not(gender_intent='kids')
    @model(internal_package_with_logic.GLM, 'some_model_name', output_column='percent_clients_something')
    def percent_clients_something_model() -> pd.Series:
        pass
```
Note the following:
- The function cannot have the same name in the same file (or python gets unhappy), so we name it with a
  __ (dunderscore) as a suffix. The dunderscore is removed before it goes into the DAG.
- There is currently no `@config.otherwise(...)` decorator, so make sure to have `config.when` specify set of
  configuration possibilities.
Any missing cases will not have that output column (and subsequent downstream nodes may error out if they ask for it).
To make this easier, we have a few more `@config` decorators:

    - `@config.when_not(param=value)` Will be included if the parameter is _not_ equal to the value specified.
    - `@config.when_in(param=[value1, value2, ...])` Will be included if the parameter is equal to one of the specified
      values.
    - `@config.when_not_in(param=[value1, value2, ...])` Will be included if the parameter is not equal to any of the
      specified values.
    - `@config` If you're feeling adventurous, you can pass in a lambda function that takes in the entire configuration
      and resolves to
    `True` or `False`. You probably don't want to do this.

## @tag

Allows you to attach metadata to a node (any node decorated with the function).
A common use of this is to enable marking nodes as part of some data product, or for GDPR/privacy purposes.

For instance:

```python
import pandas as pd
from hamilton.function_modifiers import tag

def intermediate_column() -> pd.Series:
    pass

@tag(data_product='final', pii='true')
def final_column(intermediate_column: pd.Series) -> pd.Series:
    pass
```

### How do I query by tags?
Right now, we don't have a specific interface to query by tags, however we do expose them via the driver.
Using the `list_available_variables()` capability exposes tags along with their names & types,
enabling querying of the available outputs for specific tag matches.
E.g.
```python

from hamilton import driver
dr = driver.Driver(...)  # create driver as required
all_possible_outputs = dr.list_available_variables()
desired_outputs = [o.name for o in all_possible_outputs
                   if 'my_tag_value' == o.tags.get('my_tag_key')]
output = dr.execute(desired_outputs)
```

## @check_output

The `@check_output` decorator enables you to add simple data quality checks to your code.

For example:

```python
import pandas as pd
import numpy as np
from hamilton.function_modifiers import check_output

@check_output(
    data_type=np.int64,
    data_in_range=(0,100),
)
def some_int_data_between_0_and_100() -> pd.Series:
    pass
```

The check_output validator takes in arguments that each correspond to one of the default validators.
These arguments tell it to add the default validator to the list. The above thus creates
two validators, one that checks the datatype of the series, and one that checks whether the data is in a certain range.

Note that you can also specify custom decorators using the `@check_output_custom` decorator.

See [data_quality](data_quality.md) for more information on available validators and how to build custom ones.
