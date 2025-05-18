# main.py
from flask import Flask, request, abort
import requests
import json
import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from configparser import ConfigParser
import google.generativeai as genai
from linebot.models import (
    TextSendMessage,
    StickerSendMessage,
    LocationSendMessage,
    ImageSendMessage,
    VideoSendMessage
)
from linebot import LineBotApi

app = Flask(__name__)

HISTORY_FILE = "chat_history.json"

# 儲存對話紀錄
def save_history(user_input, ai_response=None, msg_type="text", extra_url=None):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                history = []

    if msg_type == "text":
        entry = {
            "type": "text",
            "user": user_input,
            "ai": ai_response
        }
    elif msg_type == "image":
        entry = {
            "type": "image",
            "user": user_input,
            "ai_image_url": extra_url
        }
    elif msg_type == "video":
        entry = {
            "type": "video",
            "user": user_input,
            "ai_video_url": extra_url
        }
    elif msg_type == "location":
        entry = {
            "type": "location",
            "user": user_input,
            "address": "320桃園市中壢區遠東路135號"
        }
    elif msg_type == "sticker":
        entry = {
            "type": "sticker",
            "user": user_input,
            "sticker_id": "1"
        }

    history.append(entry)

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
                user_input = event['message']['text'].strip().lower()
                reply_token = event['replyToken']

                if user_input == "貼圖":
                    sticker = StickerSendMessage(package_id='1', sticker_id='1')
                    line_bot_api.reply_message(reply_token, sticker)
                    return "OK"

                elif user_input == "location":
                    location_msg = LocationSendMessage(
                        title="元智大學",
                        address="320桃園市中壢區遠東路135號",
                        latitude=24.970198,
                        longitude=121.267625
                    )
                    line_bot_api.reply_message(reply_token, location_msg)
                    save_history(user_input, msg_type="location")
                    return "OK"

                elif user_input == "圖片":
                    image_url = "https://s.yimg.com/ny/api/res/1.2/v2ics1Z_DbOFT6wrjTaxGw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTY0MDtoPTQyNw--/https://s.yimg.com/os/creatr-uploaded-images/2022-06/3757bb00-eca8-11ec-bf3f-7c2b69f1b53a"
                    image_msg = ImageSendMessage(
                        original_content_url=image_url,
                        preview_image_url="https://s.yimg.com/ny/api/res/1.2/v2ics1Z_DbOFT6wrjTaxGw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTY0MDtoPTQyNw--/https://s.yimg.com/os/creatr-uploaded-images/2022-06/3757bb00-eca8-11ec-bf3f-7c2b69f1b53a"
                    )
                    line_bot_api.reply_message(reply_token, image_msg)
                    save_history(user_input, msg_type="image", extra_url=image_url)
                    return "OK"

                elif user_input == "影片":
                    video_url="https://videos.pexels.com/video-files/12156088/12156088-hd_1920_1080_24fps.mp4"
                    video_msg = VideoSendMessage(
                        original_content_url=video_url,
                        preview_image_url="https://i.imgur.com/3Q3Z8Ja.jpg"
                    )
                    line_bot_api.reply_message(reply_token, video_msg)
                    save_history(user_input, msg_type="video", extra_url=video_url)
                    return "OK"

                else:
                    ai_response = generate_gemini_reply(user_input)
                    save_history(user_input, ai_response)
                    reply_message(reply_token, ai_response)
                    return "OK"

        return "OK"

    except Exception as e:
        print("Webhook 處理錯誤：", e)
        return abort(400)


if __name__ == "__main__":
    app.run(port=5000)

