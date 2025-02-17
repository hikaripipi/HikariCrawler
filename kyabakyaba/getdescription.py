from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time


def get_store_info():
    # Chromeのオプションを設定
    options = Options()
    options.add_argument("--headless")  # ヘッドレスモードで実行
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 対象のURLを開く
        url = "https://www.caba2.net/tokyo/_list"
        driver.get(url)
        time.sleep(3)  # ページがロードされるのを待つ

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 特定の店舗のタイトルと説明文を取得
        text_wrapper = soup.select_one(
            "#list-tab-content > div > div > div.infinite-scroll > div:nth-child(1) > div.club-content > div.club-right > div.club-tab-container.pc > div.club-outer-wrapper > div > div > div > section.card > div.text-wrapper"
        )

        if text_wrapper:
            title = text_wrapper.select_one("h3 a").text.strip()
            description = text_wrapper.select_one("p.description").text.strip()
            print("店舗タイトル:", title)
            print("店舗説明文:", description)
        else:
            print("店舗情報が見つかりませんでした。")

    finally:
        driver.quit()


get_store_info()
