import os
import json
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 四大戰情追蹤組別
SEARCH_TARGETS = [
    {
        "category": "📊 0050 / 台指期 / 美股ADR（大盤與資金面）",
        "keyword": "0050 OR 台指期 OR 台積電ADR OR 費城半導體",
        "color": 3066993  # 綠色
    },
    {
        "category": "💵 匯率與三大法人籌碼（外資動向）",
        "keyword": "台幣匯率 OR 外資買賣超 OR 三大法人期貨",
        "color": 3447003  # 藍色
    },
    {
        "category": "📺 友達 / 面板產業與報價",
        "keyword": "友達 OR 面板報價 OR TrendForce 面板 OR 群創",
        "color": 15105570 # 橘黃色
    },
    {
        "category": "🤝 友達客戶、車用訂單與合作夥伴",
        "keyword": "友達 車用 合作 OR 友達 訂單 OR 友達 供應鏈 OR 友達 車用面板",
        "color": 10181046 # 紫色
    }
]

def fetch_google_news(keyword, limit=2):
    """預先爬取並整理新聞資料"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item', limit=limit)
        
        news_list = []
        for item in items:
            news_list.append({
                "title": item.title.text if item.title else "無標題",
                "link": item.link.text if item.link else "",
                "date": item.pubDate.text if item.pubDate else "",
                "source": item.source.text if item.source else "財經媒體"
            })
        return news_list
    except Exception as e:
        print(f"抓取 {keyword} 失敗: {e}")
        return []

def prepare_embeds():
    """整理好的 Discord 卡片資料"""
    embeds = []
    for target in SEARCH_TARGETS:
        news_items = fetch_google_news(target["keyword"], limit=2)
        for item in news_items:
            embeds.append({
                "title": item["title"],
                "url": item["link"],
                "color": target["color"],
                "author": {"name": target["category"]},
                "footer": {"text": f"來源：{item['source']} | {item['date']}"}
            })
    return embeds

def wait_until_target_time(target_hour=11, target_minute=30):
    """等待直到台灣時間 11:30"""
    tz_taiwan = timezone(timedelta(hours=8))
    now = datetime.now(tz_taiwan)
    target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    wait_seconds = (target_time - now).total_seconds()
    if wait_seconds > 0:
        print(f"[{now.strftime('%H:%M:%S')}] 資料已預先整理完成，將等待 {int(wait_seconds)} 秒，於 {target_hour}:{target_minute:02d} 推送至 Discord...")
        time.sleep(wait_seconds)
    else:
        print(f"[{now.strftime('%H:%M:%S')}] 當前時間已過目標時間，立即發送！")

def send_to_discord(embeds):
    if not DISCORD_WEBHOOK_URL or not embeds:
        print("未設定 DISCORD_WEBHOOK_URL 或無資料可發送")
        return

    payload = {
        "username": "台股戰情小幫手",
        "content": "☀️ **【午安！0050、大盤與 友達(車用/客戶) 最新消息早報】**",
        "embeds": embeds
    }

    try:
        res = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if res.status_code == 204:
            print("新聞成功推送至 Discord！")
    except Exception as e:
        print(f"發送 Discord 失敗: {e}")

if __name__ == "__main__":
    print("開始執行爬蟲預處理...")
    embeds = prepare_embeds() 
    wait_until_target_time(11, 30) 
    send_to_discord(embeds)
