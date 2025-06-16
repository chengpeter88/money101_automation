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

class PersonalLoanCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        
        # 初始化 WebDriver
        if not self.initialize_driver():
            raise Exception("WebDriver 初始化失敗")
            
        # 設定 URL
        self.url = "https://roo.cash/personal-loan"
        
        # 設定輸出目錄
        self.output_dir = os.path.join(self.base_output_dir, "personal_loans")
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_loans(self):
        """抓取個人貸款資訊 - 優化版本"""
        print("正在前往個人貸款頁面...")
        try:
            self.driver.get(self.url)
            # 使用 WebDriverWait 替代固定等待
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='product-card']"))
            )
        except Exception as e:
            print(f"導向頁面時出錯: {e}")
            return []

        print("開始抓取個人貸款資訊...")
        
        # 滾動到頁面底部確保所有產品都載入
        self.scroll_to_bottom()

        # 獲取所有貸款產品
        loan_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-card']")
        print(f"找到 {len(loan_elements)} 個貸款產品")
        
        if len(loan_elements) == 0:
            print("警告：未找到任何貸款產品")
            return []

        loans_data = []
        
        # 批次處理，每次處理10個產品
        batch_size = 10
        for i in range(0, len(loan_elements), batch_size):
            batch = loan_elements[i:i+batch_size]
            print(f"處理第 {i+1}-{min(i+batch_size, len(loan_elements))} 個貸款產品...")
            
            for idx, loan in enumerate(batch, start=i):
                try:
                    # 只在必要時滾動
                    if idx % 3 == 0:  # 每3個產品才滾動一次
                        self.scroll_to_element(loan)
                        time.sleep(0.1)

                    # 使用優化的資料提取方法
                    loan_data = self.extract_loan_data(loan, idx + 1)
                    loans_data.append(loan_data)
                    
                except Exception as e:
                    print(f"處理第 {idx+1} 個貸款產品時發生錯誤: {str(e)}")
                    continue

        return loans_data

    def extract_loan_data(self, loan, idx):
        """提取單個貸款產品資料 - 優化版本"""
        # 使用更簡潔的選擇器策略
        selectors = {
            'loan_name': ["h3[data-testid='product-title']", "h3"],
            'info_blocks': ["div[data-testid='product-content'] > div.border-l"],
            'highlights': ["div[data-testid^='product-highlight-']"],
            'activity': ["div[data-testid='product-activity']"],
            'tags': ["div[data-testid='product-taxonomy'] div.whitespace-nowrap.rounded-full"],
            'banner': ["div[data-testid='product-banner'] img"],
            'apply_button': ["div[data-testid='product-apply-cta']"],
            'detail_link': ["a[data-testid='product-detail']"]
        }
        
        # 1. 貸款名稱
        loan_name = self.safe_find_text(loan, selectors['loan_name'], f"未知貸款產品 {idx}")
        
        # 2. 貸款資訊
        loan_info = self.extract_loan_info(loan, selectors['info_blocks'])
        
        # 3. 特色亮點
        highlights = self.safe_find_multiple_text(loan, selectors['highlights'])
        
        # 4. 活動資訊
        activity_text = self.safe_find_text(loan, selectors['activity'], "")
        
        # 5. 分類標籤
        tags_text = self.safe_find_multiple_text(loan, selectors['tags'])
        
        # 6. 廣告橫幅
        banner_info = self.extract_banner_info(loan, selectors['banner'])
        
        # 7. 操作按鈕
        apply_button = self.safe_find_text(loan, selectors['apply_button'], "立即申請")
        
        # 8. 詳細頁連結
        detail_link = self.safe_find_attribute(loan, selectors['detail_link'], "href", "")

        return {
            "貸款名稱": loan_name,
            "貸款資訊": loan_info,
            "特色亮點": highlights,
            "活動資訊": {"活動名稱": activity_text, "活動倒數": ""},
            "分類標籤": tags_text,
            "廣告橫幅": banner_info,
            "操作按鈕": {"申請按鈕": apply_button},
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

    def extract_loan_info(self, loan, selectors):
        """提取貸款資訊 - 優化版"""
        loan_info = {}
        try:
            info_blocks = loan.find_elements(By.CSS_SELECTOR, selectors[0])
            for block in info_blocks[:5]:  # 限制處理前5個，避免過度處理
                try:
                    label_elem = block.find_element(By.CSS_SELECTOR, "p.text-xs")
                    value_elem = block.find_element(By.CSS_SELECTOR, "p.font-bold")
                    
                    label = label_elem.text.strip()
                    value = value_elem.text.strip()
                    
                    if label and value:
                        loan_info[label] = value
                except:
                    continue
        except:
            pass
        return loan_info

    def extract_banner_info(self, loan, selectors):
        """提取廣告橫幅資訊 - 優化版"""
        try:
            banner_elements = loan.find_elements(By.CSS_SELECTOR, selectors[0])
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
        """將個人貸款多層結構數據轉為適合 Excel 的平坦結構"""
        records = []
        for loan in data:
            record = {}
            record["貸款名稱"] = loan.get("貸款名稱", "")
            
            # 貸款資訊
            loan_info = loan.get("貸款資訊", {})
            record["貸款資訊"] = ", ".join(f"{k}: {v}" for k, v in loan_info.items())
            
            # 特色亮點
            record["特色亮點"] = ", ".join(loan.get("特色亮點", []))
            
            # 活動資訊
            activity = loan.get("活動資訊", {})
            record["活動名稱"] = activity.get("活動名稱", "")
            record["活動倒數"] = activity.get("活動倒數", "")
            
            # 分類標籤
            record["分類標籤"] = ", ".join(loan.get("分類標籤", []))
            
            # 廣告橫幅
            # banner = loan.get("廣告橫幅", {})
            # record["廣告橫幅_URL"] = banner.get("url", "")
            # record["廣告橫幅_ALT"] = banner.get("alt", "")
            
            # 操作按鈕
            buttons = loan.get("操作按鈕", {})
            record["申請按鈕"] = buttons.get("申請按鈕", "立即申請")
            
            # 詳細頁連結
            record["詳細頁連結"] = loan.get("詳細頁連結", "")
            
            records.append(record)
        
        return records