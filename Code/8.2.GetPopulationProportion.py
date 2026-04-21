import glob
import os.path

import pandas as pd
import numpy as np

def cumulative_proportion_by_minute(df, pop_col='value_band1', time_col='value_band2', minute_cap=120):
    d = df.copy()
    d[time_col] = pd.to_numeric(d[time_col], errors='coerce')
    d[pop_col] = pd.to_numeric(d[pop_col], errors='coerce')
    d = d.dropna(subset=[time_col, pop_col])
    d = d[d[pop_col] > 0]
    d = d.sort_values(time_col)

    d['cum_pop'] = d[pop_col].cumsum()
    total_pop = d[pop_col].sum()

    minutes = pd.DataFrame({'Within Minutes': np.arange(1, minute_cap + 1).astype(float)})
    ref = d[[time_col, 'cum_pop']].rename(columns={time_col: 'Within Minutes'}).sort_values('Within Minutes')
    merged = pd.merge_asof(minutes, ref, on='Within Minutes', direction='backward')
    merged['cum_pop'] = merged['cum_pop'].fillna(0)

    proportions = merged['cum_pop'] / total_pop * 100.0
    greater = 100.0 - proportions.iloc[-1]
    return proportions.to_list(), float(greater)

def build_output(slum_df, non_df, minute_cap=120, decimals=None):
    slum_props, slum_greater = cumulative_proportion_by_minute(slum_df, minute_cap=minute_cap)
    non_props, non_greater   = cumulative_proportion_by_minute(non_df, minute_cap=minute_cap)

    if decimals is not None:
        slum_props = [round(x, decimals) for x in slum_props]
        non_props  = [round(x, decimals) for x in non_props]
        slum_greater = round(slum_greater, decimals)
        non_greater  = round(non_greater, decimals)

    columns = ['Within Minutes'] + list(range(1, minute_cap + 1)) + ['Greater', 'Total Population']
    data = [
        ['slum proportion'] + slum_props + [slum_greater, 100.0],
        ['non proportion']  + non_props  + [non_greater, 100.0],
    ]
    out = pd.DataFrame(data, columns=columns)
    return out


def dir_loop():
    slum_csv_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\PopulationRelated-2010-10km\PopulationRelated-SlumArea"
    non_slum_csv_dir = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\PopulationRelated-2010-10km\PopulationRelated-SlumArea"
    save_dir = r'C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\PopulationRelated-2010-10km\CSV'

    os.makedirs(save_dir, exist_ok=True)
    slum_csv_list = glob.glob(os.path.join(slum_csv_dir, '*.csv'))
    for slum_csv_path in slum_csv_list:
        city_name = os.path.basename(slum_csv_path).split('-')[0]
        non_slum_csv_path = os.path.join(non_slum_csv_dir, city_name + '-2010_slum.csv')    # -2025_non-slum.csv
        save_path = os.path.join(save_dir, city_name + '_ProportionInPopulation.csv')

        result = build_output(
            pd.read_csv(slum_csv_path),
            pd.read_csv(non_slum_csv_path),
            minute_cap=120, decimals=None
        )
        result.to_csv(save_path, index=False)
        print(city_name)


if __name__ == '__main__':
    dir_loop()
