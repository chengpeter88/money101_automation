import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from wordcloud import WordCloud
import jieba
import os

# 設定中文字體
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "Microsoft YaHei",
    "SimHei",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

# 建立輸出目錄
output_dir = "視覺化分析結果"
os.makedirs(output_dir, exist_ok=True)

# 載入分析結果
with open("partner_analysis_results.json", "r", encoding="utf-8") as f:
    analysis_results = json.load(f)

# 1. 合作夥伴出現文章數量視覺化
partner_counts = analysis_results["partner_article_counts"]
partners = list(partner_counts.keys())
counts = list(partner_counts.values())

# 只顯示有出現的合作夥伴
non_zero_indices = [i for i, count in enumerate(counts) if count > 0]
partners = [partners[i] for i in non_zero_indices]
counts = [counts[i] for i in non_zero_indices]

# 依照數量排序
sorted_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
partners = [partners[i] for i in sorted_indices]
counts = [counts[i] for i in sorted_indices]

# 只取前15名，避免圖表太擁擠
partners = partners[:15]
counts = counts[:15]

plt.figure(figsize=(12, 8))
ax = sns.barplot(x=counts, y=partners)
plt.title("各合作夥伴出現在文章的次數 (前15名)", fontsize=16)
plt.xlabel("文章數量", fontsize=12)
plt.ylabel("合作夥伴", fontsize=12)

# 在每個條形上顯示數值
for i, v in enumerate(counts):
    ax.text(v + 0.1, i, str(v), va="center")

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "partner_article_counts.png"), dpi=300)
plt.close()

# 2. 合作夥伴被提及次數視覺化
mentions = analysis_results["all_mentions"]
partners = list(mentions.keys())
mention_counts = list(mentions.values())

# 依照提及次數排序
sorted_indices = sorted(
    range(len(mention_counts)), key=lambda i: mention_counts[i], reverse=True
)
partners = [partners[i] for i in sorted_indices][:15]  # 只取前15名
mention_counts = [mention_counts[i] for i in sorted_indices][:15]

plt.figure(figsize=(12, 8))
ax = sns.barplot(x=mention_counts, y=partners)
plt.title("前15名最常被提及的合作夥伴", fontsize=16)
plt.xlabel("提及次數", fontsize=12)
plt.ylabel("合作夥伴", fontsize=12)

# 在每個條形上顯示數值
for i, v in enumerate(mention_counts):
    ax.text(v + 0.1, i, str(v), va="center")

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "partner_mention_counts.png"), dpi=300)
plt.close()

# 3. 合作夥伴網路圖
with open("partner_article_mapping.json", "r", encoding="utf-8") as f:
    partner_articles = json.load(f)

# 建立合作夥伴之間的關聯（基於共同的文章）
G = nx.Graph()

# 添加節點
for partner in partner_articles:
    articles_count = len(partner_articles[partner])
    G.add_node(partner, size=articles_count)

# 添加邊 - 如果兩個合作夥伴有共同的文章，則它們之間有連接
for partner1 in partner_articles:
    articles1 = set([article["filename"] for article in partner_articles[partner1]])

    for partner2 in partner_articles:
        if partner1 >= partner2:  # 避免重複計算
            continue

        articles2 = set([article["filename"] for article in partner_articles[partner2]])
        common_articles = articles1.intersection(articles2)

        if common_articles:
            G.add_edge(partner1, partner2, weight=len(common_articles))

# 繪製網路圖
plt.figure(figsize=(14, 10))

# 使用節點大小表示文章數量
node_sizes = [G.nodes[node]["size"] * 50 for node in G.nodes]

# 使用邊的粗細表示共同文章的數量
edge_weights = [G[u][v]["weight"] * 0.5 for u, v in G.edges()]

# 計算節點位置
pos = nx.spring_layout(G, seed=42, k=0.3)

# 繪製網路圖
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="lightblue", alpha=0.7)
nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, edge_color="gray")
nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

plt.axis("off")
plt.title("合作夥伴關聯網路圖", fontsize=16)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "partner_network.png"), dpi=300)
plt.close()

print(f"視覺化分析結果已保存至 {output_dir} 目錄")

# 4. 生成合作夥伴詞雲圖 (前5名)
top_partners = sorted(
    analysis_results["partner_article_counts"].items(), key=lambda x: x[1], reverse=True
)[:5]

# 讀取所有文章內容
article_contents = {}
txt_files = [f for f in os.listdir(".") if f.endswith(".txt")]

for txt_file in txt_files:
    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            article_contents[txt_file] = f.read()
    except Exception as e:
        print(f"無法讀取 {txt_file}: {e}")

# 為前5名合作夥伴生成詞雲
for partner, _ in top_partners:
    if not partner or partner not in partner_articles:
        continue

    # 合併所有相關文章內容
    articles = partner_articles[partner]
    all_text = ""

    for article in articles:
        filename = article["filename"]
        if filename in article_contents:
            all_text += article_contents[filename] + " "

    if not all_text:
        continue

    # 使用結巴分詞
    words = jieba.cut(all_text)
    processed_text = " ".join(words)

    # 生成詞雲
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        font_path="/System/Library/Fonts/PingFang.ttc",  # Mac 中文字體
        max_words=100,
        collocations=False,  # 避免重複短語
    ).generate(processed_text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"{partner} 相關文章詞雲")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{partner}_wordcloud.png"), dpi=300)
    plt.close()

print("合作夥伴詞雲圖已生成")
