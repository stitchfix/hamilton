import gc

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import TimeSeriesSplit

from hamilton.function_modifiers import does, extract_fields


def _create_dataframe(**kwargs) -> pd.DataFrame:
    return pd.DataFrame(kwargs)


@does(_create_dataframe)
def training_set(
    item_id_encoded: pd.Series,
    dept_id_encoded: pd.Series,
    cat_id_encoded: pd.Series,
    store_id_encoded: pd.Series,
    state_id_encoded: pd.Series,
    year: pd.Series,
    month: pd.Series,
    week: pd.Series,
    day: pd.Series,
    dayofweek: pd.Series,
    event_name_1_encoded: pd.Series,
    event_type_1_encoded: pd.Series,
    event_name_2_encoded: pd.Series,
    event_type_2_encoded: pd.Series,
    snap_CA: pd.Series,
    snap_TX: pd.Series,
    snap_WI: pd.Series,
    sell_price: pd.Series,
    lag_t28: pd.Series,
    lag_t29: pd.Series,
    lag_t30: pd.Series,
    rolling_mean_t7: pd.Series,
    rolling_std_t7: pd.Series,
    rolling_mean_t30: pd.Series,
    rolling_mean_t90: pd.Series,
    rolling_mean_t180: pd.Series,
    rolling_std_t30: pd.Series,
    price_change_t1: pd.Series,
    price_change_t365: pd.Series,
    rolling_price_std_t7: pd.Series,
    rolling_price_std_t30: pd.Series,
    date: pd.Series,
    demand: pd.Series,
) -> pd.DataFrame:
    pass


@extract_fields({"x": pd.DataFrame, "y": pd.Series, "test": pd.DataFrame})
def data_sets(training_set: pd.DataFrame, cut_off_date: str = "2016-04-24") -> dict:
    training_set.sort_values("date", inplace=True)
    x = training_set[(training_set["date"] <= cut_off_date)]
    y = x["demand"]
    test = training_set[(training_set["date"] > cut_off_date)]
    return {
        "x": x[list(set(x.columns) - set(["demand", "date"]))],
        "y": y,
        "test": test[list(set(x.columns) - set(["demand"]))],
    }


@extract_fields({"filled_test": pd.DataFrame, "feature_importances": pd.DataFrame})
def train(
    x: pd.DataFrame, y: pd.Series, test: pd.DataFrame, n_fold: int, model_params: dict
) -> dict:
    folds = TimeSeriesSplit(n_splits=n_fold)
    columns = [
        "item_id_encoded",
        "dept_id_encoded",
        "cat_id_encoded",
        "store_id_encoded",
        "state_id_encoded",
        "year",
        "month",
        "week",
        "day",
        "dayofweek",
        "event_name_1_encoded",
        "event_type_1_encoded",
        "event_name_2_encoded",
        "event_type_2_encoded",
        "snap_CA",
        "snap_TX",
        "snap_WI",
        "sell_price",
        "lag_t28",
        "lag_t29",
        "lag_t30",
        "rolling_mean_t7",
        "rolling_std_t7",
        "rolling_mean_t30",
        "rolling_mean_t90",
        "rolling_mean_t180",
        "rolling_std_t30",
        "price_change_t1",
        "price_change_t365",
        "rolling_price_std_t7",
        "rolling_price_std_t30",
    ]
    assert set(columns) == set(x.columns), "Error: columns aren't correct."
    splits = folds.split(x, y)
    y_preds = np.zeros(test.shape[0])
    y_oof = np.zeros(x.shape[0])
    feature_importances = pd.DataFrame()
    feature_importances["feature"] = columns
    mean_score = []
    for fold_n, (train_index, valid_index) in enumerate(splits):
        print("Fold:", fold_n + 1)
        X_train, X_valid = x.iloc[train_index], x.iloc[valid_index]
        y_train, y_valid = y.iloc[train_index], y.iloc[valid_index]
        dtrain = lgb.Dataset(X_train, label=y_train)
        dvalid = lgb.Dataset(X_valid, label=y_valid)
        clf = lgb.train(
            model_params,
            dtrain,
            2500,
            valid_sets=[dtrain, dvalid],
            early_stopping_rounds=50,
            verbose_eval=100,
        )
        feature_importances[f"fold_{fold_n + 1}"] = clf.feature_importance()
        y_pred_valid = clf.predict(X_valid, num_iteration=clf.best_iteration)
        y_oof[valid_index] = y_pred_valid
        val_score = np.sqrt(metrics.mean_squared_error(y_pred_valid, y_valid))
        print(f"val rmse score is {val_score}")
        mean_score.append(val_score)
        y_preds += (
            clf.predict(
                test[list(set(test.columns) - set(["date"]))], num_iteration=clf.best_iteration
            )
            / n_fold
        )
        del X_train, X_valid, y_train, y_valid
        gc.collect()
    print("mean rmse score over folds is", np.mean(mean_score))
    test["demand"] = y_preds
    return {"filled_test": test, "feature_importances": feature_importances}


def predicted_df(filled_test: pd.DataFrame, submission: pd.DataFrame) -> pd.DataFrame:
    predictions = filled_test[["date", "demand"]]
    predictions["id"] = predictions.index
    predictions = pd.pivot(predictions, index="id", columns="date", values="demand").reset_index()
    predictions.columns = ["id"] + ["F" + str(i + 1) for i in range(28)]
    evaluation_rows = [row for row in submission["id"] if "evaluation" in row]
    evaluation = submission[submission["id"].isin(evaluation_rows)]
    validation = submission[["id"]].merge(predictions, on="id")
    final = pd.concat([validation, evaluation])
    # final.to_csv('submission.csv', index = False)
    return final
