# fig2c_gdp_bar.py —— GDP 相对变化率的水平条形图
# Purpose: Horizontal bar chart of GDP relative change (2010–2025) by city.

import pandas as pd
import matplotlib.pyplot as plt

INPUT_XLSX = "./si_fig39bc.xlsx"
SHEET_NAME = 'Sheet1'
OUTPUT_PNG = './si_fig39c'
FIGSIZE = (7, 5)
DPI = 300

def load_and_reshape(path: str, sheet: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.rename(columns={'Country': 'Metric'})
    long = raw.melt(id_vars='Metric', var_name='City', value_name='Value')
    wide = long.pivot(index='City', columns='Metric', values='Value').reset_index()
    col_map = {
        'Population Change': 'Population_Change',
        'Informal Settlements Area Change': 'Informal_Area_Change',
        'Residential Area Change': 'Residential_Area_Change',
        'GDP Change': 'GDP_Change'
    }
    wide = wide.rename(columns=col_map)
    keep = ['City', 'GDP_Change']
    return wide[keep]

def main():
    df = load_and_reshape(INPUT_XLSX, SHEET_NAME)
    bar_df = df.sort_values('GDP_Change', ascending=True)

    # Style
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['font.size'] = 10

    fig, ax = plt.subplots(figsize=FIGSIZE)

    colors = ['#1f78b4' if v < 0 else '#e39f2d' for v in bar_df['GDP_Change']]
    ax.barh(bar_df['City'], bar_df['GDP_Change'], color=colors)
    ax.axvline(0, color='0.3', lw=1)

    ax.set_xlabel('GDP change (relative to 2010)')
    ax.set_title('GDP changes by city (2010–2025)')

    plt.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=DPI)
    print(f'Saved {OUTPUT_PNG}')

if __name__ == '__main__':
    main()