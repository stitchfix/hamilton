# Hamilton

The micro-framework to create dataframes from functions.

Specifically, Hamilton is a framework that allows for delayed executions of functions in a Directed Acyclic Graph (DAG).
This is meant to solve the problem of creating complex data pipelines. Core to the design of hamilton is a 1:1 mapping of
key (function name) to implementation. Rather than defining flexible, reusable transformations, Hamilton aims for DAG clarity,
easy modifications, and documentation.

## Hamilton API

### Hamilton Functions
Hamilton is composed of functions. A simple (but rather contribed) example of a hamilton subdag that adds two numbers is as follows:

```python
def _sum(*vars):
    """Helper function to sum numbers.
    This is here to demonstrate that functions starting with _ do not get processed by hamilton.
    """
    return sum(vars)

def sum_a_b(a: int, b: int) -> int:
    """Adds a and b together
    :param a: The first number to add
    :param b: The second number to add
    :return: The sum of a and b
    """
    return _sum(a,b) # Delegates to a helper function
```

While this looks like a simple python function, there are a few components to note:
1. The function name `sum_a_b` is a globally unique key. In the DAG there can only be one function named `sum_a_b`.
While this is not optimal for functionality reuse, it makes it extremely easy to learn exactly how a node in the DAG is generated,
and separate out that logic for debugging/iterating.
2. The function `sum_a_b` depends on two upstream nodes -- `a` and `b`. This means that these values must either be:
    * Defined by another function
    * Passed in by the user as a configuration variable (see `Configuring Hamilton` below)
3. . The function `sum_a_b` makes full use of the python type-hint system. This is required in hamilton,
as it allows us to type-check the inputs and outputs to match with upstream producers and downstream consumers. In this case,
we know that the input `a` has to be an integer, the input `b` has to also be an integer, and anythying that declares `sum_a_b` as an input
has to declare it as an integer.
4. Standard python documentation is a first-class citizen. As we have a 1:1 relationship between python functions and nodes, each function documentation also describes a piece of business logic.
5. Functions that start with _ are ignored, and not included in the DAG. Hamilton tries to make use of every function in a module, so this allows us to easily indicate helper functions that
won't become part of the DAG.


### Decorators

While the 1:1 mapping of key -> implementation is powerful, we've implemented a few decorators to promote business-logic reuse. The decorators we've used are as follows.
While the following decorator examples are all taken from demandpy, they reside within the hamilton codebase, and are not specific to demandpy.

#### @parameterized
Expands a single function into n, each of which corresponds to a function in which the parameter value is replaced by that specific value.
```python
ONE_OFF_DATES = {
     #output name        # doc string               # input value to function
    ('D_ELECTION_2016', 'US Election 2016 Dummy'): '2016-11-12',
    ('SOME_OUTPUT_NAME', 'Doc string for this thing'): 'value to pass to function',
}
              # parameter matches the name of the argument in the function below
@parametrized(parameter='one_off_date', assigned_output=ONE_OFF_DATES)
def create_one_off_dates(DATE: pd.Series, one_off_date: str) -> pd.Series:
    """Helper create one off dates that aren't buisness related. E.g. elections."""
    one_off_dates = utils.get_end_of_fiscal_week(one_off_date)
    return utils.bool_to_int(DATE.isin([one_off_dates]))
```
We see here that `parameterized` allows you keep your code DRY by reusing the same function to create multiple
distinct outputs. The _parameter_ key word argument has to match one of the arguments in the function. The rest of
the arguments are pulled from outside the DAG. The _assigned_output_ key word argument takes in a dictionary of
tuple(Output Name, Documentation string) -> value.

#### @extract_columns
This works on a function that outputs a dataframe, that we want to extract the columns from and make them individually
available for consumption. So it expands a single function into _n functions_, each of which take in the output dataframe
 and output a specific column as named in the `extract_coumns` decorator.
```python
@extract_columns('fiscal_date', 'fiscal_week_name', 'fiscal_month', 'fiscal_quarter', 'fiscal_year')
def fiscal_columns(DATE: pd.Series, fiscal_dates: pd.DataFrame) -> pd.DataFrame:
    """Extracts the fiscal column data.
    We want to ensure that it has the same spine as DATE.
    :param fiscal_dates: the input dataframe to extract.
    :return:
    """
    df = pd.DataFrame({'DATE': DATE}, index=DATE.index)
    merged = df.join(fiscal_dates, how='inner')
    return merged
```
Note: if you have a list of columns to extract, then when you call `@extract_columns` you should call it with an asterix like this:
```python
@extract_columns(*my_list_of_column_names)
def my_func(...) -> pd.DataFrame:
   """..."""
```

#### @does
`@does` is a decorator that essentially allows you to run a function over all the input parameters. So you can't pass
any function to `@does`, it has to take any amount of inputs and process them in the same way.
```python
def sum_series(**series: pd.Series) -> pd.Series:
    ...

@does(sum_series)
def D_XMAS_GC_WEIGHTED_BY_DAY(D_XMAS_GC_WEIGHTED_BY_DAY_1: pd.Series,
                              D_XMAS_GC_WEIGHTED_BY_DAY_2: pd.Series) -> pd.Series:
    """Adds D_XMAS_GC_WEIGHTED_BY_DAY_1 and D_XMAS_GC_WEIGHTED_BY_DAY_2"""
    pass

@does(identity)
def copy_of_x(x: pd.Series) -> pd.Series:
    """Just returns x"""
    pass
```
The example here is a function, that all that it does, is sum all the parameters together. So we can annotate it with
the `@does` decorator and pass it the `sum_series` function. Browse through `utils.py` to see what's already defined for you.
The `@does` decorator is currently limited to just allow functions that consist only of one argument, a generic **kwargs.
That will likely change to be less restrictive in the future.

#### @model
`@model` allows you to run one of a few pre-configured models. Currently implemented model types include:

- `OngoingCancellationModel` For historical models that predict ongoing cancellations towards the end of the `create_database` time range. This is roughly equivalent to https://github.com/stitchfix/demandr/blob/master/R/model_evaluation.R#L11.
- `GLM` For standard Generalized Linear Models, roughly equivalent to https://github.com/stitchfix/demandr/blob/master/R/model_evaluation.R#L136.

Under the hood, they're just DAG nodes whose inputs are determined by a configuration parameter. A model takes in two required parameters:
1. The class it uses to run the model. This is (currently) one of the above two classes, and determines what the function actually does.
2. The configuration key that determines how the model functions. This is just the name of a configuration parameter that stores the way the model is run.

The following is an example usage of `@model`:

```python
@model(GLM, 'model_p_cancel_manual_res')
# This runs a GLM (Generalized Linear Model)
# The associated configuration parameter is 'model_p_cancel_manual_res',
# which points to the results of loading the model_p_cancel_manual_res table
def prob_cancel_manual_res() -> pd.Series:
    pass
```

The `@model` decorator is part of the hamilton framework, whereas `GLM` and `OngoingCancellationModel` contain significant
demand-model-based business logic. To define a new model type, look at `GLM` and and `OngoingCancellationModel` in models.py.
Models (optionally) accept a `output_column` parameter -- this is specifically if the name of the function differs from the output column that it right to.
E.G. if you use the model result as an intermediate object, and manipulate it all later. This is necessary because various dependent columns that a model queries
(`MULTIPLIER_...` and `OFFSET_...`) are derived from the model's name.

#### @config.when*

`@config.when` allows you to specify different implementations depending on configuration parameters.

The following use cases are supported:
1. A column is present for only one value of a config parameter -- in this case, we define a function only once, with a `@config.when`
    ```python
    # signups_parent_before_launch is only present in the kids business line
    @config.when(business_line='kids')
    def signups_parent_before_launch(signups_from_existing_womens_tf: pd.Series) -> pd.Series:
        """TODO:
        :param signups_from_existing_womens_tf:
        :return:
        """
        return signups_from_existing_womens_tf
    ```
2. A column is implemented differently for different business lines
    ```python
    # 21 day autoship cadence does not exist for kids, so we just return 0s
    @config.when(business_line='kids')
    def percent_clients_21d_autoship_cadence_model__kids(DATE: pd.Series) -> pd.Series:
        return pd.Series(index=DATE.index, data=0.0)

    # In other business lines, we have a model for it
    @config.when_not(business_line='kids')
    @model(GLM, 'model_p_clients_autoship21d', output_column='percent_clients_21d_autoship_cadence')
    def percent_clients_21d_autoship_cadence_model() -> pd.Series:
        pass
    ```
Note the following:
- The function cannot have the same name in the same file (or python gets unhappy), so we name it with a __ (dunderscore) as a suffix. The dunderscore is
removed before it goes into the function.
- There is currently no `@config.otherwise(...)` decorator, so make sure to have `config.when` specify set of configuration possibilities.
Any missing cases will not have that output column (and subsequent downstream nodes may error out if they ask for it). To make this easier, we have a few more
`@config` decorators:

    - `@config.when_not(param=value)` Will be included if the parameter is _not_ equal to the value specified.
    - `@config.when_in(param=[value1, value2, ...])` Will be included if the parameter is equal to one of the specified values.
    - `@config.when_not_in(param=[value1, value2, ...])` Will be included if the parameter is not equal to any of the specified values.
    - `@config` If you're feeling adventurous, you can pass in a lambda function that takes in the entire configuration and resolves to
    `True` or `False`. You probably don't want to do this.

## Implementation details
### Configuration
The configuration is used not just to feed data to the DAG, but also to determine the strcuture of the DAG.
As such, it is passed in in the constructor, and used during DAG creation.

### Execution
Execution of the DAG is done using an externally maintained cache. As such, the caller is responsible for storing the dictionary of results and passing
it into the execution engine. Note that this may change as we abstract execution from DAG construction. Execution of the DAG
is currently implemented with a recursive depth-first-traversal, meaning that it is possible (although highly unlikely) to hit recursion depth errors.
If that happens, the culprit is almost always a circular reference in the graph.

## Configuring Hamilton
In hamilton, configuration is built in as a simple key-value store. Thus, the config is a `Dict[str, Any]`, that should contain a key for
every input not produced by another function.

### Overrides
The configuration dictionary should not be used for overriding functions that are already implemented. To do this, use the `override` parameter in `execute`.
## Running Hamilton
See the function `execute(...)`.

## Visualizing the DAG
To visualize the DAG, pass the flag `display_graph=True` to execute. It will render an image in a pdf format.

### Typing System

Hamilton makes use of python's type-hinting feature to check compatibility between function outputs and function inputs. However,
this is not particularly sophisticated, largely due to the lack of available tooling in python. Thus, generic types do not function correctly.
The following will not work:

```python
def some_func() -> Dict[str, int]:
    return {1: 2}
```

The following will both work:
```python
def some_func() -> Dict:
    return {1: 2}
```

```python
def some_func() -> dict:
    return {1: 2}
```

While this is unfortunate, the typing API in python is not yet sophisticated enough to rely on accurate subclass validation.


## Repo organization

This repository is organized as follows:

1. hamilton/ is platform code to orchestrate and execute the graph.
2. tests/ is the place where unit tests (or light integration tests) are located.

## How to contribute

1. Checkout the repo.
2. Create a virtual environment for it. See python algo curriculum slides for details.
3. Activate the virtual environment and install all dependencies. One for the package, one for making comparisons, one for running unit tests. I.e. `pip install -r requirements*.txt` should install all three for you.
3. Make pycharm depend on that virtual environment & install required dependencies (it should prompt you because it'll read the requirements.txt file).
4. `brew install pre-commit` if you haven't.
5. Run `pre-commit install` from the root of the repository.
6. Create a branch off of the latest master branch. `git checkout -b my_branch`.
7. Do you work & commit it.
8. Push to github and create a PR.
9. When you push to github circle ci will kick off unit tests and migration tests.


## How to run unit tests

You need to have installed the `requirements-test.txt` dependencies into the environment you're running for this to work. You can run tests two ways:

1. Through pycharm/command line.
2. Using circle ci locally. The config for this lives in `.circleci/config.yml` which also shows commands to run tests
from the command line.

## How to run compare integration tests

You need to have installed the `requirements-demandpy-migration.txt` dependencies into the environment you're running for this to work. You can run tests two ways:

1. Through pycharm/command line.
2. Using circle ci locally. The config for this lives in `.circleci/config.yml` which also shows commands to run the migration integration tests from the command line.

### Using pycharm to execute & debug unit tests

You can debug and execute unit tests in pycharm easily. To set it up, you just hit `Edit configurations` and then
add New > Python Tests > pytest. You then want to specify the `tests/` folder under `Script path`, and ensure the
python environment executing it is the appropriate one with all the dependencies installed. If you add `-v` to the
additional arguments part, you'll then get verbose diffs if any tests fail.

### Using circle ci locally

You need to install the circleci command line tooling for this to work. See the unit testing algo curriculum slides for details.
Once you have installed it you just need to run `circleci local execute` from the root directory and it'll run the entire suite of tests
that are setup to run each time you push a commit to a branch in github.

## PyCharm Tips

### Live templates
Live templates are a cool feature and allow you to type in a name which expands into some code.

E.g. graphfunc ->

```python
def _(_: pd.Series) -> pd.Series:
   """""""
   return _
```

Where the blanks are where you can tab with the cursor and fill things in. See your preferences for setting this up.

### Multiple Cursors
If you are doing a lot of repetitive work, one might consider multiple cursors. Multiple cursors allow you to do things on multiple lines at once. This is great if you are copying and pasting R code that is very similar and need to do a bunch of changes quickly, and search + replace won't cut it for you.

To use it hit `option + mouse click` to create multiple cursors. `Esc` to revert back to a normal mode.
