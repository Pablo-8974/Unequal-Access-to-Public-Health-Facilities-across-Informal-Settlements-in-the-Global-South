# -*- coding: utf-8 -*-
"""
到达交通设施的通行时间洛伦兹曲线与基尼系数计算/绘图（多文件、多行选择）
------------------------------------------------------------
输入：
- file_paths:  每个类别一个 CSV 文件的路径列表
- row_indices: 每个文件中要使用的“行号”列表（默认 1-based，可改 0-based）
- （可选）category_names: 每个类别在图表/输出中的名称；不提供则尝试读取该行的 'Within Minutes' 列

数据假设：
- 列名包含从 '1' 到 '120' 的分钟列（值为 0~100 的累计百分比）
- 可选的 'Greater' 列表示 >120 分钟的人口百分比
- 可选的 'Total Population' 列会被忽略（不参与计算）

输出：
- 图像：lorenz_access_time.png（可自定义路径）
- CSV：gini_summary.csv、lorenz_points.csv
- 返回：summary_df（每类别的 Gini 与平均通行时间）、lorenz_df（所有类别的洛伦兹曲线点）

作者：Mingyu 的 Copilot 伙伴
"""
from __future__ import annotations

import glob
import os
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _find_minute_columns(df: pd.DataFrame) -> List[str]:
    """找到 1..120 的分钟列（作为字符串），并按从小到大排序。"""
    minute_cols = [str(i) for i in range(1, 121)]
    existing = [c for c in minute_cols if c in df.columns]
    if len(existing) < 5:
        raise ValueError("未找到足够的分钟列（1..120）。请检查表头是否为字符串 '1','2',...,'120'。")
    return existing


def _prep_row(row: pd.Series, minute_cols: List[str],
              add_residual_if_missing: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    从某一行的累计百分比 F(t) 生成 (times, weights)：
    - times: 1..120 (如有 Greater 或残差则补 121)
    - weights: 各分钟“桶”的人口份额（和为 1）
    """
    # # 取 F(t) 并做基本清洗
    # F = row[minute_cols].astype(float).to_numpy()
    # # 前向填充 + 单调不降（避免异常噪声）
    # # 注意：Series.ffill 对行切片不生效，这里手工处理
    # for i in range(1, len(F)):
    #     if np.isnan(F[i]):
    #         F[i] = F[i-1]
    #     F[i] = max(F[i], F[i-1] if not np.isnan(F[i-1]) else F[i])
    # # 限幅到 [0,100]
    # F = np.clip(F, 0.0, 100.0)
    # # 转比例
    # F = F / 100.0
    #
    # # 差分得到每分钟桶的人口份额
    # w = np.empty_like(F)
    # w[0] = F[0]
    # w[1:] = np.diff(F)
    # # 数值噪声下的负值置零
    # w[w < 0] = 0.0

    times = np.arange(1, len(minute_cols) + 1, dtype=float)
    w = row[minute_cols].astype(float).to_numpy()
    # # 处理 >120 分钟
    # greater_share = 0.0
    # if "Greater" in row.index and pd.notnull(row["Greater"]):
    #     greater_share = max(0.0, float(row["Greater"]) / 100.0)
    # else:
    #     # 如果没有 Greater 且 F(120) < 1，则把残差视为 121 分钟（保守下界）
    #     if add_residual_if_missing and F[-1] < 1.0 - 1e-12:
    #         greater_share = 1.0 - float(F[-1])
    #
    # if greater_share > 0.0:
    #     times = np.append(times, 121.0)
    #     w = np.append(w, greater_share)

    # 归一化（以防轻微漂移）
    # W = np.max(w)
    # if W <= 0:
    #     raise ValueError("该行计算得到的权重为 0，请检查数据。")
    # w = w / W
    return times, w


def _lorenz_gini_unsumed(times: np.ndarray, w: np.ndarray) -> Tuple[pd.DataFrame, float, float]:
    """
    根据 (times, w) 计算：
    - 洛伦兹曲线点：人口累计占比 P vs 通行时间累计占比 S
    - 基尼系数 G
    - 平均通行时间 mu
    """
    # times 已按升序（1..120..121），w 为各桶份额（求和=1）
    mu = float(np.sum(w * times))

    # 人口累计占比
    P = np.cumsum(w)
    P = np.insert(P, 0, 0.0)

    # 通行时间累计占比
    cum_time = np.cumsum(w * times)
    S = cum_time / cum_time[-1]
    S = np.insert(S, 0, 0.0)

    # 洛伦兹曲线下面积（梯形法）
    area = float(np.trapz(S, P))
    gini = float(1.0 - 2.0 * area)

    lorenz_df = pd.DataFrame({"x": P, "y": S})
    return lorenz_df, gini, mu


def _lorenz_gini(times: np.ndarray, P_cum: np.ndarray):
    """
    输入:
    - times: 通行时间（已按升序）
    - P_cum: 人口累计占比 (从0上升到1)

    输出:
    - 洛伦兹曲线 P vs S
    - 基尼系数 G
    - 平均通行时间 mu
    """

    # -------- 核心改动：把累计占比转成份额 --------
    P_cum = np.asarray(P_cum)/100
    P_cum = np.clip(P_cum, 0, 1)
    w = np.diff(np.insert(P_cum, 0, 0.0))    # 份额 (PDF)

    # 平均通行时间
    mu = float(np.sum(w * times))

    # 人口累计占比（你本来就给了，只补上开头 0）
    P = np.insert(P_cum, 0, 0.0)

    # 通行时间累计占比
    cum_time = np.cumsum(w * times)
    S = cum_time / cum_time[-1]
    S = np.insert(S, 0, 0.0)

    # 洛伦兹曲线面积
    area = float(np.trapz(S, P))
    gini = float(1.0 - 2.0 * area)

    lorenz_df = pd.DataFrame({"x": P, "y": S})
    return lorenz_df, gini, mu


def _coverage_CV(times: np.ndarray, P: np.ndarray):
    """
    Coefficient of Variation
    输入:
    - times: 通行时间（已按升序）
    - P: 人口累计占比 (从0上升到1)

    输出:
    - 洛伦兹曲线 P vs S
    - 基尼系数 G
    - 平均通行时间 mu
    """
    # 计算每一分钟的人口占比，小数
    x = np.asarray(P)/100   # 输入数据为百分比数据，所以此处除以一百就得到小数形式的占比

    # 计算CV
    # 把累加数据转化为每一分钟的人口比例x[1:] - x[:-1]
    x_cv = x.copy()
    x_cv[1:] -= x_cv[:-1]
    mean_v = np.mean(x_cv)
    std_v = np.std(x_cv)
    cv = std_v / mean_v

    times = np.insert(times, 0, 0.0)
    x = np.insert(x, 0, 0.0)

    lorenz_df = pd.DataFrame({"x": x, "y": times})
    return lorenz_df, cv, 0


def _read_row_from_file(path: str, row_index: int, minute_cols: List[str]) -> pd.Series:
    """读取文件中的指定行（0-based 索引），并返回该行 Series。"""
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # 若文件内分钟列缺失，尝试在这里重新识别
    minutes_in_file = _find_minute_columns(df)
    if set(minutes_in_file) != set(minute_cols):
        # 使用文件自己的分钟列集合
        minute_cols[:] = minutes_in_file  # 就地更新引用
    if row_index < 0 or row_index >= len(df):
        raise IndexError(f"文件 {os.path.basename(path)} 行号越界：{row_index}")
    return df.iloc[row_index]


def run_access_gini(
    file_paths: List[str],
    row_indices: List[int],
    row_index_starts_at_1: bool = True,
    category_names: Optional[List[str]] = None,
    add_residual_if_missing: bool = True,
    save_figure_path: str=None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    主函数：从多个文件、多个行构建类别的洛伦兹曲线和基尼系数，并绘图/导出。
    """
    if len(file_paths) != len(row_indices):
        raise ValueError("file_paths 与 row_indices 长度不一致。")

    # 为了识别分钟列，先看第一个文件
    df0 = pd.read_csv(file_paths[0])
    df0.columns = [c.strip() for c in df0.columns]
    minute_cols = _find_minute_columns(df0)

    results: Dict[str, Dict] = {}
    import numpy as np
    for i, (path, r) in enumerate(zip(file_paths, row_indices)):
        idx0 = r - 1 if row_index_starts_at_1 else r
        row = _read_row_from_file(path, idx0, minute_cols)

        # 类别命名：优先用传入的 category_names，否则试图使用该行的 'Within Minutes'
        if category_names and i < len(category_names):
            name = str(category_names[i])
        else:
            name = str(row["Within Minutes"]) if "Within Minutes" in row.index else f"Cat{i+1}"

        # 生成 times 与权重
        times, w = _prep_row(row, minute_cols, add_residual_if_missing=add_residual_if_missing)
        # lorenz_df, gini, mu = _lorenz_gini(times, w)
        lorenz_df, gini, mu = _coverage_CV(times, w)

        results[name] = {"lorenz": lorenz_df, "gini": gini, "mean_time": mu}

    # —— 绘图：洛伦兹曲线 —— #
    plt.figure(figsize=(7, 6))
    # 完全平等线
    plt.plot([0, 1], [0, max(results['IS-2025']["lorenz"]['y'])],
             color="gray", linestyle="--", linewidth=1, label="Perfect Equality Line")

    cmap = plt.cm.get_cmap('Set1')
    import numpy as np
    colors = [cmap(x) for x in np.linspace(0, 1, 9)]

    # 逐类绘制
    top_text_lines = []
    for i, (name, res) in enumerate(results.items()):
        lor = res["lorenz"]
        g = res["gini"]
        label = f"{name}"       # (Gini={g:.3f})
        plt.plot(lor["x"], lor["y"], linewidth=2.5, label=label, color=colors[i],
                 linestyle="--" if name == "IS-2025" else "-"
                 )
        # plt.plot(lor["通行时间累计占比"], lor["人口累计e占比"], linewidth=2.5, label=label, color=colors[i],
        #          linestyle="--" if name == "IS-2025" els "-")
        top_text_lines.append(f"{name}: Gini={g:.3f}")

    plt.xlabel("Proportion of Population Coverage", fontsize=15)
    plt.ylabel("Time Cost (minutes)", fontsize=15)
    # plt.title("到达交通设施通行时间的洛伦兹曲线（按类别）", fontsize=13)
    # plt.legend(loc="lower right", frameon=True, fontsize=12)
    plt.grid(alpha=0.25)

    # 把基尼系数“标注在上边”：在图的上方贴一段多行文字（避免盖住曲线）
    # 使用轴域坐标系，在 y>1 的位置显示
    # ax = plt.gca()
    # ax.text(
    #     0.01, 1.02, "\n".join(top_text_lines),
    #     transform=ax.transAxes, va="bottom", ha="left", fontsize=11
    # )


    # ===== 在主图左上角添加“基尼指数对比”的柱状图 inset =====
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    import numpy as np
    import matplotlib as mpl

    ax = plt.gca()

    # 如果你用的是 results 字典（如 results[name]["gini"]）
    cats = list(results.keys())
    ginis = np.array([results[k]["gini"] for k in cats], dtype=float)

    # 2) 创建 inset 坐标轴（相对主坐标轴，左上角，宽高占主图的 35%×45%）
    #    参数 loc='upper left' + borderpad 控制贴边距离，可按需微调
    ax_in = inset_axes(ax, width="20%", height="40%", loc="upper left",
                       bbox_to_anchor=(0.1, -0.1, 1.00, 1.00),   # ← y=1.12 表示比原来的 upper-left 再往上移动
                       bbox_transform=ax.transAxes, borderpad=0)

    # 3) 画柱状图
    x = np.arange(len(cats))
    bars = ax_in.bar(x, ginis, color=colors, edgecolor="white", linewidth=0.5)

    # 4) 样式与标注
    # ax_in.set_title("Gini by Category", fontsize=9, pad=4)
    ax_in.set_title("Coefficient of Variation\nby Category", fontsize=14, pad=10)
    ax_in.set_xticks(x)
    ax_in.set_xticklabels(cats, rotation=90, ha="center", fontsize=14)
    # ax_in.set_ylabel("Gini", fontsize=12)
    ax_in.tick_params(axis="y", labelsize=10)
    # ax_in.tick_params(axis="x", labelsize=12)
    ax_in.set_ylim(0, max(0.01 + ginis.max(), 2.5))  # 给顶端留些空间，按需调整上限

    # 给每个柱子顶部标注数值
    for rect, g in zip(bars, ginis):
        ax_in.text(
            rect.get_x() + rect.get_width() / 2, rect.get_height(),
            f"{g:.2f}",
            ha="center", va="bottom", fontsize=13, color="#333333", rotation=0
        )

    # 5) 边框与网格（可选）
    for spine in ["top", "right"]:
        ax_in.spines[spine].set_visible(False)
    ax_in.grid(axis="y", linestyle=":", alpha=0.35)
    # ===== inset 结束 =====

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # ax.spines['bottom'].set_visible(False)
    # ax.spines['left'].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 1])  # 给顶部留空间
    plt.savefig(save_figure_path, dpi=300, transparent=False)
    # plt.show()
    plt.close()

    # —— 导出结果 —— #
    # summary_df = pd.DataFrame({
    #     "类别": list(results.keys()),
    #     "基尼系数(Gini)": [results[k]["gini"] for k in results],
    #     "平均通行时间(分钟)": [results[k]["mean_time"] for k in results],
    # })
    # # 收集所有洛伦兹点
    # lorenz_records = []
    # for name, res in results.items():
    #     tmp = res["lorenz"].copy()
    #     tmp["类别"] = name
    #     lorenz_records.append(tmp)
    # lorenz_df = pd.concat(lorenz_records, ignore_index=True)
    #
    # summary_df.to_csv(save_summary_csv, index=False)
    # lorenz_df.to_csv(save_lorenz_csv, index=False)
    #
    # return summary_df, lorenz_df


def dir_loop():
    dir_2010 = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig5\fig5b-j_CoverageCurve\2010"
    dir_2025 = r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig5\fig5b-j_CoverageCurve\2025"
    save_dir = r'C:\Users\k\Desktop\slum\paper\Nature-2\data\Pic\fig5\fig5b-j_CoverageCurve'

    any_tif_list = glob.glob(os.path.join(dir_2010, '*.csv'))
    for tif_path_2010 in any_tif_list:
        file_name = os.path.basename(tif_path_2010)
        save_path = os.path.join(save_dir, file_name.split('_')[0] + '.png')
        os.path.join(dir_2010, file_name)

        files = [tif_path_2010, os.path.join(dir_2025, file_name)]
        rows = [1, 1]  # 1-based 行    , 2, 2
        run_access_gini(
            file_paths=files,
            row_indices=rows,
            row_index_starts_at_1=True,
            category_names=["IS-2010", "IS-2025"],      # , "FS-2025-3km", "FS-2025-10km"
            # 或 ["IS 3km","IS 10km","FS 3km","FS 5km"]
            add_residual_if_missing=True,
            save_figure_path=save_path
        )
        print(file_name)


if __name__ == "__main__":
    dir_loop()
    #
    # # 一个简单的演示，可以按需替换成你的路径/行号
    # files = [r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2010\With2025RoadNetwork\PopulationRelated-2010-10km\CSV\Cairo_ProportionInPopulation.csv",
    #          r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2025\PopulationRelated-2025-10km\CSV\Cairo_ProportionInPopulation.csv",
    #          # r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2025\PopulationRelated-2025-3km\CSV\Cairo_ProportionInPopulation.csv",
    #          # r"C:\Users\k\Desktop\slum\paper\Nature-2\data\Accessbility\2025\PopulationRelated-2025-10km\CSV\Cairo_ProportionInPopulation.csv"
    #          ]
    # rows = [1, 1,
    #         # 2, 2
    #         ]  # 1-based 行
    # run_access_gini(
    #     file_paths=files,
    #     row_indices=rows,
    #     row_index_starts_at_1=True,
    #     category_names=[
    #         "IS-2010","IS-2025",
    #         # "FS-2025-3km","FS-2025-10km"
    #     ],  # 或 ["IS 3km","IS 10km","FS 3km","FS 5km"]
    #     add_residual_if_missing=True,
    #     save_figure_path="./fig/lorenz_access_time.png"
    # )
