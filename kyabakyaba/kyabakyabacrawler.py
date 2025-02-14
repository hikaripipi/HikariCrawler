import requests
from bs4 import BeautifulSoup
import time
import json


def scrape_cabacaba():
    print("🌸 C-chan: スクレイピングを開始します！")

    # メインページのURL
    url = "https://www.caba2.net/tokyo/_list"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        stores_data = []
        count = 0

        # 店舗情報を含むdiv要素を取得
        club_tops = soup.select("div.club-top")
        store_infos = soup.select("div.list-info")

        # 最初の5件の店舗情報を取得
        for club_top, store_info in zip(club_tops[:5], store_infos[:5]):
            store_data = {
                "name": "",
                "area": "",
                "business_hours": "",
                "holiday": "",
                "budget": "",
                "phone": "",
                "address": "",
            }

            # 店舗名とエリアを取得
            text_wrapper = club_top.select_one("div.text-wrapper")
            if text_wrapper:
                # 店舗名を取得
                blog_title = text_wrapper.select_one("h2.blog-title a.link")
                if blog_title:
                    store_data["name"] = blog_title.text.strip()

                # エリアを取得
                area_text = text_wrapper.select_one("p.comment")
                if area_text:
                    # "のキャバクラ"を除去してエリアのみを取得
                    area = area_text.text.replace("のキャバクラ", "").strip()
                    store_data["area"] = area

            # その他の情報を取得
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
                        # 税込情報も含めて取得
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

            stores_data.append(store_data)
            count += 1

            print(f"\n✨ 店舗情報 {count}:")
            print(f"📍 店舗名: {store_data['name']}")
            print(f"🏢 エリア: {store_data['area']}")
            print(f"🕒 営業時間: {store_data['business_hours']}")
            print(f"📅 定休日: {store_data['holiday']}")
            print(f"💰 予算: {store_data['budget']}")
            print(f"📱 電話: {store_data['phone']}")
            print(f"🏠 住所: {store_data['address']}")

        # 結果をJSONファイルに保存
        output_file = "cabacaba_stores.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(stores_data, f, ensure_ascii=False, indent=2)

        print(f"\n🎉 スクレイピング完了！ {count}件の店舗情報を取得しました")
        print(f"📝 結果は {output_file} に保存されました")

    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")


if __name__ == "__main__":
    scrape_cabacaba()
