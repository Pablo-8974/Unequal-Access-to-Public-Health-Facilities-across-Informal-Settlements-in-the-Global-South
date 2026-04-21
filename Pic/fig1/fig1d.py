import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats


def load_regional_data(filepath):
    """
    从 Excel 文件中加载区域数据。
    文件结构应与示例一致：Sheet1 中，每个区域以一行区域名称开始，
    随后是该区域的城市数据行（城市名、非正规住区比例、医疗设施密度），
    区域之间由空行分隔。
    """
    # 读取 Excel 文件
    try:
        df_raw = pd.read_excel(filepath, sheet_name=0, header=None, dtype=str, engine='openpyxl')
    except:
        try:
            df_raw = pd.read_excel(filepath, sheet_name=0, header=None, dtype=str, engine='xlrd')
        except:
            df_raw = pd.read_excel(filepath, sheet_name=0, header=None, dtype=str)

    data_records = []
    current_region = None

    for idx, row in df_raw.iterrows():
        # 获取 A、B、C 列的值
        a_val = str(row[0]).strip() if pd.notna(row[0]) else ''
        b_val = str(row[1]).strip() if pd.notna(row[1]) else ''
        c_val = str(row[2]).strip() if pd.notna(row[2]) else ''

        # 跳过完全空的行
        if not a_val and not b_val and not c_val:
            continue

        # 检查是否是区域标题行
        if a_val and ('proportion' in b_val.lower() or 'informal' in b_val.lower() or
                      'medical' in c_val.lower() or 'density' in c_val.lower()):
            current_region = a_val
            continue

        # 检查是否是数据行
        if a_val and b_val and c_val and current_region:
            try:
                informal = float(b_val)
                medical = float(c_val)

                if informal >= 0 and medical >= 0:
                    data_records.append({
                        'Region': current_region,
                        'City': a_val,
                        'Informal_Settlement': informal,
                        'Medical_Density': medical
                    })
            except ValueError:
                continue

    df = pd.DataFrame(data_records)
    return df


def plot_regression_lines_only(df):
    """
    绘制子区域回归线（不带置信区间）和带置信区间的全局回归线。
    不显示散点。回归线限制在实际数据范围内。
    """
    if len(df) == 0:
        print("没有数据可绘制")
        return

    # 设置绘图风格
    # sns.set_style('whitegrid')
    plt.figure(figsize=(6.5, 13))

    # 获取唯一的区域列表
    regions = df['Region'].unique()
    print(f"发现的区域: {list(regions)}")

    # 使用调色板 - 为每个区域分配不同颜色
    palette = sns.color_palette('husl', n_colors=len(regions))
    color_map = {region: palette[i] for i, region in enumerate(regions)}

    # 存储每个区域的回归统计信息
    regression_stats = []

    # 获取整体数据范围
    x_min, x_max = df['Informal_Settlement'].min(), df['Informal_Settlement'].max()

    # 为每个区域绘制回归线（不带置信区间）
    for region in regions:
        subset = df[df['Region'] == region]

        if len(subset) < 2:  # 至少需要2个点才能计算回归
            print(f"警告: {region} 只有 {len(subset)} 个数据点，无法绘制回归线")
            continue

        # 计算线性回归
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            subset['Informal_Settlement'], subset['Medical_Density'])
        r_squared = r_value ** 2

        # 获取该区域的数据范围
        region_x_min, region_x_max = subset['Informal_Settlement'].min(), subset['Informal_Settlement'].max()
        # 只在该区域数据范围内生成x值
        # region_x_range = np.linspace(x_min, x_max, 100)
        region_x_range = np.linspace(region_x_min, region_x_max, 100)

        # 计算回归线
        y_line = slope * region_x_range + intercept

        # 先画散点
        plt.scatter(
            subset['Informal_Settlement'],
            subset['Medical_Density'],
            color=color_map[region],
            alpha=1,
            s=50,
            edgecolor='white',
            linewidth=0.5
        )

        # 绘制回归线（不带置信区间）- 只在该区域数据范围内
        plt.plot(region_x_range, y_line,
                 color=color_map[region],
                 linewidth=2.5,
                 label=f'{region} (R={r_value:.3f})')       # n={len(subset)},

        regression_stats.append({
            'Region': region,
            'n': len(subset),
            'Slope': slope,
            'Intercept': intercept,
            'R²': r_squared,
            'P-value': p_value,
            'Std_Error': std_err,
            'X_min': region_x_min,
            'X_max': region_x_max,
            'Y_min': np.min(y_line),
            'Y_max': np.max(y_line)
        })

    # 计算全局回归统计
    global_slope, global_intercept, global_r, global_p, global_std = stats.linregress(
        df['Informal_Settlement'], df['Medical_Density'])
    global_r2 = global_r ** 2

    # 计算全局回归的置信区间
    n = len(df)
    x_mean = np.mean(df['Informal_Settlement'])
    x_var = np.var(df['Informal_Settlement'], ddof=1)
    se_slope = global_std / np.sqrt(x_var * (n - 1))

    # 在整体数据范围内生成x值
    x_global = np.linspace(x_min, x_max, 100)
    y_global = global_slope * x_global + global_intercept

    # 计算置信区间
    t_value = stats.t.ppf(0.975, n - 2)  # 95% 置信区间的 t 值
    y_pred_se = np.sqrt(global_std ** 2 * (1 / n + (x_global - x_mean) ** 2 / ((n - 1) * x_var)))
    ci_upper = y_global + t_value * y_pred_se
    ci_lower = y_global - t_value * y_pred_se

    # 绘制全局回归线
    plt.plot(x_global, y_global,
             color='black',
             linewidth=3,
             label=f'Global trend (n={n}, R={global_r:.3f})')

    # 绘制全局回归线
    sns.regplot(x='Informal_Settlement', y='Medical_Density', data=df,
                scatter=False,
                ci=95,
                line_kws={'color': 'black', 'linewidth': 0, 'label': f'Global trend (n={len(df)})'},
                scatter_kws={'alpha': 0}
                )

    # 绘制置信区间阴影
    # plt.fill_between(x_global, ci_lower, ci_upper,
    #                  color='gray', alpha=0.5,
    #                  label='95% Confidence Interval')

    # 设置标题和轴标签
    # plt.title('Regional Regression Lines and Global Trend\nwith 95% Confidence Interval',
    #           fontsize=14, fontweight='bold')
    plt.xlabel('Proportion of Informal Settlement Area (%)', fontsize=15, fontweight='bold')
    plt.ylabel('Medical Facility Density (per km²)', fontsize=15, fontweight='bold')

    # 添加网格
    plt.grid(True, alpha=0.3)

    # 设置x轴从0开始（如果最小值接近0）
    # if x_min > 0 and x_min < 1:
    #     plt.xlim(left=0)
    # else:
    #     plt.xlim(left=max(0, x_min - 0.1))
    # plt.xlim(right=x_max)
    plt.xlim(0, x_max + x_min)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # 图例 - 放在图外右侧
    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Region', fontsize=12)
    # plt.legend(loc='upper left', title_fontsize=12, fontsize=12, title='Region')
    plt.tight_layout()
    # plt.show()
    plt.savefig(r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig1\fig1d.png",
                dpi=300, transparent=True)
    plt.close()

    # 打印详细统计信息
    print("\n" + "=" * 60)
    print("各子区域回归分析统计")
    print("=" * 60)

    # 创建统计表格
    stats_df = pd.DataFrame(regression_stats)
    stats_df = stats_df.round(4)
    # stats_df.to_excel(r'C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig1\regress.xlsx')
    print(stats_df.to_string(index=False))

    # 打印全局统计
    print("\n" + "=" * 60)
    print("全局回归分析统计")
    print("=" * 60)
    print(f"总城市数: {n}")
    print(f"全局斜率: {global_slope:.4f}")
    print(f"全局截距: {global_intercept:.4f}")
    print(f"全局R²: {global_r2:.4f}")
    print(f"全局P值: {global_p:.4f}")
    print(f"全局标准误: {global_std:.4f}")
    print(f"数据范围: {x_min:.3f} - {x_max:.3f}")

    # 打印每个区域的详细统计
    print("\n" + "=" * 60)
    print("各区域数据统计")
    print("=" * 60)
    for region in regions:
        subset = df[df['Region'] == region]
        print(f"\n{region}:")
        print(f"  城市数量: {len(subset)}")
        print(
            f"  非正规住区比例范围: {subset['Informal_Settlement'].min():.3f} - {subset['Informal_Settlement'].max():.3f}")
        print(f"  医疗设施密度范围: {subset['Medical_Density'].min():.6f} - {subset['Medical_Density'].max():.6f}")


# 使用示例
if __name__ == '__main__':
    # 请将文件路径替换为您的实际路径
    file_path = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig1\fig1d.density_proportion.xlsx"  # 修改为您的文件路径

    df = load_regional_data(file_path)

    print("\n" + "=" * 50)
    print("数据加载成功！")
    print("=" * 50)
    print(f"总城市数: {len(df)}")
    print("\n数据区域分布：")
    print(df['Region'].value_counts())
    plot_regression_lines_only(df)
