from route_optimizer import RouteOptimizer
import urllib.parse


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


def main():
    # 1. ルートの最適化
    print("ルートを計算中...")
    optimizer = RouteOptimizer("harajuku_restaurants_with_coordinates.csv")
    route, total_distance = optimizer.find_optimal_route()

    # 最適化されたルートを表示
    optimizer.print_route(route, total_distance)

    # Google MapsのURLを生成して表示
    google_maps_url = generate_google_maps_url(route)
    print(f"\nGoogle Mapsで経路を確認: {google_maps_url}")

    print(f"\n処理が完了しました！")


if __name__ == "__main__":
    main()
