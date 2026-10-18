import os
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 專注於 0050 與大盤、台積電、美股動態
SEARCH_TARGETS = [
    {
        "category": "📊 0050 / 台灣50成分股動態",
        "keyword": "0050 OR 台灣50 OR 台積電法說 OR 0050 成份股",
        "color": 3066993  # 綠色
    },
    {
        "category": "🇺🇸 美股ADR與大盤總經面",
        "keyword": "台積電ADR OR 費城半導體 OR 美股四大指數 OR 外資買賣超",
        "color": 3447003  # 藍色
    }
]

def fetch_google_news(keyword, limit=2):
    """抓取精選新聞"""
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
                "source": item.source.text if item.source else "財經媒體"
            })
        return news_list
    except Exception as e:
        print(f"抓取 {keyword} 失敗: {e}")
        return []

def analyze_market_sentiment(embeds):
    """分析大盤恐慌程度與買入投報率建議"""
    text_blob = "".join([e["title"] for e in embeds])
    
    panic_keywords = ["重挫", "暴跌", "崩盤", "利空", "衰退", "砍倉", "恐慌", "下殺", "急跌"]
    panic_count = sum(text_blob.count(kw) for kw in panic_keywords)
    
    if panic_count >= 2:
        panic_level = "🔴 高恐慌 (市場悲觀，逢低分批佈局 0050 好時機)"
        roi_advice = "預估長期年化投報率：約 12% ~ 18%（恐慌往往是市值型 ETF 的甜甜價，適合資金分批進場）"
    elif panic_count == 1:
        panic_level = "🟡 中度震盪 (多空交織，適合定期定額)"
        roi_advice = "預估長期年化投報率：約 8% ~ 12%（維持紀律扣款，不急著一次買滿）"
    else:
        panic_level = "🟢 低恐慌 / 偏向樂觀 (情緒平穩)"
        roi_advice = "預估長期年化投報率：約 6% ~ 10%（基期相對平穩，持續定期定額累積張數）"
        
    return panic_level, roi_advice

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("未設定 DISCORD_WEBHOOK_URL")
        return

    embeds = []
    for target in SEARCH_TARGETS:
        news_items = fetch_google_news(target["keyword"], limit=2)
        for item in news_items:
            embeds.append({
                "title": item["title"],
                "url": item["link"],
                "color": target["color"],
                "author": {"name": target["category"]},
                "footer": {"text": f"來源：{item['source']}"}
            })

    if not embeds:
        print("無新聞資料")
        return

    panic_level, roi_advice = analyze_market_sentiment(embeds)

    payload = {
        "username": "0050 戰情小幫手",
        "content": f"☀️ **【今日 0050 與大盤戰情快報】**\n\n🌡️ **市場恐慌指標**：{panic_level}\n💡 **投資評估建議**：{roi_advice}",
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
            print("0050 專用戰情順利發送至 Discord！")
    except Exception as e:
        print(f"發送 Discord 失敗: {e}")

if __name__ == "__main__":
    send_to_discord()
