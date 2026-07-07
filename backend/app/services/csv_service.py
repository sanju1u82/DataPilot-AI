import pandas as pd
from app.services.profiling_service import generate_profile


def read_csv_file(file):
    try:
        df = pd.read_csv(file.file)

        profile = generate_profile(df)

        return {
            "success": True,
            "filename": file.filename,
            "profile": profile
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }