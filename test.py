import requests

response = requests.post("http://127.0.0.1:5000/add", json={"content": "Flask 공부하기"})

print(response.json())  # 응답 출력

res = requests.get("http://127.0.0.1:5000/memos")
print(res.json())