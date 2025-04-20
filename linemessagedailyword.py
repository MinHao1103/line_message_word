import os
import sys
import json
import time
import logging
import requests
import schedule
import pytz
from datetime import datetime, date

# 檢查作業系統平台
IS_WINDOWS = os.name == 'nt'
TIMEZONE = 'Asia/Taipei'

if IS_WINDOWS:
    tz = pytz.timezone(TIMEZONE)
    get_now = lambda: datetime.now(tz)
    get_today = lambda: get_now().date()
else:
    os.environ['TZ'] = TIMEZONE
    time.tzset()
    get_now = lambda: datetime.now()
    get_today = lambda: date.today()

# 日誌設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logging.info(f"目前時間: {get_now()}")

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = "dvqS3RJtN07Wqg6EXvWgnSdR3X+koAaL1GbDZWCnjHToBqw7IykTO2JNBjKi9UkOKuxI6Z90MdXCx/32j/NrcAbpx1RRIl+s2Yt6f0XuNP8WMuuXkfEcPyDXW4AV5ewQJtCG3jF+XRC08gP7zPDZvQdB04t89/1O/w1cDnyilFU="
USER_ID = "Ubb2c2ab2b4f1f6f7d457c09c288b8976"

# TODO: 從資料庫讀取今天的單字
def load_today_word():
    today = str(get_today())
    with open("word.json", "r", encoding="utf-8") as f:
        words = json.load(f)
    for word in words:
        if word["date"] == today:
            return word
    return None

# 產生 Google TTS 音訊連結
def generate_audio_url(text):
    # 將文字轉換為URL安全格式
    encoded_text = requests.utils.quote(text)
    return f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={encoded_text}"

# 發送錯誤訊息
def send_simple_message():
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": USER_ID,
        "messages": [{
            "type": "text",
            "text": "❌ No word found for today."
        }]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Response: {response.text}")

# 發送 Flex 訊息
def send_flex_message(word_data):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # 生成單字發音連結
    if "audio_url" not in word_data or not word_data["audio_url"]:
        word_data["audio_url"] = generate_audio_url(word_data["word"])
    
    # 生成例句發音連結
    example_audio_url = generate_audio_url(word_data["example"])

    body = {
        "to": USER_ID,
        "messages": [{
            "type": "flex",
            "altText": f"Word of the Day: {word_data['word']}",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [{
                        "type": "text",
                        "text": "📖 今日單字",
                        "weight": "bold",
                        "size": "lg"
                    }]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"📚 {word_data['word']} ({word_data['part_of_speech']})",
                            "weight": "bold",
                            "size": "xl",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": f"💡 英文解釋: {word_data['definition']}",
                            "size": "sm",
                            "color": "#555555",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": f"📘 中文解釋: {word_data['definition_zh']}",
                            "size": "sm",
                            "color": "#555555",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": "✏️ 例句:",
                            "weight": "bold",
                            "size": "sm",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": f"● {word_data['example']}",
                            "wrap": True,
                            "size": "sm",
                            "color": "#333333"
                        },
                        {
                            "type": "text",
                            "text": f"○ {word_data['example_zh']}",
                            "wrap": True,
                            "size": "sm",
                            "color": "#666666"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "🔊 單字發音",
                                "uri": word_data["audio_url"]
                            },
                            "style": "primary",
                            "color": "#00C300"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "🔊 例句發音",
                                "uri": example_audio_url
                            },
                            "style": "secondary",
                            "color": "#1E90FF"
                        }
                    ]
                }
            }
        }]
    }

    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Response: {response.text}")

# 任務排程
def job():
    word = load_today_word()
    if word:
        send_flex_message(word)
    else:
        logging.info("❌ 今天沒有對應的單字。")
        send_simple_message()

# 設定每天9點執行
schedule.every().day.at("09:00").do(job)

if __name__ == "__main__":
    while True:
        logging.info(f"Checking at {get_now()}...")
        schedule.run_pending()
        time.sleep(10)