from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from .base_crawler import BaseCrawler

class CreditCardCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        
        # 初始化 WebDriver
        if not self.initialize_driver():
            raise Exception("WebDriver 初始化失敗")
        
        # 設定 URL
        self.url = "https://roo.cash/creditcard"
        
        # 設定輸出目錄
        self.output_dir = os.path.join(self.base_output_dir, "credit_cards")
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_credit_cards(self):
        """抓取信用卡資訊 - 優化版本"""
        print("正在前往信用卡頁面...")
        try:
            self.driver.get(self.url)
            # 使用 WebDriverWait 替代固定等待
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card-large, div[data-testid='product-card']"))
            )
        except Exception as e:
            print(f"導向頁面時出錯: {e}")
            return []

        print("開始抓取信用卡資訊...")
        
        # 滾動到頁面底部確保所有卡片都載入
        self.scroll_to_bottom()
        
        # 獲取所有卡片
        card_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.product-card-large")
        if not card_elements:
            card_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-card']")
        
        print(f"找到 {len(card_elements)} 張信用卡")
        
        if len(card_elements) == 0:
            print("警告：未找到任何信用卡元素")
            return []

        cards_data = []
        
        # 批次處理，每次處理5張卡片
        batch_size = 5
        for i in range(0, len(card_elements), batch_size):
            batch = card_elements[i:i+batch_size]
            print(f"處理第 {i+1}-{min(i+batch_size, len(card_elements))} 張信用卡...")
            
            for idx, card in enumerate(batch, start=i):
                try:
                    # 只在必要時滾動
                    if idx % 3 == 0:  # 每3張卡片才滾動一次
                        self.scroll_to_element(card)
                        time.sleep(0.1)
                    
                    # 使用優化的資料提取方法
                    card_data = self.extract_card_data(card, idx + 1)
                    cards_data.append(card_data)
                    
                except Exception as e:
                    print(f"處理第 {idx+1} 張信用卡時發生錯誤: {str(e)}")
                    continue

        return cards_data

    def extract_card_data(self, card, idx):
        """提取單張卡片資料 - 優化版本"""
        # 使用更簡潔的選擇器策略
        selectors = {
            'card_name': ["h3[data-testid='product-title']", "h3"],
            'tags': ["div[data-testid='product-taxonomy'] div", ".whitespace-nowrap.rounded-full"],
            'activity': ["div[data-testid='product-activity']", ".flex.flex-col.items-start.justify-between"],
            'gifts': [".flex.min-w-\\[86px\\] p.c1-regular", ".scrollbar-hidden img"],
            'button': ["div[data-testid='product-cta']", ".bg-NRooOrange-120"],
            'link': ["a[data-testid='product-detail']", "a[href*='credit-card/info']"]
        }
        
        # 1. 卡片名稱
        card_name = self.safe_find_text(card, selectors['card_name'], f"未知信用卡 {idx}")
        
        # 2. 分類標籤
        tags_text = self.safe_find_multiple_text(card, selectors['tags'])
        
        # 3. 首刷活動
        activity_text = self.safe_find_text(card, selectors['activity'], "")
        countdown = self.extract_countdown(card)
        
        # 4. 首刷禮
        gift_items = self.extract_gifts(card)
        
        # 5. 卡片回饋
        rewards = self.extract_rewards_simple(card)
        
        # 6. 按鈕文字
        apply_button = self.safe_find_text(card, selectors['button'], "立即申請")
        
        # 7. 詳細頁連結
        detail_link = self.safe_find_attribute(card, selectors['link'], "href", "")
        
        return {
            "卡片名稱": card_name,
            "分類標籤": tags_text,
            "首刷活動": {"活動名稱": activity_text, "活動倒數": countdown},
            "首刷禮": gift_items,
            "卡片回饋": rewards,
            "立即申請按鈕": apply_button,
            "詳細頁連結": detail_link,
        }

    def safe_find_text(self, element, selectors, default=""):
        """安全地尋找文字內容"""
        for selector in selectors:
            try:
                found = element.find_element(By.CSS_SELECTOR, selector)
                text = found.text.strip()
                if text:
                    return text
            except:
                continue
        return default

    def safe_find_multiple_text(self, element, selectors):
        """安全地尋找多個文字內容"""
        for selector in selectors:
            try:
                elements = element.find_elements(By.CSS_SELECTOR, selector)
                texts = [elem.text.strip() for elem in elements if elem.text.strip()]
                if texts:
                    return texts
            except:
                continue
        return []

    def safe_find_attribute(self, element, selectors, attribute, default=""):
        """安全地尋找屬性值"""
        for selector in selectors:
            try:
                found = element.find_element(By.CSS_SELECTOR, selector)
                attr_value = found.get_attribute(attribute)
                if attr_value:
                    return attr_value
            except:
                continue
        return default

    def extract_countdown(self, card):
        """提取倒數時間 - 簡化版"""
        try:
            countdown_elements = card.find_elements(By.CSS_SELECTOR, ".flex.items-center.gap-1 div.b1-bold")
            if len(countdown_elements) >= 4:
                countdown_parts = [elem.text for elem in countdown_elements[:4]]
                return f"{countdown_parts[0]} 天 {countdown_parts[1]} 時 {countdown_parts[2]} 分 {countdown_parts[3]} 秒"
        except:
            pass
        return ""

    def extract_gifts(self, card):
        """提取首刷禮 - 優化版"""
        gift_items = []
        
        # 嘗試文字提取
        try:
            gift_elements = card.find_elements(By.CSS_SELECTOR, ".flex.min-w-\\[86px\\] p.c1-regular")
            if not gift_elements:
                gift_elements = card.find_elements(By.CSS_SELECTOR, ".scrollbar-hidden .flex.min-w-\\[86px\\] p")
            
            gift_items = [gift.text.strip() for gift in gift_elements if gift.text.strip()]
        except:
            pass
        
        # 如果找不到文字，嘗試圖片alt屬性
        if not gift_items:
            try:
                gift_imgs = card.find_elements(By.CSS_SELECTOR, ".scrollbar-hidden img")
                gift_items = [img.get_attribute("alt") for img in gift_imgs if img.get_attribute("alt")]
            except:
                pass
        
        return gift_items

    def extract_rewards_simple(self, card):
        """簡化的回饋提取方法"""
        rewards = {}
        try:
            reward_elements = card.find_elements(By.CSS_SELECTOR, ".max-w-60.flex-1")
            for reward in reward_elements[:3]:  # 限制只處理前3個
                try:
                    # 嘗試標準結構
                    category = reward.find_element(By.CSS_SELECTOR, "p.c1-regular").text.strip()
                    value = reward.find_element(By.CSS_SELECTOR, "p.b1-bold").text.strip()
                    if category and value:
                        rewards[category] = value
                except:
                    # 備選方案：解析整個文字
                    try:
                        text = reward.text.strip()
                        if ":" in text or "：" in text:
                            key, value = text.replace("：", ":").split(":", 1)
                            rewards[key.strip()] = value.strip()
                    except:
                        continue
        except:
            pass
        return rewards

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

