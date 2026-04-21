# fig2a_quadrant_scatter.py —— 人口 × 非正规住区（IS）变化的象限散点（点大小=住宅用地变化，点色=GDP 变化）
# Purpose: Plot quadrant scatter of Population change vs Informal settlements (IS) change
# Marker size encodes Residential land change; color encodes GDP change.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

INPUT_XLSX = "./Parameters2.xlsx"
SHEET_NAME = 'Sheet1'
OUTPUT_PNG = './si_fig39a'
FIGSIZE = (7, 5)   # inches
DPI = 300

def load_and_reshape(path: str, sheet: str) -> pd.DataFrame:
    """
    Read the wide-by-city Excel where the first column holds metric names
    (Population Change, Informal Settlements Area Change, Residential Area Change, GDP Change)
    and the remaining columns are city names. Return tidy DataFrame with columns:
    City, Population_Change, Informal_Area_Change, Residential_Area_Change, GDP_Change
    """
    raw = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.rename(columns={'Country': 'Metric'})  # first column
    long = raw.melt(id_vars='Metric', var_name='City', value_name='Value')
    wide = long.pivot(index='City', columns='Metric', values='Value').reset_index()

    col_map = {
        'Population Change': 'Population_Change',
        'Informal Settlements Area Change': 'Informal_Area_Change',
        'Residential Area Change': 'Residential_Area_Change',
        'Informal Settlement Proportion Change': 'Informal_Settlement_Proportion_Change'
    }
    wide = wide.rename(columns=col_map)
    keep = ['City', 'Population_Change', 'Informal_Area_Change', 'Residential_Area_Change',
            'Informal_Settlement_Proportion_Change']
    return wide[keep]

def main():
    # Load
    df = load_and_reshape(INPUT_XLSX, SHEET_NAME)

    # Matplotlib style
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['font.size'] = 10

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Axes data
    x = df['Population_Change']
    y = df['Informal_Area_Change']

    # Marker size ~ Residential change (scaled to readable radii)
    res = df['Residential_Area_Change']
    size = 300 * (res - res.min()) / (res.max() - res.min() + 1e-9) + 80

    # Marker color ~ GDP change (diverging around 0)
    # gdp = df['GDP_Change']
    # norm = TwoSlopeNorm(vmin=gdp.min(), vcenter=0, vmax=gdp.max())
    # sc = ax.scatter(x, y, c=gdp, s=size, cmap='coolwarm', norm=norm,
    #                 edgecolor='k', linewidth=0.5)
    gdp = df['Informal_Settlement_Proportion_Change'].to_numpy()
    m = np.nanmax(np.abs(gdp))  # 取绝对值最大值做对称范围
    norm = TwoSlopeNorm(vmin=-m, vcenter=0.0, vmax=m)
    sc = ax.scatter(x, y, c=gdp, s=size, cmap='coolwarm', norm=norm,
                    edgecolor='k', linewidth=0.5)

    # Quadrant lines
    ax.axhline(0, color='0.3', lw=1)
    ax.axvline(0, color='0.3', lw=1)

    # Labels
    # for _, row in df.iterrows():
    #     ax.annotate(row['City'], (row['Population_Change'], row['Informal_Area_Change']),
    #                 xytext=(5, 5), textcoords='offset points')

    # Axes titles
    ax.set_xlabel('Population change (relative to 2010)')
    ax.set_ylabel('Informal settlements area change (relative to 2010)')
    ax.set_title('Population vs. Informal Settlements Change (2010–2025)')

    # Colorbar for GDP
    cbar = fig.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label('Informal Settlement Proportion Change (relative to 2010)')

    # Manual legend for marker sizes (Residential change)
    handles = []
    labels = []
    for v in np.linspace(res.min(), res.max(), 3):
        s = 300 * (v - res.min()) / (res.max() - res.min() + 1e-9) + 100
        handles.append(plt.scatter([], [], s=s, color='none', edgecolor='k', linewidth=1.))
        labels.append(f'Residential change {v:+.2f}')
    ax.legend(handles, labels, title='Marker size:', loc='upper left',
              bbox_to_anchor=(0.5, 1.0), frameon=True, labelspacing=1.2)

    plt.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=DPI, transparent=True)
    print(f'Saved {OUTPUT_PNG}')

if __name__ == '__main__':
    main()