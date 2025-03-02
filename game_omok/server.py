# server.py
from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # 세션 암호화 등 보안에 사용됨
socketio = SocketIO(app)

# 게임판 설정 (15x15 오목판, 0: 빈 칸, 1: 플레이어 1, 2: 플레이어 2)
BOARD_SIZE = 15
board = [[0 for _ in range(BOARD_SIZE+1)] for _ in range(BOARD_SIZE+1)]
dp_h = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
dp_v = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
dp_d1 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
dp_d2 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
current_turn = 1  # 현재 턴: 1 또는 2
isEnd = False
restart_votes = [False, False]  # 두 명이 클릭해야 게임이 재시작됨

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

@socketio.on('start')
def on_start():
    global players
    if len(players) < 2:
        emit('noready',{'message' : "플레이어가 준비되지 않았습니다.", 'flag' : False})
        return
    else: emit('noready',{'message' : "플레이어가 준비되었습니다.", 'flag' : True})

@socketio.on('restart')
def on_restart():
    global isEnd, board, restart_votes, dp_h, dp_v, dp_d1, dp_d2, current_turn
    sid = request.sid

    # 플레이어가 1 또는 2인 경우에만 카운트
    if players[sid] in [1, 2]:
        if players[sid] == 1 : restart_votes[0] = True
        if players[sid] == 2 : restart_votes[1] = True
        print(f"플레이어 {players[sid]}가 재시작을 원함 ({restart_votes}/2)")

        # 두 명이 모두 클릭하면 게임 초기화
        if restart_votes[0] and restart_votes[1]:
            print("게임을 다시 시작합니다!")
            isEnd = False
            restart_votes = 0
            board = [[0 for _ in range(BOARD_SIZE+1)] for _ in range(BOARD_SIZE+1)]
            dp_h = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_v = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_d1 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_d2 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            current_turn = 1  # 다시 1번 플레이어부터 시작

            # 클라이언트에게 게임이 리셋되었음을 알림
            emit('reset_game', {'board': board, 'current_turn': current_turn, 'is_end': isEnd}, broadcast=True)

def isWin(x,y):
    # --------------------------------------
    # 승 패 로직
    global isEnd
    # 1. 가로
    left_x = x  # 왼쪽 끝
    while left_x > 0 and board[y][left_x-1] == current_turn:
        left_x -= 1
    right_x = x  # 오른쪽
    while right_x < BOARD_SIZE - 1 and board[y][right_x+1] == current_turn:
        right_x += 1
    dp_h[x][y] = right_x - left_x + 1  # 가로

    # 2. 세로
    top_y = y  # 위쪽 끝
    while top_y > 0 and board[top_y-1][x] == current_turn:
        top_y -= 1
    bottom_y = y  # 아래쪽
    while bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][x] == current_turn:
        bottom_y += 1
    dp_v[x][y] = bottom_y - top_y + 1  # 세로

    # 3. 대각선 ↘ (↖)
    left_x, top_y = x, y  # ↖
    while left_x > 0 and top_y > 0 and board[top_y-1][left_x-1] == current_turn:
        left_x -= 1
        top_y -= 1
    right_x, bottom_y = x, y  # ↘
    while right_x < BOARD_SIZE - 1 and bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][right_x+1] == current_turn:
        right_x += 1
        bottom_y += 1
    dp_d1[x][y] = right_x - left_x + 1  #↘

    # 4. 대각선 ↙ (↗)
    left_x, bottom_y = x, y  # ↙
    while left_x > 0 and bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][left_x-1] == current_turn:
        left_x -= 1
        bottom_y += 1
    right_x, top_y = x, y  # ↗
    while right_x < BOARD_SIZE - 1 and top_y > 0 and board[top_y-1][right_x+1] == current_turn:
        right_x += 1
        top_y -= 1
    dp_d2[x][y] = right_x - left_x + 1  #↙
    
    # 디버깅용..
    print(f"현재 위치: ({x}, {y}), 플레이어 {current_turn}")
    print(f"가로 : {dp_h[x][y]}, 세로 : {dp_v[x][y]}")
    print(f"대각선 ↘: {dp_d1[x][y]}, 대각선 ↙: {dp_d2[x][y]}")

    # 승리 체크
    if dp_h[x][y] >= 5 or dp_v[x][y] >= 5 or dp_d1[x][y] >= 5 or dp_d2[x][y] >= 5:
        isEnd = True
        print(f" 플레이어 {current_turn} 승리! ")
    # --------------------------------------
    
@socketio.on('move')        # socketio 는 서버 측에서
def on_move(data):
    """ data 정보
        'player': 플레이어 번호 (1 또는 2),
        'position': (x, y)  # 보드상의 좌표 (0부터 BOARD_SIZE-1)
    """
    global board, current_turn , players
    sid = request.sid
    player = data.get('player')
    pos = data.get('position')
    if not pos or player is None:
        emit('error', {'message': "잘못된 데이터"})
        return
    
    if len(players) < 2:
        emit('noready',{'message' : "플레이어가 준비되지 않았습니다.", 'flag' : False})
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

    isWin(x,y)

    # 턴 교체: 1->2, 2->1
    if isEnd :
        pass
    else:
        current_turn = 2 if current_turn == 1 else 1

    # 모든 클라이언트에 업데이트된 오목판과 현재 턴 정보를 브로드캐스트
    emit('update', {'board': board, 'current_turn': current_turn, 'is_end' : isEnd}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True) # port = 번호 로 원하는 포트번호로 할당가능!
