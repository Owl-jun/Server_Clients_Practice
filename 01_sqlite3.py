import sqlite3

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("memo.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# 초기화 실행
init_db()
