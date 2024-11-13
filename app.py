from flask import Flask, request, jsonify
from transformers import pipeline, BertTokenizer, GPT2LMHeadModel
from flask_cors import CORS
import pymysql
import torch
import re

app = Flask(__name__)
CORS(app)

# NLP 模型初始化
classifier = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")

# 載入分詞器和模型
tokenizer = BertTokenizer.from_pretrained('thu-coai/CDial-GPT2_LCCC-base', use_fast=False)
model = GPT2LMHeadModel.from_pretrained('thu-coai/CDial-GPT2_LCCC-base')

# 添加特殊標記
special_tokens_dict = {'additional_special_tokens': ['[unused{}]'.format(i) for i in range(1, 100)]}
tokenizer.add_special_tokens(special_tokens_dict)
model.resize_token_embeddings(len(tokenizer))

# 設定特殊標記的 ID
model.config.pad_token_id = tokenizer.convert_tokens_to_ids('[PAD]')
model.config.eos_token_id = tokenizer.convert_tokens_to_ids('[SEP]')
model.config.bos_token_id = tokenizer.convert_tokens_to_ids('[CLS]')

# 通用的分類標籤
general_labels = ["arms", "legs", "chest", "upper body", "small upper body muscles", "back", "small lower body muscles", "muscle gain", "fat loss"]

# 標籤到 BodyPart 的對應
label_to_bodyparts = {
    "arms": ["Biceps", "Triceps", "Forearms"],
    "legs": ["Hamstrings", "Quadriceps", "Calves", "Glutes"],
    "chest": ["Chest"],
    "small upper body muscles": ["Shoulders", "Abdominals", "Neck"],
    "back": ["Lats", "Traps", "Middle Back", "Lower Back"],
    "small lower body muscles": ["Adductors", "Abductors"],
    "muscle gain": ["Chest", "Lats", "Traps", "Back", "Hamstrings", "Quadriceps"],
    "fat loss": ["Abdominals"]
}

# Database connection function
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="springboot",
        database="gym_bot_db"
    )


def get_high_rated_exercises(bodyparts, limit=2):
    connection = get_db_connection()
    cursor = connection.cursor()
    exercises = []
    if bodyparts:
        format_strings = ','.join(['%s'] * len(bodyparts))
        query = f"""
        SELECT Title, Description, Rating 
        FROM exercises 
        WHERE BodyPart IN ({format_strings}) AND Description IS NOT NULL AND Description != '' AND Description != 'No description'
        ORDER BY Rating DESC 
        LIMIT {limit}
        """
        cursor.execute(query, bodyparts)
        exercises = cursor.fetchall()
        print("Fetched exercises:", exercises)  # 調試：打印查詢到的運動建議
    cursor.close()
    connection.close()

    # 格式化運動建議
    formatted_exercises = [f"{row[0]}: {row[1]}" for row in exercises if row[1] and row[1] != 'No description']
    return "\n".join(formatted_exercises)

# 測試模型生成功能
def test_model_generation():
    test_input = "Hello, can you provide some advice on fitness?"
    input_ids = tokenizer.encode(test_input, return_tensors='pt')
    generated_ids = model.generate(
        input_ids,
        max_length=50,
        pad_token_id=model.config.pad_token_id,
        eos_token_id=model.config.eos_token_id,
        do_sample=True,
        top_p=0.9,
        temperature=0.7
    )
    test_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print("Test output from model:", test_output)

# 呼叫測試函數
test_model_generation()

# API 路由
@app.route('/api/get_suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    user_id = data.get("user_id")
    user_input = data.get("input")

    # 手動關鍵字匹配，用於檢查使用者的具體需求
    keyword_to_label = {
        "chest": "chest",
        "legs": "legs",
        "arms": "arms",
        "shoulder": "small upper body muscles",
        "back": "back",
        "abs": "small upper body muscles"
    }
    
    # 先進行關鍵字匹配
    top_label = None
    for keyword, label in keyword_to_label.items():
        if keyword in user_input:
            top_label = label
            break
    
    # 如果無匹配的關鍵字，則依照 NLP 模型的結果選擇標籤
    if not top_label:
        result = classifier(user_input, general_labels)
        print("Classification result:", result)  # 調試：打印 NLP 模型的分類結果
        top_label = result['labels'][0]

    print("Selected label:", top_label)  # 調試：打印選擇的標籤

    # 獲取對應的 BodyPart
    bodyparts = label_to_bodyparts.get(top_label, [])
    print("Bodyparts for query:", bodyparts)  # 調試：打印要查詢的部位

    # 查詢資料庫獲取建議
    exercise_suggestions = get_high_rated_exercises(bodyparts)

    # 使用 AI 生成對話回應
    chat_input = f"I am asking for advice on {user_input}. Can you provide some guidance?"
    input_ids = tokenizer.encode(chat_input, return_tensors='pt')

    chat_response_ids = model.generate(
        input_ids,
        max_length=60,       # 增加 max_length 值，允許更長的生成回應
        pad_token_id=model.config.pad_token_id,
        eos_token_id=model.config.eos_token_id,
        do_sample=True,
        top_p=0.9,
        temperature=0.7
    )
    ai_response = tokenizer.decode(
        chat_response_ids[0][input_ids.shape[-1]:],
        skip_special_tokens=True
    )

    # 如果生成的回應是空的，設置默認回應
    if not ai_response.strip():
        ai_response = "I'm here to help with your workout. Here are some suggestions for you."

    # 清理生成的回應，去除無意義字符
    ai_response = re.sub(r'[^A-Za-z0-9.,?!\s]', '', ai_response).strip()

    # 最終的回應
    if exercise_suggestions:
        response_text = f"{ai_response}\n\nRecommended exercises:\n{exercise_suggestions}"
    else:
        response_text = f"{ai_response}\n\nSorry, no exercises matched your criteria."

    return jsonify({"Message": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
