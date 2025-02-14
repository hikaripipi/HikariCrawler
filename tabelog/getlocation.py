import pandas as pd
import googlemaps
import time
from dotenv import load_dotenv
import os


def get_coordinates(gmaps_client, address):
    """住所から座標を取得する関数"""
    try:
        # Geocoding APIを使用して住所から座標を取得
        result = gmaps_client.geocode(address)
        if result:
            location = result[0]["geometry"]["location"]
            return location["lat"], location["lng"]
        return None, None
    except Exception as e:
        print(f"Error getting coordinates for {address}: {e}")
        return None, None


def main():
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # 環境変数からAPIキーを取得
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        print("Error: API_KEY not found in .env file")
        return

    # Google Maps クライアントを初期化
    gmaps = googlemaps.Client(key=API_KEY)

    # CSVファイルを読み込む
    df = pd.read_csv("shinjuku_restaurants.csv")

    # 新しい列を作成して座標を格納
    df["latitude"] = None
    df["longitude"] = None

    # 各行の住所から座標を抽出
    for index, row in df.iterrows():
        lat, lng = get_coordinates(gmaps, row["住所"])
        df.at[index, "latitude"] = lat
        df.at[index, "longitude"] = lng

        # 座標を表示
        print(f"店舗名: {row['店舗名']}")
        print(f"住所: {row['住所']}")
        print(f"座標: 緯度={lat}, 経度={lng}")
        print("-" * 50)  # 区切り線

        # API制限を考慮して少し待機
        time.sleep(0.5)

    # 結果を新しいCSVファイルに保存
    # 結果を新しいCSVファイルに保存
    output_file = "shinjuku_restaurants_with_coordinates.csv"  # ここも修正！
    df.to_csv(output_file, index=False)
    print(f"\nCompleted! Coordinates have been saved to {output_file}")


if __name__ == "__main__":
    main()
