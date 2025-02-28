# Server_Clients_Practice
서버-클라이언트 구조 맛보기 부터

## 미니 프로젝트 : 1:1 오목대전 구현

### 1회차 작업


https://github.com/user-attachments/assets/cac6a10c-6a93-47aa-b1fc-05e908e6155c


- [서버](./game_omok/server.py)
  - flask 로 서버를 열고 실시간 통신을 위해 flask_socketio로 통신 구현
  - 서버측에서는 @socketio.on('keyword')를 통해 메시지를 주고 받는다.

- [클라이언트](./game_omok/main.py)
  - pygame을 통해 간단한 UI 구현, socketio 를 통해 서버와 통신을 주고받음
  - 클라이언트 측에서는 @sio.on('keyword')를 통해 메시지를 주고 받는다.

```python
# 기본적으로 sio.on('key'), socketio.on('key') 와 emit('key', 데이터) 를 통해 통신을 함
@sio.event
def connect():
  """서버 연결 됬을 시 행동"""
@sio.event
def disconnect():
  """연결 종료 시 행동"""
```

- 후기 : Flask가 뭐고, 소켓 프로그래밍이 뭔지 말만 들어보고, 혼자 KOCW 대학교 네트워크 강의를 들으면서 이론만 대충 알고 있었는데, 머리로는 구상이 되지만 막상 구현하려면 매번 막혀서 도망쳤었다. 그런데, **처음으로 서버를 열고 "서버에 연결됨" 메시지를 보았을 때, 카타르시스를 느꼇다.** 현재 게임은 버그 투성이이며 고칠 것도 많지만 오늘은 서버와 연동을 성공했고, 메시지를 성공적으로 주고받았다는 것에 의의를 두어본다. **이번 프로젝트는 완벽을 기하기 보다는 하고싶은거 다 해보며 서버-클라이언트 구조에 익숙해지는 시간을 갖는 것이 목표**이다, 역시 100번 강의 보다, 1번 강의 + 몸통박치기가 최고의 학습인것 같다.


## Flask 기본 개념 이해
- Flask 란?
  - 가벼운 웹 프레임워크로, 웹 애플리케이션과 API 서버를 쉽게 만들 수 있다.
  - 요청을 처리하고 JSON 응답을 반환하는 REST API 서버를 개발할 때 많이 사용됨.
  - Django보다 간단한 구조를 가짐.

- 설치하기
  ```shell
  pip install flask
  ```

