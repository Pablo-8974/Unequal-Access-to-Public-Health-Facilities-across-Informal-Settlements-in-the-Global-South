import glob
import os.path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import matplotlib.colors as mcolors
print('Import finished')


def minimize_distance(x_arr, value):
    if value in x_arr:
        return value

    sub_x_arr = x_arr[x_arr >= 0]
    x_distance = np.abs(sub_x_arr - value)
    pos = np.argmin(x_distance)
    return pos + len(x_arr) - len(sub_x_arr)        # 把负数部分的索引补上去


def get_color(num_colors):
    def create_elegant_pink_cmap():
        """创建优雅的玫红色渐变"""
        pink_palette = [
            (0.0, '#2E1B3B'),  # 深紫
            (0.2, '#6A1B9A'),  # 紫红
            (0.4, '#AD1457'),  # 玫瑰红
            (0.6, '#E91E63'),  # 玫红
            (0.8, '#F48FB1'),  # 浅玫红
            (1.0, '#FCE4EC')  # 极浅粉
        ]
        return mcolors.LinearSegmentedColormap.from_list('elegant_pink', pink_palette)

    # 设置颜色
    colors_slum = plt.cm.binary(np.linspace(0, 0.7, num_colors))
    # colors_non_slum = plt.cm.pink(np.linspace(0.2, 0.8, len(df.columns)))

    pink_cmap = create_elegant_pink_cmap()
    colors_non_slum = pink_cmap(np.linspace(0, 1, num_colors))

    return colors_slum[::-1], colors_non_slum


def get_blue_and_green_color(num_colors):
    green_palette = [
        (0.0, '#92C2A6'),
        (0.2, '#BCF4C5'),
        (0.4, '#BFE8C1'),
        (0.6, '#CEEFCC'),
        (0.8, '#E9F7E5'),
        (1.0, '#F7FEF0')
    # 92C2A6, #BCF4C5, #BFE8C1, #CEEFCC, #E9F7E5, #F7FEF0
    ]
    blue_palette = [
        (0.0, '#04579B'),(0.2, '#3492B2'),(0.4, '#58B8D1'),(0.6, '#6FC8CA'),(0.8, '#ACEEFE'),(1.0, '#D6F6FF')
        #04579B, #3492B2, #58BB8D1, #6FC8CA, #ACEEFE, #D6F6FF
    ]

    green_cmap = mcolors.LinearSegmentedColormap.from_list('elegant_green', green_palette)
    blue_cmap = mcolors.LinearSegmentedColormap.from_list('elegant_blue', blue_palette)

    colors_non_slum = green_cmap(np.linspace(0, 1, num_colors))
    colors_slum = blue_cmap(np.linspace(0, 1, num_colors))

    return colors_slum, colors_non_slum


def get_red_and_orange(num_colors):
    red_palette = [
        (0.0, '#97007E'),
        (0.2, '#CA178D'),
        (0.4, '#F14FA2'),
        (0.6, '#FF88B0'),
        (0.8, '#FEB7BF'),
        (1.0, '#FFD9D6'),
    ]
    orange_palette = [
        (0.0, '#3B2B1B'), (0.2, '#EF6C00'), (0.4, '#FFA726'), (0.6, '#FFCC80'), (0.8, '#FFE0B2'), (1.0, '#FFF3E0')
    ]

    green_cmap = mcolors.LinearSegmentedColormap.from_list('elegant_red', red_palette)
    blue_cmap = mcolors.LinearSegmentedColormap.from_list('elegant_orange', orange_palette)

    colors_non_slum = green_cmap(np.linspace(0, 1, num_colors))
    colors_slum = blue_cmap(np.linspace(0, 1, num_colors))

    return colors_slum, colors_non_slum


def single_csv_file():
    # 读取数据
    csv_path = r'C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\test\Blantyre.csv'
    height = 0.5        # 岭高

    df = pd.read_csv(csv_path)  # 替换为你的文件名
    city_name = os.path.basename(csv_path).replace('.csv', '')

    # 创建图形
    fig, ax = plt.subplots(figsize=(18, 6))

    # 确定共同的x轴范围（所有数据的范围）
    all_data = pd.concat([df[col].dropna() for col in df.columns])
    x_min = all_data.min()
    x_max = all_data.max()
    x_range = x_max - x_min
    x = np.linspace(x_min - 0.1 * x_range, x_max + 0.1 * x_range, 1000)
    # x = np.linspace(x_min, x_max, 1000)

    # 获取颜色数值
    colors_slum, colors_non_slum = get_color(len(df.columns))

    # 设置纵向间距
    vertical_spacing = 1
    overlap = 0.7  # 重叠程度

    # 设置指标标注
    ax.text(max(x) - 0.2 * x_range, len(df.columns) - vertical_spacing, 'Mean', fontsize=18, ha='center', va='center')
    ax.text(max(x) - 0.05 * x_range, len(df.columns) - vertical_spacing, 'Median', fontsize=18, ha='center', va='center')

    # 从下往上绘制每一列
    for i, column in enumerate(reversed(df.columns)):       # 先formal后informal
        if 'density' in column:
            continue

        data = df[column].dropna().values

        if len(data) > 1:
            base_color = colors_slum[i] if not (i % 2) else colors_non_slum[i]
            # 计算核密度估计
            kde = stats.gaussian_kde(data, bw_method=0.3)  # bw_method控制平滑度
            density = kde(x)

            # 归一化密度（使高度一致）
            density_normalized = density / np.max(density) * height

            # 计算纵向偏移，从上往下画，上面被下面遮蔽
            y_offset = len(df.columns) - i * vertical_spacing * (1 - overlap) - 1

            # 绘制填充区域
            ax.fill_between(x, density_normalized + y_offset, y_offset,
                            alpha=1, color=base_color, linewidth=0)

            # 绘制轮廓线
            ax.plot(x, density_normalized + y_offset, color='white', linewidth=1.2, alpha=1)
            # 绘制基底线
            # ax.plot(x, [y_offset] * len(x), color=base_color, linewidth=1.2, alpha=1)
            ax.hlines(y=y_offset, xmin=min(x), xmax=max(x),
                     color=base_color, linewidth=3, alpha=0.6, zorder=i)

            # 设置均值中位数标签
            mean_val = np.mean(data)
            ax.text(max(x) - 0.2 * x_range, y_offset + 0.4 * vertical_spacing * (1 - overlap), f"{mean_val:.2f}",
                    fontsize=18, ha='center', va='center', color='black')
            median_val = np.median(data)
            ax.text(max(x) - 0.05 * x_range, y_offset + 0.4 * vertical_spacing * (1 - overlap), f"{median_val:.2f}",
                    fontsize=18, ha='center', va='center', color='black')

            # 添加列名标签
            if i % 2:
                label_x = min(x) - 0.02 * x_range
                label_y = y_offset  # 标签位置在曲线中间
                ax.text(label_x, label_y, city_name,
                        fontsize=15, ha='center', va='center', rotation=45,
                        # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
                        )

    # 设置图形属性
    # ax.set_xlabel('Value', fontsize=12)
    # ax.set_title('Ridgeline Plot - Each Column on Separate Line', fontsize=14, pad=20)

    # 隐藏y轴（因为我们使用人工偏移）
    # ax.set_yticks([])
    # ax.set_ylabel('')

    # 设置y轴范围
    ax.set_ylim(y_offset, 2.25)

    # 美化图形
    sns.despine(left=True)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.show()
    # plt.savefig(csv_path.replace('csv', 'png'))
    # plt.close(fig)


def get_violin_xy(data, norm=False):
    fig, ax = plt.subplots()

    sns.violinplot(
        data=data,
        inner=None,
        alpha=1,
        linecolor='black',
        linewidth=5,
        # cut=1,
        fill=False
    )

    paths = ax.collections[0].get_paths()  # 第一个小提琴的路径
    vertices = paths[0].vertices  # 顶点坐标数组

    # 找到中心线（通常x=0，但可能有偏移）
    center_x = np.mean(vertices[:, 0])

    # 分离右侧半边（x >= center_x）
    right_mask = vertices[:, 0] >= center_x
    right_vertices = vertices[right_mask]

    # 按y值排序
    sorted_idx = np.argsort(right_vertices[:, 1])
    y_values = right_vertices[sorted_idx, 1]  # y轴位置
    x_density = right_vertices[sorted_idx, 0] - center_x  # 一半宽度

    # 归一化数据
    if norm:
        max_density = max(x_density)
        x_density = x_density / max_density

    # 筛选出正常值
    mask = y_values >= 0
    _x_density = x_density[mask]
    _y_values = y_values[mask]

    # 但是保存尾巴，存一个小于0的数值
    pos = len(x_density) - len(_x_density) - 1
    x_density = np.insert(_x_density, 0, x_density[pos])
    y_values = np.insert(_y_values, 0, y_values[pos])

    plt.close(fig)
    return x_density, y_values


def data_percentage_filter(data, percentage=98):
    if percentage < 100:
        data = np.array(data)
        percentile = np.percentile(data, percentage)
        filtered_data = data[data <= percentile]
        return filtered_data
    else:
        return data


def dir_csv2():
    # csv_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/Distance/distance_excel_with_whole'
    # save_path = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/Health/Distance'
    csv_dir = r'C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\excel_in_region'
    save_path = r'C:\Users\k\Desktop\slum\paper\data\Accessibility\Health\Distance\excel_in_region\RidgeRegion.png'

    height = 0.5  # 岭高
    vertical_spacing = 1    # 设置纵向间距
    overlap = 0.5  # 重叠程度
    filter_name = '2'   # 去掉某一列

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    csv_list = glob.glob(os.path.join(csv_dir, '*.csv'))

    # 创建图形
    fig, ax = plt.subplots()        # figsize=(18, 6)

    file_name_list = []
    all_data = []
    x_min = 0
    x_max = 0
    for csv_path in csv_list:
        # 读取所有数据后，确定共同的x轴范围（所有数据的范围）
        df = pd.read_csv(csv_path)
        file_name_list.append(os.path.basename(csv_path).replace('.csv', ''))

        for col in df.columns:
            if filter_name in col:
                continue

            origin_value = df[col].dropna().values
            col_data = data_percentage_filter(origin_value, 98)
            x_max = max([max(col_data), x_max])
            x_min = min([min(col_data), x_min])

            core_density, value = get_violin_xy(col_data, norm=True)
            all_data.append([core_density, value, origin_value])      # 密度值，和对应数值

        # 先informal 后formal
        temp = all_data[-2]
        all_data[-2] = all_data[-1]
        all_data[-1] = temp

    # file_name_list = file_name_list[::-1]
    x_range = x_max - x_min
    x = np.linspace(x_min, x_max + 0.1 * x_range, 1000)

    # 获取颜色数值
    colors_slum, colors_non_slum = get_color(len(all_data))

    # 设置指标标注
    ax.text(max(x) - 0.2 * x_range, len(all_data) - vertical_spacing, 'Mean', fontsize=18, ha='center', va='center')
    ax.text(max(x) - 0.05 * x_range, len(all_data) - vertical_spacing, 'Median', fontsize=18, ha='center', va='center')

    # 从下往上绘制每一列
    y_offset = len(all_data) - 1
    for i, (data, x_aix_range, origin_value) in enumerate(all_data):       # 后formal-双数再后informal-单数

        if len(data) > 1:
            base_color = colors_slum[i // 2] if (i % 2) else colors_non_slum[i // 2]

            if i == 0:
                pass
            elif not i % 2 and i != 0:
                y_offset -= vertical_spacing * (1 - overlap)
            y_offset -= vertical_spacing * (1 - overlap)
            # print(y_offset)

            # 归一化密度（使高度一致）
            density_normalized = data * height

            # 绘制填充区域
            ax.fill_between(x_aix_range, density_normalized + y_offset, y_offset,
                            alpha=1, color=base_color, linewidth=0, zorder=i)
            # 绘制轮廓线
            ax.plot(x_aix_range, density_normalized + y_offset, color='white', linewidth=1.2, alpha=1, zorder=i)
            # 绘制基底线
            ax.hlines(y=y_offset, xmin=min(x), xmax=max(x), color=base_color, linewidth=1.2, alpha=1, zorder=i)

            # 设置均值中位数标签
            mean_val = np.mean(origin_value)
            ax.text(max(x) - 0.2 * x_range, y_offset + 0.4 * vertical_spacing * (1 - overlap), f"{mean_val:.2f}",
                    fontsize=18, ha='center', va='center', color='black')
            median_val = np.median(origin_value)
            ax.text(max(x) - 0.05 * x_range, y_offset + 0.4 * vertical_spacing * (1 - overlap), f"{median_val:.2f}",
                    fontsize=18, ha='center', va='center', color='black')

            # 添加列名标签
            if not i % 2:
                label_x = min(x) - 0.02 * x_range
                label_y = y_offset  # 标签位置在曲线中间
                ax.text(label_x, label_y, file_name_list[i // 2],
                        fontsize=15, ha='center', va='center', rotation=45,
                        # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
                        )
                print(file_name_list[i // 2])

    # 设置y轴范围
    # ax.set_ylim(y_offset, 2.25)

    # 隐藏y轴（因为我们使用人工偏移）
    ax.set_yticks([])
    ax.set_ylabel('')

    # 美化图形
    sns.despine(left=True)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    # plt.show()
    plt.savefig(save_path, dpi=900)


def dir_csv():
    height = 0.5  # 岭高
    vertical_spacing = 1  # 设置纵向间距
    overlap = 0.8  # 重叠程度

    # x_aix_limit = [-10000, 25000]
    filter_name = '2'   # 去掉某一列

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    _csv_list = glob.glob(os.path.join(csv_dir, '*.csv'))
    csv_list = []
    if file_order is not None:
        for name in file_order:
            for csv_path in _csv_list:
                csv_name = os.path.basename(csv_path)
                if name in csv_name:
                    csv_list.append(csv_path)
        # csv_list = csv_list[::-1]
    else:
        csv_list = _csv_list
    print('File order: ', csv_list)

    # 创建图形
    print('create map')
    fig, ax = plt.subplots(figsize=(14, 10))

    print('get data')
    file_name_list = []
    all_data = []
    for csv_path in csv_list:
        # 读取所有数据后，确定共同的x轴范围（所有数据的范围）
        df = pd.read_csv(csv_path, na_values=["inf", "-inf", "Infinity"], keep_default_na=True)
        file_name_list.append(os.path.basename(csv_path).replace('.csv', '').split('_')[0])

        for col in df.columns:
            if filter_name in col:
                continue
            all_data.append(df[col].dropna())      # 密度值，和对应数值

    temp = pd.concat(all_data)
    x_max = temp.max()
    x_min = temp.min()
    x_range = x_max - x_min

    # 设定x轴范围
    if None in x_limit:
        x = np.linspace(x_min - 0.1 * x_range, x_max + 0.1 * x_range, 1000)
    else:
        x = np.linspace(min([x_min - 0.1 * x_range, x_limit[0]]), min([x_max + 0.1 * x_range, x_limit[1]]), 1000)
    # 设定数值范围
    print('X range: ', min(x), max(x))

    # 获取颜色数值
    colors_slum, colors_non_slum = color_func(len(all_data))

    # 设置指标标注
    if draw_metrics:
        mean_x_pos = max(x) * 0.82
        median_x_pos = max(x) * 0.95
        ax.text(mean_x_pos, len(all_data) - vertical_spacing + 0.1, 'Mean', fontsize=18, ha='center', va='center')
        ax.text(median_x_pos, len(all_data) - vertical_spacing + 0.1, 'Median', fontsize=18, ha='center', va='center')

    print('drawing')
    # 从下往上绘制每一列
    y_offset = len(all_data) - 1
    file_name_list = file_name_list[::-1]
    for i, data in enumerate(reversed(all_data)):       # formal-双数再后informal-单数

        if len(data) > 1:
            base_color = colors_slum[i // 2] if (i % 2) else colors_non_slum[i // 2]

            if i == 0:
                pass
            elif not i % 2 and i != 0:
                y_offset -= vertical_spacing * (1 - overlap)
            y_offset -= vertical_spacing * (1 - overlap)
            # print(y_offset)

            # 计算核密度估计
            kde = stats.gaussian_kde(data, bw_method=0.3)  # bw_method控制平滑度
            # density = kde(x)
            density = kde(x)

            # 归一化密度（使高度一致）
            density_normalized = density / np.max(density) * height

            # 绘制填充区域
            # ax.fill_between(x, density_normalized + y_offset, y_offset, alpha=1, color=base_color, linewidth=0, zorder=i)
            ax.fill_between(x, density_normalized + y_offset, y_offset, alpha=1, color=base_color, linewidth=0, zorder=i)

            # 设置均值中位数标签
            mean_val = np.mean(data)
            median_val = np.median(data)
            if draw_metrics:
                ax.text(mean_x_pos, (y_offset + 0.4 * vertical_spacing * (1 - overlap)), f"{mean_val:.2f}",
                        fontsize=18, ha='center', va='center', color='black', zorder=1000)
                ax.text(median_x_pos, (y_offset + 0.4 * vertical_spacing * (1 - overlap)), f"{median_val:.2f}",
                        fontsize=18, ha='center', va='center', color='black', zorder=1000)

            # 绘制均值虚线
            mean_val = int(mean_val)
            x_mean_loc = minimize_distance(x, mean_val)
            # print(mean_val, x_mean_loc)
            ax.vlines(x=mean_val, ymin=y_offset, ymax=y_offset+density_normalized[x_mean_loc+2],
                     color=(0, 176/255, 240/255), linewidth=1., alpha=1, zorder=i, linestyle='--')
            # 绘制中位数虚线
            median_val = int(median_val)
            x_median_loc = minimize_distance(x, median_val)
            # print(median_val, x_median_loc)
            ax.vlines(x=median_val, ymin=y_offset, ymax=y_offset+density_normalized[x_median_loc+2],
                     color='black', linewidth=1., alpha=1, zorder=i, linestyle='--')

            # 绘制轮廓线
            # ax.plot(x, density_normalized + y_offset, color='white', linewidth=1.2, alpha=1, zorder=i)
            ax.plot(x, density_normalized + y_offset, color='white', linewidth=1.2, alpha=1, zorder=i)
            # 绘制基底线
            ax.hlines(y=y_offset, xmin=min(x), xmax=max(x),
                     color=base_color, linewidth=1.2, alpha=1, zorder=i)

            # 添加列名标签
            if i % 2 and draw_name:
                ax.text(min(x) + 0.01 * x_range, y_offset + 0.35*vertical_spacing, file_name_list[i // 2],
                        fontsize=15, ha='center', va='center', rotation=0,
                        # bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
                        )
            print(file_name_list[i // 2])

    # 设置y轴范围
    # ax.set_ylim(y_offset, 2.25)
    if not None in x_limit:
        ax.set_xlim(min(x) - 0.01 * x_range, max(x) + 0.01 * x_range)

    # 隐藏y轴（因为我们使用人工偏移）
    ax.set_yticks([])
    ax.set_ylabel('')

    # 美化图形
    sns.despine(left=True)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    # plt.show()
    plt.savefig(save_path, dpi=300)
    plt.close()


if __name__ == '__main__':
    # single_csv_file()
    # Health School TimeCost Distance
    # csv_dir = '/intelnvme04/jiang.mingyu/slum/Accessibility/data/School/Distance/excel_in_region'
    # save_path = csv_dir + '/RidgeRegion.png'

    file_order = ['All', 'America', 'Southeast Asia', 'South Asia', 'Northern Africa', 'Southern Africa']
    file_order = file_order[::-1]
    draw_name = True
    draw_metrics = True

    # fig 2a
    csv_dir = './distance'
    save_path = 'fig2a.png'
    x_limit = [-5000, 25000]    # [-5000, 25000] medical distance, [-10000, 35000] school distance
    color_func = get_blue_and_green_color     # get_blue_and_green_color  get_red_and_orange
    print('fig 2a')
    dir_csv()

    # fig 2b
    csv_dir = './time'
    save_path = 'fig2b.png'
    x_limit = [-80, 350]    # [-5000, 25000] medical distance, [-10000, 35000] school distance
    color_func = get_red_and_orange     # get_blue_and_green_color  get_red_and_orange
    print('fig 2b')
    dir_csv()

