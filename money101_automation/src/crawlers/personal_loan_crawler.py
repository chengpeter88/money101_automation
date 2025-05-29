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
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import os
from datetime import datetime
from .base_crawler import BaseCrawler

class PersonalLoanCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.output_dir = "output/personal_loans"
        os.makedirs(self.output_dir, exist_ok=True)

    def crawl_loans(self):
        print("正在前往 roo.cash/personal-loan...")
        self.driver.get("https://roo.cash/personal-loan")
        time.sleep(3)

        self.scroll_to_bottom()

        loan_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-card']")
        print(f"找到 {len(loan_elements)} 個貸款產品")

        loans_data = []
        for idx, loan in enumerate(loan_elements):
            try:
                print(f"\n正在處理第 {idx+1} 個貸款產品...")
                self.scroll_to_element(loan)
                time.sleep(0.5)

                loan_data = self.extract_loan_data(loan)
                loans_data.append(loan_data)
                print(f"第 {idx+1} 個貸款產品處理完成")

            except Exception as e:
                print(f"處理第 {idx+1} 個貸款產品時發生錯誤: {str(e)}")

        return loans_data

    def extract_loan_data(self, loan):
        loan_name = self.get_loan_name(loan)
        loan_info = self.get_loan_info(loan)
        highlights = self.get_highlights(loan)
        activity_info = self.get_activity_info(loan)
        tags_text = self.get_tags(loan)
        banner_info = self.get_banner_info(loan)
        cta_buttons = self.get_cta_buttons(loan)
        detail_link = self.get_detail_link(loan)

        loan_data = {
            "貸款名稱": loan_name,
            "貸款資訊": loan_info,
            "特色亮點": highlights,
            "活動資訊": activity_info,
            "分類標籤": tags_text,
            "廣告橫幅": banner_info,
            "操作按鈕": cta_buttons,
            "詳細頁連結": detail_link,
        }

        return loan_data

    def get_loan_name(self, loan):
        try:
            title_element = loan.find_element(By.CSS_SELECTOR, "h3[data-testid='product-title']")
            return title_element.text
        except NoSuchElementException:
            return "未知貸款產品"

    def get_loan_info(self, loan):
        loan_info = {}
        info_blocks = loan.find_elements(By.CSS_SELECTOR, "div[data-testid='product-content'] > div.border-l")
        for block in info_blocks:
            label = block.find_element(By.CSS_SELECTOR, "p.text-xs").text
            value = block.find_element(By.CSS_SELECTOR, "p.font-bold").text
            loan_info[label] = value
        return loan_info

    def get_highlights(self, loan):
        highlights = []
        highlight_elements = loan.find_elements(By.CSS_SELECTOR, "div[data-testid^='product-highlight-']")
        for highlight in highlight_elements:
            highlights.append(highlight.text.strip())
        return highlights

    def get_activity_info(self, loan):
        activity_text = ""
        countdown = ""
        activity_elements = loan.find_elements(By.CSS_SELECTOR, "div[data-testid='product-activity']")
        if activity_elements:
            activity_text = activity_elements[0].text.strip()
        return {"活動名稱": activity_text, "活動倒數": countdown}

    def get_tags(self, loan):
        tags_text = []
        taxonomy_element = loan.find_element(By.CSS_SELECTOR, "div[data-testid='product-taxonomy']")
        tag_elements = taxonomy_element.find_elements(By.CSS_SELECTOR, "div.whitespace-nowrap.rounded-full")
        tags_text = [tag.text for tag in tag_elements if tag.text.strip()]
        return tags_text

    def get_banner_info(self, loan):
        banner_elements = loan.find_elements(By.CSS_SELECTOR, "div[data-testid='product-banner'] img")
        if banner_elements:
            return {"url": banner_elements[0].get_attribute("src"), "alt": banner_elements[0].get_attribute("alt")}
        return {"url": "", "alt": ""}

    def get_cta_buttons(self, loan):
        cta_buttons = {}
        apply_elements = loan.find_elements(By.CSS_SELECTOR, "div[data-testid='product-apply-cta']")
        if apply_elements:
            cta_buttons["申請按鈕"] = apply_elements[0].text
        return cta_buttons

    def get_detail_link(self, loan):
        link_elements = loan.find_elements(By.CSS_SELECTOR, "a[data-testid='product-detail']")
        if link_elements:
            return link_elements[0].get_attribute("href")
        return ""