import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def medical_density():
    # === 读取与整理 ===
    raw = pd.read_excel(
        "./fig1b.Medical Facility Density.xlsx",
                        sheet_name=0, header=None, engine='openpyxl')
    records, current_region = [], None
    for _, row in raw.iterrows():
        a, b = row[0], row[1]
        if pd.isna(a) and pd.isna(b):
            continue
        if isinstance(a, str) and isinstance(b, str):  # 地区表头
            current_region = a
            continue
        if isinstance(a, str) and pd.notna(b):         # 城市行
            records.append({'子大洲': current_region, '城市': a, '贫民窟面积百分比': float(b)})

    df = pd.DataFrame(records)

    # === 分箱 ===
    bins = [0, 0.1, 0.3, 0.6, 1]
    labels = ['0–0.1', '0.1–0.3', '0.3–0.6', '0.6–1']
    df['分组'] = pd.cut(df['贫民窟面积百分比'], bins=bins, labels=labels,
                       right=True, include_lowest=True)

    # === 口径：按“贫民窟占比之和”的份额（而非城市个数） ===
    # 每个子大洲：各分组内“百分比之和” / 该子大洲“百分比之和”
    # 注意：这里直接对百分比求和并归一化，以得到在该子大洲内部的份额结构
    sum_by_region_bin = df.groupby(['子大洲','分组'])['贫民窟面积百分比'].sum().unstack(fill_value=0)
    sum_by_region = sum_by_region_bin.sum(axis=1)
    share_within = sum_by_region_bin.div(sum_by_region, axis=0)

    # === 整体 Overall：所有城市一起，各分组“百分比之和”在总体中的份额 ===
    overall_sum_by_bin = df.groupby('分组')['贫民窟面积百分比'].sum().reindex(labels).fillna(0)
    overall_share = (overall_sum_by_bin / overall_sum_by_bin.sum()).rename('Overall')

    # === 排序并绘图 ===
    regions_order = ['Southern Africa','Northern Africa','Southern America','South Asia','Southeast Asia','Overall']

    def get_series(name):
        if name == 'Overall':
            return overall_share.reindex(labels)
        return share_within.loc[name].reindex(labels)

    colors = ['#d8cbe6','#b7a6d9','#8f6bb3','#b03060','#67001f','#1f77b4']
    bar_width = 0.14
    x = np.arange(len(labels))

    plt.figure(figsize=(12, 6.4))
    bar_containers = []
    for i, name in enumerate(regions_order):
        y = get_series(name).fillna(0).values
        bars = plt.bar(x + (i - (len(regions_order)-1)/2)*bar_width, y, width=bar_width,
                       label=name, color=colors[i])
        bar_containers.append((bars, y))

    # 标注：以百分比显示份额
    for bars, yvals in bar_containers:
        for rect, y in zip(bars, yvals):
            h = rect.get_height()
            if h <= 0: continue
            plt.annotate(f"{h*100:.0f}%", xy=(rect.get_x()+rect.get_width()/2, h),
                         xytext=(0, 3), textcoords='offset points', ha='center', va='bottom',
                         fontsize=10, color='#333')

    plt.xticks(x, labels, fontsize=12)
    plt.yticks(fontsize=12)

    plt.xlabel('Medical Facility Density (per km²)', fontsize=15, fontweight='bold')
    plt.ylabel('Gradient Distribution Percentages', fontsize=15, fontweight='bold')
    # plt.title('各子大洲内部 vs 整体：按“贫民窟占比之和”分组的份额（带标注）', fontsize=13)
    plt.legend(title='Sub-region', title_fontsize=12, fontsize=12, ncol=2, loc='upper right')
    plt.ylim(0, 0.9)
    plt.tight_layout()

    # out_fn='slum_area_proportion.png'
    out_fn='medical_density.png'
    # plt.show()
    plt.savefig(out_fn, dpi=300)
    plt.close()
    print('SAVED_FILE:', out_fn)

    print('\n校验（各子大洲内部四组份额之和=1）：')
    print(share_within.sum(axis=1))
    print('\n整体（Overall）各分组份额：')
    print(overall_share)

def slum_proportion():
    # === 读取与整理 ===
    raw = pd.read_excel(
        "./Fig.1c_Proportion_of_informal_settlement_area.xlsx",
        sheet_name=0, header=None, engine='openpyxl')
    records, current_region = [], None
    for _, row in raw.iterrows():
        a, b = row[0], row[1]
        if pd.isna(a) and pd.isna(b):
            continue
        if isinstance(a, str) and isinstance(b, str):  # 地区表头
            current_region = a
            continue
        if isinstance(a, str) and pd.notna(b):  # 城市行
            records.append({'子大洲': current_region, '城市': a, '贫民窟面积百分比': float(b)})

    df = pd.DataFrame(records)

    # === 分箱 ===
    bins = [0, 2, 4, 6, 9]
    labels = ['0–2', '2–4', '4–6', '6–9']
    df['分组'] = pd.cut(df['贫民窟面积百分比'], bins=bins, labels=labels,
                        right=True, include_lowest=True)

    # === 口径：按“贫民窟占比之和”的份额（而非城市个数） ===
    # 每个子大洲：各分组内“百分比之和” / 该子大洲“百分比之和”
    # 注意：这里直接对百分比求和并归一化，以得到在该子大洲内部的份额结构
    sum_by_region_bin = df.groupby(['子大洲', '分组'])['贫民窟面积百分比'].sum().unstack(fill_value=0)
    sum_by_region = sum_by_region_bin.sum(axis=1)
    share_within = sum_by_region_bin.div(sum_by_region, axis=0)

    # === 整体 Overall：所有城市一起，各分组“百分比之和”在总体中的份额 ===
    overall_sum_by_bin = df.groupby('分组')['贫民窟面积百分比'].sum().reindex(labels).fillna(0)
    overall_share = (overall_sum_by_bin / overall_sum_by_bin.sum()).rename('Overall')

    # === 排序并绘图 ===
    regions_order = ['Southern Africa', 'Northern Africa', 'Southern America', 'South Asia', 'Southeast Asia',
                     'Overall']

    def get_series(name):
        if name == 'Overall':
            return overall_share.reindex(labels)
        return share_within.loc[name].reindex(labels)

    colors = ['#d6e685','#8cc665','#44a340','#1e6823','#00441b','#1f77b4']
    # colors = ['#d8cbe6', '#b7a6d9', '#8f6bb3', '#b03060', '#67001f', '#1f77b4']

    bar_width = 0.14
    x = np.arange(len(labels))

    plt.figure(figsize=(12, 6.4))
    bar_containers = []
    for i, name in enumerate(regions_order):
        y = get_series(name).fillna(0).values
        bars = plt.bar(x + (i - (len(regions_order) - 1) / 2) * bar_width, y, width=bar_width,
                       label=name, color=colors[i])
        bar_containers.append((bars, y))

    # 标注：以百分比显示份额
    for bars, yvals in bar_containers:
        for rect, y in zip(bars, yvals):
            h = rect.get_height()
            if h <= 0: continue
            plt.annotate(f"{h * 100:.0f}%", xy=(rect.get_x() + rect.get_width() / 2, h),
                         xytext=(0, 3), textcoords='offset points', ha='center', va='bottom',
                         fontsize=10, color='#333')

    plt.xticks(x, labels, fontsize=12)
    plt.yticks(fontsize=12)

    plt.xlabel('Informal Settlements Area Proportion (%)', fontsize=15, fontweight='bold')
    plt.ylabel('Gradient Distribution Percentages', fontsize=15, fontweight='bold')
    # plt.title('各子大洲内部 vs 整体：按“贫民窟占比之和”分组的份额（带标注）', fontsize=13)
    plt.legend(title='Sub-region', title_fontsize=12, fontsize=12, ncol=2, loc='upper left')
    plt.ylim(0, 0.6)
    plt.tight_layout()

    out_fn = 'slum_area_proportion.png'
    # plt.show()
    plt.savefig(out_fn, dpi=300)
    plt.close()
    print('SAVED_FILE:', out_fn)

    print('\n校验（各子大洲内部四组份额之和=1）：')
    print(share_within.sum(axis=1))
    print('\n整体（Overall）各分组份额：')
    print(overall_share)

if __name__ == '__main__':
    slum_proportion()   # fig 1b
    medical_density()   # fig 1c
