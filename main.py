import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TextSendMessage, StickerSendMessage, LocationSendMessage,
    ImageSendMessage, VideoSendMessage
)
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

app = Flask(__name__)
HISTORY_FILE = "chat_history.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=GEMINI_API_KEY
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def save_history(user_input, ai_response=None, msg_type="text", extra_url=None):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                history = []

    entry = {"type": msg_type, "user": user_input}
    if msg_type == "text":
        entry["ai"] = ai_response
    elif msg_type == "image":
        entry["ai_image_url"] = extra_url
    elif msg_type == "video":
        entry["ai_video_url"] = extra_url
    elif msg_type == "location":
        entry["address"] = "320桃園市中壢區遠東路135號"
    elif msg_type == "sticker":
        entry["sticker_id"] = "1"

    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_gemini_reply(user_input):
    try:
        human = HumanMessage(content=[{"type": "text", "text": user_input + "，請用繁體中文回答"}])
        result = llm.invoke([human])
        return result.content
    except Exception as e:
        print("Gemini 回覆錯誤：", e)
        return "AI 回覆失敗"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    try:
        for event in body['events']:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_input = event['message']['text'].strip().lower()
                reply_token = event['replyToken']

                if user_input == "貼圖":
                    sticker = StickerSendMessage(package_id='1', sticker_id='1')
                    line_bot_api.reply_message(reply_token, sticker)
                    save_history(user_input, msg_type="sticker")
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
                    img_url = "https://s.yimg.com/ny/api/res/1.2/v2ics1Z_DbOFT6wrjTaxGw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTY0MDtoPTQyNw--/https://s.yimg.com/os/creatr-uploaded-images/2022-06/3757bb00-eca8-11ec-bf3f-7c2b69f1b53a"
                    image_msg = ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
                    line_bot_api.reply_message(reply_token, image_msg)
                    save_history(user_input, msg_type="image", extra_url=img_url)
                    return "OK"

                elif user_input == "影片":
                    video_url = "https://videos.pexels.com/video-files/12156088/12156088-hd_1920_1080_24fps.mp4"
                    preview_img = "https://i.imgur.com/3Q3Z8Ja.jpg"
                    video_msg = VideoSendMessage(original_content_url=video_url, preview_image_url=preview_img)
                    line_bot_api.reply_message(reply_token, video_msg)
                    save_history(user_input, msg_type="video", extra_url=video_url)
                    return "OK"

                else:
                    ai_response = generate_gemini_reply(user_input)
                    save_history(user_input, ai_response)
                    line_bot_api.reply_message(reply_token, TextSendMessage(text=ai_response))
                    return "OK"

        return "OK"
    except Exception as e:
        print("Webhook 處理錯誤：", e)
        return abort(400)

#GET
@app.route("/history", methods=["GET"])
def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

#DELETE
@app.route("/history", methods=["DELETE"])
def delete_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return {"status": "deleted_all"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
