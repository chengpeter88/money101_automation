# %%

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# import sqlite3
import pandas as pd


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)



# 啟動瀏覽器
service = None
try:
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
except Exception:
    pass
    # driver = webdriver.Chrome()

# 進入目標頁面
url = "https://icard.ai/home/all_cards"
driver.get(url)
time.sleep(3)  # 等待網頁載入

scroll_step = 800  # 每次滑動的像素
SCROLL_PAUSE_TIME = 3  # 每次滑動後等待秒數
MAX_NOCHANGE = 10  # 連續幾次沒新資料就結束

nochange_count = 0
last_count = 0
last_position = 0

while nochange_count < MAX_NOCHANGE:
    # 慢慢往下滑動
    last_position += scroll_step
    driver.execute_script(f"window.scrollTo(0, {last_position});")
    time.sleep(SCROLL_PAUSE_TIME)
    # 取得目前卡片數量
    card_names = driver.find_elements(By.CSS_SELECTOR, "div.sc-fkouio-0.kMjtwV")
    now_count = len(card_names)
    if now_count == last_count:
        nochange_count += 1
    else:
        nochange_count = 0
    last_count = now_count

# 取得所有卡片外層區塊
card_blocks = driver.find_elements(
    By.CSS_SELECTOR, "div.sc-fkouio-0.jdQMAt"
)  # 這是每張卡片的外層 class，請依實際 class 名稱調整

data = []

for block in card_blocks:
    # 取得卡片名稱
    name_elem = block.find_element(By.CSS_SELECTOR, "div.sc-fkouio-0.kMjtwV")
    name = name_elem.text.strip()

    # 取得所有優惠說明
    info_elems = block.find_elements(
        By.CSS_SELECTOR, "div.sc-fkouio-0.sc-9y76ir-2.ewghcY.jcdfEI"
    )
    for info_elem in info_elems:
        info = info_elem.text.strip()
        data.append({"卡片名稱": name, "優惠說明": info})

# 關閉
driver.quit()

# 輸出成 xlsx
df = pd.DataFrame(data)
df.to_excel("icard_cards.xlsx", index=False)
print("已輸出為 icard_cards.xlsx")


# 關閉
# driver.quit()
# %%

# <div color="black" class="sc-fkouio-0 sc-9y76ir-2 ewghcY jcdfEI">新戶享玉山e point回饋最優2.5%，活動期間上限玉山e point回饋500點 + 玉山e point回饋最優3.5%，每月上限玉山e point回饋2000點 + 玉山e point回饋最優1%，無上限 + 新戶享核卡90天內於指定通路刷卡不限金額玉山e point回饋最優0.5%，活動期間上限玉山e point回饋500點</div>

# <div color="black" class="sc-fkouio-0 sc-9y76ir-2 ewghcY jcdfEI">玉山e point回饋最優3.5%，每月上限玉山e point回饋2000點 + 玉山e point回饋最優1%，無上限 + 新戶享核卡90天內於指定通路刷卡不限金額玉山e point回饋最優0.5%，活動期間上限玉山e point回饋500點</div>
