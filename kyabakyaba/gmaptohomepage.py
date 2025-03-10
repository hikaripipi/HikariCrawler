import time
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from typing import Optional, List, Dict
import aiohttp
from urllib.parse import urlparse
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GMapScraper:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.browser = None
        self.context = None

    async def init_browser(self):
        """Playwrightブラウザの初期化"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800}
        )

    async def close_browser(self):
        """ブラウザのクリーンアップ"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def get_official_website(self, gmap_url: str) -> Optional[str]:
        """Google Maps URLから公式サイトのURLを取得"""
        if not gmap_url or not isinstance(gmap_url, str):
            return None

        async with self.semaphore:
            try:
                page = await self.context.new_page()
                await page.goto(gmap_url, wait_until="networkidle")

                # ウェブサイトボタンを探す
                website_button = await page.query_selector(
                    'a[data-item-id="authority"]'
                )
                if not website_button:
                    return None

                official_url = await website_button.get_attribute("href")
                logger.info(f"✨ 公式サイト発見: {official_url}")

                return official_url

            except Exception as e:
                logger.error(f"❌ エラーが発生しました: {str(e)}")
                return None

            finally:
                await page.close()

    async def process_urls_batch(self, urls: List[str]) -> List[Optional[str]]:
        """URLのバッチ処理"""
        tasks = [self.get_official_website(url) for url in urls]
        return await asyncio.gather(*tasks)


async def process_csv_file(input_csv: str, batch_size: int = 10):
    """CSVファイルを処理して公式サイトURLを追加する"""
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(input_csv)

        if "gmap_url" not in df.columns:
            logger.error("❌ CSVファイルにgmap_urlカラムがありません")
            return

        # 公式サイトカラムを追加
        df["official_website"] = None

        # スクレイパーの初期化
        scraper = GMapScraper(max_concurrent=5)
        await scraper.init_browser()

        # バッチ処理
        total_rows = len(df)
        for i in range(0, total_rows, batch_size):
            batch_urls = df.iloc[i : i + batch_size]["gmap_url"].tolist()
            results = await scraper.process_urls_batch(batch_urls)

            # 結果を保存
            for j, result in enumerate(results):
                if i + j < total_rows:
                    df.at[i + j, "official_website"] = result

            logger.info(f"📊 進捗: {min(i + batch_size, total_rows)}/{total_rows}")

        # ブラウザのクリーンアップ
        await scraper.close_browser()

        # 結果を新しいCSVファイルに保存
        output_file = input_csv.replace(".csv", "_with_websites.csv")
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(f"\n✅ 処理が完了しました！")
        logger.info(f"📝 結果は {output_file} に保存されました")

    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {str(e)}")


def main():
    input_csv = "/Users/hikarimac/Documents/python/crawler/東京夜の遊び調査まとめ - 新宿 (2).csv"
    asyncio.run(process_csv_file(input_csv))


if __name__ == "__main__":
    main()
