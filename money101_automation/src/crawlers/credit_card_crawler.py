from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import pandas as pd
from .base_crawler import BaseCrawler
import os

class CreditCardCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        
        # 初始化 WebDriver
        if not self.initialize_driver():
            raise Exception("WebDriver 初始化失敗")
        
        # 修正 URL (加入連字符)
        self.url = "https://roo.cash/creditcard"  # 從 creditcard 改為 credit-card
        
        # 設定輸出目錄
        self.output_dir = os.path.join(self.base_output_dir, "credit_cards")
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_credit_cards(self):
        """抓取信用卡資訊 - 採用單次載入策略，避免過度刷新頁面"""
        print("正在前往信用卡頁面...")
        try:
            self.driver.get(self.url)
            time.sleep(3)  # 等待頁面載入
        except Exception as e:
            print(f"導向頁面時出錯: {e}")
            return []

        print("開始抓取信用卡資訊...")
        
        # 滾動到頁面底部確保所有卡片都載入
        self.scroll_to_bottom()
        
        # 只獲取一次所有卡片，不進行分批刷新
        card_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.product-card-large")
        if not card_elements:
            # 嘗試其他可能的選擇器
            card_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-card']")
        
        print(f"找到 {len(card_elements)} 張信用卡")
        
        if len(card_elements) == 0:
            print("警告：未找到任何信用卡元素，請檢查選擇器或網站結構")
            return []

        cards_data = []
        for idx, card in enumerate(card_elements):
            try:
                print(f"正在處理第 {idx+1} 張信用卡...")
                
                # 滾動到當前卡片，確保它在視窗內
                self.scroll_to_element(card)
                time.sleep(0.5)  # 短暫等待確保元素完全可見
                
                # 使用安全的方法提取卡片資料
                try:
                    # 1. 卡片名稱
                    try:
                        card_name = card.find_element(By.CSS_SELECTOR, "h3[data-testid='product-title']").text
                    except NoSuchElementException:
                        # 嘗試替代選擇器
                        try:
                            card_name = card.find_element(By.CSS_SELECTOR, "h3").text
                        except:
                            card_name = f"未知信用卡 {idx+1}"

                    # 2. 分類標籤
                    tags_text = []
                    try:
                        tags = card.find_elements(By.CSS_SELECTOR, "div[data-testid='product-taxonomy'] div")
                        tags_text = [tag.text for tag in tags if tag.text.strip()]
                        if not tags_text:
                            # 備選方案：尋找所有圓形標籤
                            tags = card.find_elements(By.CSS_SELECTOR, ".whitespace-nowrap.rounded-full")
                            tags_text = [tag.text for tag in tags if tag.text.strip()]
                    except:
                        pass

                    # 3. 首刷活動
                    activity_text = ""
                    countdown = ""
                    try:
                        activity_element = card.find_element(By.CSS_SELECTOR, "div[data-testid='product-activity']")
                        activity_text = activity_element.text

                        # 獲取倒數時間
                        try:
                            countdown_elements = card.find_elements(By.CSS_SELECTOR, ".flex.items-center.gap-1 div.b1-bold")
                            if len(countdown_elements) >= 4:
                                countdown_days = countdown_elements[0].text
                                countdown_hours = countdown_elements[1].text
                                countdown_minutes = countdown_elements[2].text
                                countdown_seconds = countdown_elements[3].text
                                countdown = f"{countdown_days} 天 {countdown_hours} 時 {countdown_minutes} 分 {countdown_seconds} 秒"
                        except:
                            pass
                    except:
                        # 嘗試尋找可能的活動文字
                        try:
                            activity_containers = card.find_elements(By.CSS_SELECTOR, ".flex.flex-col.items-start.justify-between")
                            for container in activity_containers:
                                if container.text.strip():
                                    activity_text = container.text.strip()
                                    break
                        except:
                            pass

                    # 4. 首刷禮
                    gift_items = []
                    try:
                        # 嘗試多種選擇器來找到禮品項目
                        gift_elements = card.find_elements(By.CSS_SELECTOR, ".flex.min-w-\\[86px\\] p.c1-regular")
                        if not gift_elements:
                            gift_elements = card.find_elements(By.CSS_SELECTOR, ".scrollbar-hidden .flex.min-w-\\[86px\\] p")

                        gift_items = [gift.text for gift in gift_elements if gift.text.strip()]

                        # 如果還是找不到，嘗試從圖片的alt屬性獲取
                        if not gift_items:
                            gift_imgs = card.find_elements(By.CSS_SELECTOR, ".scrollbar-hidden img")
                            gift_items = [img.get_attribute("alt") for img in gift_imgs if img.get_attribute("alt")]
                    except:
                        pass

                    # 5. 卡片回饋
                    rewards = {}
                    try:
                        reward_elements = card.find_elements(By.CSS_SELECTOR, ".max-w-60.flex-1")
                        for reward in reward_elements:
                            try:
                                category = reward.find_element(By.CSS_SELECTOR, "p.c1-regular").text
                                value = reward.find_element(By.CSS_SELECTOR, "p.b1-bold").text
                                rewards[category] = value
                            except:
                                # 如果常規方法失敗，嘗試獲取所有文本
                                reward_text = reward.text
                                if ":" in reward_text or "：" in reward_text:
                                    try:
                                        key, value = reward_text.replace("：", ":").split(":", 1)
                                        rewards[key.strip()] = value.strip()
                                    except:
                                        pass
                    except:
                        pass

                    # 6. 操作按鈕
                    apply_button = "立即申請"  # 默認值
                    try:
                        button = card.find_element(By.CSS_SELECTOR, "div[data-testid='product-cta']")
                        apply_button = button.text
                    except NoSuchElementException:
                        # 嘗試其他可能的按鈕選擇器
                        try:
                            button = card.find_element(By.CSS_SELECTOR, ".bg-NRooOrange-120")
                            apply_button = button.text or "立即申請"
                        except:
                            try:
                                buttons = card.find_elements(By.CSS_SELECTOR, ".rounded-md.bg-NRooOrange-120, .whitespace-nowrap.rounded-md")
                                if buttons:
                                    apply_button = buttons[0].text or "立即申請"
                            except:
                                pass

                    # 7. 詳細頁連結
                    detail_link = ""
                    try:
                        link_element = card.find_element(By.CSS_SELECTOR, "a[data-testid='product-detail']")
                        detail_link = link_element.get_attribute("href")
                    except:
                        # 嘗試找到任何可能的連結
                        links = card.find_elements(By.CSS_SELECTOR, "a")
                        for link in links:
                            href = link.get_attribute("href")
                            if href and ("credit-card/info" in href or "creditcard/info" in href):
                                detail_link = href
                                break

                    # 整理資料
                    card_data = {
                        "卡片名稱": card_name,
                        "分類標籤": tags_text,
                        "首刷活動": {"活動名稱": activity_text, "活動倒數": countdown},
                        "首刷禮": gift_items,
                        "卡片回饋": rewards,
                        "立即申請按鈕": apply_button,
                        "詳細頁連結": detail_link,
                    }
                    
                    cards_data.append(card_data)
                    print(f"第 {idx+1} 張信用卡處理完成")
                    
                except StaleElementReferenceException:
                    print(f"第 {idx+1} 張信用卡元素已過期，嘗試跳過...")
                    # 不再嘗試更新頁面，直接跳過這張卡片
                    continue
                except Exception as e:
                    print(f"提取第 {idx+1} 張信用卡資料時出錯: {e}")
                    # 跳過這張卡片，繼續處理下一張
                    continue
                    
            except Exception as e:
                print(f"處理第 {idx+1} 張信用卡時發生錯誤: {str(e)}")
                # 即使有錯誤也繼續處理下一張卡片，不中斷流程

        return cards_data
    
    def create_default_card_data(self, idx):
        """創建默認卡片數據結構"""
        return {
            "卡片名稱": f"未知卡片 {idx+1}",
            "分類標籤": [],
            "首刷活動": {"活動名稱": "", "活動倒數": ""},
            "首刷禮": [],
            "卡片回饋": {},
            "立即申請按鈕": "立即申請",
            "詳細頁連結": "",
        }
    
    def flatten_data_for_excel(self, data):
        """將信用卡多層結構數據轉為適合 Excel 的平坦結構"""
        records = []
        for card in data:
            record = {}
            record["卡片名稱"] = card.get("卡片名稱", "")
            
            # 分類標籤
            record["分類標籤"] = ", ".join(card.get("分類標籤", []))
            
            # 首刷活動
            activity = card.get("首刷活動", {})
            record["活動名稱"] = activity.get("活動名稱", "")
            record["活動倒數"] = activity.get("活動倒數", "")
            
            # 首刷禮
            record["首刷禮"] = ", ".join(card.get("首刷禮", []))
            
            # 卡片回饋
            rewards = card.get("卡片回饋", {})
            record["卡片回饋"] = ", ".join(f"{k}: {v}" for k, v in rewards.items())
            
            # 其他資訊
            record["立即申請按鈕"] = card.get("立即申請按鈕", "立即申請")
            record["詳細頁連結"] = card.get("詳細頁連結", "")
            
            records.append(record)
        
        return records

