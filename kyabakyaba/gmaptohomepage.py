import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd


def get_official_website(gmap_url):
    """Google Maps URLから公式サイトのURLを取得する"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"🔍 アクセス中: {gmap_url}")
        driver.get(gmap_url)

        # ウェブサイトボタンが表示されるまで待機
        wait = WebDriverWait(driver, 10)
        website_button = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            )
        )

        official_url = website_button.get_attribute("href")
        print(f"✨ 公式サイト発見: {official_url}")
        return official_url

    except TimeoutException:
        print("⚠️ ウェブサイトボタンが見つかりませんでした")
        return None
    except NoSuchElementException:
        print("⚠️ 要素が見つかりませんでした")
        return None
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return None
    finally:
        driver.quit()


def process_csv_file(input_csv):
    """CSVファイルを処理して公式サイトURLを追加する"""
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(input_csv)

        if "gmap_url" not in df.columns:
            print("❌ CSVファイルにgmap_urlカラムがありません")
            return

        # 公式サイトカラムを追加
        df["official_website"] = None

        # 各行を処理
        for index, row in df.iterrows():
            print(f"\n🏢 処理中: {row['name']}")  # 'store_name' を 'name' に修正

            if pd.isna(row["gmap_url"]):
                print("⚠️ Google Maps URLが空です")
                continue

            official_url = get_official_website(row["gmap_url"])
            df.at[index, "official_website"] = official_url

            # APIレート制限を考慮して待機
            time.sleep(2)

        # 結果を新しいCSVファイルに保存
        output_file = input_csv.replace(".csv", "_with_websites.csv")
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n✅ 処理が完了しました！")
        print(f"📝 結果は {output_file} に保存されました")

    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")


def main():
    input_csv = "/Users/hikarimac/Documents/python/tabelog-crawler/kyabakyaba/cabacaba_stores.csv"  # 入力CSVファイル名
    process_csv_file(input_csv)


if __name__ == "__main__":
    main()
