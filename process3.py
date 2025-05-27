import os
import json
import re
from collections import Counter
import jieba
jieba.setLogLevel(20) # 關閉結巴日誌輸出

# 讀取合作夥伴-文章映射數據
with open('partner_article_mapping.json', 'r', encoding='utf-8') as f:
    partner_articles = json.load(f)

# 讀取原始文章內容
article_contents = {}
txt_files = [f for f in os.listdir(".") if f.endswith('.txt')]

for txt_file in txt_files:
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            article_contents[txt_file] = f.read()
    except Exception as e:
        print(f"無法讀取 {txt_file}: {e}")

def extract_keywords(text, top_n=20):
    """從文本中提取關鍵詞"""
    # 使用結巴分詞
    words = jieba.cut(text)
    
    # 過濾停用詞
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                '一', '一个', '上', '也', '很', '到', '說', '要', '去', '你', '會',
                '可以', '這', '那', '又', '得', '著', '沒', '他', '她', '但', '從'}
    
    filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]
    
    # 計算詞頻
    word_counts = Counter(filtered_words)
    
    # 返回前N個高頻詞
    return word_counts.most_common(top_n)

def summarize_content(text, max_length=500):
    """簡單的內容摘要"""
    # 如果文本短於最大長度，直接返回
    if len(text) <= max_length:
        return text
    
    # 否則截取開頭部分
    return text[:max_length] + "..."

# 為每個主要合作夥伴生成摘要
output_dir = "合作夥伴摘要"
os.makedirs(output_dir, exist_ok=True)

# 讀取分析結果
with open('partner_analysis_results.json', 'r', encoding='utf-8') as f:
    analysis_results = json.load(f)

# 依據文章數量排序合作夥伴
sorted_partners = sorted(analysis_results['partner_article_counts'].items(), 
                         key=lambda x: x[1], reverse=True)

for partner, count in sorted_partners:
    if count == 0:
        continue
    
    articles = partner_articles.get(partner, [])
    if not articles:
        continue
    
    # 創建合作夥伴的摘要文件
    output_file = os.path.join(output_dir, f"{partner}_摘要.md")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {partner} 相關文章摘要\n\n")
        
        all_content = ""
        
        # 處理每篇文章
        for i, article in enumerate(articles, 1):
            filename = article['filename']
            title = article['title']
            
            f.write(f"## {i}. {title}\n\n")
            
            if filename in article_contents:
                content = article_contents[filename]
                all_content += content + " "
                
                # 寫入摘要
                f.write(f"### 內容摘要\n\n")
                f.write(f"{summarize_content(content)}\n\n")
            else:
                f.write("*無法獲取文章內容*\n\n")
        
        # 為所有文章生成關鍵詞列表
        if all_content:
            keywords = extract_keywords(all_content)
            
            f.write("## 主要關鍵詞\n\n")
            f.write("| 關鍵詞 | 頻次 |\n")
            f.write("|--------|------|\n")
            
            for word, freq in keywords:
                f.write(f"| {word} | {freq} |\n")

print(f"合作夥伴摘要已生成於 {output_dir} 目錄下")