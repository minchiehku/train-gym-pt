import pandas as pd

df = pd.read_csv("megaGymDataset.csv")
print(df.info())  # 查看每個欄位的資料類型和缺失值
print(df.describe())  # 查看數字欄位的描述性統計
print(df.isnull().sum())  # 查看每個欄位的缺失值數量
