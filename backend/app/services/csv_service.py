import pandas as pd


def read_csv_file(file):
    try:
        df = pd.read_csv(file.file)

        return {
            "success": True,
            "filename": file.filename,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": df.columns.tolist(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }