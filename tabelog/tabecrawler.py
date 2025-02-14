import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse


def scrape_tabelog(url, limit=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }

    session = requests.Session()
    restaurants = []
    seen_urls = set()
    page = 1

    while len(restaurants) < limit:
        try:
            page_url = f"{url}{page}/" if page > 1 else url
            print(f"\nFetching page {page}...")

            response = session.get(page_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            restaurant_list = soup.select("div.list-rst")

            if not restaurant_list:
                print("No more restaurants found.")
                break

            print(f"Found {len(restaurant_list)} restaurants on page {page}")

            for restaurant in restaurant_list:
                try:
                    # 基本情報の取得
                    url_elem = restaurant.select_one("a.list-rst__rst-name-target")
                    if not url_elem or "href" not in url_elem.attrs:
                        continue

                    website = url_elem["href"]
                    if website in seen_urls:
                        continue
                    seen_urls.add(website)

                    name = url_elem.text.strip()
                    if not name:
                        continue

                    print(f"\nProcessing restaurant {len(restaurants) + 1}:")
                    print(f"Name: {name}")
                    print(f"Website: {website}")

                    # 評価点数の取得
                    rating = ""
                    rating_elem = restaurant.select_one("span.list-rst__rating-val")
                    if rating_elem:
                        rating = rating_elem.text.strip()
                        print(f"Rating: {rating}")

                    # 詳細ページから情報を取得
                    try:
                        detail_response = session.get(website, headers=headers)
                        detail_soup = BeautifulSoup(detail_response.text, "lxml")

                        # 住所の取得
                        address = ""
                        gmap_url = ""
                        address_elem = detail_soup.select_one(
                            "p.rstinfo-table__address"
                        )
                        if address_elem:
                            address = address_elem.text.strip()
                            gmap_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
                            print(f"Address: {address}")

                        # 最寄駅の取得
                        station = ""
                        station_elem = detail_soup.select_one(
                            "span.linktree__parent-target-text"
                        )
                        if station_elem:
                            station = station_elem.text.strip()
                            print(f"Station: {station}")

                        # ジャンルの取得
                        genre = ""
                        genre_elem = detail_soup.select(
                            "span.linktree__parent-target-text"
                        )
                        if len(genre_elem) > 1:
                            genre = genre_elem[1].text.strip()
                            print(f"Genre: {genre}")

                        time.sleep(2)  # 詳細ページへのアクセス後の待機

                    except Exception as e:
                        print(f"Error fetching detail page: {e}")

                    restaurants.append(
                        {
                            "店舗名": name,
                            "エリア": "原宿・表参道・青山",
                            "最寄駅": station,
                            "ジャンル": genre,
                            "食べログURL": website,
                            "住所": address,
                            "Google Maps": gmap_url,
                            "評価点数": rating,
                        }
                    )

                    if len(restaurants) >= limit:
                        return restaurants

                except Exception as e:
                    print(f"Error processing restaurant: {e}")
                    continue

                time.sleep(1)  # 各店舗の処理後の待機

            page += 1
            time.sleep(2)  # ページ遷移前の待機

        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            break

    return restaurants if restaurants else None


def main():
    url = "https://tabelog.com/tokyo/A1306/rstLst/cond58-00-00/"  # 原宿・表参道・青山エリアのURL
    results = scrape_tabelog(url, limit=100)

    if results:
        df = pd.DataFrame(results)
        df.to_csv("harajuku_restaurants.csv", index=False, encoding="utf-8-sig")
        print("\nデータの取得が完了しました！")
        print(f"取得件数: {len(results)}件")
        print("\n取得したデータ:")
        print(df.to_string())
    else:
        print("\nデータの取得に失敗しました。")


if __name__ == "__main__":
    main()
