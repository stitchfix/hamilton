import importlib
import logging
import sys

import pandas as pd
import ray

from hamilton import base
from hamilton import driver
from hamilton import log_setup
from hamilton.experimental import h_ray

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    log_setup.setup_logging()
    ray.init()
    module_names = [
        'data_loaders',  # functions to help load data
        'business_logic'  # where our important logic lives
    ]
    modules = [importlib.import_module(m) for m in module_names]
    initial_columns = {  # could load data here via some other means, or delegate to a module as we have done.
        # 'signups': pd.Series([1, 10, 50, 100, 200, 400]),
        'signups_location': 'some_path',
        # 'spend': pd.Series([10, 10, 20, 40, 40, 50]),
        'spend_location': 'some_other_path'
    }
    rga = h_ray.RayGraphAdapter(result_builder=base.PandasDataFrameResult())
    dr = driver.Driver(initial_columns, *modules, adapter=rga)  # can pass in multiple modules
    # we need to specify what we want in the final dataframe.
    output_columns = [
        'spend',
        'signups',
        'avg_3wk_spend',
        'spend_per_signup',
        'spend_zero_mean_unit_variance'
    ]
    # let's create the dataframe!
    df = dr.execute(output_columns, display_graph=False)
    print(df.to_string())
    ray.shutdown()
