from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

# 建立用於儲存結果的目錄
output_dir = "money101_data"
os.makedirs(output_dir, exist_ok=True)


def setup_driver():
    """設定並初始化 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # 無頭模式（不顯示瀏覽器視窗）
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        print("嘗試初始化 Chrome WebDriver...")
        # 使用更穩健的初始化方式
        chrome_driver_path = ChromeDriverManager().install()
        print(f"ChromeDriver 路徑: {chrome_driver_path}")

        # 顯式建立 Service 物件
        service = Service(executable_path=chrome_driver_path)

        # 使用最簡化的初始化方式 (避免 urllib3 timeout 問題)
        driver = webdriver.Chrome(options=options, service=service)
        print("WebDriver 初始化成功")
        return driver
    except Exception as e:
        print(f"WebDriver 初始化失敗: {e}")

        # 嘗試不使用 service 參數
        try:
            print("嘗試替代初始化方法 1...")
            driver = webdriver.Chrome(options=options)
            print("WebDriver 初始化成功")
            return driver
        except Exception as e2:
            print(f"替代初始化方法 1 失敗: {e2}")

            # 嘗試完全不使用 webdriver_manager
            try:
                print("嘗試替代初始化方法 2 (不使用 WebDriverManager)...")
                driver = webdriver.Chrome(options=options)
                print("WebDriver 初始化成功")
                return driver
            except Exception as e3:
                print(f"替代初始化方法 2 失敗: {e3}")

                # 嘗試使用最基本方法
                print("嘗試最基本的初始化方法...")
                return webdriver.Chrome()


def extract_articles(driver, url):
    """從指定 URL 提取文章標題和連結"""
    articles = []
    current_page = 1
    max_pages = 50  # 設定最大頁數

    print(f"開始從 {url} 抓取文章")
    driver.get(url)
    time.sleep(3)  # 等待頁面載入

    while current_page <= max_pages:
        print(f"正在處理第 {current_page} 頁")

        # 等待文章元素載入
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        "div.type-body-lg.md\\:type-headline-sm.font-bold",
                    )
                )
            )
        except TimeoutException:
            print("等待文章元素超時")

        # 獲取當前頁面上的所有文章
        article_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.type-body-lg.md\\:type-headline-sm.font-bold"
        )

        if not article_elements:
            print("找不到文章元素，嘗試其他選擇器")
            # 嘗試其他可能的選擇器
            article_elements = driver.find_elements(By.CSS_SELECTOR, ".article-card")

            if not article_elements:
                print("無法找到任何文章元素，可能頁面結構已變更")
                break

        # 提取文章資訊
        for element in article_elements:
            try:
                # 尋找標題連結和文字
                link_element = element.find_element(By.CSS_SELECTOR, "a")
                title_element = element.find_element(By.CSS_SELECTOR, "h2")

                href = link_element.get_attribute("href")
                title = title_element.text.strip()

                # 嘗試提取更新日期（如果有）
                try:
                    date_element = element.find_element(
                        By.CSS_SELECTOR, "div.type-caption.tws-mt-2"
                    )
                    update_date = date_element.text.replace("最後更新於", "").strip()
                except NoSuchElementException:
                    update_date = "未知日期"

                # 檢查是否已存在此連結
                if not any(article["連結"] == href for article in articles):
                    article_data = {
                        "標題": title,
                        "連結": href,
                        "更新日期": update_date,
                    }
                    articles.append(article_data)
                    print(f"已找到文章: {title}")
            except Exception as e:
                print(f"處理文章元素時出錯: {e}")
                continue

        # 檢查是否有下一頁
        try:
            # 找到分頁元素
            next_page_element = None
            pagination_elements = driver.find_elements(
                By.CSS_SELECTOR, "div.pagination-nav-item"
            )

            for element in pagination_elements:
                if (
                    element.text.strip() == str(current_page + 1)
                    or "下一頁" in element.text
                ):
                    next_page_element = element
                    break

            if next_page_element:
                # 捲動到分頁元素
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    next_page_element,
                )
                time.sleep(1)
                # 點擊下一頁
                driver.execute_script("arguments[0].click();", next_page_element)
                current_page += 1
                print(f"已點擊跳轉至第 {current_page} 頁")
                time.sleep(3)  # 等待新頁面載入
            else:
                # 嘗試查找 "right-sibling-page" 元素
                right_sibling = driver.find_elements(
                    By.CSS_SELECTOR, "div.right-sibling-page.pagination-nav-item"
                )
                if right_sibling:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        right_sibling[0],
                    )
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", right_sibling[0])
                    current_page += 1
                    print(f"已點擊右側分頁跳轉至第 {current_page} 頁")
                    time.sleep(3)
                else:
                    print("沒有找到下一頁按鈕，已到達最後一頁")
                    break
        except Exception as e:
            print(f"處理分頁時出錯: {e}")
            # 嘗試直接構建下一頁的 URL
            try:
                # 分析當前 URL 並構建下一頁 URL
                current_url = driver.current_url
                if "page/" in current_url:
                    # URL 已經有頁數參數，需要替換
                    next_url = re.sub(
                        r"page/\d+", f"page/{current_page + 1}", current_url
                    )
                else:
                    # URL 還沒有頁數參數，需要添加
                    if current_url.endswith("/"):
                        next_url = f"{current_url}page/{current_page + 1}/"
                    else:
                        next_url = f"{current_url}/page/{current_page + 1}/"

                print(f"嘗試直接訪問下一頁 URL: {next_url}")
                driver.get(next_url)
                time.sleep(3)

                # 檢查新頁面是否有效
                if (
                    len(
                        driver.find_elements(
                            By.CSS_SELECTOR,
                            "div.type-body-lg.md\\:type-headline-sm.font-bold",
                        )
                    )
                    > 0
                ):
                    current_page += 1
                    print(f"成功透過直接 URL 訪問第 {current_page} 頁")
                else:
                    print("透過 URL 訪問下一頁失敗，已到達最後一頁")
                    break
            except Exception as url_e:
                print(f"嘗試直接訪問下一頁失敗: {url_e}")
                break

    print(f"從 {url} 總共獲取到 {len(articles)} 篇文章")
    return articles


def save_articles_to_csv(articles, filename):
    """將文章資訊儲存為 CSV 檔案"""
    df = pd.DataFrame(articles)
    file_path = os.path.join(output_dir, filename)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"已將 {len(articles)} 篇文章資訊儲存至 {file_path}")
    return file_path


def scrape_article_content(driver, articles):
    """訪問每篇文章頁面並獲取內容"""
    article_details = []

    for i, article in enumerate(articles):
        try:
            print(f"正在訪問第 {i+1}/{len(articles)} 篇文章: {article['標題']}")
            driver.get(article["連結"])
            time.sleep(3)  # 等待頁面載入

            # 獲取文章內容
            content = ""
            try:
                # 從頁面獲取主要內容
                content_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.tws-prose.type-body-md, article.entry-content, div.entry-content",
                )

                if content_elements:
                    content = content_elements[0].text
                else:
                    # 嘗試獲取整個文章區域
                    article_body = driver.find_element(
                        By.CSS_SELECTOR, "div.article-body, article"
                    )
                    content = article_body.text
            except Exception as e:
                print(f"提取文章內容時出錯: {e}")
                content = "無法獲取內容"

            # 提取圖片
            image_urls = []
            try:
                image_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.article-body img, article img, div.entry-content img",
                )
                for img in image_elements:
                    img_src = img.get_attribute("src")
                    if img_src:
                        image_urls.append(img_src)
            except Exception as e:
                print(f"提取圖片時出錯: {e}")

            # 提取相關標籤
            tags = []
            try:
                tag_elements = driver.find_elements(
                    By.CSS_SELECTOR, "div.article-tags a, span.tags-links a, div.tags a"
                )
                tags = [tag.text for tag in tag_elements if tag.text.strip()]
            except Exception as e:
                print(f"提取標籤時出錯: {e}")

            # 將每篇文章內容單獨保存為文本文件
            content_file = os.path.join(
                output_dir,
                f"article_{i+1}_{article['標題'][:30].replace('/', '_')}.txt",
            )
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(f"標題: {article['標題']}\n\n")
                f.write(f"連結: {article['連結']}\n\n")
                f.write(f"更新日期: {article['更新日期']}\n\n")
                f.write(
                    f"圖片連結: {', '.join(image_urls) if image_urls else '無圖片'}\n\n"
                )
                f.write(f"標籤: {', '.join(tags) if tags else '無標籤'}\n\n")
                f.write("文章內容:\n\n")
                f.write(content)

            # 添加到文章詳情
            article_detail = {
                "標題": article["標題"],
                "連結": article["連結"],
                "更新日期": article["更新日期"],
                "分類": article.get("分類", "未分類"),
                "圖片數量": len(image_urls),
                "圖片連結": (
                    "; ".join(image_urls[:3]) if image_urls else "無圖片"
                ),  # 只保存前3個圖片連結
                "標籤": ", ".join(tags) if tags else "無標籤",
                "內容檔案": content_file,
                "內容長度": len(content),
            }

            article_details.append(article_detail)

            # 每5篇文章儲存一次臨時結果
            if (i + 1) % 5 == 0 or i == len(articles) - 1:
                temp_df = pd.DataFrame(article_details)
                temp_file = os.path.join(
                    output_dir, "money101_article_details_temp.csv"
                )
                temp_df.to_csv(temp_file, index=False, encoding="utf-8-sig")
                print(f"已臨時保存 {len(article_details)} 篇文章詳情")

        except Exception as e:
            print(f"處理文章 {article['標題']} 時出錯: {e}")
            continue

    # 儲存所有文章詳情
    details_file = os.path.join(output_dir, "money101_article_details.csv")
    details_df = pd.DataFrame(article_details)
    details_df.to_csv(details_file, index=False, encoding="utf-8-sig")
    print(f"成功獲取 {len(article_details)} 篇文章的詳細資訊，已儲存至 {details_file}")

    return article_details


def main():
    # Money101 要爬取的分類頁面 URL 列表
    urls = [
        "https://www.money101.com.tw/blog/category/%E4%BF%A1%E7%94%A8%E6%B6%88%E8%B2%BB%E7%94%9F%E6%B4%BB",
    ]

    driver = None
    all_articles = []

    try:
        print("====== Money101 爬蟲程式開始執行 ======")

        # 初始化瀏覽器
        print("正在初始化瀏覽器...")
        driver = setup_driver()
        print("瀏覽器初始化完成")

        # 處理每個URL
        for url in urls:
            # 提取網址中的分類名稱
            category_name = url.split("/")[-1]
            print(f"\n====== 開始處理分類: {category_name} ======")

            # 提取此分類的文章
            articles = extract_articles(driver, url)

            # 添加分類信息
            for article in articles:
                article["分類"] = category_name

            # 儲存此分類的文章
            save_articles_to_csv(articles, f"money101_{category_name}_articles.csv")

            # 添加到總列表
            all_articles.extend(articles)

            # 每個分類後稍等一下，避免伺服器負擔
            time.sleep(2)

        # 儲存所有文章
        if all_articles:
            all_file = save_articles_to_csv(all_articles, "money101_all_articles.csv")
            print(f"所有文章連結已儲存至 {all_file}")
        else:
            print("未找到任何文章")

        # 提取文章內容
        print("\n====== 開始獲取文章內容 ======")
        article_details = scrape_article_content(driver, all_articles)

        print("\n====== 爬蟲程式執行完畢 ======")
        print(f"總共獲取了 {len(all_articles)} 篇文章")
        print(f"數據已儲存到目錄: {os.path.abspath(output_dir)}")

    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
        import traceback

        print(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            print("瀏覽器已關閉")


if __name__ == "__main__":
    main()
