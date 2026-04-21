import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

# 读取数据
df = pd.read_csv(
    "./si_fig39d.csv",
    engine='python'
)
save_path = './si_fig39d'

df.columns = [c.strip() for c in df.columns]
if 'file' in df.columns:
    df = df.rename(columns={'file': '城市'})

# 年份列
year_cols = [c for c in df.columns if c != '城市']
for c in year_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# 配色（色盲友好）
colors = {
    '2010': '#1f77b4',  # 蓝
    '2025': '#ff7f0e',  # 橙
}

# 字体设置
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['font.size'] = 10

cities = df['城市']
years = [c for c in year_cols]
assert len(years) == 2

x = range(len(cities))
bar_width = 0.6  # 同轴重叠时的统一柱宽

fig, ax = plt.subplots(figsize=(7, 5))

# 采用透明度实现重叠效果
ax.bar(x, df[years[1]], width=bar_width, color=colors[str(years[1])],
       alpha=1, label=str(years[1]), edgecolor='white', linewidth=0.4)
ax.bar(x, df[years[0]], width=bar_width, color=colors[str(years[0])],
       alpha=1, label=str(years[0]), edgecolor='white', linewidth=0.4)

# 轴与标题
# ax.set_title('各城市医疗设施数量（同轴重叠：2010 与 2025）', fontsize=14, pad=12)
ax.set_ylabel('Medical Facilities Count')   # , fontsize=14
ax.set_xticks(list(x))
ax.set_xticklabels(cities, rotation=20, ha='right')     # , fontsize=12
ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

# 网格与图例
ax.grid(axis='y', linestyle='--', alpha=0.3)
ax.legend(title='Year', frameon=True, fontsize=10, title_fontsize=12)

# 数值标签（左右微偏移，避免完全重叠）
# pad = max(df[years].max()) * 0.01
pad = 0.2
for xi, (y0, y1) in enumerate(zip(df[years[0]], df[years[1]])):
    ax.text(xi - 0.25, y0 + pad, f"{int(y0)}", ha='center', va='bottom',
            fontsize=10, color=colors[str(years[0])])
    ax.text(xi + 0.25, y1 + pad, f"{int(y1)}", ha='center', va='bottom',
            fontsize=10, color=colors[str(years[1])])

plt.tight_layout()
plt.savefig(save_path, dpi=300)
# plt.show()
plt.close()
print('图已保存：medical_facilities_overlap_2010_2025.png')
