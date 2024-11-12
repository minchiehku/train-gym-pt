import requests

test_inputs = [
    "train chest"
    "我想要增肌",
    "推薦一些減脂運動",
    "鍛鍊腹肌的動作有哪些？",
    "胸肌訓練推薦",
    "腿部肌肉的鍛鍊"
]

for user_input in test_inputs:
    response = requests.post(
        "http://127.0.0.1:5000/api/get_suggestions",
        json={"input": user_input}
    )
    print(f"Input: {user_input}")
    
    try:
        print(f"Response: {response.json()}\n")
    except requests.exceptions.JSONDecodeError:
        print("Response is not in JSON format.")
        print(f"Raw Response: {response.text}\n")
