import pandas as pd

def cast_data_types(df, type_mapping):
    """
    Cast columns in a DataFrame to specified data types and display before and after data types.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        type_mapping (dict): A dictionary mapping column names to data types.

    Returns:
        None
    """
    before_types = df.dtypes.to_dict()

    for column, dtype in type_mapping.items():
        if dtype == 'datetime':
            df[column] = pd.to_datetime(df[column])
        else:
            df[column] = df[column].astype(dtype)

    after_types = df.dtypes.to_dict()

    print("Data Types Before:")
    for column, dtype in before_types.items():
        print(f"{column}: {dtype}")

    print("\nData Types After:")
    for column, dtype in after_types.items():
        print(f"{column}: {dtype}")