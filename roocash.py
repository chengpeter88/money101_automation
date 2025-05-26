from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
import os

# import sqlite3


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
# driver.get("https://roo.cash/blog/category/roo-creditcard/")

url = "https://roo.cash/blog/category/roo-creditcard/"
driver.get(url)
time.sleep(3)  # 等待網頁載入

# 建立用於儲存結果的目錄
output_dir = "/Users/heng/Documents/money101_cal/roocash_data"
os.makedirs(output_dir, exist_ok=True)


# 抓取所有文章連結
def get_all_articles():
    articles = []
    page_num = 1

    while True:
        print(f"正在獲取第 {page_num} 頁的文章...")
        # 找出所有文章卡片
        article_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.elementor-post__card"
        )

        # 如果沒有找到任何文章，可能是頁面結構不同或已到最後一頁
        if not article_elements:
            article_elements = driver.find_elements(
                By.CSS_SELECTOR, "h2.elementor-heading-title a"
            )
            if not article_elements:
                print("找不到更多文章，結束爬取")
                break

        # 獲取當前頁面的所有文章
        for element in article_elements:
            try:
                # 嘗試不同的方式獲取文章標題和連結
                if element.tag_name == "a":
                    title = element.text.strip()
                    href = element.get_attribute("href")
                else:
                    # 在卡片中尋找標題和連結
                    title_element = element.find_element(
                        By.CSS_SELECTOR,
                        "h3.elementor-post__title a, h2.elementor-heading-title a",
                    )
                    title = title_element.text.strip()
                    href = title_element.get_attribute("href")

                if title and href:
                    articles.append({"標題": title, "連結": href})
                    print(f"找到文章: {title} - {href}")
            except Exception as e:
                print(f"處理文章時出錯: {e}")
                continue

        # 檢查是否有下一頁
        try:
            next_page = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.page-numbers.next"))
            )
            next_page.click()
            time.sleep(3)  # 等待新頁面加載
            page_num += 1
        except TimeoutException:
            print("沒有更多頁面了")
            break
        except Exception as e:
            print(f"前往下一頁時出錯: {e}")
            break

    # 儲存所有文章連結
    df_articles = pd.DataFrame(articles)
    articles_file = os.path.join(output_dir, "roocash_articles.csv")
    df_articles.to_csv(articles_file, index=False, encoding="utf-8-sig")
    print(f"成功獲取 {len(articles)} 篇文章，已儲存至 {articles_file}")

    return articles


# 訪問每個文章頁面並提取詳細資訊
def scrape_article_details(articles):
    article_details = []
    
    for i, article in enumerate(articles):
        try:
            print(f"正在訪問第 {i+1}/{len(articles)} 篇文章: {article['標題']}")
            driver.get(article['連結'])
            time.sleep(3)  # 等待頁面加載
            
            # 嘗試找到文章內容 - 使用更多選擇器來提高命中率
            content = ""
            try:
                # 首先嘗試找到文章元素
                article_element = driver.find_element(By.CSS_SELECTOR, "article.bam-single-post, article.post")
                
                # 從文章元素中獲取內容
                try:
                    content_element = article_element.find_element(By.CSS_SELECTOR, "div.entry-content, div.elementor-widget-theme-post-content")
                    content = content_element.text
                except:
                    # 如果找不到特定內容區域，就獲取整個文章的文本
                    content = article_element.text
            except Exception as e:
                print(f"提取文章內容時出錯: {e}")
                content = "無法獲取內容"
                
            # 提取發佈日期
            publish_date = "未知日期"
            try:
                date_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "span.elementor-post-info__item--type-date, time.entry-date, meta[property='article:published_time']")
                if date_elements:
                    for date_element in date_elements:
                        if date_element.tag_name == 'meta':
                            publish_date = date_element.get_attribute('content').split('T')[0]
                        else:
                            publish_date = date_element.text
                        if publish_date and publish_date != "未知日期":
                            break
            except Exception as e:
                print(f"提取發佈日期時出錯: {e}")
            
            # 提取文章分類
            categories = "未分類"
            try:
                category_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "span.elementor-post-info__terms-list a, span.cat-links a, div.category-list a")
                if category_elements:
                    categories = ", ".join([cat.text for cat in category_elements])
            except Exception as e:
                print(f"提取文章分類時出錯: {e}")
            
            # 提取圖片
            image_url = "無圖片"
            try:
                # 嘗試多種可能的圖片選擇器
                image_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.elementor-featured-image img, div.post-thumbnail img, img.wp-post-image")
                if image_elements:
                    image_url = image_elements[0].get_attribute("src")
            except Exception as e:
                print(f"提取圖片時出錯: {e}")
            
            # 提取文章中的段落
            paragraphs = []
            try:
                paragraph_elements = driver.find_elements(By.CSS_SELECTOR, "div.entry-content p, div.elementor-widget-theme-post-content p")
                paragraphs = [p.text for p in paragraph_elements if p.text.strip()]
            except Exception as e:
                print(f"提取段落時出錯: {e}")
            
            # 提取標題
            headings = []
            try:
                heading_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.entry-content h1, div.entry-content h2, div.entry-content h3, div.entry-content h4, div.entry-content h5, div.entry-content h6, div.elementor-widget-theme-post-content h1, div.elementor-widget-theme-post-content h2, div.elementor-widget-theme-post-content h3, div.elementor-widget-theme-post-content h4, div.elementor-widget-theme-post-content h5, div.elementor-widget-theme-post-content h6")
                headings = [h.text for h in heading_elements if h.text.strip()]
            except Exception as e:
                print(f"提取標題時出錯: {e}")
            
            # 提取列表項
            list_items = []
            try:
                list_item_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.entry-content li, div.elementor-widget-theme-post-content li")
                list_items = [li.text for li in list_item_elements if li.text.strip()]
            except Exception as e:
                print(f"提取列表項時出錯: {e}")
            
            # 提取表格
            tables = []
            try:
                table_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.entry-content table, div.elementor-widget-theme-post-content table")
                for table in table_elements:
                    table_rows = table.find_elements(By.CSS_SELECTOR, "tr")
                    table_data = []
                    for row in table_rows:
                        cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                        row_data = [cell.text for cell in cells]
                        if row_data:
                            table_data.append(row_data)
                    if table_data:
                        tables.append(table_data)
            except Exception as e:
                print(f"提取表格時出錯: {e}")
            
            # 尋找文章中提到的信用卡
            credit_cards = []
            card_patterns = [
                r"(\w+)信用卡",
                r"(\w+)卡",
                r"(\w+)(現金|鑽石|御璽|白金|鈦金|金)卡"
            ]
            
            for pattern in card_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            card = "".join(match)
                        else:
                            card = match + "信用卡"
                        credit_cards.append(card)
            
            # 去重
            credit_cards = list(set(credit_cards))
            
            # 合併為完整內容
            full_content = "\n\n".join([
                "## 文章標題\n" + "\n".join(headings) if headings else "## 文章標題\n無標題",
                "## 文章段落\n" + "\n\n".join(paragraphs) if paragraphs else "## 文章段落\n無段落內容",
                "## 文章列表\n" + "\n".join(list_items) if list_items else "## 文章列表\n無列表內容"
            ])
            
            # 創建豐富的文章詳情
            article_detail = {
                "標題": article["標題"],
                "連結": article["連結"],
                "發佈日期": publish_date,
                "分類": categories,
                "圖片連結": image_url,
                "提到的信用卡": ", ".join(credit_cards) if credit_cards else "無提及信用卡",
                "標題數量": len(headings),
                "段落數量": len(paragraphs),
                "列表項數量": len(list_items),
                "表格數量": len(tables),
                "完整內容": full_content,
                "原始內容": content,
                "段落內容": paragraphs,
                "標題內容": headings,
                "列表內容": list_items,
            }
            
            # 保存表格數據（如果有）
            if tables:
                table_file = os.path.join(output_dir, f"article_{i+1}_tables.txt")
                with open(table_file, "w", encoding="utf-8") as f:
                    for t_idx, table in enumerate(tables):
                        f.write(f"表格 {t_idx+1}:\n")
                        for row in table:
                            f.write(" | ".join(row) + "\n")
                        f.write("\n\n")
                article_detail["表格檔案"] = table_file
            
            # 將每篇文章內容單獨保存為文本文件
            content_file = os.path.join(output_dir, f"article_{i+1}_content.txt")
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(f"標題: {article['標題']}\n\n")
                f.write(f"連結: {article['連結']}\n\n")
                f.write(f"發布日期: {publish_date}\n\n")
                f.write(f"分類: {categories}\n\n")
                f.write("完整內容:\n\n")
                f.write(full_content)
                
            article_detail["內容檔案"] = content_file
            article_details.append(article_detail)
            
            # 每5篇文章儲存一次，避免中途出錯損失數據
            if (i + 1) % 5 == 0 or i == len(articles) - 1:
                temp_df = pd.DataFrame(
                    [
                        {k: v for k, v in detail.items() if not isinstance(v, list)}
                        for detail in article_details
                    ]
                )
                temp_file = os.path.join(output_dir, "roocash_article_details_temp.csv")
                temp_df.to_csv(temp_file, index=False, encoding="utf-8-sig")
                print(f"已臨時保存 {len(article_details)} 篇文章細節")
                
        except Exception as e:
            import traceback
            print(f"處理文章 {article['標題']} 時出錯: {str(e)}")
            print(traceback.format_exc())
            continue

    # 儲存所有文章詳細資訊
    # 移除不適合存入CSV的欄位
    simplified_details = []
    for detail in article_details:
        simplified = {
            k: v
            for k, v in detail.items()
            if not isinstance(v, list) and k not in ["完整內容", "原始內容"]
        }
        simplified_details.append(simplified)

    df_details = pd.DataFrame(simplified_details)
    details_file = os.path.join(output_dir, "roocash_article_details.csv")
    df_details.to_csv(details_file, index=False, encoding="utf-8-sig")
    print(f"成功獲取 {len(article_details)} 篇文章的詳細資訊，已儲存至 {details_file}")

    return article_details


try:
    # 執行爬蟲
    all_articles = get_all_articles()
    article_details = scrape_article_details(all_articles)

    print("爬蟲完成！")
    print(f"總共爬取了 {len(all_articles)} 篇文章")
    print(f"數據已儲存到目錄: {output_dir}")

finally:
    # 關閉瀏覽器
    driver.quit()
