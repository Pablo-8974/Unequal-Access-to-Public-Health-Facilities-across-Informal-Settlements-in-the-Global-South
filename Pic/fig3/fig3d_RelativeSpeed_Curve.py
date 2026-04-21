import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mmcv.image.geometric import bbox_clip

# =========================
# 1. 读取 CSV
# =========================
df = pd.read_csv(
    "RelativeSpeed.csv"
)

# =========================
# 2. 绘图风格（无内部线）
# =========================
# sns.set_theme(style="white")   # ✅ 本身就不画 grid

color_informal = "#4C72B0"
color_formal   = "#DD1C77"

# =========================
# 3. 从第二列开始：每一列画一张图
# =========================
for col in df.columns[1:]:

    values = df[col].values

    # 行号规则（你确认过的）
    informal_y = values[:2]     # Informal 3km, 10km
    formal_y   = values[2:5]    # Formal 3km, 5km, 10km

    # ✅ 等间距的 x 轴（位置索引）
    informal_x = [0, 2]         # 3km, 10km
    formal_x   = [0, 1, 2]      # 3km, 5km, 10km

    plt.figure(figsize=(4, 3))

    plt.plot(
        informal_x,
        informal_y,
        marker="o",
        color=color_informal,
        linewidth=2,
        label="Informal"
    )

    plt.plot(
        formal_x,
        formal_y,
        marker="o",
        color=color_formal,
        linewidth=2,
        label="Formal"
    )

    # ✅ 等间距刻度 + 正确标签
    plt.xticks([0, 1, 2], ["3km", "5km", "10km"], fontsize=10)
    plt.yticks(fontsize=10)


    plt.xlabel("Distance", fontsize=12)
    plt.ylabel("Relative walking speed", fontsize=12)
    plt.title(col, fontsize=12)

    # plt.ylim(0.65, 0.86)
    plt.ylim(0.5, 1.25)
    plt.grid(True, alpha=0.5)

    # plt.legend(frameon=True)

    plt.legend(
        # loc="lower right",
        loc="upper left",
        # bbox_to_anchor=(1.02, 0.5),
        frameon=True
    )

    plt.tight_layout()
    # plt.show()
    plt.savefig(f'fig3d_{col}.png',
                dpi=300, transparent=False, bbox_inches="tight")
    plt.close()
