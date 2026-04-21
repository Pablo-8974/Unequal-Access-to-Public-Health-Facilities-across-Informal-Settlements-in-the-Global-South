import glob
import os.path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import matplotlib.colors as mcolors
import matplotlib as mpl
mpl.rcParams["font.family"] = "DejaVu Sans"
print('Import finished')


def minimize_distance(x_arr, value):
    if value in x_arr:
        return value

    sub_x_arr = x_arr[x_arr >= 0]
    x_distance = np.abs(sub_x_arr - value)
    pos = np.argmin(x_distance)
    return pos + len(x_arr) - len(sub_x_arr)        # 把负数部分的索引补上去


def single_csv_file():
    # 读取数据
    csv_path = 'Weighted.csv'
    height = 0.5        # 岭高
    # 设置纵向间距
    vertical_spacing = 1
    overlap = 0.8  # 重叠程度

    df = pd.read_csv(csv_path)  # 替换为你的文件名

    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 6))

    # 数据清洗
    new_data = {}
    all_data = []
    for col in df.columns:
        data = np.array(df[col].dropna())
        data = np.array(data[data > 0])
        # data = data[data <= 1.1]
        new_data[col] = data

        all_data.append(data)
    all_data = np.concatenate(all_data)
    overall_median = np.median(all_data)

    df = pd.DataFrame({
        col: pd.Series(values)
        for col, values in new_data.items()
    })

    # 确定共同的x轴范围（所有数据的范围）
    x_min = -50
    x_max = 200
    x_range = x_max - x_min
    x = np.linspace(x_min, x_max, 1000)

    # 获取颜色数值
    colors = [[108, 85, 127, 255], [104, 114, 147, 255], [95, 144, 149, 255], [104, 177, 150, 255], [154, 205, 129, 255]]
    for i in range(len(colors)):
        colors[i] = np.array(colors[i]) / 255
    colors = colors[:len(df.columns)]
    colors = colors[::-1]

    # 设置指标标注
    ax.text(max(x) - 0.2 * x_range, len(df.columns) - vertical_spacing*0.8, 'Mean', fontsize=15, ha='center', va='center')
    ax.text(max(x) - 0.05 * x_range, len(df.columns) - vertical_spacing*0.8, 'Median', fontsize=15, ha='center', va='center')

    # 从下往上绘制每一列
    class_label_pos = []
    for i, column in enumerate(reversed(df.columns)):       # 先formal后informal
        data = df[column].dropna().values

        if len(data) > 1:
            base_color = colors[len(df.columns)-i-1]
            # 计算核密度估计
            kde = stats.gaussian_kde(data, bw_method=0.3)  # bw_method控制平滑度
            density = kde(x)

            # 归一化密度（使高度一致）
            density_normalized = density / np.max(density) * height

            # 计算纵向偏移，从上往下画，上面被下面遮蔽
            y_offset = len(df.columns) - i * vertical_spacing * (1 - overlap) - 1
            class_label_pos.append(y_offset + 0.6 * vertical_spacing * (1 - overlap))

            # 绘制填充区域
            ax.fill_between(x, density_normalized + y_offset, y_offset,
                            alpha=0.8, color=base_color, linewidth=0, zorder=i)

            # 设置均值中位数标签
            mean_val = np.mean(data)
            ax.text(max(x) - 0.2 * x_range, y_offset + 0.6 * vertical_spacing * (1 - overlap), f"{mean_val:.2f}",
                    fontsize=15, ha='center', va='center', color='black')
            # 用红色实线标注均值位置
            mean_val = int(mean_val)
            x_mean_loc = minimize_distance(x, mean_val)
            ax.vlines(x=mean_val, ymin=y_offset, ymax=y_offset+density_normalized[x_mean_loc],
                      colors='red', linestyles='solid', linewidth=1.5, zorder=i)

            median_val = np.median(data)
            ax.text(max(x) - 0.05 * x_range, y_offset + 0.6 * vertical_spacing * (1 - overlap), f"{median_val:.2f}",
                    fontsize=15, ha='center', va='center', color='black')
            # 用红色实线标注均值位置
            median_val = int(median_val)
            x_median_loc = minimize_distance(x, median_val)
            ax.vlines(x=median_val, ymin=y_offset, ymax=y_offset+density_normalized[x_median_loc],
                      colors='blue', linestyles='solid', linewidth=1.5, zorder=i)

            # 绘制轮廓线
            ax.plot(x, density_normalized + y_offset, color='black', linewidth=1.2, alpha=1, zorder=i)
            # 绘制基底线
            # ax.plot(x, [y_offset] * len(x), color=base_color, linewidth=1.2, alpha=1)
            # ax.hlines(y=y_offset, xmin=min(x), xmax=max(x),
            #          color=base_color, linewidth=3, alpha=0.6, zorder=i)

            # # 添加列名标签
            # if i % 2:
            #     label_x = min(x) - 0.02 * x_range
            #     label_y = y_offset  # 标签位置在曲线中间
            #     ax.text(label_x, label_y, city_name,
            #             fontsize=15, ha='center', va='center', rotation=45,
            #             # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
            #             )

    # 设置图形属性
    ax.set_xlabel('Population Weighted Relative Walking Speed', fontsize=18)
    # ax.set_title('Ridgeline Plot - Each Column on Separate Line', fontsize=14, pad=20)
    plt.xticks(fontsize=0)

    # y轴
    ax.set_yticks(class_label_pos)
    ax.set_yticklabels(["Informal 3km", "Informal 10km", "Formal 3km", "Formal 5km", "Formal 10km"], fontsize=15)
    ax.set_ylabel('Settlement Types', fontsize=18)

    # 设置y轴范围
    # ax.set_ylim(y_offset, 2.25)

    # 美化图形
    sns.despine(right=True, top=True)
    # ax.grid(True, axis='x', alpha=0.5, linestyle='--')

    plt.tight_layout()
    # plt.show()
    plt.savefig('./fig3c.png', dpi=300, transparent=False, bbox_inches="tight")
    plt.close(fig)


if __name__ == '__main__':
    single_csv_file()
