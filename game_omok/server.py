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
restart_votes = [False, False]

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
            restart_votes[0] = False
            restart_votes[1] = False
            isEnd = False
            board = [[0 for _ in range(BOARD_SIZE+1)] for _ in range(BOARD_SIZE+1)]
            dp_h = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_v = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_d1 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            dp_d2 = [[0] * (BOARD_SIZE+1) for _ in range(BOARD_SIZE+1)]
            current_turn = 1  # 다시 1번 플레이어부터 시작

            # 클라이언트에게 게임이 리셋되었음을 알림
            emit('reset_game', {'board': board, 'current_turn': current_turn, 'is_end': isEnd}, broadcast=True)
    
@socketio.on('move')
def on_move(data):
    global board, current_turn, players, isEnd, dp_h, dp_v, dp_d1, dp_d2

    sid = request.sid
    player = data.get('player')
    pos = data.get('position')

    if not pos or player is None:
        emit('error', {'message': "잘못된 데이터"})
        return
    
    if len(players) < 2:
        emit('noready', {'message': "플레이어가 준비되지 않았습니다.", 'flag': False})
        return

    x, y = pos

    if players.get(sid) != current_turn:
        emit('error', {'message': "지금은 상대 턴입니다."})
        return

    if board[y][x] != 0:
        emit('error', {'message': "해당 위치는 이미 사용 중입니다."})
        return

    # ------------- 백업 (돌을 놓기 전 상태 저장) -------------
    prev_dp_h, prev_dp_v, prev_dp_d1, prev_dp_d2 = dp_h[x][y], dp_v[x][y], dp_d1[x][y], dp_d2[x][y]

    # ------------- 승 패 로직 (DP 업데이트) -------------
    left_x = x
    while left_x > 0 and board[y][left_x-1] == current_turn:
        left_x -= 1
    right_x = x
    while right_x < BOARD_SIZE - 1 and board[y][right_x+1] == current_turn:
        right_x += 1
    dp_h[x][y] = right_x - left_x + 1  # 가로

    top_y = y
    while top_y > 0 and board[top_y-1][x] == current_turn:
        top_y -= 1
    bottom_y = y
    while bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][x] == current_turn:
        bottom_y += 1
    dp_v[x][y] = bottom_y - top_y + 1  # 세로

    left_x, top_y = x, y
    while left_x > 0 and top_y > 0 and board[top_y-1][left_x-1] == current_turn:
        left_x -= 1
        top_y -= 1
    right_x, bottom_y = x, y
    while right_x < BOARD_SIZE - 1 and bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][right_x+1] == current_turn:
        right_x += 1
        bottom_y += 1
    dp_d1[x][y] = right_x - left_x + 1  # ↘

    left_x, bottom_y = x, y
    while left_x > 0 and bottom_y < BOARD_SIZE - 1 and board[bottom_y+1][left_x-1] == current_turn:
        left_x -= 1
        bottom_y += 1
    right_x, top_y = x, y
    while right_x < BOARD_SIZE - 1 and top_y > 0 and board[top_y-1][right_x+1] == current_turn:
        right_x += 1
        top_y -= 1
    dp_d2[x][y] = right_x - left_x + 1  # ↙

    # ------------- 33 체크 (금수) -------------
    ttcount = 0
    if dp_h[x][y] == 3: ttcount += 1
    if dp_v[x][y] == 3: ttcount += 1
    if dp_d1[x][y] == 3: ttcount += 1
    if dp_d2[x][y] == 3: ttcount += 1
    

    if ttcount >= 2:  # 삼삼(33) 체크
        # 원래 값으로 복원
        dp_h[x][y], dp_v[x][y], dp_d1[x][y], dp_d2[x][y] = prev_dp_h, prev_dp_v, prev_dp_d1, prev_dp_d2
        emit('error', {'message': '삼삼(33) 금수로 인해 착수할 수 없습니다!'})
        return
    else : emit('error', {'message' : '화면지우기~'})

    # ------------- 돌을 놓기 & 승리 체크 -------------
    board[y][x] = current_turn

    if dp_h[x][y] >= 5 or dp_v[x][y] >= 5 or dp_d1[x][y] >= 5 or dp_d2[x][y] >= 5:
        isEnd = True
        print(f"플레이어 {current_turn} 승리!")

    # 턴 교체
    if not isEnd:
        current_turn = 2 if current_turn == 1 else 1

    emit('update', {'board': board, 'current_turn': current_turn, 'is_end': isEnd}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0', debug=True) # port = 번호 로 원하는 포트번호로 할당가능!
