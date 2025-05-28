import os
import re
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import json

# 設定輸入文件目錄
input_dir = "/Users/heng/Documents/money101_automation/roocash_data"  # 請改為您的TXT檔案所在目錄

# 建立合作夥伴關鍵詞字典
partner_keywords = {
    # 銀行
    "富邦銀行": ["富邦銀行", "富邦信用卡", "富邦"],
    "玉山銀行": ["玉山銀行", "玉山信用卡", "玉山"],
    "中信銀行": ["中信銀行", "中信信用卡", "中信"],
    "永豐銀行": ["永豐銀行", "永豐信用卡", "永豐幣倍", "永豐"],
    "滙豐銀行": ["滙豐銀行", "滙豐信用卡", "滙豐"],
    "台新銀行": ["台新銀行", "台新信用卡", "台新"],
    "國泰世華銀行": ["國泰世華銀行", "國泰世華信用卡", "國泰世華"],
    "彰化銀行": ["彰化銀行", "彰化信用卡", "彰化"],
    "華南銀行": ["華南銀行", "華南信用卡", "華南"],
    "第一銀行": ["第一銀行", "第一信用卡", "第一"],
    "合作金庫銀行": ["合作金庫銀行", "合作金庫信用卡", "合作金庫"],
    "台灣銀行": ["台灣銀行", "台灣信用卡", "台灣"],
    "台北富邦銀行": ["台北富邦銀行", "台北富邦信用卡", "台北富邦"],
    "新光銀行": ["新光銀行", "新光信用卡", "新光"],
    "遠東銀行": ["遠東銀行", "遠東信用卡", "遠東"],
    "華泰銀行": ["華泰銀行", "華泰信用卡", "華泰"],
    "星展銀行": ["星展銀行", "星展信用卡", "星展"],
    "台中銀行": ["台中銀行", "台中信用卡", "台中"],
    "台灣中小企業銀行": ["台灣中小企業銀行", "中小企業信用卡", "中小企業"],
    "新光兆豐商業銀行": ["新光兆豐商業銀行", "新光兆豐信用卡", "新光兆豐"],
    "台灣土地銀行": ["台灣土地銀行", "土地銀行信用卡", "土地銀行"],
    "台灣企銀": ["台灣企銀", "企銀信用卡", "企銀"],
    "遠東商銀": ["遠東商銀", "遠東商銀信用卡", "遠東商銀"],
    "樂天銀行": ["樂天銀行", "樂天信用卡", "樂天"],
    "渣打銀行": ["渣打銀行", "渣打信用卡", "渣打"],
    "台新國際商業銀行": ["台新國際商業銀行", "台新國際信用卡", "台新國際"],
    "聯邦銀行": ["聯邦銀行", "聯邦信用卡", "聯邦"],
    "王道銀行": ["王道銀行", "王道信用卡", "王道"],
    # 信貸
    "富邦銀行": ["富邦信貸", "富邦貸款"],
    "玉山銀行": ["玉山信貸", "玉山貸款"],
    "中信銀行": ["中信信貸", "中信貸款"],
    "永豐銀行": ["永豐信貸", "永豐貸款"],
    "台新銀行": ["台新信貸", "台新貸款"],
    "國泰銀行": ["國泰信貸", "國泰貸款"],
    "彰化銀行": ["彰化信貸", "彰化貸款"],
    "華南銀行": ["華南信貸", "華南貸款"],
    "第一銀行": ["第一信貸", "第一貸款"],
    "合作金庫銀行": ["合作金庫信貸", "合作金庫貸款"],
    "台灣銀行": ["台灣信貸", "台灣貸款"],
    "新光銀行": ["新光信貸", "新光貸款"],
    "遠東銀行": ["遠東信貸", "遠東貸款"],
    "台新國際商業銀行": [
        "台新國際信貸",
        "台新國際貸款",
        "Richart 信貸",
        "Richart 貸款",
    ],
    "匯豐銀行": ["匯豐信貸", "匯豐貸款", "信用貸款"],
    "聯邦銀行": ["聯邦信貸", "聯邦貸款"],
    "王道銀行": ["王道信貸", "王道貸款"],
    # 證券公司
    "富邦證券": ["富邦證券", "富邦開戶"],
    "元富證券": ["元富證券", "元富開戶"],
    "中信證券": ["中信證券", "中信開戶"],
    "康和證券": ["康和證券", "康和開戶", "好康fun心投"],
    "鉅亨網": ["鉅亨網", "鉅亨買基金"],
    "永豐金證券": ["永豐金證券", "永豐金開戶"],
    "台新證券": ["台新證券", "台新開戶"],
    "國泰證券": ["國泰證券", "國泰開戶"],
    "第一金證券": ["第一金證券", "第一金開戶"],
    "台灣證券交易所": ["台灣證券交易所", "台灣證交所"],
    "兆豐證券": ["兆豐證券", "兆豐開戶"],
    "永豐金證券": ["永豐金證券", "永豐金開戶"],
    "台灣證券": ["台灣證券", "台灣開戶"],
    "新光證券": ["新光證券", "新光開戶"],
    "華南永昌證券": ["華南永昌證券", "華南永昌開戶"],
    "群益證券": ["群益證券", "群益開戶"],
    "凱基證券": ["凱基證券", "凱基開戶"],
    "大華證券": ["大華證券", "大華開戶"],
    "台灣中小企業證券": ["台灣中小企業證券", "中小企業證券開戶"],
    # 投信公司
    "DWS 投信": ["DWS 投信", "DWS"],
    "富蘭克林坦伯頓": ["富蘭克林", "坦伯頓"],
    "宏利投信": ["宏利投信", "宏利"],
    "元大投信": ["元大投信", "元大"],
    # "國泰投信": ["國泰投信", "國泰"],
    # "永豐投信": ["永豐投信", "永豐"],
    # "台新投信": ["台新投信", "台新"],
    # "第一金投信": ["第一金投信", "第一金"],
    # "中信投信": ["中信投信", "中信"],
    # "華南投信": ["華南投信", "華南"],
    # "兆豐投信": ["兆豐投信", "兆豐"],
    # "新光投信": ["新光投信", "新光"],
    # "凱基投信": ["凱基投信", "凱基"],
    # "群益投信": ["群益投信", "群益"],
    # "大華投信": ["大華投信", "大華"],
    "台灣中小企業投信": ["台灣中小企業投信", "中小企業投信"],
    # 支付與行動支付
    "Garmin Pay": ["Garmin Pay", "Garmin"],
    "幣安": ["幣安", "幣安信用卡"],
    "LINE Pay": ["LINE Pay", "LINE"],
    "Apple Pay": ["Apple Pay", "Apple"],
    "Google Pay": ["Google Pay", "Google"],
    "Samsung Pay": ["Samsung Pay", "Samsung"],
    "PayPal": ["PayPal", "PayPal信用卡"],
    # 金融商品與服務
    "ETF": ["ETF", "00880", "00878", "00980A", "00929"],
    "美股": ["美股", "Disney", "Nike", "McDonald's", "Netflix", "Amazon", "Costco"],
    "台股": ["台股", "台積電", "聯發科", "鴻海", "大立光", "中華電信"],
    "基金": ["基金", "元大台灣50", "富邦科技", "國泰永續高股息", "永豐金台灣高股息"],
    # 數位平台
    "富果平台": ["富果平台", "富果"],
    "亮點App": ["亮點App", "亮點"],
    # 保險
    "富邦人壽": ["富邦人壽", "富邦保險", "富邦產險"],
    "國泰人壽": ["國泰人壽", "國泰保險", "國泰產險"],
    "新光人壽": ["新光人壽", "新光保險", "新光產險"],
    "台灣人壽": ["台灣人壽", "台灣保險", "台灣產險"],
    "中信人壽": ["中信人壽", "中信保險", "中信產險"],
    "新安東京海上保險": ["新安東京海上保險", "新安保險", "新安產險"],
    "安達保險": ["安達保險", "安達產險"],
    "明台產險": ["明台產險", "明台保險", "明台產物保險"],
    "和泰產險": ["和泰產險", "和泰保險", "和泰人壽"],
}


def extract_title_from_filename(filename):
    """從檔名中提取文章標題"""
    # 假設檔名格式為: 文章標題.txt
    base_name = os.path.basename(filename)
    title = os.path.splitext(base_name)[0]
    return title


def extract_url_from_content(content):
    """從文章內容中提取URL (如果有的話)"""
    url_match = re.search(r"(https?://\S+)", content)
    if url_match:
        return url_match.group(1)
    return "無連結"


# 處理所有TXT檔案
results = []
article_data = []  # 儲存轉換後的文章資料

txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
print(f"找到 {len(txt_files)} 個TXT檔案")

for txt_file in txt_files:
    file_path = os.path.join(input_dir, txt_file)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取標題和URL
        title = extract_title_from_filename(txt_file)
        url = extract_url_from_content(content)

        # 儲存文章資料
        article = {"title": title, "url": url, "content": content, "filename": txt_file}
        article_data.append(article)

        # 分析合作夥伴
        article_partners = {}
        for partner, keywords in partner_keywords.items():
            mentions = 0
            for keyword in keywords:
                # 使用正則表達式找出每個關鍵詞的出現次數
                mentions += len(
                    re.findall(
                        r"\b" + re.escape(keyword) + r"\b", content, re.IGNORECASE
                    )
                )

            if mentions > 0:
                article_partners[partner] = mentions

        results.append(
            {
                "title": title,
                "filename": txt_file,
                "url": url,
                "partners": article_partners,
                "total_mentions": sum(article_partners.values()),
            }
        )

    except Exception as e:
        print(f"處理檔案 {txt_file} 時出錯: {e}")

# 儲存轉換後的資料為JSON格式以便後續使用
with open("roocash_data.json", "w", encoding="utf-8") as f:
    json.dump(article_data, f, ensure_ascii=False, indent=2)
print("文章資料已保存為 roocash_data.json")

# 輸出每個合作夥伴出現的文章數量
partner_article_counts = {}
for partner in partner_keywords.keys():
    count = sum(1 for result in results if partner in result["partners"])
    partner_article_counts[partner] = count

# 按文章數量排序
sorted_partners = sorted(
    partner_article_counts.items(), key=lambda x: x[1], reverse=True
)
print("\n合作夥伴出現在文章的次數:")
for partner, count in sorted_partners:
    if count > 0:
        print(f"{partner}: {count} 篇文章")

# 輸出前10名最常被提及的合作夥伴
all_mentions = {}
for result in results:
    for partner, count in result["partners"].items():
        if partner not in all_mentions:
            all_mentions[partner] = 0
        all_mentions[partner] += count

sorted_mentions = sorted(all_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
print("\n前10名最常被提及的合作夥伴:")
for partner, mentions in sorted_mentions:
    print(f"{partner}: 被提及 {mentions} 次")

# 儲存分析結果
output = {
    "partner_article_counts": partner_article_counts,
    "all_mentions": all_mentions,
    "article_details": [
        {
            "title": r["title"],
            "url": r["url"],
            "filename": r["filename"],
            "partners": list(r["partners"].keys()),
        }
        for r in results
        if r["partners"]
    ],
}

with open("partner_analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n分析結果已保存到 partner_analysis_results.json")

# 建立合作夥伴-文章映射
partner_to_articles = {}
for article in output["article_details"]:
    for partner in article["partners"]:
        if partner not in partner_to_articles:
            partner_to_articles[partner] = []
        partner_to_articles[partner].append(
            {
                "title": article["title"],
                "url": article["url"],
                "filename": article["filename"],
            }
        )

with open("partner_article_mapping.json", "w", encoding="utf-8") as f:
    json.dump(partner_to_articles, f, ensure_ascii=False, indent=2)

print("合作夥伴對應文章資料已保存到 partner_article_mapping.json")
