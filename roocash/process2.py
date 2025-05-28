import json
import os
import pandas as pd
from tabulate import tabulate

# 讀取合作夥伴-文章映射數據
try:
    with open("partner_article_mapping.json", "r", encoding="utf-8") as f:
        partner_articles = json.load(f)
except FileNotFoundError:
    print("未找到 partner_article_mapping.json 檔案，請先執行 txt_partner_analysis.py")
    exit(1)

# 讀取分析結果
with open("partner_analysis_results.json", "r", encoding="utf-8") as f:
    analysis_results = json.load(f)

# 依據文章數量排序合作夥伴
sorted_partners = sorted(
    analysis_results["partner_article_counts"].items(), key=lambda x: x[1], reverse=True
)

# 為每個合作夥伴生成報告
output_file = "合作夥伴文章報告.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# roocash 合作夥伴文章報告\n\n")

    # 依序處理每個有關聯文章的合作夥伴
    for partner, count in sorted_partners:
        if count == 0:
            continue

        articles = partner_articles.get(partner, [])

        f.write(f"## {partner} (共 {len(articles)} 篇文章)\n\n")
        f.write("| 文章標題 | 檔案名稱 |\n")
        f.write("|---------|----------|\n")

        for article in articles:
            title = article["title"]
            filename = article["filename"]
            f.write(f"| {title} | {filename} |\n")

        f.write("\n")

print(f"合作夥伴文章報告已生成: {output_file}")

# 產生合作夥伴排名表格
rank_data = []
for i, (partner, count) in enumerate(sorted_partners[:20], 1):
    if count > 0:
        mentions = analysis_results["all_mentions"].get(partner, 0)
        rank_data.append([i, partner, count, mentions])

df = pd.DataFrame(rank_data, columns=["排名", "合作夥伴", "文章數量", "提及次數"])
print("\n合作夥伴排名 (前20名):")
print(tabulate(df, headers="keys", tablefmt="pipe", showindex=False))

# 儲存為CSV
df.to_csv("合作夥伴排名.csv", index=False, encoding="utf-8-sig")
print("排名資料已儲存為 '合作夥伴排名.csv'")
