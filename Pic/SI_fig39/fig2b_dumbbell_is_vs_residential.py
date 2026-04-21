# fig2b_dumbbell_is_vs_residential.py —— 哑铃图：逐城 IS 与住宅用地相对变化的并置
# Purpose: Dumbbell chart comparing Informal settlements vs Residential land relative change (2010–2025) for each city.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
print(plt.rcParams['font.sans-serif'])

INPUT_XLSX = "./si_fig39bc.xlsx"
SHEET_NAME = 'Sheet1'
OUTPUT_PNG = './si_fig39b'
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
    keep = ['City', 'Informal_Area_Change', 'Residential_Area_Change']
    return wide[keep]

def main():
    df = load_and_reshape(INPUT_XLSX, SHEET_NAME)
    # Sort by IS change (descending)
    plot_df = df.sort_values('Informal_Area_Change', ascending=False).reset_index(drop=True)

    # Style
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['font.size'] = 10

    fig, ax = plt.subplots(figsize=FIGSIZE)

    ypos = np.arange(len(plot_df))
    # Connector lines
    ax.hlines(y=ypos,
              xmin=plot_df['Residential_Area_Change'],
              xmax=plot_df['Informal_Area_Change'],
              color='0.75', lw=2)

    # End points
    ax.scatter(plot_df['Residential_Area_Change'], ypos,
               color='dimgray', s=60, zorder=3, label='Residential land')
    ax.scatter(plot_df['Informal_Area_Change'], ypos,
               color='#d73027', s=60, zorder=3, label='Informal settlements')

    # Cosmetics
    ax.set_yticks(ypos)
    ax.set_yticklabels(plot_df['City'])
    ax.axvline(0, color='0.3', lw=1)
    ax.set_xlabel('Relative change since 2010')
    ax.set_title('Informal settlements vs. residential land change (2010–2025)')
    ax.legend(loc='upper right', frameon=False)

    plt.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=DPI)
    print(f'Saved {OUTPUT_PNG}')

if __name__ == '__main__':
    main()