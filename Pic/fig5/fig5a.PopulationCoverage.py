import numpy as np
import matplotlib.pyplot as plt
import os
import glob


def get_parameters_from_csv(csv_path, pop_split_list):
    with open(csv_path, 'r') as src:
        src_rows = src.readlines()
        head = src_rows[0].split(',')

        time_list = np.array(head[1:121]).astype(np.float32)
        time_list = np.insert(time_list, 0, 0)

        # ————————————————————————————————————    数据预处理    ———————————————————————————————————— #
        data_rows = src_rows[1:]
        category_list = []      # 有几行，每行的名称是什么
        for i in range(len(data_rows)):
            data_rows[i] = data_rows[i].split(',')
            category_list.append(data_rows[i][0].replace(' ', '\n'))   # 类别名称
            data_rows[i] = np.float32(data_rows[i][1:121])         # 剩余的是人口比例数据
            data_rows[i] = np.insert(data_rows[i], 0, 0)

        # ——————————————————    柱状图，完成每一个类别针对每个人口比例划分的取值    —————————————————— #
        category_height = []     # 每行的绘图数据
        # category_col_bottom = []
        for i, cat in enumerate(category_list):  # 遍历每一个分组进行计算
            _category_time = []
            for j, pop_range in enumerate(pop_split_list):    # 计算人口百分比分组，在哪一分钟这个人口百分比能够到达设施
                data_rows[i] = (data_rows[i] / np.max(data_rows[i])) * 100      # 进行归一化计算，只求120分钟之内的人口
                pop_range_pos = np.where(data_rows[i]>=pop_range)[0]    # 取第一个就可以
                if not len(pop_range_pos):
                    _category_time.append(time_list[-1])
                else:
                    _category_time.append(time_list[pop_range_pos[0]])
            _category_time = np.array(_category_time)
            # category_col_bottom.append(_category_time[:-1])    #
            category_height.append(_category_time[1:] - _category_time[:-1])

        category_height = np.array(category_height).T
        # category_col_bottom = np.array(category_col_bottom).T

        # ——————————————————    折线图，完成每一个类别的人口加权平均通行时间    —————————————————— #
        # 首先要获取某一分钟内可以抵达目标的人口百分比，不是累计占比
        weighted_time_cost = []
        for row in data_rows:
            pp_in_minute = row[1:] - row[:-1]
            weighted_pp = pp_in_minute * time_list[1:]
            total_pp = np.sum(pp_in_minute)
            total_weighted_pp = np.sum(weighted_pp)
            weighted_time_cost.append(
                np.floor(total_weighted_pp / total_pp)
            )

    # return category_list, category_height, category_col_bottom, weighted_time_cost
    return category_list, category_height, weighted_time_cost


def plot_accessibility_analysis(
        file_path,
        n_quantiles=None,
        cutoff_percent=99.0,
        line_axis_range=None,
        output_file='accessibility_chart.png',
        bar_width=0.4,
        fig_size=(8,6)
):
    """
    绘制累积通行时间柱状图 + 加权平均时间折线图。

    参数:
    ----------
    file_path : str
        数据文件路径 (CSV或Excel).
        格式要求: 第一列为类别名称(Index)，表头为时间点(0, 15, 30...)，内容为累积百分比(0-100)。
    n_quantiles : int
        将人口划分成多少份 (例如 4 代表四分位数: 0-25%, 25-50%...)。
    cutoff_percent : float
        截断统计的人口比例 (默认 99，即丢弃最后 1% 的长尾数据)。
    line_axis_range : tuple or None
        控制折线图纵坐标的范围 (min, max)。
        如果为 None，则自动适应数据。手动设置可控制折线在图表中的上下位置。
    output_file : str
        保存图片的文件名。
    """

    # 1. 数据读取与预处理
    # -------------------------------------------------------
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件未找到: {file_path}")

    # 生成切分点 (例如 n=4, cutoff=99 -> [0, 24.75, 49.5, 74.25, 99.0])
    # 注意：这里是按 cutoff_percent 切分，而不是 100
    if isinstance(n_quantiles, list):
        percent_steps = n_quantiles
        n_quantiles = len(n_quantiles)-1
    else:
        percent_steps = np.linspace(0, cutoff_percent, n_quantiles + 1)

    categories, segments_data, avg_times = get_parameters_from_csv(file_path, percent_steps)

    # 3. 绘图执行
    # -------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=fig_size)

    # 动态生成颜色映射 (从绿色到红色)
    # 使用 'RdYlGn_r' (Red-Yellow-Green reversed) 使得绿色在底部(快)，红色在顶部(慢)
    cmap = plt.cm.get_cmap('RdYlGn_r')
    # 生成 n_quantiles 个颜色，取值范围 0.2 到 0.9 避免过淡或过黑
    colors = [cmap(x) for x in np.linspace(0.8, 0.2, n_quantiles)]
    bottom_vals = np.zeros(len(categories))

    # 循环绘制每一段堆叠
    for i in range(n_quantiles):
        # 标签逻辑
        start_p = percent_steps[i]
        end_p = percent_steps[i+1]
        label_text = f"{start_p:.1f}% - {end_p:.1f}% Pop"

        ax1.bar(
            categories,
            segments_data[i],
            bottom=bottom_vals,
            label=label_text,
            color=colors[i],
            edgecolor='white',
            width=bar_width,
            alpha=0.85
        )
        bottom_vals += np.array(segments_data[i])

    # 设置主坐标轴 (左侧)
    # ax1.set_ylabel(f'Time Cost (Minutes) - Top {cutoff_percent}% Pop', fontsize=16, fontweight='bold')
    ax1.set_xlabel(os.path.basename(file_path).split('_')[0], fontsize=18, fontweight='bold')
    # ax1.tick_params(axis='x', labelsize=12)
    ax1.set_ylim(0, 139)
    # ax1.grid(axis='y', linestyle='--', alpha=0.4)
    # 关闭纵坐标（刻度 + 标签）
    ax1.yaxis.set_visible(False)
    # ax1.tick_params(axis='y', labelsize=12, rotation=90)

    # 添加总时间标签 (P99)
    for idx, val in enumerate(bottom_vals):
        ax1.text(idx, val + (val * 0.02), f"{val}m",   # "PP{int(cutoff_percent)}: {val:.1f}m"
                 ha='center', fontsize=10, fontweight='bold', color='#333333')

    # 4. 绘制折线图 (双轴)
    # -------------------------------------------------------
    ax2 = ax1.twinx()
    line_plot = ax2.plot(
        categories,
        avg_times,
        color='#2c3e50',
        marker='D',
        markersize=10,
        linewidth=3,
        linestyle='--',
        label='Weighted Avg Time'
    )

    # 关键：折线位置控制参数
    # ax2.set_ylabel('Weighted Average Time (min)', fontsize=12, fontweight='bold', color='#2c3e50')
    if line_axis_range:
        # 如果用户指定了范围，强制设置
        ax2.set_ylim(line_axis_range[0], line_axis_range[1])
    else:
        # 默认逻辑：为了不让折线和柱子重叠，让折线的 Y 轴范围稍微宽一点
        # 或者你可以设置一个偏移量
        y_min = min(avg_times) * 0.8
        y_max = max(avg_times) * 1.2
        ax2.set_ylim(y_min, y_max)
    # 关闭纵坐标（刻度 + 标签）
    ax2.yaxis.set_visible(False)

    # 为折线添加数值标签
    for i, v in enumerate(avg_times):
        ax2.annotate(
            f"{v:.1f}m",
            (i, v),
            xytext=(0, 10),
            textcoords='offset points',
            ha='center',
            fontweight='bold',
            color='#2c3e50',
            # bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7)
        )

    # 5. 图例与布局优化
    # -------------------------------------------------------
    # plt.title(f'Accessibility Analysis: Distribution (Top {cutoff_percent}%) & Average Time', fontsize=14, pad=20)

    # 合并图例
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    # 将折线图例放在最上面
    final_handles = handles2 + handles1[::-1]  # 反转柱状图顺序符合视觉习惯
    final_labels = labels2 + labels1[::-1]

    # ax1.legend(final_handles, final_labels, loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    # ax1.spines['bottom'].set_visible(False)
    ax1.spines['left'].set_visible(False)

    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    # ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)

    # # 隐藏所有柱子（bars）
    # for bar in ax1.patches:
    #     bar.set_visible(False)
    # for bar in ax2.patches:
    #     bar.set_visible(False)
    # # 隐藏柱子上的数值标签（如果有）
    # for text in ax1.texts:
    #     text.set_visible(False)
    # for text in ax2.texts:
    #     text.set_visible(False)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', transparent=True)
    print(f"图表已生成并保存至: {output_file}")
    # plt.show()
    plt.close()


def dir_loop():
    csv_dir = './fig5a_PopulationCoverage'
    save_dir = "./fig5a_PopulationCoverage"

    csv_10km_list = glob.glob(os.path.join(csv_dir, '*.csv'))
    for csv_path in csv_10km_list:
        city_name = os.path.basename(csv_path)
        save_path = os.path.join(save_dir, city_name.replace('csv', 'png'))

        plot_accessibility_analysis(
            file_path=csv_path,
            n_quantiles=7,  # [0, 15, 30, 45, 60 , 75, 90, 99]
            cutoff_percent=99,
            line_axis_range=(-250, 45),  # 这里的参数控制折线在图上的视觉高度
            output_file=save_path,
            bar_width=0.7,
            fig_size=(3, 8)
        )
        print(city_name)


if __name__ == "__main__":
    dir_loop()
