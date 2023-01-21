import time

import data_loaders
import model_pipeline
import pandas as pd
import transforms

from hamilton import driver

model_params = {
    "num_leaves": 555,
    "min_child_weight": 0.034,
    "feature_fraction": 0.379,
    "bagging_fraction": 0.418,
    "min_data_in_leaf": 106,
    "objective": "regression",
    "max_depth": -1,
    "learning_rate": 0.005,
    "boosting_type": "gbdt",
    "bagging_seed": 11,
    "metric": "rmse",
    "verbosity": -1,
    "reg_alpha": 0.3899,
    "reg_lambda": 0.648,
    "random_state": 222,
}


def main():
    start_time = time.time()
    config = {
        "calendar_path": "m5-forecasting-accuracy/calendar.csv",
        "sell_prices_path": "m5-forecasting-accuracy/sell_prices.csv",
        "sales_train_validation_path": "m5-forecasting-accuracy/sales_train_validation.csv",
        "submission_path": "m5-forecasting-accuracy/sample_submission.csv",
        "load_test2": "False",
        "n_fold": 3,
        "model_params": model_params,
        "num_rows": 27500000,  # for training set
    }
    dr = driver.Driver(config, data_loaders, transforms, model_pipeline)
    dr.visualize_execution(["predicted_df"], "./predicted_df.dot.png", {})
    predicted_df: pd.DataFrame = dr.execute(["predicted_df"])
    print(len(predicted_df))
    print(predicted_df.head())
    duration = time.time() - start_time
    predicted_df.to_csv("predicted_df.csv", index=False)
    print("Duration: ", duration)
    print(predicted_df.head())


if __name__ == "__main__":
    main()
    # 275s to load data with ray
    # 173.4898989200592s to load data without ray
