from flask import Flask, request, jsonify
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from flask_cors import CORS
import pymysql
import random

app = Flask(__name__)
CORS(app)

# NLP 模型初始化
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# 通用的分類標籤
general_labels = ["增肌", "減脂", "腹肌", "胸肌", "腿部"]

# 標籤到 BodyPart 的對應
label_to_bodyparts = {
    "增肌": ["Lats", "Biceps", "Chest", "Triceps"],
    "減脂": ["Middle Back", "Lower Back", "Forearms", "Calves"],
    "腹肌": ["Abdominals"],
    "胸肌": ["Chest"],
    "腿部": ["Hamstrings", "Quadriceps", "Calves", "Glutes"]
}

# 資料庫連接
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="springboot",
        database="gym_bot_db"
    )

# 獲取高評分且有描述的運動建議
def get_high_rated_exercises(bodyparts, limit=2):
    connection = get_db_connection()
    cursor = connection.cursor()
    if bodyparts:
        format_strings = ','.join(['%s'] * len(bodyparts))
        query = f"SELECT Title, Description, Rating FROM exercises WHERE BodyPart IN ({format_strings}) AND Description IS NOT NULL ORDER BY Rating DESC LIMIT {limit}"
        cursor.execute(query, bodyparts)
        exercises = cursor.fetchall()
    else:
        exercises = []
    cursor.close()
    connection.close()
    
    # 格式化運動建議（僅顯示有描述且評分較高的動作）
    formatted_exercises = [f"{row[0]}：{row[1]}" for row in exercises if row[1]]
    return "\n".join(formatted_exercises)

# API 路由
@app.route('/api/get_suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    user_id = data.get("user_id")
    user_input = data.get("input")

    # NLP 分類
    result = classifier(user_input, general_labels)
    best_match = result['labels'][0]
    bodyparts = label_to_bodyparts.get(best_match, [])

    # 查詢數據庫獲取建議
    exercise_suggestions = get_high_rated_exercises(bodyparts)

    # 使用AI模型生成對話回應開場白
    chat_input = f"{user_input} I need workout suggestions"
    chat_history_ids = tokenizer.encode(chat_input, return_tensors='pt')
    chat_response_ids = model.generate(chat_history_ids, max_length=100, pad_token_id=tokenizer.eos_token_id)
    ai_response = tokenizer.decode(chat_response_ids[:, chat_history_ids.shape[-1]:][0], skip_special_tokens=True)

    # 最終的回應
    response_text = f"{ai_response}\n\n推薦的運動：\n{exercise_suggestions}"

    return jsonify({"Message": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
