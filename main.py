# main.py
from flask import Flask, request, abort
import requests
import json
import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from configparser import ConfigParser
import google.generativeai as genai
from linebot.models import StickerSendMessage
from linebot.models import LocationSendMessage
from linebot import LineBotApi

app = Flask(__name__)

HISTORY_FILE = "chat_history.json"

# 儲存對話紀錄
def save_history(user_input, ai_response):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                history = []
    history.append({"user": user_input, "ai": ai_response})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# 查詢對話紀錄
@app.route("/history", methods=["GET"])
def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        return history
    else:
        return []

# 刪除對話紀錄
@app.route("/history", methods=["DELETE"])
def delete_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return {"status": "deleted"}

# 👉 將這兩個資訊填入你的實際值
CHANNEL_ACCESS_TOKEN = 'kOx9PJ6WpRvQRK5xnsgMKyQi3r/sum++wJKHCqjcNWwEr5VJQBO8DcMpKqytz1DIdSo22lciUH1Va3KnL3kUT8iia05meCSGyzrSVhXw+6TLFuPGduCqtsSUQhhhFFO/K2sGzYIiv0ch4NI0yjkikAdB04t89/1O/w1cDnyilFU='
#GEMINI_API_KEY = 'AIzaSyAb5hL0EPmBnpPOU7pI5KzTX3paZQ9Lla8'

config = ConfigParser()
config.read("config.ini")

genai.configure(api_key=config["Gemini"]["API_KEY"])
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=config["Gemini"]["API_KEY"],
)

def generate_gemini_reply(user_input):
    try:
        user_messages = []
        user_messages.append({"type": "text", "text": user_input + "，請用繁體中文回答。"})
        human_messages = HumanMessage(content=user_messages)
        result = llm.invoke([human_messages])
        return result.content
    except Exception as e:
        print("Gemini 回覆錯誤：", e)
        return "AI 回應失敗，請稍後再試～"

def reply_message(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
    print("LINE 回應狀態碼：", res.status_code)

@app.route("/webhook", methods=['POST'])
def webhook():
    body = request.json
    print(json.dumps(body, indent=2))  # 印出收到的 webhook 請求
    try:
        for event in body['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_input = event['message']['text']
                reply_token = event['replyToken']

                # 如果使用者輸入「貼圖」
                if user_input.strip().lower() == "貼圖":
                    sticker = StickerSendMessage(
                        package_id='1',
                        sticker_id='1'
                    )
                    line_bot_api.reply_message(reply_token, sticker)
                    return "OK"

                # 如果使用者輸入「location」
                elif user_input.strip().lower() == "location":
                    location_msg = LocationSendMessage(
                        title="元智大學",
                        address="320桃園市中壢區遠東路135號",
                        latitude=24.970198,
                        longitude=121.267625
                    )
                    line_bot_api.reply_message(reply_token, location_msg)
                    return "OK"

                # 否則用 Gemini 回覆
                else:
                    ai_response = generate_gemini_reply(user_input)
                    save_history(user_input, ai_response)
                    reply_message(reply_token, ai_response)

        return "OK"

    except Exception as e:
        print("Webhook 處理錯誤：", e)
        return abort(400)


if __name__ == "__main__":
    app.run(port=5000)

