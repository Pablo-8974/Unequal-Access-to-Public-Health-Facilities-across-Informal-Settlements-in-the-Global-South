import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
mpl.rcParams["font.family"] = "DejaVu Sans"
from statannotations.Annotator import Annotator

def main(csv_path, save_path):
    # =========================
    # Load the data
    # =========================
    inputData = pd.read_csv(
        csv_path,
        header=0,
    )

    # 数据清洗
    new_data = {}
    for col in inputData.columns:
        data = np.array(inputData[col].dropna())
        data = np.array(data[data > 0])
        data = data[data <= 1.1]

        new_data[col] = data
    new_data = pd.DataFrame({
        col: pd.Series(values)
        for col, values in new_data.items()
    })

    # =========================
    # Select the columns
    # =========================
    inputData = new_data[new_data.columns]

    # =========================
    # Reformat data (wide → long)
    # =========================
    plotData = (inputData.melt(var_name="condition", value_name="value").dropna())

    # =========================
    # Set ColorBrewer Set1 (exact)
    # =========================
    conditions = new_data.columns
    # colors = [[152, 156, 169, 255], [151, 164, 174, 255], [148, 173, 177, 255], [152, 181, 179, 255], [173, 189, 179, 255]]
    # colors = [[70, 120, 142, 255], [120, 183, 201, 255], [246, 224, 147, 255], [229, 139, 123, 255], [151, 179, 25, 255]]
    # for i in range(len(colors)):
    #     colors[i] = np.array(colors[i]) / 255
    colors = ['#29648A', '#73B3D5', '#C49649', '#E8C582', '#F5E6BA']
    colors = colors[:len(conditions)]

    # =========================
    # Plot
    # =========================
    plt.figure(figsize=(9, 6))

    # sns.violinplot(
    #     data=plotData,
    #     x="condition",
    #     y="value",
    #     palette=colors,
    #     inner=None,
    #     cut=0,              # trim = TRUE
    #     scale="width",
    #     bw_adjust=2,        # adjust = 2
    #     linewidth=1,
    #     alpha=0.8
    # )

    for cond, color in zip(conditions, colors):
        sns.boxplot(
            data=plotData[plotData["condition"] == cond],
            x="condition",
            y="value",
            width=0.6,
            notch=True,
            showfliers=False,
            boxprops={
                "facecolor": color,
                "alpha": 1.,
                "edgecolor": "black"
            },
            medianprops={"color": "black"},
            whiskerprops={"color": "black"},
            capprops={"color": "black"}     # , 'linewidth':0
        )

    # =========================
    # Plot mean as hollow circles
    # =========================
    for i, cond in enumerate(conditions):
        mean_val = plotData.loc[
            plotData["condition"] == cond, "value"
        ].mean()
        print(mean_val)
        plt.scatter(
            i, mean_val,
            s=50,                      # 圆圈大小，可调
            facecolors='white',         # ✅ 空心
            edgecolors='black',        # ✅ 边框颜色
            linewidths=1,              # ✅ 圆环粗细
            zorder=10                  # ✅ 保证在最上层
        )

    # 显著性比较组合（按 column 名）
    pairs = [
        (conditions[0], conditions[2]),
        (conditions[1], conditions[3]),
        (conditions[1], conditions[4]),
    ]

    annotator = Annotator(
        ax=plt.gca(),
        pairs=pairs,
        data=plotData,
        x="condition",
        y="value",
    )

    annotator.configure(
        test="Mann-Whitney",      # ✅ 非正态分布更稳妥
        text_format="star",       # 或 "simple" 显示 p < 0.05star
        loc="outside",            # ✅ 标记放在箱体上方
        comparisons_correction="bonferroni",  # ✅ 多重比较"bonferroni"
        line_width=1.2,
        fontsize=14,
        pvalue_thresholds=[
            (1e-3, "***"),
            (1e-2, "**"),
            (0.05, "*"),
            (1, "ns")
        ]
    )

    annotator.apply_and_annotate()

    # =========================
    # Titles and theme
    # =========================
    plt.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.5)

    plt.xlabel("Settlement Types", fontsize=18)
    plt.ylabel("Relative Walking Speed", fontsize=18)
    plt.ylim(0.25, 1.15)

    plt.xticks(
        ticks=[i for i in range(len(conditions))],
        labels=["Informal 3km", "Informal 10km", "Formal 3km", "Formal 5km", "Formal 10km"],
        fontsize=15
    )
    plt.yticks(fontsize=15)

    sns.set_style("white")
    sns.despine()

    plt.legend([], [], frameon=False)
    plt.tight_layout()
    # plt.show()
    plt.savefig(save_path, transparent=False, bbox_inches="tight", dpi=300)
    plt.close()


if __name__ == '__main__':
    main('Raster.csv', 'fig3a.png')
    main('RodeNode.csv', 'fig3b.png')

