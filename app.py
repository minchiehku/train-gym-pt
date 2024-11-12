from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import pymysql

app = Flask(__name__)

# 初始化 NLP 模型
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# 通用的分類標籤，例如增肌、減脂、腹肌等
general_labels = ["增肌", "減脂", "腹肌", "胸肌", "腿部"]

# 對應每個通用標籤到特定的 BodyPart
label_to_bodyparts = {
    "增肌": ["Lats", "Biceps", "Chest", "Triceps"],
    "減脂": ["Middle Back", "Lower Back", "Forearms", "Calves"],
    "腹肌": ["Abdominals"],
    "胸肌": ["Chest"],
    "腿部": ["Hamstrings", "Quadriceps", "Calves", "Glutes"]
}

# 資料庫連接函數
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="springboot",  # 替換為您的 MySQL 密碼
        database="gym_bot_db"
    )


# 格式化運動描述，將專業術語簡化並增強可讀性
def format_exercise_description(name, description):
    if not description or description == "No description":
        description = "這是一個有效的訓練，可以幫助增強目標肌群的力量和耐力。"
    else:
        # 簡化過於詳細的專業描述
        if "self-myofascial release" in description:
            description = "這是一種針對肌肉放鬆的自我按摩方式，適合用於減輕肌肉緊繃。"
        elif "isometric hold" in description:
            description = "這個動作專注於靜態肌肉收縮，有助於提升肌肉耐力。"
        elif "concentration curl" in description:
            description = "這是一個針對手臂肌群的專注訓練，有助於增強手臂力量。"
        # 可以繼續添加更多關鍵字和簡化語句
    return f"{name}：{description}"


app = Flask(__name__)
CORS(app)  # 啟用 CORS

# API 路由，用於處理用戶輸入並返回推薦運動
@app.route('/api/get_suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    user_input = data.get("input")
    
    # 使用 NLP 模型進行意圖分類
    result = classifier(user_input, general_labels)
    best_match = result['labels'][0]  # 選擇最相關的標籤（意圖）
    bodyparts = label_to_bodyparts.get(best_match, [])

    # 根據意圖查詢對應的 BodyPart 資料
    connection = get_db_connection()
    cursor = connection.cursor()

    # 構建 SQL 查詢語句，查找多個 BodyPart 的資料
    if bodyparts:
        format_strings = ','.join(['%s'] * len(bodyparts))
        query = f"SELECT * FROM exercises WHERE BodyPart IN ({format_strings}) LIMIT 5"
        cursor.execute(query, bodyparts)
        exercises = cursor.fetchall()
    else:
        exercises = []

    cursor.close()
    connection.close()

    # 格式化查詢結果
    if exercises:
        formatted_exercises = "\n".join([format_exercise_description(row[1], row[2]) for row in exercises])
        message = f"您可以試試這些{best_match}訓練：\n{formatted_exercises}"
    else:
        message = f"抱歉，目前沒有找到相關的{best_match}訓練。"

    return jsonify({"Message": message})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
