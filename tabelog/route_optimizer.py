import pandas as pd
import folium
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime


class RouteConfig:
    """ルート設定用のクラス"""

    MAX_STORE_DISTANCE = 500  # 店舗間の最大距離(m)
    MAX_TOTAL_DISTANCE = 2000  # 総移動距離の上限(m)
    MIN_RATING = 3.0  # 最低評価点数
    MAX_LOCATIONS = 20  # 最大店舗数
    WALKING_SPEED = 4.8  # 平均歩行速度(km/h)


class RouteOptimizer:
    def __init__(self, csv_file, start_point=None):
        # 表参道駅の座標をデフォルトの開始点とする
        self.start_point = start_point or {
            "name": "表参道駅",
            "latitude": 35.6654,
            "longitude": 139.7090,
        }

        # CSVファイルの読み込み
        self.df = pd.read_csv(csv_file)
        self.config = RouteConfig()

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """二点間の距離をメートルで計算（Haversine公式）"""
        R = 6371000  # 地球の半径（メートル）

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def find_optimal_route(self):
        """訪問順序を決定"""
        # 評価点数でフィルタリング
        filtered_df = self.df[self.df["評価点数"] >= self.config.MIN_RATING].copy()

        route = [self.start_point]
        remaining_locations = filtered_df.to_dict("records")
        total_distance = 0

        current_point = self.start_point

        while remaining_locations and len(route) < self.config.MAX_LOCATIONS + 1:
            # 現在地から指定距離以内の店舗を抽出
            valid_locations = []
            for loc in remaining_locations:
                distance = self.calculate_distance(
                    current_point["latitude"],
                    current_point["longitude"],
                    loc["latitude"],
                    loc["longitude"],
                )
                if distance <= self.config.MAX_STORE_DISTANCE:
                    valid_locations.append((loc, distance))

            if not valid_locations:
                break

            # 距離が近い順にソート（同じ距離帯の場合は評価点数考慮）
            # 距離を100mごとの帯に分けて、その中で評価点数を考慮
            valid_locations.sort(key=lambda x: (int(x[1] / 100), -x[0]["評価点数"]))
            next_location, distance = valid_locations[0]

            # 総距離チェック
            if total_distance + distance > self.config.MAX_TOTAL_DISTANCE:
                break

            route.append(next_location)
            total_distance += distance
            current_point = next_location
            remaining_locations.remove(next_location)

        return route, total_distance

    def calculate_walking_time(self, distance):
        """歩行時間を計算（分）"""
        hours = distance / 1000 / self.config.WALKING_SPEED
        return int(hours * 60)

    def create_map(self, route, total_distance):
        """地図の作成"""
        center_lat = sum(point["latitude"] for point in route) / len(route)
        center_lon = sum(point["longitude"] for point in route) / len(route)

        m = folium.Map(
            location=[center_lat, center_lon], zoom_start=16, tiles="OpenStreetMap"
        )

        # 経路を描画
        coordinates = []
        for i, point in enumerate(route):
            # マーカーの色（開始点は赤、それ以外は青）
            color = "red" if i == 0 else "blue"

            # ポップアップテキストの作成
            if i == 0:
                popup_text = f"開始地点: {point['name']}"
            else:
                distance = self.calculate_distance(
                    route[i - 1]["latitude"],
                    route[i - 1]["longitude"],
                    point["latitude"],
                    point["longitude"],
                )
                popup_text = f"{i}. {point['店舗名']}\n"
                popup_text += f"評価点数: {point['評価点数']}\n"
                popup_text += f"前地点からの距離: {int(distance)}m"

            # マーカーの追加
            folium.Marker(
                [point["latitude"], point["longitude"]],
                popup=popup_text,
                icon=folium.Icon(color=color),
            ).add_to(m)

            coordinates.append([point["latitude"], point["longitude"]])

        # 経路を線で接続
        folium.PolyLine(coordinates, weight=2, color="blue", opacity=0.8).add_to(m)

        # 現在時刻をファイル名に含める
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        map_file = f"optimal_route_{timestamp}.html"
        m.save(map_file)
        return map_file

    def print_route(self, route, total_distance):
        """経路の詳細を表示"""
        print("\n=== 推奨訪問順序 ===")
        for i, point in enumerate(route):
            if i == 0:
                print(f"{i + 1}. {point['name']} (開始地点)")
            else:
                distance = self.calculate_distance(
                    route[i - 1]["latitude"],
                    route[i - 1]["longitude"],
                    point["latitude"],
                    point["longitude"],
                )
                print(f"{i + 1}. {point['店舗名']}")
                print(f"   距離: 約{int(distance)}m")
                print(f"   評価点数: {point['評価点数']}")

        walking_time = self.calculate_walking_time(total_distance)
        print(f"\n総移動距離: 約{total_distance / 1000:.1f}km")
        print(f"予想所要時間: 約{walking_time}分（休憩時間を除く）")


def main():
    # RouteOptimizerのインスタンス作成
    optimizer = RouteOptimizer("harajuku_restaurants_with_coordinates.csv")

    # 最適な経路を計算
    route, total_distance = optimizer.find_optimal_route()

    # 結果の出力
    optimizer.print_route(route, total_distance)

    # 地図の作成
    map_file = optimizer.create_map(route, total_distance)
    print(f"\n地図を '{map_file}' に保存しました！")


if __name__ == "__main__":
    main()
