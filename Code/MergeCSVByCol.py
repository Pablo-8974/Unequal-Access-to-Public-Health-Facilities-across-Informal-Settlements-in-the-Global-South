import os
import pandas as pd

def mergeCSVbycol(input_folder, output_csv):
    csv_files = sorted(
        f for f in os.listdir(input_folder)
        if f.lower().endswith(".csv")
    )

    if not csv_files:
        raise RuntimeError("no csv files")

    df = pd.read_csv(os.path.join(input_folder, csv_files[0]))
    merged_columns = {}
    for col in df.columns:
        merged_columns[col] = []

    for fname in csv_files:
        df = pd.read_csv(os.path.join(input_folder, fname))

        for col in df.columns:
            col_values = df[col].dropna().tolist()
            merged_columns[col] += col_values

    result_df = pd.DataFrame({
        col: pd.Series(values)
        for col, values in merged_columns.items()
    })

    result_df.to_csv(output_csv, index=False, encoding="utf-8-sig")


if __name__ == '__main__':
    input_folder = '/intelnvme04/jiang.mingyu/slum/RelativeSpeed/BoxParam/Time/10km/slum'
    output_csv = input_folder + "/merge.csv"
    mergeCSVbycol(input_folder, output_csv)

