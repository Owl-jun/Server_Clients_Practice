from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# 📌 메모 추가 API (POST)
@app.route("/add", methods=["POST"])
def add_memo():
    data = request.json  # JSON 데이터 받기
    content = data.get("content")  # "content" 필드 가져오기
    
    if not content:
        return jsonify({"error": "메모 내용을 입력하세요!"}), 400

    conn = sqlite3.connect("memo.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memos (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()

    return jsonify({"message": "메모 추가 완료!"})

# 📌 모든 메모 조회 API (GET)
@app.route("/memos", methods=["GET"])
def get_memos():
    conn = sqlite3.connect("memo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memos")
    memos = [{"id": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()

    return jsonify(memos)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
