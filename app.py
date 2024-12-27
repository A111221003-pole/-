from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import datetime
import requests

# 初始化 Flask 應用程式
app = Flask(__name__)

# 設定資料庫連結
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://linebotproject:rzcT8LvNQNBGEPaGcrtaXhwErZy7uv9m@dpg-ctmki4bv2p9s73fcbnmg-a.oregon-postgres.render.com/linebotproject'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Line Bot 設定
line_bot_api = LineBotApi('/cuCbOZ42TY8UOVjqSg7L/X2nk955E9emuWqqz6F1Gj2/90Ir0CbWu/jPNexfxFu+NcJmZv5LDbYmrZjwOjZ/PZgGsS4XcxFaYM8NS6hfsaOs+VEzm0/ddZUYh4yLhXRvQ+aRH24ZGcocSr7KezzzAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('f021ff0c04ee67be09a39d54f1ba7ae6')

# 定義資料庫模型
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Boolean, default=False)

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.now())

# 定義倒數日功能
def get_countdown(target_date):
    today = datetime.date.today()
    days_left = (target_date - today).days
    return f"距離 {target_date.strftime('%Y-%m-%d')} 還有 {days_left} 天！"

# Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK', 200

# 訊息處理函數
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text.startswith("新增待辦"):
        content = text.replace("新增待辦 ", "")
        new_todo = Todo(user_id=event.source.user_id, content=content)
        db.session.add(new_todo)
        db.session.commit()
        reply = f"已新增待辦事項：{content}"

    elif text.startswith("查詢待辦"):
        todos = Todo.query.filter_by(user_id=event.source.user_id, status=False).all()
        reply = "\n".join([f"{i+1}. {todo.content}" for i, todo in enumerate(todos)]) if todos else "目前沒有待辦事項。"

    elif text.startswith("倒數日"):
        try:
            target_date = datetime.datetime.strptime(text.replace("倒數日 ", ""), '%Y-%m-%d').date()
            reply = get_countdown(target_date)
        except ValueError:
            reply = "請輸入正確的日期格式，例如：倒數日 2024-12-31"

    elif text.startswith("記錄支出"):
        parts = text.split(" ")
        if len(parts) >= 3:
            amount = float(parts[1])
            category = parts[2]
            new_finance = Finance(user_id=event.source.user_id, amount=-amount, category=category)
            db.session.add(new_finance)
            db.session.commit()
            reply = f"已記錄支出：{amount} 元，類別：{category}"
        else:
            reply = "請輸入正確的格式，例如：記錄支出 500 食物"

    elif text.startswith("記錄收入"):
        parts = text.split(" ")
        if len(parts) >= 3:
            amount = float(parts[1])
            category = parts[2]
            new_finance = Finance(user_id=event.source.user_id, amount=amount, category=category)
            db.session.add(new_finance)
            db.session.commit()
            reply = f"已記錄收入：{amount} 元，類別：{category}"
        else:
            reply = "請輸入正確的格式，例如：記錄收入 1000 薪水"

    elif text.startswith("查詢財務"):
        finances = Finance.query.filter_by(user_id=event.source.user_id).all()
        total = sum([f.amount for f in finances]) if finances else 0
        reply = f"你的總餘額為：{total} 元"

    else:
        reply = "請輸入正確的指令，如：新增待辦、查詢待辦、倒數日 YYYY-MM-DD、記錄支出、記錄收入、查詢財務等。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 初始化資料表並啟動應用程式
if __name__ == "__main__":
    with app.app_context():
        if os.getenv("INIT_DB", "false").lower() == "true":
            try:
                db.create_all()  # 創建資料表
                print("Database tables created successfully!")
            except Exception as e:
                print(f"Error creating database tables: {e}")
        app.run(host='0.0.0.0', port=5000, debug=True)
