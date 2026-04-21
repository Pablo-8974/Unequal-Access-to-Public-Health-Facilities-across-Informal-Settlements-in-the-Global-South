import os.path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
from matplotlib import patches
from skimage.filters.rank import maximum


def draw_full_violin():
    # 1. 读取数据
    input_data = pd.read_csv(sub_file_path)

    # 2. 选择需要的列
    input_data = input_data[input_data.columns.tolist()]

    # 3. 转换数据格式（长格式）
    plot_data = input_data.melt(var_name="condition", value_name="value")
    plot_data = plot_data.dropna(subset=["value"])

    # 4. 绘制箱型图 + 半小提琴图
    plt.figure(figsize=(8, 6))
    palette = sns.color_palette("Set1")

    if violin_flag:
        if filter_data_flag:
            filtered_data = pd.DataFrame(columns=["condition", "value"])
            for cond in plot_data["condition"].unique():
                subset = plot_data[plot_data["condition"] == cond]
                q1 = subset["value"].quantile(0.25)
                q3 = subset["value"].quantile(0.75)
                iqr = q3 - q1
                lower_whisker = q1 - 1.5 * iqr
                upper_whisker = q3 + 1.5 * iqr
                subset_filtered = subset[(subset["value"] >= lower_whisker) & (subset["value"] <= upper_whisker)]
                filtered_data = pd.concat([filtered_data, subset_filtered])
        else:
            filtered_data = plot_data

        sns.violinplot(
            x="condition", y="value", data=filtered_data,
            inner=None,  # 不显示内部元素
            palette=palette,  # 自动根据分组上色
            cut=0,  # 不超出数据范围
            scale="width", alpha=0.2,
            linewidth=0.0,
        )

    # 修改 x 轴标签
    plt.xticks([x for x in range(len(col_name))], col_name, fontsize=15)

    # sns.boxplot(
    #     x="condition", y="value", data=plot_data,
    #     width=0.3, notch=True, showcaps=True,
    #     boxprops={'alpha': 0.8, 'facecolor': 'white'},
    #     medianprops={'color': 'black'},
    #     showfliers=False
    # )
    sns.boxplot(
        x="condition", y="value", data=plot_data,
        width=0.1, notch=True, showcaps=True,
        palette=palette,  # 自动根据分组上色
        medianprops={'color': 'black'},
        showfliers=False
    )

    # 5. 设置标题和样式
    plt.title(title, fontsize=20)
    plt.xlabel(xlabel, fontsize=15)
    plt.ylabel(ylabel, fontsize=15)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    sns.set_palette("Set1")
    plt.grid(True, linestyle='--', alpha=0.35)

    # plt.show()
    save_path = os.path.join(save_dir, sub_file_name + '.png')

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(sub_file_name)


def draw_violin():
    df = pd.read_csv(sub_file_path, sep=",", na_filter=False, keep_default_na=False)

    required_cols = df.columns.tolist()[:select_col]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"CSV 中缺少列: {c}")
    df = df[required_cols].copy()

    plotData = df.melt(value_vars=required_cols, var_name="condition", value_name="value")
    plotData = plotData[plotData["value"].astype(str).str.strip() != ""]
    plotData["value"] = pd.to_numeric(plotData["value"], errors="coerce")
    plotData = plotData.dropna(subset=["value"]).reset_index(drop=True)

    filtered_data = pd.DataFrame(columns=["condition", "value"])
    if maximum_value:
        for cond in plotData["condition"].unique():
            subset = plotData[plotData["condition"] == cond]
            subset_filtered = subset[subset['value'] <= maximum_value]
            filtered_data = pd.concat([filtered_data, subset_filtered])
        plotData = filtered_data
    elif maximum_percentage:
        for cond in plotData["condition"].unique():
            subset = plotData[plotData["condition"] == cond]
            q1 = subset["value"].quantile(maximum_percentage)
            print('filter by', q1)
            subset_filtered = subset[subset['value'] <= q1]
            filtered_data = pd.concat([filtered_data, subset_filtered])
        plotData = filtered_data
    del filtered_data

    # conditions = ["Informal", "Formal"]
    conditions = required_cols
    base_positions = {cond: i for i, cond in enumerate(conditions)}  # slum->0, non_slum->1

    # =========================
    # 2) 样式与参数
    # =========================
    sns.set_theme(style="white")
    palette = sns.color_palette("Set1", n_colors=len(conditions))
    color_map = {cond: palette[i] for i, cond in enumerate(conditions)}

    # =========================
    # 3) 绘图：sns.violinplot（遮左半）+ 箱型图（在左侧）
    # =========================
    fig, ax = plt.subplots(figsize=(2.5, 6))

    if violin_flag:
        if filter_data_flag:
            for cond in plotData["condition"].unique():
                subset = plotData[plotData["condition"] == cond]
                q1 = subset["value"].quantile(0.25)
                q3 = subset["value"].quantile(0.75)
                iqr = q3 - q1
                lower_whisker = q1 - 1.5 * iqr
                upper_whisker = q3 + 1.5 * iqr
                subset_filtered = subset[(subset["value"] >= lower_whisker) & (subset["value"] <= upper_whisker)]
                filtered_data = pd.concat([filtered_data, subset_filtered])
        else:
            filtered_data = plotData

        # 画完整小提琴（不绘制内部统计）
        sns.violinplot(
            data=filtered_data,
            x="condition",
            y="value",
            palette=palette,
            inner=None,  # 不在小提琴内部画箱线
            cut=0,  # 限制到数据范围（类似 R 的 trim=TRUE）
            density_norm="width",  # 最大水平宽度恒定（便于遮罩半宽）
            linewidth=0.0,
            alpha=violin_alpha
        )

    # 叠加箱型图（在左侧：类别中心 i - 0.25）
    for i, cond in enumerate(conditions):
        vals = plotData.loc[plotData["condition"] == cond, "value"].to_numpy()
        bp = ax.boxplot(
            [vals],
            positions=[i],  # 左侧位置
            widths=0.7,
            notch=True,
            showfliers=False,
            patch_artist=True,
            zorder=4
        )

        for element in ["boxes", "caps", "whiskers", "medians"]:
            plt.setp(bp[element], color="black", linewidth=1.2)
        plt.setp(bp["boxes"], facecolor=color_map[cond], alpha=box_alpha)

    # =========================
    # 4) 标题、轴标签、刻度与风格
    # =========================
    ax.minorticks_on()
    # 主刻度（major ticks）样式：长度、线宽、方向；这里在下/左侧显示
    ax.tick_params(axis='x', which='major', length=6, width=1.2, direction='out', bottom=True, top=False)
    ax.tick_params(axis='y', which='major', length=6, width=1.2, direction='out', left=True, right=False,
                   rotation=90)

    for label in ax.get_yticklabels():
        # label.set_ha("center")
        label.set_va("center")

    # ax.set_title(title, fontsize=20)
    # ax.set_xlabel(xlabel, fontsize=15)
    ax.set_ylabel(ylabel, fontsize=25)
    # ax.set_title(' ', fontsize=20)
    # ax.set_xlabel(' ', fontsize=15)
    # ax.set_ylabel(' ', fontsize=15)

    ax.set_xticks([0, 1], labels=["IS", "FS"])

    # ax.set_xticks([base_positions[c] for c in conditions])
    # ax.set_xticklabels(col_name[:select_col], fontsize=15)       # col_name
    ax.tick_params(axis="y", labelsize=17)
    ax.tick_params(axis="x", labelsize=17)
    ax.locator_params(axis="y", nbins=6)
    sns.despine(ax=ax)
    ax.grid(True, linestyle='--', alpha=0.35)

    fig.tight_layout()

    save_path = os.path.join(save_dir, sub_file_name + '.png')
    fig.savefig(save_path, dpi=300)
    # plt.show()
    plt.close()
    print(sub_file_name)


def draw_half_violin():
    df = pd.read_csv(sub_file_path, sep=",", na_filter=False, keep_default_na=False)

    required_cols = df.columns.tolist()[:select_col]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"CSV 中缺少列: {c}")
    df = df[required_cols].copy()

    plotData = df.melt(value_vars=required_cols, var_name="condition", value_name="value")
    plotData = plotData[plotData["value"].astype(str).str.strip() != ""]
    plotData["value"] = pd.to_numeric(plotData["value"], errors="coerce")
    plotData = plotData.dropna(subset=["value"]).reset_index(drop=True)

    # conditions = ["Slum", "non-Slum", "City"]
    conditions = required_cols
    base_positions = {cond: i for i, cond in enumerate(conditions)}  # slum->0, non_slum->1

    # =========================
    # 2) 样式与参数
    # =========================
    sns.set_theme(style="white")
    palette = sns.color_palette("Set1", n_colors=len(conditions))
    color_map = {cond: palette[i] for i, cond in enumerate(conditions)}

    # 箱型图要在左侧：相对类别中心左移 0.25
    box_nudge_left = 0.15

    # =========================
    # 3) 绘图：sns.violinplot（遮左半）+ 箱型图（在左侧）
    # =========================
    fig, ax = plt.subplots(figsize=(8, 6))

    if violin_flag:
        if filter_data_flag:
            filtered_data = pd.DataFrame(columns=["condition", "value"])
            for cond in plotData["condition"].unique():
                subset = plotData[plotData["condition"] == cond]
                q1 = subset["value"].quantile(0.25)
                q3 = subset["value"].quantile(0.75)
                iqr = q3 - q1
                lower_whisker = q1 - 1.5 * iqr
                upper_whisker = q3 + 1.5 * iqr
                subset_filtered = subset[(subset["value"] >= lower_whisker) & (subset["value"] <= upper_whisker)]
                filtered_data = pd.concat([filtered_data, subset_filtered])
        else:
            filtered_data = plotData

        # 提前设定 y 轴范围（遮罩需要覆盖整个可视区域）
        ymin = filtered_data["value"].min()
        ymax = filtered_data["value"].max()
        pad = (ymax - ymin) * 0.05 if ymax > ymin else 1.0
        ax.set_ylim(ymin - pad, ymax + pad)

        # 画完整小提琴（不绘制内部统计）
        sns.violinplot(
            data=filtered_data,
            x="condition",
            y="value",
            palette=palette,
            inner=None,  # 不在小提琴内部画箱线
            cut=0,  # 限制到数据范围（类似 R 的 trim=TRUE）
            scale="width",  # 最大水平宽度恒定（便于遮罩半宽）
            width=v_width,  # 控制视觉最大宽度
            linewidth=0.0,
            ax=ax
        )

        # 设置透明度和颜色（保障风格一致）
        # seaborn 会创建一个 PolyCollection 列表（每个类别一个主 violin body）
        # 简单遍历 collections 并按顺序赋色与透明度
        count = 0
        for coll in ax.collections:
            # 只处理主填充小提琴的集合（有面填充）
            if hasattr(coll, "get_facecolor"):
                fc = coll.get_facecolor()
                if fc is not None and len(fc) > 0:
                    # 为稳妥，仅前 len(conditions) 个主 violin body 赋值
                    if count < len(conditions):
                        coll.set_alpha(violin_alpha)
                        coll.set_edgecolor("none")
                        coll.set_facecolor(palette[count])
                        count += 1

        # 遮罩：对每个类别遮掉左半，使之成为“右半小提琴”
        facecol = ax.get_facecolor()  # 与背景同色
        for i, cond in enumerate(conditions):
            # 小提琴中心在类别索引 i，半宽为 v_width/2
            # 需遮掉 [i - v_width/2, i] 这段的水平范围
            left_edge = i - (v_width / 2.0)
            rect = patches.Rectangle(
                (left_edge, ymin),  # 左下角   - pad
                v_width / 2.0,  # 遮掉左半宽度
                (ymax + pad) - (ymin - pad),  # 高度覆盖整个 y 轴可视范围
                facecolor=facecol,
                edgecolor=facecol,
                zorder=3,  # 在小提琴之上
                transform=ax.transData
            )
            ax.add_patch(rect)

    # 叠加箱型图（在左侧：类别中心 i - 0.25）
    for i, cond in enumerate(conditions):
        vals = plotData.loc[plotData["condition"] == cond, "value"].to_numpy()
        bp = ax.boxplot(
            [vals],
            positions=[i - box_nudge_left],  # 左侧位置
            widths=0.1,
            notch=True,
            showfliers=False,
            patch_artist=True,
            zorder=4
        )
        for element in ["boxes", "caps", "whiskers", "medians"]:
            plt.setp(bp[element], color="black", linewidth=1.2)
        plt.setp(bp["boxes"], facecolor=color_map[cond], alpha=box_alpha)

    # =========================
    # 4) 标题、轴标签、刻度与风格
    # =========================
    ax.minorticks_on()
    # 主刻度（major ticks）样式：长度、线宽、方向；这里在下/左侧显示
    ax.tick_params(axis='x', which='major', length=6, width=1.2, direction='out', bottom=True, top=False)
    ax.tick_params(axis='y', which='major', length=6, width=1.2, direction='out', left=True, right=False)

    ax.set_title(title, fontsize=20)
    ax.set_xlabel(xlabel, fontsize=15)
    ax.set_ylabel(ylabel, fontsize=15)
    ax.set_xticks([base_positions[c] for c in conditions])
    ax.set_xticklabels(col_name[:select_col], fontsize=15)  # col_name
    ax.tick_params(axis="y", labelsize=15)
    sns.despine(ax=ax)
    ax.grid(True, linestyle='--', alpha=0.35)

    fig.tight_layout()
    plt.show()

    save_path = os.path.join(save_dir, sub_file_name + '.png')
    # fig.savefig(save_path, dpi=300)
    plt.close()
    print(sub_file_name)

violin_flag = False
filter_data_flag = False
# ——位置与宽度参数——
v_width = 0.80  # sns.violinplot 的最大水平宽度（视觉半宽为 v_width/2）
violin_alpha = 0.20
box_alpha = 0.80
# ——filter——  不能共存，value优先级最高
maximum_value = 0
maximum_percentage = 0  # 百分比 0.98

# Distance
csv_dir = "./Boxplot/Distance/csv"
save_dir = "./Boxplot/Distance"
file_list = glob.glob(os.path.join(csv_dir, '*.csv'))
os.makedirs(save_dir, exist_ok=True)
for sub_file_path in file_list:
    sub_file_name = os.path.basename(sub_file_path).split('.')[0]
    col_name = [" ", " "]  # , "City"
    select_col = len(col_name)  # only the first x cols
    title = ''
    for s in sub_file_name.split('_'):
        title += f' {s}'
    xlabel = title
    ylabel = "Euclidean Distance (meter)"  # Euclidean Distance (meter)       Time Cost (minute)
    draw_violin()

# Time
csv_dir = "./Boxplot/Time/csv"
save_dir = "./Boxplot/Time"
file_list = glob.glob(os.path.join(csv_dir, '*.csv'))
os.makedirs(save_dir, exist_ok=True)
for sub_file_path in file_list:
    sub_file_name = os.path.basename(sub_file_path).split('.')[0]
    col_name = [" ", " "]
    select_col = len(col_name)
    title = ''
    for s in sub_file_name.split('_'):
        title += f' {s}'
    xlabel = title
    ylabel = "Time Cost (minute)"
    draw_violin()
