import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Union, Tuple

# ----------------------------
# 1) 读取 CSV，并按行选择器取值
# ----------------------------
def read_row_values(
    filepath: str,
    row_selector: Union[str, int],
    drop_total_population: bool = True
) -> Tuple[List[Union[int, float, str]], np.ndarray]:
    """
    返回 (minutes, values)：
      - minutes：分钟标签（int/float 或 'Greater'），自动剔除 'Total Population'
      - values：所选数据行对应这些列上的值（float）

    row_selector:
      - str：行首单元格精确匹配，如 'Share fine'、'Population'、'Share coarse'
      - int：表头之后的行号（0=第二行Population，1=第三行Share fine，2=第四行Share coarse）
    """
    df = pd.read_csv(filepath, header=None)
    if df.empty:
        raise ValueError(f"File {filepath} is empty.")

    headers = df.iloc[0].astype(str).str.strip().tolist()
    raw_minutes = headers[1:]  # 排除第一列 'Within Minutes'

    # 规范化分钟标签（'5.0' -> 5；保留 'Greater'）
    minutes: List[Union[int, float, str]] = []
    for lab in raw_minutes:
        lab = lab.strip()
        if lab.lower() == 'total population' and drop_total_population:
            break
        try:
            val = float(lab)
            minutes.append(int(val) if val.is_integer() else val)
        except ValueError:
            minutes.append(lab)

    # 定位数据行
    if isinstance(row_selector, str):
        mask = (df.iloc[:, 0].astype(str).str.strip() == row_selector)
        if not mask.any():
            raise ValueError(f"Row label '{row_selector}' not found in {filepath}")
        row_idx = mask[mask].index[0]
    else:
        row_idx = 1 + int(row_selector)  # 表头是第 0 行
        if row_idx >= len(df):
            raise IndexError(f"Row index {row_selector} out of range in {filepath}")

    values = (
        df.iloc[row_idx, 1:1+len(minutes)]
          .astype(str).str.strip().replace('', np.nan).astype(float).values
    )
    return minutes, values

# ----------------------------
# 2) 按自定义分组聚合
# ----------------------------
def group_minutes(
    minutes: List[Union[int, float, str]],
    values: np.ndarray,
    groups: List[Union[Union[int, float, str], List[Union[int, float, str]]]]
) -> Tuple[List[str], np.ndarray]:
    """
    对分钟列按 groups 聚合:
      例：groups = [[5, 10, 15], 20, 30, 60, 'Greater']
      -> 第一组为 5+10+15 的和，其余为单列值。
    返回 (group_labels, grouped_values)
    """
    idx = pd.Index(minutes)
    grouped_vals, labels = [], []

    for g in groups:
        if isinstance(g, list):
            members = g
            label = '+'.join(str(x) for x in members)
        else:
            members = [g]
            label = str(g)

        pos = [idx.get_loc(m) if m in idx else -1 for m in members]
        pos = [p for p in pos if p != -1]

        grouped_vals.append(np.nansum(values[pos]) if pos else np.nan)
        labels.append(label)

    return labels, np.array(grouped_vals, dtype=float)

# ----------------------------
# 3) 折线图绘制（三类三色）
# ----------------------------
def line_chart_three_categories(
    grouped_data: List[Tuple[str, List[str], np.ndarray]],
    show_markers: bool = False,
):
    """
    grouped_data: [(category_name, group_labels, grouped_values), ...]
      如 ('Whole city', ['5+10+15','20','30','60','Greater'], array([...]))
    """
    if not grouped_data:
        raise ValueError("grouped_data is empty.")

    # X 轴标签与位置
    groups = grouped_data[0][1]
    X = np.arange(len(groups))

    plt.rcParams.update({'font.size': 10})
    # fig, ax = plt.subplots(figsize=(max(10, len(groups) * 1.6), 5))
    fig, ax = plt.subplots(figsize=(8, 5))

    # 调色盘（3 类）
    palette = ['#10b981', '#2563eb', '#dc2626']
    color_map = {cat: palette[i % len(palette)] for i, (cat, _, _) in enumerate(grouped_data)}

    # 绘制三条线
    for cat, _, vals in grouped_data:
        color = color_map[cat]
        if show_markers:
            ax.plot(X, vals, color=color, linewidth=2.0, marker='o', markersize=5,
                    label=cat)
        else:
            ax.plot(X, vals, color=color, linewidth=2.0, label=cat)

    # 坐标轴/网格/标签
    ax.set_xticks(x_ticks_to_show)
    ax.set_xticklabels(x_ticks_to_show, rotation=0)
    ax.set_xlabel(x_label, fontsize=18)
    ax.set_yticks(y_ticks_to_show)
    ax.set_yticklabels(y_ticks_to_show, rotation=0)
    ax.set_ylabel(y_label, fontsize=18)

    ax.set_title(title_words, loc='center', pad=6, fontsize=28)
    ax.grid(True, linestyle='--', alpha=0.35)

    ax.set_xlim(-5, 125)  # 比如 Xmax = 120
    ax.set_ylim(-5, 105)  # 比如 Ymax = 100（人口占比上限）

    # 图例
    ax.legend(title='Category', loc='lower right', frameon=True, fontsize=12, title_fontsize=13)
    legend = ax.get_legend()
    legend.get_texts()[0].set_text("Whole City")
    legend.get_texts()[1].set_text("Formal Settlements")
    legend.get_texts()[2].set_text("Informal Settlements")

    # 指示箭头
    start = (0.055, 0.8)  # 箭头尾部，轴域坐标（0~1，左下为(0,0)，右上为(1,1)）
    end = (0.03, 0.95)  # 箭头头部位置（水平指向右侧）
    ax.annotate(
        "Better",  # 说明文字（可按需修改）
        rotation=45,  # 文字相对水平轴倾斜 45°
        rotation_mode="anchor",  # 围绕尾点旋转，更自
        xy=end, xytext=start,
        xycoords=ax.transAxes, textcoords=ax.transAxes,
        arrowprops=dict(
            arrowstyle="Simple,tail_width=17,head_width=35,head_length=18",  # 简单箭头
            color="#4db6ac",  # 深灰色
            lw=1.8,  # 线宽
            shrinkA=0, shrinkB=0,
            mutation_scale=1  # 箭头头部尺寸
        ),
        ha="left", va="center",  # 文本对齐方式
        fontsize=13, color="#000000",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=2)  # 半透明白底避免与折线重叠
    )

    # 提示：如果标签很长，可加 tight_layout
    fig.tight_layout()
    fig.savefig(out_file_path, dpi=300)
    # plt.show()
    print(f"Saved {out_file_path}")
    plt.close(fig)


def main():
    files = [
        (f_whole, 'Whole city'),
        (f_non,   'Non-slum'),
        (f_slum,       'Slum'),
    ]

    grouped_data = []
    for fp, cat in files:
        minutes, values = read_row_values(fp, target_row)
        g_labels, g_values = group_minutes(minutes, values, groups)
        grouped_data.append((cat, g_labels, g_values))

    # 折线图（单位若为百分比，可以把 y_label 改成 'Share (%)'）
    line_chart_three_categories(
        grouped_data,
    )

# ----------------------------
# 4) 示例调用（与你的数据一致）
# ----------------------------
if __name__ == '__main__':
    title_words = 'test'

    # 细粒度分组（示例与此前一致）
    groups = list(np.linspace(1, 120, num=120, dtype=np.int8))  # [[5, 10, 15], 20, 30, 60, 'Greater']
    # groups.append('Greater')

    x_axi_ticks = list(np.linspace(0, 120, num=121, dtype=np.int8))
    y_axi_ticks = list(np.linspace(0, 100, num=101, dtype=np.int8))

    # 横轴：只显示每隔 10 的刻度
    x_ticks_to_show = [i for i in x_axi_ticks if i % 10 == 0]
    # 纵轴：只显示每隔 20 的刻度
    y_ticks_to_show = [i for i in y_axi_ticks if i % 20 == 0]

    x_label = 'Walking Time Cost'
    y_label = 'Proportion of Population'
    # 选择哪一行：'Share fine' / 'Population' / 'Share coarse' 或数字索引 0/1/2
    target_row = 'Share coarse'

    # in city
    facility = 'Health'  # School  Health
    f_whole_dir = "./Curve/WholeLine"
    f_non_dir = "./Curve/NonSlumLine"
    f_slum_dir = "./Curve/SlumLine"

    pic_save_dir = r"./Curve"

    os.makedirs(pic_save_dir, exist_ok=True)
    file_list = glob.glob(os.path.join(f_whole_dir, '*.csv'))
    for f_whole in file_list:
        city_name = os.path.basename(f_whole).replace('_ProportionInPopulation.csv', '')

        f_non = os.path.join(f_non_dir, city_name + '_non_slum_distance.csv')
        f_slum = os.path.join(f_slum_dir, city_name + '_slum_distance.csv')
        out_file_path = os.path.join(pic_save_dir, city_name + '_curve.png')

        title_words = ''
        for string in city_name.split('_'):
            title_words += f' {string}'
        main()
