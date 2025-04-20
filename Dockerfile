# 使用輕量版 Python 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製依賴並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式檔案
COPY linemessagedailyword.py .
COPY word.json .

# 預設執行指令
CMD ["python", "linemessagedailyword.py"]