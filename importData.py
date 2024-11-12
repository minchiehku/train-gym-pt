import pandas as pd
import pymysql

# 讀取 CSV 檔案
df = pd.read_csv("D:/Java_project/trainGymPT/megaGymDataset.csv")

# 刪除不必要的索引欄位
if 'Unnamed: 0' in df.columns:
    df.drop(columns=['Unnamed: 0'], inplace=True)

# 填補缺失值
df = df.fillna({
    "Desc": "No description",
    "Equipment": "None",
    "Rating": 0,
    "RatingDesc": "No rating"
})

# 去除重複的標題
df.drop_duplicates(subset="Title", keep="first", inplace=True)

# 連接到 MySQL 資料庫
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="springboot",
    database="gym_bot_db"
)
cursor = connection.cursor()

# 清空舊資料
cursor.execute("TRUNCATE TABLE exercises;")

# 將清理後的資料插入資料庫
for _, row in df.iterrows():
    sql = """
    INSERT INTO exercises (Title, Description, Type, BodyPart, Equipment, Level, Rating, RatingDesc)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (row['Title'], row['Desc'], row['Type'], row['BodyPart'], row['Equipment'], row['Level'], row['Rating'], row['RatingDesc']))

connection.commit()
cursor.close()
connection.close()
print("Data has been successfully re-imported")
