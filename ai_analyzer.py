import os
import re
import jieba
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from colorama import init, Fore, Style
from tabulate import tabulate
import seaborn as sns
from tqdm import tqdm
import json
from dotenv import load_dotenv
import openai
from openai import OpenAI
import time
import logging

# 載入環境變數（存放 API 金鑰）
load_dotenv()

# 設置 OpenAI API 金鑰
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    print(
        f"{Fore.RED}警告: 未設置 OPENAI_API_KEY 環境變數。AI 分析功能將不可用。{Style.RESET_ALL}"
    )
    print(
        f"{Fore.YELLOW}請設置環境變數或創建 .env 檔案並包含: OPENAI_API_KEY=您的金鑰{Style.RESET_ALL}"
    )

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("text_analysis.log"), logging.StreamHandler()],
)
logger = logging.getLogger("text_analyzer")

# 初始化 colorama
init(autoreset=True)


STOPWORDS = set(
    [
        "的", "了", "是", "在", "有", "和", "與", "也", "就", "都", "及", "為", "或",
        "而", "於", "被", "由", "到", "這", "那", "一個", "我們", "你們", "他們", "她們",
        "它們", "我", "你", "他", "她", "它", "其", "之", "及", "等", "上", "下", "後",
        "前", "更", "再", "又", "還", "會", "能", "要", "把", "但", "並", "如果", "因為",
        "所以", "而且", "但是", "就是", "沒有", "不是", "可以", "可能", "已經", "正在",
        "以及", "其中", "對於", "關於", "關係", "相關", "方面",
    ]
)

# 關鍵字分類 (原有代碼)
KEYWORD_CATEGORIES = {
    "銀行": [
        "富邦銀行", "玉山銀行", "中信銀行", "永豐銀行", "滙豐銀行",
        "台新銀行", "國泰世華銀行", "彰化銀行", "華南銀行", "第一銀行",
    ],
    "信貸": [
        "富邦信貸", "玉山信貸", "中信信貸", "永豐信貸", "台新信貸",
        "國泰信貸", "彰化信貸", "華南信貸", "第一信貸",
    ],
    "證券": [
        "富邦證券", "元富證券", "中信證券", "康和證券", "鉅亨網",
        "永豐金證券", "台新證券", "國泰證券",
    ],
    "支付": ["LINE Pay", "Apple Pay", "Google Pay", "Samsung Pay", "PayPal"],
    "金融商品": ["ETF", "美股", "台股", "基金", "信用卡"],
    "保險": ["富邦人壽", "國泰人壽", "新光人壽", "台灣人壽", "中信人壽"],
}

# 輸出目錄
output_dir = "analysis_results"
os.makedirs(output_dir, exist_ok=True)

# AI 分析相關的目錄
ai_analysis_dir = os.path.join(output_dir, "ai_analysis")
os.makedirs(ai_analysis_dir, exist_ok=True)


def print_header(text):
    """打印美觀的標題"""
    width = 70
    print("\n" + "=" * width)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(width)}")
    print("=" * width)


def print_info(text):
    """打印資訊文字"""
    print(f"{Fore.GREEN}ℹ {Style.RESET_ALL}{text}")


def print_section(text):
    """打印小節標題"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}▶ {text}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'-' * 50}{Style.RESET_ALL}")


def get_all_content_files(folder):
    """獲取所有內容檔案"""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith("_content.txt") or f.endswith(".txt")
    ]


def read_all_articles(folder):
    """讀取所有文章內容"""
    files = get_all_content_files(folder)
    print_info(f"發現 {len(files)} 個文本檔案")

    articles = []
    article_names = []

    for file in tqdm(files, desc="讀取檔案", ncols=70):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                articles.append(content)
                article_names.append(os.path.basename(file))
        except Exception as e:
            print(f"無法讀取檔案 {file}: {e}")

    return articles, article_names


# 原有的分詞和分析函數 (略)
def tokenize(text):
    """對文本分詞並過濾停用詞"""
    words = jieba.cut(text)
    return [
        w.strip()
        for w in words
        if w.strip() and w not in STOPWORDS and len(w.strip()) > 1
    ]


def analyze_keywords(text, categories):
    """分析文本中的關鍵字"""
    results = defaultdict(int)
    keyword_instances = defaultdict(list)

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                results[category] += 1
                keyword_instances[category].append(keyword)

    return results, keyword_instances


# 創建詞雲圖
def create_word_cloud(words_freq, title, output_file):
    """創建詞雲圖"""
    try:
        from wordcloud import WordCloud

        # 生成詞雲
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            font_path="/System/Library/Fonts/PingFang.ttc",  # Mac中文字體
            max_words=100,
        ).generate_from_frequencies(dict(words_freq))

        # 繪製詞雲圖
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()

        print_info(f"詞雲已保存至: {output_file}")
    except ImportError:
        print_info("無法創建詞雲圖: 需要安裝 wordcloud 套件 (pip install wordcloud)")
    except Exception as e:
        print_info(f"創建詞雲圖時出錯: {e}")


def plot_category_stats(category_stats, output_file):
    """繪製類別統計條形圖"""
    # 排序數據
    categories = list(category_stats.keys())
    values = list(category_stats.values())
    sorted_indices = sorted(range(len(values)), key=lambda i: values[i], reverse=True)

    categories = [categories[i] for i in sorted_indices]
    values = [values[i] for i in sorted_indices]

    # 設置繪圖風格
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")

    # 繪製條形圖
    bars = plt.bar(
        categories, values, color=sns.color_palette("viridis", len(categories))
    )

    # 添加數值標籤
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.1,
            int(height),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # 設置標題和標籤
    plt.title("關鍵字分類統計", fontsize=16)
    plt.xlabel("分類", fontsize=12)
    plt.ylabel("出現次數", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # 保存圖表
    plt.savefig(output_file, dpi=300)
    plt.close()

    print_info(f"類別統計圖已保存至: {output_file}")


def extract_article_metadata(text):
    """提取文章的標題、連結和分類等元數據"""
    metadata = {
        "title": None,
        "url": None,
        "categories": [],
        "publish_date": None
    }
    
    # 尋找標題
    title_match = re.search(r'標題:\s*(.*?)(?:\r?\n)', text)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    
    # 尋找連結
    url_match = re.search(r'連結:\s*(.*?)(?:\r?\n)', text)
    if url_match:
        metadata["url"] = url_match.group(1).strip()
    
    # 尋找分類
    category_match = re.search(r'分類:\s*(.*?)(?:\r?\n)', text)
    if category_match:
        categories = category_match.group(1).strip()
        # 分割分類，通常以逗號分隔
        metadata["categories"] = [cat.strip() for cat in categories.split(',')]
    
    # 尋找發布日期
    date_match = re.search(r'發布日期:\s*(.*?)(?:\r?\n)', text)
    if date_match:
        metadata["publish_date"] = date_match.group(1).strip()
    
    return metadata


#  OpenAI analysis functions
def analyze_text_with_openai(text, article_id="", retries=3):
    """使用 OpenAI 進行文本分析"""
    if not api_key:
        return {"error": "未設置 OPENAI_API_KEY，無法進行 AI 分析"}

    # 提取文章元數據
    metadata = extract_article_metadata(text)
    
    # 如果文本過長，截斷
    max_length = 14000  # GPT-4 可處理的大約最大字數 (保守估計)
    if len(text) > max_length:
        print_info(f"文章過長，截斷至 {max_length} 字符")
        text = text[:max_length]

    # 分析提示
    prompt = f"""
    請分析以下金融相關文章，並以 JSON 格式輸出以下分析結果:
    
    1. main_topic: 文章的主要主題
    2. financial_products: 文章中提及的金融產品 (如信用卡、貸款產品、基金等)的列表
    3. financial_institutions: 文章中提及的金融機構 (如銀行、券商等)的列表
    4. summary: 200字左右的文章摘要
    5. recommendations: 從文章中提煉出的關鍵建議或結論
    
    請確保返回的 JSON 格式正確且全部用繁體中文。
    
    文章內容:
    {text}
    """

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一個專業金融文本分析助手，擅長識別文章中的金融產品、機構和核心觀點，並提供客觀分析。",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            # 解析 JSON 結果
            result = json.loads(response.choices[0].message.content)

            # 添加文章 ID 
            if article_id:
                result["article_id"] = article_id
            
            # 添加元數據到結果中
            if metadata["title"]:
                result["title"] = metadata["title"]
            if metadata["url"]:
                result["url"] = metadata["url"]
            if metadata["categories"]:
                result["categories"] = metadata["categories"]
            if metadata["publish_date"]:
                result["publish_date"] = metadata["publish_date"]

            return result

        except Exception as e:
            # 如果這不是最後一次嘗試，則等待後重試
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # 指數退避策略
                logger.warning(f"AI 分析出錯，{wait_time}秒後重試: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"AI 分析失敗: {e}")
                return {"error": f"AI 分析失敗: {str(e)}", "article_id": article_id}


# 新增函數：讓使用者選擇要分析的文章
def select_articles_for_analysis(articles, article_names):
    """讓使用者選擇要分析的文章"""
    print_section("選擇要分析的文章")
    print_info("可用選項:")
    print("1. 分析所有文章")
    print("2. 分析前 N 篇文章")
    print("3. 手動選擇特定文章")
    print("4. 根據關鍵字篩選文章")

    choice = (
        input(f"{Fore.GREEN}請選擇文章選擇方式 (1/2/3/4): {Style.RESET_ALL}").strip()
        or "1"
    )

    if choice == "1":
        print_info(f"已選擇: 分析所有 {len(articles)} 篇文章")
        return articles, article_names

    elif choice == "2":
        num = input(f"{Fore.GREEN}請輸入要分析的文章數量: {Style.RESET_ALL}").strip()
        try:
            num = int(num)
            if num <= 0 or num > len(articles):
                print_info(f"輸入無效，將分析所有 {len(articles)} 篇文章")
                return articles, article_names

            print_info(f"已選擇: 分析前 {num} 篇文章")
            return articles[:num], article_names[:num]
        except ValueError:
            print_info(f"輸入無效，將分析所有 {len(articles)} 篇文章")
            return articles, article_names

    elif choice == "3":
        # 顯示所有文章供選擇
        print_info("請選擇要分析的文章 (輸入編號，用逗號分隔):")

        # 分頁顯示文章列表
        page_size = 20
        for i in range(0, len(article_names), page_size):
            page_articles = article_names[i : i + page_size]

            table_data = []
            for j, name in enumerate(page_articles):
                article_idx = i + j
                # 顯示文章編號和檔案名
                table_data.append([article_idx + 1, name])

            print(tabulate(table_data, headers=["編號", "文章檔案名"], tablefmt="grid"))

            if i + page_size < len(article_names):
                more = (
                    input(f"{Fore.YELLOW}顯示更多? (Y/n): {Style.RESET_ALL}")
                    .strip()
                    .lower()
                )
                if more == "n":
                    break

        # 獲取用戶選擇
        selected_indices_str = input(
            f"{Fore.GREEN}請輸入要分析的文章編號 (例如: 1,3,5-7): {Style.RESET_ALL}"
        ).strip()

        # 解析選擇
        selected_indices = []
        parts = selected_indices_str.split(",")

        for part in parts:
            part = part.strip()
            if "-" in part:
                # 範圍選擇，如 "5-7"
                try:
                    start, end = map(int, part.split("-"))
                    # 轉換為 0-based 索引
                    selected_indices.extend(range(start - 1, end))
                except ValueError:
                    continue
            else:
                # 單個編號選擇
                try:
                    idx = int(part) - 1  # 轉換為 0-based 索引
                    if 0 <= idx < len(articles):
                        selected_indices.append(idx)
                except ValueError:
                    continue

        # 移除重複並排序
        selected_indices = sorted(set(selected_indices))

        if not selected_indices:
            print_info("未選擇任何文章，將分析所有文章")
            return articles, article_names

        # 根據選擇獲取對應的文章和名稱
        selected_articles = [
            articles[idx] for idx in selected_indices if idx < len(articles)
        ]
        selected_names = [
            article_names[idx] for idx in selected_indices if idx < len(article_names)
        ]

        print_info(f"已選擇 {len(selected_articles)} 篇文章進行分析")
        return selected_articles, selected_names

    elif choice == "4":
        # 根據關鍵字篩選文章
        keyword = input(f"{Fore.GREEN}請輸入要搜尋的關鍵字: {Style.RESET_ALL}").strip()

        if not keyword:
            print_info("未輸入關鍵字，將分析所有文章")
            return articles, article_names

        # 篩選包含關鍵字的文章
        filtered_articles = []
        filtered_names = []

        print_info(f"正在搜尋包含 '{keyword}' 的文章...")

        for idx, (article, name) in enumerate(zip(articles, article_names)):
            if keyword.lower() in article.lower() or keyword.lower() in name.lower():
                filtered_articles.append(article)
                filtered_names.append(name)

        if not filtered_articles:
            print_info(f"未找到包含關鍵字 '{keyword}' 的文章，將分析所有文章")
            return articles, article_names

        print_info(f"找到 {len(filtered_articles)} 篇包含關鍵字 '{keyword}' 的文章")

        # 顯示篩選後的文章
        table_data = []
        for i, name in enumerate(filtered_names):
            table_data.append([i + 1, name])

        print(tabulate(table_data, headers=["編號", "文章檔案名"], tablefmt="grid"))

        confirm = (
            input(f"{Fore.GREEN}是否要分析這些文章? (Y/n): {Style.RESET_ALL}")
            .strip()
            .lower()
        )
        if confirm == "n":
            print_info("將分析所有文章")
            return articles, article_names

        return filtered_articles, filtered_names

    else:
        print_info(f"無效選擇，將分析所有 {len(articles)} 篇文章")
        return articles, article_names


def batch_analyze_with_ai(articles, article_names, max_articles=None, batch_size=5):
    """批次處理多篇文章"""
    print_section("OpenAI 智能文本分析")

    if not api_key:
        print_info("未設置 OPENAI_API_KEY，跳過 AI 分析")
        return []

    if max_articles:
        print_info(f"將處理前 {max_articles} 篇文章")
        articles = articles[:max_articles]
        article_names = article_names[:max_articles]

    results = []

    print_info(f"開始處理 {len(articles)} 篇文章")

    # 分批處理，每批 batch_size 篇文章
    for i in range(0, len(articles), batch_size):
        batch_articles = articles[i : i + batch_size]
        batch_names = article_names[i : i + batch_size]

        for j, (article, name) in enumerate(zip(batch_articles, batch_names)):
            overall_index = i + j + 1

            # 從文件名中提取 ID 或使用索引作為 ID
            article_id = name.replace("_content.txt", "").replace(".txt", "")
            if not article_id:
                article_id = f"article_{overall_index}"

            print_info(f"正在處理第 {overall_index}/{len(articles)} 篇文章: {name}")

            # 檢查是否已存在分析結果
            output_file = os.path.join(ai_analysis_dir, f"analysis_{article_id}.json")
            if os.path.exists(output_file):
                print_info(f"已存在分析結果，跳過: {output_file}")
                with open(output_file, "r", encoding="utf-8") as f:
                    result = json.load(f)
                    results.append(result)
                continue

            # 分析文章
            result = analyze_text_with_openai(article, article_id)

            # 保存分析結果
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            results.append(result)
            print_info(f"已保存分析結果: {output_file}")

            # 避免 API 速率限制
            if j < len(batch_articles) - 1:
                time.sleep(1)

        # 批次之間的等待，避免 API 限制
        if i + batch_size < len(articles):
            print_info(f"等待 3 秒後處理下一批...")
            time.sleep(3)

    return results


def create_ai_analysis_summary(ai_results):
    """生成 AI 分析結果的摘要報告"""
    if not ai_results:
        return

    print_section("AI 分析摘要報告")

    # 1. 提取所有金融產品
    all_products = []
    for result in ai_results:
        if "financial_products" in result:
            all_products.extend(result["financial_products"])

    product_counter = Counter(all_products)
    top_products = product_counter.most_common(10)

    print_info("最常提及的金融產品:")
    product_table = [
        [i + 1, prod, count] for i, (prod, count) in enumerate(top_products)
    ]
    print(
        tabulate(
            product_table, headers=["排名", "金融產品", "提及次數"], tablefmt="grid"
        )
    )

    # 2. 提取所有金融機構
    all_institutions = []
    for result in ai_results:
        if "financial_institutions" in result:
            all_institutions.extend(result["financial_institutions"])

    institution_counter = Counter(all_institutions)
    top_institutions = institution_counter.most_common(10)

    print_info("最常提及的金融機構:")
    institution_table = [
        [i + 1, inst, count] for i, (inst, count) in enumerate(top_institutions)
    ]
    print(
        tabulate(
            institution_table, headers=["排名", "金融機構", "提及次數"], tablefmt="grid"
        )
    )

    # 3. 主題分類
    topics = [
        result.get("main_topic", "N/A")
        for result in ai_results
        if "main_topic" in result
    ]

    print_info(f"分析了 {len(topics)} 個主題:")
    for i, topic in enumerate(topics[:10], 1):  # 只顯示前 10 個主題
        print(f"{i}. {topic}")

    if len(topics) > 10:
        print_info(f"...以及其他 {len(topics) - 10} 個主題")
        
    # 4. 收集文章分類信息
    all_categories = []
    for result in ai_results:
        if "categories" in result:
            all_categories.extend(result["categories"])
            
    category_counter = Counter(all_categories)
    top_categories = category_counter.most_common()
    
    print_info("最常見的文章分類:")
    category_table = [
        [i + 1, cat, count] for i, (cat, count) in enumerate(top_categories)
    ]
    print(
        tabulate(
            category_table, headers=["排名", "文章分類", "出現次數"], tablefmt="grid"
        )
    )

    # 保存摘要分析
    summary_data = {
        "top_products": dict(top_products),
        "top_institutions": dict(top_institutions),
        "topics": topics,
        "categories": dict(top_categories)
    }

    with open(
        os.path.join(ai_analysis_dir, "ai_summary.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    # 保存為 CSV 方便在 Excel 中查看
    df_products = pd.DataFrame(top_products, columns=["產品", "提及次數"])
    df_institutions = pd.DataFrame(top_institutions, columns=["機構", "提及次數"])
    df_topics = pd.DataFrame({"主題": topics})
    df_categories = pd.DataFrame(top_categories, columns=["分類", "出現次數"])

    with pd.ExcelWriter(os.path.join(ai_analysis_dir, "ai_summary.xlsx")) as writer:
        df_products.to_excel(writer, sheet_name="金融產品", index=False)
        df_institutions.to_excel(writer, sheet_name="金融機構", index=False)
        df_topics.to_excel(writer, sheet_name="主題分類", index=False)
        df_categories.to_excel(writer, sheet_name="文章分類", index=False)

    print_info(
        f"AI 分析摘要已保存至: {os.path.join(ai_analysis_dir, 'ai_summary.json')} 和 {os.path.join(ai_analysis_dir, 'ai_summary.xlsx')}"
    )


def main():
    folder = (
        input(
            f"{Fore.GREEN}請輸入文本資料夾路徑{Style.RESET_ALL} [預設:roocash_data]: "
        ).strip()
        or "roocash_data"
    )

    print_header("Money101 / RooCash 文本分析系統")
    print_info(f"分析資料夾: {os.path.abspath(folder)}")

    articles, article_names = read_all_articles(folder)

    if not articles:
        print(f"{Fore.RED}未找到任何文章!{Style.RESET_ALL}")
        return

    print_info(f"成功讀取 {len(articles)} 篇文章")

    # 詢問使用者要執行哪種分析
    print_section("選擇分析模式")
    print("1. 基本詞頻統計和關鍵字分析")
    print("2. 使用 OpenAI API 進行深度文本分析")
    print("3. 執行所有分析")

    choice = (
        input(f"{Fore.GREEN}請選擇分析模式 (1/2/3) [預設:3]: {Style.RESET_ALL}").strip()
        or "3"
    )

    # 基本詞頻分析
    if choice in ["1", "3"]:
        # 1. 基本詞頻統計
        print_section("詞頻統計分析")

        all_words = []
        print_info("正在進行分詞處理...")
        for i, article in enumerate(tqdm(articles, desc="分詞處理", ncols=70)):
            words = tokenize(article)
            all_words.extend(words)

        counter = Counter(all_words)

        # 輸出表格
        most_common = counter.most_common(30)

        # 詞頻表格
        word_table = [[i + 1, word, freq] for i, (word, freq) in enumerate(most_common)]
        print(tabulate(word_table, headers=["排名", "詞彙", "頻率"], tablefmt="grid"))

        # 保存到CSV
        df_words = pd.DataFrame(most_common, columns=["詞彙", "頻次"])
        df_words.index = range(1, len(df_words) + 1)
        df_words.to_csv(os.path.join(output_dir, "top_words.csv"), encoding="utf-8-sig")
        print_info(f"熱門詞彙已保存至: {os.path.join(output_dir, 'top_words.csv')}")

        # 創建詞雲
        create_word_cloud(
            counter.most_common(100),
            "熱門詞彙詞雲",
            os.path.join(output_dir, "word_cloud.png"),
        )

        # 2. 關鍵字分類統計
        print_section("關鍵字分類統計")

        category_stats = defaultdict(int)
        all_keyword_instances = defaultdict(list)

        for article in tqdm(articles, desc="關鍵字分析", ncols=70):
            article_stats, keyword_instances = analyze_keywords(
                article, KEYWORD_CATEGORIES
            )
            for category, count in article_stats.items():
                category_stats[category] += count
                all_keyword_instances[category].extend(keyword_instances[category])

        # 排序並顯示分類統計
        sorted_stats = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)

        cat_table = [
            [i + 1, category, count] for i, (category, count) in enumerate(sorted_stats)
        ]
        print(
            tabulate(cat_table, headers=["排名", "類別", "出現次數"], tablefmt="grid")
        )

        # 保存分類統計
        df_cats = pd.DataFrame(sorted_stats, columns=["類別", "出現次數"])
        df_cats.index = range(1, len(df_cats) + 1)
        df_cats.to_csv(
            os.path.join(output_dir, "category_stats.csv"), encoding="utf-8-sig"
        )
        print_info(
            f"類別統計已保存至: {os.path.join(output_dir, 'category_stats.csv')}"
        )

        # 繪製分類統計圖
        plot_category_stats(
            category_stats, os.path.join(output_dir, "category_stats.png")
        )

        # 3. 關鍵字實例分析
        print_section("關鍵字實例分析")

        for category, keywords in sorted(
            all_keyword_instances.items(), key=lambda x: len(x[1]), reverse=True
        ):
            # 計算每個關鍵字的出現次數
            keyword_counter = Counter(keywords)
            top_keywords = keyword_counter.most_common()

            print(f"{Fore.GREEN}【{category}】{Style.RESET_ALL} 類別中出現的關鍵字:")

            keyword_table = [[keyword, count] for keyword, count in top_keywords]
            if keyword_table:
                print(
                    tabulate(
                        keyword_table,
                        headers=["關鍵字", "出現次數"],
                        tablefmt="simple",
                        colalign=("left", "right"),
                    )
                )
            print()

        # 4. 文章關鍵字分析 (僅顯示包含關鍵字的文章)
        print_section("文章關鍵字分佈")

        article_results = []

        for i, (article, name) in enumerate(zip(articles, article_names)):
            article_stats, keyword_instances = analyze_keywords(
                article, KEYWORD_CATEGORIES
            )

            if sum(article_stats.values()) > 0:  # 只處理有關鍵字的文章
                result = {
                    "文章編號": i + 1,
                    "文章名稱": name,
                    "總關鍵字數": sum(article_stats.values()),
                }

                # 添加每個類別的統計
                for category in KEYWORD_CATEGORIES:
                    result[category] = article_stats.get(category, 0)

                article_results.append(result)

        # 按關鍵字總數排序
        article_results.sort(key=lambda x: x["總關鍵字數"], reverse=True)

        # 輸出文章關鍵字表格 (僅顯示前10篇)
        if article_results:
            # 準備表格數據
            headers = ["編號", "文章名稱", "總數"] + list(KEYWORD_CATEGORIES.keys())

            table_data = []
            for result in article_results[:10]:  # 只顯示前10篇
                name = result["文章名稱"]
                if len(name) > 30:
                    name = name[:27] + "..."

                row = [result["文章編號"], name, result["總關鍵字數"]]

                # 添加每個類別的值
                for category in KEYWORD_CATEGORIES:
                    row.append(result.get(category, 0))

                table_data.append(row)

            print(tabulate(table_data, headers=headers, tablefmt="grid"))

            if len(article_results) > 10:
                print_info(f"僅顯示前10篇 (共 {len(article_results)} 篇文章含有關鍵字)")

            # 保存完整結果
            df_articles = pd.DataFrame(article_results)
            df_articles.to_csv(
                os.path.join(output_dir, "article_keywords.csv"),
                encoding="utf-8-sig",
                index=False,
            )
            print_info(
                f"文章關鍵字分析已保存至: {os.path.join(output_dir, 'article_keywords.csv')}"
            )
        else:
            print_info("未找到包含關鍵字的文章")

    # OpenAI API 深度文本分析
    if choice in ["2", "3"] and api_key:
        # 使用新增加的選擇文章功能選擇要分析的文章
        selected_articles, selected_article_names = select_articles_for_analysis(
            articles, article_names
        )

        # 如果選擇的文章數量過多，提示確認
        if len(selected_articles) > 10:
            confirm = (
                input(
                    f"{Fore.YELLOW}警告: 您選擇了 {len(selected_articles)} 篇文章，這可能耗費大量 API 額度。確定要分析全部嗎? (y/n): {Style.RESET_ALL}"
                )
                .strip()
                .lower()
            )
            if confirm != "y":
                max_articles = 10
                print_info(f"將只分析前 {max_articles} 篇文章")
                selected_articles = selected_articles[:max_articles]
                selected_article_names = selected_article_names[:max_articles]

        # 執行 AI 分析
        ai_results = batch_analyze_with_ai(selected_articles, selected_article_names)

        # 生成 AI 分析摘要
        if ai_results:
            create_ai_analysis_summary(ai_results)

    print_header("分析完成")
    print_info(f"所有分析結果已保存至: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}分析已被使用者中斷{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}分析過程中發生錯誤: {e}{Style.RESET_ALL}")
        import traceback

        traceback.print_exc()
