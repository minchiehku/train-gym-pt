import pandas as pd
import pymysql

# 連接 MySQL 資料庫
connection = pymysql.connect(
    host="localhost",
    user="root",
    password="springboot",
    database="gym_bot_db"
)
cursor = connection.cursor()

# 讀取 CSV 檔案
df = pd.read_csv(r"D:\Java_project\trainGymPT\megaGymDataset.csv")

# 使用 fillna() 確保所有 NaN 被替換為 None
df = df.where(pd.notnull(df), None)

# 將資料插入資料表
for _, row in df.iterrows():
    # 將每一列轉換為 tuple 並替換 NaN 值
    row = tuple(None if pd.isna(value) else value for value in row)
    
    sql = """
    INSERT INTO exercises (ID, Title, Description, Type, BodyPart, Equipment, Level, Rating, RatingDesc)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, row)

connection.commit()
cursor.close()
connection.close()
