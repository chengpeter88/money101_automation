from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time
import os
from colorama import init, Fore, Style
from tabulate import tabulate
from tqdm import tqdm
import datetime

# 初始化 colorama 以支援彩色輸出
init(autoreset=True)

# 建立簡易儲存目錄
output_dir = "money101_simple_data"
os.makedirs(output_dir, exist_ok=True)


def print_banner(text):
    """印出美觀的標題橫幅"""
    width = 70
    print("\n" + "=" * width)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(width)}")
    print("=" * width + "\n")


def print_info(text):
    """印出資訊文字"""
    print(f"{Fore.GREEN}ℹ {Style.RESET_ALL}{text}")


def print_warning(text):
    """印出警告文字"""
    print(f"{Fore.YELLOW}⚠ {Style.RESET_ALL}{text}")


def print_error(text):
    """印出錯誤文字"""
    print(f"{Fore.RED}✖ {Style.RESET_ALL}{text}")


def print_success(text):
    """印出成功文字"""
    print(f"{Fore.GREEN}✓ {Style.RESET_ALL}{text}")


def simple_crawler():
    """簡化版的 Money101 爬蟲，只爬取單頁文章"""

    # 要爬取的單頁 URL
    url = "https://www.money101.com.tw/blog/category/%E4%BF%A1%E7%94%A8%E6%B6%88%E8%B2%BB%E7%94%9F%E6%B4%BB"

    print_banner("Money101 信用消費生活文章爬蟲")
    print_info(f"目標頁面: {url}")
    print_info(f"執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"輸出目錄: {os.path.abspath(output_dir)}")
    print()

    try:
        # 初始化瀏覽器 (不使用 headless 模式以便觀察)
        print_info("正在初始化瀏覽器...")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        print_success("瀏覽器初始化完成")

        # 訪問頁面
        print_info("正在載入頁面...")
        driver.get(url)

        # 使用 tqdm 顯示頁面載入進度條
        for _ in tqdm(
            range(5),
            desc="頁面載入中",
            ncols=70,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
        ):
            time.sleep(1)

        print_banner("開始抓取文章")

        # 修改選擇器，直接定位 a 標籤
        article_links = driver.find_elements(
            By.CSS_SELECTOR, "div.type-body-lg.md\\:type-headline-sm.font-bold > a"
        )

        if not article_links:
            print_warning("找不到預期的文章連結，嘗試其他選擇器...")
            # 截取當前頁面以診斷
            driver.save_screenshot(os.path.join(output_dir, "page_screenshot.png"))
            print_info(
                f"已保存頁面截圖至: {os.path.join(output_dir, 'page_screenshot.png')}"
            )

            # 嘗試其他可能的選擇器
            article_links = driver.find_elements(By.CSS_SELECTOR, ".article-card a")

            if not article_links:
                # 嘗試更一般的選擇器
                article_links = driver.find_elements(By.CSS_SELECTOR, "a > h2")

                if not article_links:
                    print_error("找不到任何文章連結")
                    with open(
                        os.path.join(output_dir, "page_source.html"),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(driver.page_source)
                    print_info(
                        f"已保存頁面源碼至: {os.path.join(output_dir, 'page_source.html')}"
                    )
                    return

        # 從找到的連結中提取資訊
        articles = []

        print_success(f"找到 {len(article_links)} 個文章連結")
        print()

        # 使用 tqdm 建立一個進度條來顯示文章處理進度
        for i, link in enumerate(tqdm(article_links, desc="處理文章", ncols=70)):
            try:
                # 先獲取連結資訊
                href = link.get_attribute("href")

                # 獲取標題
                try:
                    # 先嘗試獲取連結內的 h2 標題
                    title_element = link.find_element(By.CSS_SELECTOR, "h2")
                    title = title_element.text.strip()
                except:
                    # 如果沒有 h2，則使用連結的文字
                    title = link.text.strip() or "無法獲取標題"

                # 獲取日期 - 需要找到父元素後的兄弟元素
                try:
                    # 先找到連結的父元素
                    parent = link.find_element(By.XPATH, "..")
                    # 然後找到該父元素中的日期元素
                    date_element = parent.find_element(
                        By.CSS_SELECTOR, "div.type-caption.tws-mt-2"
                    )
                    update_date = date_element.text.replace("最後更新於", "").strip()
                except:
                    update_date = "未知日期"

                # 創建文章資訊
                article_info = {"標題": title, "連結": href, "更新日期": update_date}

                # 添加到文章列表
                articles.append(article_info)

            except Exception as e:
                print_error(f"處理文章連結時出錯: {e}")
                continue

        # 輸出結果
        if articles:
            print_banner(f"成功獲取 {len(articles)} 篇文章")

            # 保存為CSV
            df = pd.DataFrame(articles)
            csv_file = os.path.join(output_dir, "simple_articles.csv")
            df.to_csv(csv_file, index=False, encoding="utf-8-sig")
            print_success(f"已將文章資訊保存至: {csv_file}")

            # 使用 tabulate 美化表格輸出
            print("\n" + Fore.CYAN + Style.BRIGHT + "文章列表:" + Style.RESET_ALL)

            # 準備表格數據
            table_data = []
            for i, article in enumerate(articles):
                title = article.get("標題", "無標題")
                if len(title) > 50:
                    title = title[:47] + "..."

                table_data.append(
                    [
                        i + 1,
                        title,
                        article.get("更新日期", "未知日期"),
                        (
                            article.get("連結", "無連結")[:60] + "..."
                            if article.get("連結") and len(article.get("連結")) > 60
                            else article.get("連結", "無連結")
                        ),
                    ]
                )

            # 印出美化的表格
            print(
                tabulate(
                    table_data,
                    headers=["編號", "標題", "更新日期", "連結"],
                    tablefmt="grid",
                )
            )

            print(
                f"\n{Fore.GREEN}爬蟲執行完成，共獲取 {len(articles)} 篇文章資訊{Style.RESET_ALL}"
            )
        else:
            print_error("未找到任何文章資訊")

    except Exception as e:
        print_error(f"爬蟲過程中發生錯誤: {e}")
        import traceback

        print(Fore.RED + traceback.format_exc())

    finally:
        # 關閉瀏覽器
        try:
            driver.quit()
            print_info("瀏覽器已關閉")
        except:
            pass


if __name__ == "__main__":
    simple_crawler()
