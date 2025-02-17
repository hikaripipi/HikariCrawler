import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus  # URLエンコード用


def scrape_cabacaba():
    print("🌸 C-chan: スクレイピングを開始します！")

    url = "https://www.caba2.net/tokyo/_list"
    options = Options()
    options.add_argument("--headless")  # ヘッドレスモードで実行
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 正しいChromeDriverのパスを指定
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # 10件取得するために「もっと見る」ボタンをクリック
        while True:
            try:
                load_more_button = wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "load-more__btn"))
                )
                load_more_button.click()
                time.sleep(2)  # ページがロードされるのを待つ
            except Exception as e:
                print("❌ ボタンが見つからないか、クリックできませんでした。")
                break

            # 10件以上表示されたらループを抜ける
            soup = BeautifulSoup(driver.page_source, "html.parser")
            if len(soup.select("div.club-top")) >= 10:
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        stores_data = []
        seen_names = set()
        count = 0

        club_tops = soup.select("div.club-top")
        store_infos = soup.select("div.list-info")

        for club_top, store_info in zip(club_tops, store_infos):
            if count >= 10:  # 10件でループを終了
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
                "website": "",  # ウェブサイトURLを追加
                "gmap_url": "",  # GoogleマップURLを追加
            }

            text_wrapper = club_top.select_one("div.text-wrapper")
            if text_wrapper:
                blog_title = text_wrapper.select_one("h2.blog-title a.link")
                if blog_title:
                    full_name = blog_title.text.strip()
                    if full_name in seen_names:
                        continue
                    seen_names.add(full_name)

                    # 店舗名と読み仮名を分ける
                    if " - " in full_name:
                        store_data["name"], store_data["kana"] = full_name.split(" - ")

                    # ウェブサイトURLを取得
                    store_data["website"] = blog_title["href"]

                area_text = text_wrapper.select_one("p.comment")
                if area_text:
                    full_area = area_text.text.strip()
                    # エリアと店舗種類を分ける
                    if "の" in full_area:
                        store_data["area"], store_data["type"] = full_area.split("の")

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
                        # 店舗名、エリア、番地を使ってGoogleマップURLを生成
                        search_query = f"{store_data['name']} {store_data['area']} {value_text.split(' ')[0]}"
                        encoded_query = quote_plus(search_query)
                        store_data["gmap_url"] = (
                            f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
                        )

            stores_data.append(store_data)
            count += 1

            print(f"\n✨ 店舗情報 {count}:")
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
                "website",  # ウェブサイトURLを追加
                "gmap_url",  # GoogleマップURLを追加
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for store in stores_data:
                writer.writerow(store)

        print(f"\n🎉 スクレイピング完了！ {count}件の店舗情報を取得しました")
        print(f"📝 結果は {output_file} に保存されました")

    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")

    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_cabacaba()
