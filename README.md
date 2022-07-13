<div align="center">
    <h1>Welcome to Hamilton's Github Repository</h1>
    <a href="https://circleci.com/gh/stitchfix/hamilton/tree/main" target="_blank"><img src="https://circleci.com/gh/stitchfix/hamilton/tree/main.svg?style=svg" alt="Hamilton CircleCI/></a>
    <a href="https://join.slack.com/t/hamilton-opensource/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg" target="_blank"><img src="https://img.shields.io/badge/Join-Hamilton_Slack-brightgreen?logo=slack" alt="Hamilton Slack"/></a>
    <br>
    <a href="https://www.python.org/downloads/" target="_blank"><img src="https://img.shields.io/badge/python-3.6%20|%203.7|%203.8|%203.9-brightgreen.svg" alt="Python supported"/></a>
    <a href="https://pypi.org/project/sf-hamilton/" target="_blank"><img src="https://badge.fury.io/py/sf-hamilton.svg" alt="PyPi Version"/></a>
    <a href="https://twitter.com/hamilton_os" target="_blank"><img src="https://img.shields.io/twitter/url/http/shields.io.svg?style=social" alt="Twitter"/></a>
</div>

# Hamilton

The general purpose micro-framework for creating dataflows from python functions!

Specifically, Hamilton defines a novel paradigm, that allows you to specify a flow of (delayed) execution, that forms a Directed Acyclic Graph (DAG).
It was original built to solve creating wide (1000+) column dataframes. Core to the design of Hamilton is a clear mapping of
function name to dataflow output. That is, Hamilton forces a certain paradigm with writing functions, and aims for DAG clarity,
easy modifications, with always unit testable and naturally documentable code.

For the backstory on how Hamilton came about, see our [blog post!](https://multithreaded.stitchfix.com/blog/2021/10/14/functions-dags-hamilton/).

# Getting Started
Here's a quick getting started guide to get you up and running in less than 15 minutes.
If you need help join our [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg) community to chat/ask Qs/etc.
For the latest updates, follow us on [twitter](https://twitter.com/hamilton_os)!

## Installation
Requirements:

* Python 3.6+

To get started, first you need to install hamilton. It is published to pypi under `sf-hamilton`:
> pip install sf-hamilton

Note: to use the DAG visualization functionality, you should instead do:
> pip install sf-hamilton[visualization]

While it is installing we encourage you to start on the next section.

Note: the content (i.e. names, function bodies) of our example code snippets are for illustrative purposes only, and don't reflect what we actually do internally.

## Hamilton in <15 minutes
Hamilton is a new paradigm when it comes to creating, um, dataframes (let's use dataframes as an example, otherwise you can create _ANY_ python object).
Rather than thinking about manipulating a central dataframe, as is normal in some data engineering/data science work,
you instead think about the column(s) you want to create, and what inputs are required. There
is no need for you to think about maintaining this dataframe, meaning you do not need to think about any "glue" code;
this is all taken care of by the Hamilton framework.

For example rather than writing the following to manipulate a central dataframe object `df`:
```python
df['col_c'] = df['col_a'] + df['col_b']
```

you write
```python
def col_c(col_a: pd.Series, col_b: pd.Series) -> pd.Series:
    """Creating column c from summing column a and column b."""
    return col_a + col_b
```
In diagram form:
![example](hamiltondag.png)
The Hamilton framework will then be able to build a DAG from this function definition.

So let's create a "Hello World" and start using Hamilton!

### Your first hello world.
By now, you should have installed Hamilton, so let's write some code.

1. Create a file `my_functions.py` and add the following functions:
```python
import pandas as pd

def avg_3wk_spend(spend: pd.Series) -> pd.Series:
    """Rolling 3 week average spend."""
    return spend.rolling(3).mean()

def spend_per_signup(spend: pd.Series, signups: pd.Series) -> pd.Series:
    """The cost per signup in relation to spend."""
    return spend / signups
```
The astute observer will notice we have not defined `spend` or `signups` as functions. That is okay,
this just means these need to be provided as input when we come to actually wanting to create a dataframe.

Note: functions can take or create scalar values, in addition to any python object type.

2. Create a `my_script.py` which is where code will live to tell Hamilton what to do:
```python
import importlib

import pandas as pd
from hamilton import driver

logging.basicConfig(stream=sys.stdout)
initial_columns = {  # load from actuals or wherever -- this is our initial data we use as input.
    # Note: these do not have to be all series, they could be scalar inputs.
    'signups': pd.Series([1, 10, 50, 100, 200, 400]),
    'spend': pd.Series([10, 10, 20, 40, 40, 50]),
}
# we need to tell hamilton where to load function definitions from
module_name = 'my_functions'
module = importlib.import_module(module_name)
dr = driver.Driver(initial_columns, module)  # can pass in multiple modules
# we need to specify what we want in the final dataframe.
output_columns = [
    'spend',
    'signups',
    'avg_3wk_spend',
    'spend_per_signup',
]
# let's create the dataframe!
# if you only did `pip install sf-hamilton` earlier:
df = dr.execute(output_columns)
# else if you did `pip install sf-hamilton[visualization]` earlier:
# dr.visualize_execution(output_columns, './my-dag.dot', {})
print(df)
```
3. Run my_script.py
> python my_script.py

You should see the following output:

       spend  signups  avg_3wk_spend  spend_per_signup
    0     10        1            NaN            10.000
    1     10       10            NaN             1.000
    2     20       50      13.333333             0.400
    3     40      100      23.333333             0.400
    4     40      200      33.333333             0.200
    5     50      400      43.333333             0.125

You should see the following image if you ran `dr.visualize_execution(output_columns, './my-dag.dot', {})`:

![hello_world_image](hello_world_image.png)

Congratulations - you just created your Hamilton dataflow that created a dataframe!

## Example Hamilton Dataflows
We have a growing list of examples showcasing how one might use Hamilton. You can find them all under the [`examples/`](https://github.com/stitchfix/hamilton/tree/main/examples) directory.
E.g.

* [Hello world](https://github.com/stitchfix/hamilton/tree/main/examples/hello_world)
* Scaling on to [Ray](https://github.com/stitchfix/hamilton/tree/main/examples/ray), [Dask](https://github.com/stitchfix/hamilton/tree/main/examples/dask), or [Pandas on Spark](https://github.com/stitchfix/hamilton/tree/main/examples/spark)
* Training [a model with scikit-learn](https://github.com/stitchfix/hamilton/tree/main/examples/model_examples)
* Doing [air quality analysis solely in numpy](https://github.com/stitchfix/hamilton/tree/main/examples/numpy/air-quality-analysis)


# Slack Community
We have a small but active community on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg). Come join us!

# License
Hamilton is released under the [BSD 3-Clause Clear License](LICENSE). If you need to get in touch about something,
contact us at algorithms-opensource (at) stitchfix.com.

# Used by
* Stitch Fix

To add your company, make a pull request to add it here.

# Contributing
We take contributions, large and small. We operate via a [Code of Conduct](CODE_OF_CONDUCT.md) and expect anyone
contributing to do the same.

To see how you can contribute, please read our [contributing guidelines](CONTRIBUTING.md) and then our [developer
setup guide](developer_setup.md).

# Blog Posts
* [Developing Scalable Feature Engineering DAGs with Metaflow & Hamilton](https://outerbounds.com/blog/developing-scalable-feature-engineering-dags)
* [Towards Data Science post on backstory & introduction](https://towardsdatascience.com/functions-dags-introducing-hamilton-a-microframework-for-dataframe-generation-more-8e34b84efc1d).
* [How to use Hamilton with Pandas in 5 minutes](https://medium.com/@stefan.krawczyk/how-to-use-hamilton-with-pandas-in-5-minutes-89f63e5af8f5).
* [How to iterate with Hamilton in a Notebook](https://towardsdatascience.com/how-to-iterate-with-hamilton-in-a-notebook-8ec0f85851ed).
* [Original Stitch Fix Post](https://multithreaded.stitchfix.com/blog/2021/10/14/functions-dags-hamilton/).
* [Extension Stitch Fix Post](https://multithreaded.stitchfix.com/blog/2021/10/14/functions-dags-hamilton/).

# Videos of talks
* [Hamilton: a python micro-framework for data/feature engineering at Stitch Fix](https://www.youtube.com/watch?v=PDGIt37dov8&ab_channel=AICamp):
[![Watch the video](https://img.youtube.com/vi/PDGIt37dov8/hqdefault.jpg)](https://youtu.be/PDGIt37dov8)



# Prescribed Development Workflow
In general we prescribe the following:

1. Ensure you understand [Hamilton Basics](basics.md).
2. Familiarize yourself with some of the [Hamilton decorators](decorators.md). They will help keep your code DRY.
3. Start creating Hamilton Functions that represent your work. We suggest grouping them in modules where it makes sense.
4. Write a simple script so that you can easily run things end to end.
5. Join our [Slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg) community to chat/ask Qs/etc.

For the backstory on Hamilton we invite you to watch a roughly-9 minute lightning talk on it that we gave at the apply conference:
[video](https://www.youtube.com/watch?v=B5Zp_30Knoo), [slides](https://www.slideshare.net/StefanKrawczyk/hamilton-a-micro-framework-for-creating-dataframes).

## PyCharm Tips
If you're using Hamilton, it's likely that you'll need to migrate some code. Here are some useful tricks we found
to speed up that process.

### Live templates
Live templates are a cool feature and allow you to type in a name which expands into some code.

E.g. For example, we wrote one to make it quick to stub out Hamilton functions: typing `graphfunc` would turn into ->

```python
def _(_: pd.Series) -> pd.Series:
   """"""
   return _
```

Where the blanks are where you can tab with the cursor and fill things in. See your pycharm preferences for setting this up.

### Multiple Cursors
If you are doing a lot of repetitive work, one might consider multiple cursors. Multiple cursors allow you to do things on multiple lines at once.

To use it hit `option + mouse click` to create multiple cursors. `Esc` to revert back to a normal mode.

# Contributors

## Code Contributors
- Stefan Krawczyk (@skrawcz)
- Elijah ben Izzy (@elijahbenizzy)
- Danielle Quinn (@danfisher-sf)
- Rachel Insoft (@rinsoft-sf)
- Shelly Jang (@shellyjang)
- Vincent Chu (@vslchusf)
- Christopher Prohm (@chmp)
- James Lamb (@jameslamb)

## Bug Hunters/Special Mentions
- Nils Olsson (@nilsso)
- Michał Siedlaczek (@elshize)
