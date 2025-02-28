# server.py
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # 세션 암호화 등 보안에 사용됨
socketio = SocketIO(app)

# 게임판 설정 (15x15 오목판, 0: 빈 칸, 1: 플레이어 1, 2: 플레이어 2)
BOARD_SIZE = 15
board = [[0 for _ in range(BOARD_SIZE+1)] for _ in range(BOARD_SIZE+1)]
current_turn = 1  # 현재 턴: 1 또는 2


# 각 클라이언트(소켓)에게 플레이어 번호를 할당 (최대 2명)
players = {}


# ---------------------------------------------------------
## socketio 라이브러리 사용 시 기본적인 이벤트 핸들링
@socketio.on('connect')
def on_connect():
    sid = request.sid
    # 플레이어가 2명 미만이면 플레이어 번호 할당, 아니면 관전자로 처리
    if len([p for p in players.values() if p in [1, 2]]) < 2:
        player_number = 1 if 1 not in players.values() else 2
        players[sid] = players.get(sid,player_number)
        emit('assign_player', {'player': player_number})
        print(f"Player {player_number} connected (sid: {sid})")
    else:
        players[sid] = 0  # 0이면 관전자
        emit('assign_player', {'player': 0})
        print(f"Spectator connected (sid: {sid})")

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in players:
        print(f"Player {players[sid]} disconnected (sid: {sid})")
        del players[sid]
# ---------------------------------------------------------



@socketio.on('move')        # socketio 는 서버 측에서
def on_move(data):
    """ data 정보
        'player': 플레이어 번호 (1 또는 2),
        'position': (x, y)  # 보드상의 좌표 (0부터 BOARD_SIZE-1)
    """
    global board, current_turn
    sid = request.sid
    player = data.get('player')
    pos = data.get('position')
    if not pos or player is None:
        emit('error', {'message': "잘못된 데이터"})
        return

    x, y = pos
    # 플레이어 번호와 현재 턴 확인
    if players.get(sid) != current_turn:
        emit('error', {'message': "지금은 상대 턴입니다."})
        return

    # 이미 돌이 놓여있는지 확인
    if board[y][x] != 0:
        emit('error', {'message': "해당 위치는 이미 사용 중입니다."})
        return

    # 오목판에 돌을 놓음
    board[y][x] = current_turn
    print(f"플레이어 {current_turn}의 돌이 {(x, y)}에 놓였습니다.")

    # (추후 여기에 승리 조건 검사를 넣을 수 있음)

    # 턴 교체: 1->2, 2->1
    current_turn = 2 if current_turn == 1 else 1

    # 모든 클라이언트에 업데이트된 오목판과 현재 턴 정보를 브로드캐스트
    emit('update', {'board': board, 'current_turn': current_turn}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True) # port = 번호 로 원하는 포트번호로 할당가능!
