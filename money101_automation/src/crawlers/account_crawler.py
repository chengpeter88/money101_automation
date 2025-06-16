from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from .base_crawler import BaseCrawler

class AccountCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        
        # 初始化 WebDriver
        if not self.initialize_driver():
            raise Exception("WebDriver 初始化失敗")
        
        # 設定 URL
        self.url = "https://roo.cash/securities/account-recommendation"
        
        # 設定輸出目錄
        self.output_dir = os.path.join(self.base_output_dir, "securities_accounts")
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_accounts(self):
        """抓取證券開戶推薦資訊 - 優化版本"""
        print("正在前往證券開戶推薦頁面...")
        try:
            self.driver.get(self.url)
            # 使用 WebDriverWait 替代固定等待
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='product-card'], div.product-card-large"))
            )
        except Exception as e:
            print(f"導向頁面時出錯: {e}")
            return []

        print("開始抓取證券開戶資訊...")
        
        # 滾動到頁面底部確保所有產品都載入
        self.scroll_to_bottom()

        # 獲取所有證券開戶產品
        account_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-card']")
        if not account_elements:
            account_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.product-card-large")
        
        print(f"找到 {len(account_elements)} 個證券開戶產品")
        
        if len(account_elements) == 0:
            print("警告：未找到任何證券開戶產品")
            return []

        accounts_data = []
        
        # 批次處理，每次處理5個產品
        batch_size = 5
        for i in range(0, len(account_elements), batch_size):
            batch = account_elements[i:i+batch_size]
            print(f"處理第 {i+1}-{min(i+batch_size, len(account_elements))} 個證券開戶產品...")
            
            for idx, account in enumerate(batch, start=i):
                try:
                    # 只在必要時滾動
                    if idx % 3 == 0:  # 每3個產品才滾動一次
                        self.scroll_to_element(account)
                        time.sleep(0.1)

                    # 使用優化的資料提取方法
                    account_data = self.extract_account_data(account, idx + 1)
                    accounts_data.append(account_data)
                    
                except Exception as e:
                    print(f"處理第 {idx+1} 個證券開戶產品時發生錯誤: {str(e)}")
                    continue

        return accounts_data

    def extract_account_data(self, account, idx):
        """提取單個證券開戶產品資料 - 優化版本"""
        # 使用更簡潔的選擇器策略
        selectors = {
            'account_name': ["h3[data-testid='product-title']", "h3", ".font-bold"],
            'broker_info': ["div[data-testid='product-content'] > div.border-l", ".border-l"],
            'highlights': ["div[data-testid^='product-highlight-']", ".highlight"],
            'activity': ["div[data-testid='product-activity']", ".activity-info"],
            'tags': ["div[data-testid='product-taxonomy'] div.whitespace-nowrap.rounded-full", ".tag"],
            'banner': ["div[data-testid='product-banner'] img", ".banner img"],
            'apply_button': ["div[data-testid='product-apply-cta']", ".apply-btn"],
            'detail_link': ["a[data-testid='product-detail']", "a[href*='securities']"],
            'fees': [".fee-info", ".commission-info"],
            'promotions': [".promotion", ".offer"]
        }
        
        # 1. 券商/開戶名稱
        account_name = self.safe_find_text(account, selectors['account_name'], f"未知證券開戶產品 {idx}")
        
        # 2. 券商資訊
        broker_info = self.extract_broker_info(account, selectors['broker_info'])
        
        # 3. 特色亮點
        highlights = self.safe_find_multiple_text(account, selectors['highlights'])
        
        # 4. 活動資訊
        activity_text = self.safe_find_text(account, selectors['activity'], "")
        
        # 5. 分類標籤
        tags_text = self.safe_find_multiple_text(account, selectors['tags'])
        
        # 6. 手續費資訊
        fee_info = self.extract_fee_info(account)
        
        # 7. 優惠活動
        promotions = self.extract_promotions(account)
        
        # 8. 廣告橫幅
        banner_info = self.extract_banner_info(account, selectors['banner'])
        
        # 9. 操作按鈕
        apply_button = self.safe_find_text(account, selectors['apply_button'], "立即開戶")
        
        # 10. 詳細頁連結
        detail_link = self.safe_find_attribute(account, selectors['detail_link'], "href", "")

        return {
            "券商名稱": account_name,
            "券商資訊": broker_info,
            "特色亮點": highlights,
            "手續費資訊": fee_info,
            "優惠活動": promotions,
            "活動資訊": {"活動名稱": activity_text, "活動倒數": ""},
            "分類標籤": tags_text,
            "廣告橫幅": banner_info,
            "操作按鈕": {"開戶按鈕": apply_button},
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

    def extract_broker_info(self, account, selectors):
        """提取券商基本資訊 - 優化版"""
        broker_info = {}
        try:
            info_blocks = account.find_elements(By.CSS_SELECTOR, selectors[0])
            for block in info_blocks[:6]:  # 限制處理前6個，避免過度處理
                try:
                    # 嘗試不同的標籤結構
                    label_selectors = ["p.text-xs", ".label", ".info-label"]
                    value_selectors = ["p.font-bold", ".value", ".info-value", "p.b1-bold"]
                    
                    label = ""
                    value = ""
                    
                    for label_sel in label_selectors:
                        try:
                            label_elem = block.find_element(By.CSS_SELECTOR, label_sel)
                            label = label_elem.text.strip()
                            if label:
                                break
                        except:
                            continue
                    
                    for value_sel in value_selectors:
                        try:
                            value_elem = block.find_element(By.CSS_SELECTOR, value_sel)
                            value = value_elem.text.strip()
                            if value:
                                break
                        except:
                            continue
                    
                    if label and value:
                        broker_info[label] = value
                except:
                    continue
        except:
            pass
        return broker_info

    def extract_fee_info(self, account):
        """提取手續費資訊"""
        fee_info = {}
        try:
            # 尋找手續費相關資訊
            fee_selectors = [
                ".fee", ".commission", ".cost",
                "[class*='fee']", "[class*='commission']",
                "div:contains('手續費')", "div:contains('折')",
                "p:contains('%')", "span:contains('折')"
            ]
            
            for selector in fee_selectors:
                try:
                    elements = account.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements[:3]:  # 限制處理數量
                        text = elem.text.strip()
                        if any(keyword in text for keyword in ['手續費', '折', '%', '優惠', '免費']):
                            # 提取關鍵資訊
                            if '手續費' in text:
                                fee_info['手續費'] = text
                            elif '折' in text:
                                fee_info['優惠折扣'] = text
                            elif '%' in text:
                                fee_info['費率'] = text
                except:
                    continue
        except:
            pass
        return fee_info

    def extract_promotions(self, account):
        """提取優惠活動資訊"""
        promotions = []
        try:
            promotion_selectors = [
                ".promotion", ".offer", ".deal",
                "[class*='promo']", "[class*='offer']",
                "div:contains('優惠')", "div:contains('活動')",
                "div:contains('限時')", "div:contains('贈')"
            ]
            
            for selector in promotion_selectors:
                try:
                    elements = account.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements[:5]:  # 限制處理數量
                        text = elem.text.strip()
                        if text and len(text) > 3:
                            if any(keyword in text for keyword in ['優惠', '活動', '贈', '送', '免費', '限時']):
                                if text not in promotions:  # 避免重複
                                    promotions.append(text)
                except:
                    continue
        except:
            pass
        return promotions

    def extract_banner_info(self, account, selectors):
        """提取廣告橫幅資訊 - 優化版"""
        try:
            for selector in selectors:
                banner_elements = account.find_elements(By.CSS_SELECTOR, selector)
                if banner_elements:
                    banner = banner_elements[0]
                    return {
                        "url": banner.get_attribute("src") or "",
                        "alt": banner.get_attribute("alt") or ""
                    }
        except:
            pass
        return {"url": "", "alt": ""}

    def flatten_data_for_excel(self, data):
        """將證券開戶多層結構數據轉為適合 Excel 的平坦結構"""
        records = []
        for account in data:
            record = {}
            record["券商名稱"] = account.get("券商名稱", "")
            
            # 券商資訊
            broker_info = account.get("券商資訊", {})
            record["券商資訊"] = ", ".join(f"{k}: {v}" for k, v in broker_info.items())
            
            # 特色亮點
            record["特色亮點"] = ", ".join(account.get("特色亮點", []))
            
            # 手續費資訊
            fee_info = account.get("手續費資訊", {})
            record["手續費資訊"] = ", ".join(f"{k}: {v}" for k, v in fee_info.items())
            
            # 優惠活動
            record["優惠活動"] = ", ".join(account.get("優惠活動", []))
            
            # 活動資訊
            activity = account.get("活動資訊", {})
            record["活動名稱"] = activity.get("活動名稱", "")
            record["活動倒數"] = activity.get("活動倒數", "")
            
            # 分類標籤
            record["分類標籤"] = ", ".join(account.get("分類標籤", []))
            
            # 廣告橫幅
            banner = account.get("廣告橫幅", {})
            record["廣告橫幅_URL"] = banner.get("url", "")
            record["廣告橫幅_ALT"] = banner.get("alt", "")
            
            # 操作按鈕
            buttons = account.get("操作按鈕", {})
            record["開戶按鈕"] = buttons.get("開戶按鈕", "立即開戶")
            
            # 詳細頁連結
            record["詳細頁連結"] = account.get("詳細頁連結", "")
            
            records.append(record)
        
        return records
