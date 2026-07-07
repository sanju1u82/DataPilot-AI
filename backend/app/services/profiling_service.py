import pandas as pd


def generate_profile(df: pd.DataFrame):
    profile = {
        "dataset": {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "duplicates": int(df.duplicated().sum()),
            "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        },
        "columns": {
            "numeric": df.select_dtypes(include="number").columns.tolist(),
            "categorical": df.select_dtypes(exclude="number").columns.tolist(),
        },
        "missing_values": (
            df.isnull()
            .sum()
            .loc[lambda x: x > 0]
            .to_dict()
        ),
        "data_types": {
            col: str(dtype)
            for col, dtype in df.dtypes.items()
        }
    }

    return profile