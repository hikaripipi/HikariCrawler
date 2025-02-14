import sys
from route_optimizer import RouteOptimizer
import urllib.parse
from getlocation import get_coordinates
import googlemaps
from dotenv import load_dotenv
import os


def format_route_data(route, total_distance, optimizer):
    """RouteOptimizerの結果をVisualizerの形式に変換"""
    route_data = []

    # 最初の地点（表参道駅）をスキップして店舗データのみを処理
    for i in range(1, len(route)):
        store = route[i]
        # 前の地点からの距離を計算
        if i > 0:
            prev_point = route[i - 1]
            distance = int(
                optimizer.calculate_distance(
                    prev_point["latitude"],
                    prev_point["longitude"],
                    store["latitude"],
                    store["longitude"],
                )
            )
        else:
            distance = 0

        route_data.append(
            {
                "店舗名": store["店舗名"],
                "評価点数": store["評価点数"],
                "距離": distance,
                "latitude": store["latitude"],
                "longitude": store["longitude"],
            }
        )

    return route_data


def generate_google_maps_url(route):
    """Google MapsのURLを生成"""
    base_url = "https://www.google.com/maps/dir/"
    locations = [route[0]["name"]] + [loc["店舗名"] for loc in route[1:]]
    encoded_locations = [urllib.parse.quote(loc) for loc in locations]
    return base_url + "/".join(encoded_locations)


def main(csv_file_path, start_station_name):
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # 環境変数からAPIキーを取得
    API_KEY = os.getenv("API_KEY")

    if not API_KEY:
        print("Error: API_KEY not found in .env file")
        return

    # Google Maps クライアントを初期化
    gmaps = googlemaps.Client(key=API_KEY)

    # 開始地点の座標を取得
    start_lat, start_lng = get_coordinates(gmaps, start_station_name)
    if start_lat is None or start_lng is None:
        print(f"Error: Could not find coordinates for {start_station_name}")
        return

    # 1. ルートの最適化
    print("ルートを計算中...")
    start_point = {
        "name": start_station_name,
        "latitude": start_lat,
        "longitude": start_lng,
    }
    optimizer = RouteOptimizer(csv_file_path, start_point=start_point)
    route, total_distance = optimizer.find_optimal_route()

    # 最適化されたルートを表示
    optimizer.print_route(route, total_distance)

    # Google MapsのURLを生成して表示
    google_maps_url = generate_google_maps_url(route)
    print(f"\nGoogle Mapsで経路を確認: {google_maps_url}")

    print(f"\n処理が完了しました！")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Error: CSVファイルのパスと開始地点の駅名を指定してください。")
    else:
        csv_file_path = sys.argv[1]
        start_station_name = sys.argv[2]
        main(csv_file_path, start_station_name)
