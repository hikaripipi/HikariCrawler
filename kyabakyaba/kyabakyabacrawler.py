import time
import csv
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def calculate_pages_needed(total_stores):
    """必要なページ数を計算する"""
    return math.ceil(total_stores / 50)


def scrape_cabacaba(total_stores=51):  # デフォルトで51件を取得
    print(f"🌸 C-chan: {total_stores}件の店舗情報のスクレイピングを開始します！")

    # 既存のCSVファイルから店舗名を読み込む
    existing_names = set()
    csv_path = "/Users/hikarimac/Documents/python/crawler/kyabakyaba/first107/cabacaba_stores.csv"
    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_names = {row["name"] for row in reader}
        print(f"📚 既存の店舗数: {len(existing_names)}件")
    except FileNotFoundError:
        print("⚠️ 既存のCSVファイルが見つかりませんでした。新規作成します。")

    pages_needed = calculate_pages_needed(total_stores)
    print(f"📚 必要なページ数: {pages_needed}ページ")

    base_url = "https://www.caba2.net/tokyo/ginza/_list"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    stores_data = []
    seen_names = existing_names.copy()

    try:
        for page in range(1, pages_needed + 1):
            url = f"{base_url}?page={page}"
            print(f"\n📄 ページ {page} をスクレイピング中...")

            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "club-top"))
                )
            except TimeoutException:
                print(f"❌ ページ {page} の読み込みがタイムアウトしました")
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")
            club_tops = soup.select("div.club-top")
            store_infos = soup.select("div.list-info")

            for idx, (club_top, store_info) in enumerate(zip(club_tops, store_infos)):
                if len(stores_data) >= total_stores:
                    break

                store_data = {
                    "name": "",
                    "kana": "",
                    "area": "",
                    "type": "",
                    "business_hours": "",
                    "holiday": "",
                    "budget": "",
                    "phone": "",
                    "address": "",
                    "website": "",
                    "gmap_url": "",
                    "description": "",
                }

                # 店舗名と読み仮名の取得
                text_wrapper = club_top.select_one("div.text-wrapper")
                if text_wrapper:
                    blog_title = text_wrapper.select_one("h2.blog-title a.link")
                    if blog_title:
                        full_name = blog_title.text.strip()
                        store_name = (
                            full_name.split(" - ")[0]
                            if " - " in full_name
                            else full_name
                        )

                        # 既存のCSVファイルとの重複チェック
                        if store_name in existing_names:
                            print(f"⏭️ スキップ: {store_name} (既存データに存在します)")
                            continue

                        if " - " in full_name:
                            store_data["name"], store_data["kana"] = full_name.split(
                                " - "
                            )
                        else:
                            store_data["name"] = full_name
                        seen_names.add(store_data["name"])
                        store_data["website"] = blog_title["href"]

                    # 説明文の取得
                    description_container = soup.select_one(
                        f"#list-tab-content > div > div > div.infinite-scroll > div:nth-child({idx + 1}) > "
                        "div.club-content > div.club-right > div.club-tab-container.pc > "
                        "div.club-outer-wrapper > div > div > div > section.card > div.text-wrapper"
                    )

                    if description_container:
                        title_elem = description_container.select_one("h3 a")
                        description_elem = description_container.select_one(
                            "p.description"
                        )
                        if title_elem and description_elem:
                            title = title_elem.text.strip()
                            description = description_elem.text.strip()
                            store_data["description"] = f"{title}\n{description}"

                    # エリアと店舗種類の取得
                    area_text = text_wrapper.select_one("p.comment")
                    if area_text:
                        full_area = area_text.text.strip()
                        if "の" in full_area:
                            store_data["area"], store_data["type"] = full_area.split(
                                "の"
                            )

                # 店舗詳細情報の取得
                info_items = store_info.select("ul li")
                for item in info_items:
                    label = item.select_one("label.text")
                    value = item.select_one("span.show")

                    if label and value:
                        label_text = label.text.strip()
                        value_text = value.text.strip()

                        if "営業時間" in label_text:
                            store_data["business_hours"] = value_text
                        elif "店休日" in label_text:
                            store_data["holiday"] = value_text
                        elif "予算目安" in label_text:
                            tax_info = value.select_one("span.tax-service-fee")
                            if tax_info:
                                store_data["budget"] = (
                                    f"{value_text.replace(tax_info.text, '')} {tax_info.text.strip()}"
                                )
                            else:
                                store_data["budget"] = value_text
                        elif "電話番号" in label_text:
                            store_data["phone"] = value_text
                        elif "所在地" in label_text:
                            store_data["address"] = value_text
                            search_query = f"{store_data['name']} {store_data['area']} {value_text.split(' ')[0]}"
                            encoded_query = quote_plus(search_query)
                            store_data["gmap_url"] = (
                                f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
                            )

                if all(store_data[field] for field in ["name", "area", "address"]):
                    stores_data.append(store_data)
                    print(f"\n✨ 店舗情報 {len(stores_data)}:")
                    print(f"📍 店舗名: {store_data['name']}")
                    print(f"📖 読み仮名: {store_data['kana']}")
                    print(f"🏢 エリア: {store_data['area']}")
                    print(f"🏷️ 店舗種類: {store_data['type']}")
                    print(f"🕒 営業時間: {store_data['business_hours']}")
                    print(f"📅 定休日: {store_data['holiday']}")
                    print(f"💰 予算: {store_data['budget']}")
                    print(f"📱 電話: {store_data['phone']}")
                    print(f"🏠 住所: {store_data['address']}")
                    print(f"🔗 ウェブサイト: {store_data['website']}")
                    print(f"🗺️ Googleマップ: {store_data['gmap_url']}")
                    print(f"📝 説明文:\n{store_data['description']}")

        # CSVに保存
        output_file = "cabacaba_stores.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "name",
                "kana",
                "area",
                "type",
                "business_hours",
                "holiday",
                "budget",
                "phone",
                "address",
                "website",
                "gmap_url",
                "description",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for store in stores_data:
                writer.writerow(store)

        print(f"\n🎉 スクレイピング完了！ {len(stores_data)}件の店舗情報を取得しました")
        print(f"📝 結果は {output_file} に保存されました")

    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")

    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_cabacaba(200)  # 取得したい店舗数を指定
