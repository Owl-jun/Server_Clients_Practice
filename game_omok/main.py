# client.py
import pygame
import socketio

# SocketIO 클라이언트 초기화
sio = socketio.Client()

# 전역 변수: 오목판 상태, 현재 턴, 할당받은 플레이어 번호
board = []
current_turn = 1
player_number = None
flag = False
isEnd = False
# 오목판 및 창 설정
READY = False
BOARD_SIZE = 15
CELL_SIZE = 40
MARGIN = 20
WINDOW_SIZE = BOARD_SIZE * CELL_SIZE + 2 * MARGIN


# ------------------------------------------
## socketio 라이브러리 사용 시 기본적인 이벤트 핸들링 기법
@sio.event
def connect():
    print("서버에 연결됨")

@sio.event
def disconnect():
    print("서버와 연결 종료됨")
# ------------------------------------------

# 에러 디버깅용
@sio.on('error')
def on_error(data):
    print(data.get('message'))

@sio.on('reset_game')
def on_reset_game(data):
    global board, current_turn, isEnd
    board = data.get('board')
    current_turn = data.get('current_turn')
    isEnd = data.get('is_end')
    print("게임이 다시 시작되었습니다!")

@sio.on('assign_player')        # sio 는 클라이언트 측에서
def on_assign_player(data):
    global player_number
    player_number = data.get('player')
    if player_number == 0:
        print("관전자 모드입니다.")
    else:
        print(f"당신은 플레이어 {player_number} 입니다.")

@sio.on('update')
def on_update(data):
    global board, current_turn , isEnd
    board = data.get('board')
    current_turn = data.get('current_turn')
    isEnd = data.get('is_end')
    print("서버로부터 업데이트를 받았습니다.")

@sio.on('noready')
def on_noready(data):
    global flag
    message = data.get('message')
    flag = data.get('flag')
    print(message)
    
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
    pygame.display.set_caption("오목")
    clock = pygame.time.Clock()

    # 서버에 연결 (포트 5000번은 디폴트값임)
    sio.connect('http://localhost:5000', wait_timeout = 10) # 연결오류가 계속 났는데 wait_timeout 이 나를 살렸다..

    global flag # 게임 준비완료 flag
    # 초기 오목판 설정 (서버에서 업데이트가 오기 전까지 사용)
    global board
    if not board:
        board = [[0 for _ in range(BOARD_SIZE+1)] for _ in range(BOARD_SIZE+1)]

    # 텍스트 설정
    textFont = pygame.font.SysFont("malgun gothic",36)
    text_surface = textFont.render('상대 플레이어를 기다리는 중입니다.', True, (0,0,0),'white')
    turn_surface = textFont.render('당신의 턴 입니다.', True, (0,0,0))
    noturn_surface = textFont.render('상대방의 턴 입니다.', True, (0,0,0))
    win_surface = textFont.render('승리! 다시하려면 클릭',True,(0,0,0))
    lose_surface = textFont.render('패배! 다시하려면 클릭',True,(0,0,0))
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if isEnd and event.type == pygame.MOUSEBUTTONDOWN:
                sio.emit('restart')
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # 보드의 격자 좌표로 변환
                x = (mouse_x - MARGIN + CELL_SIZE//2) // CELL_SIZE
                y = (mouse_y - MARGIN + CELL_SIZE//2) // CELL_SIZE
                if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                    # 현재 플레이어 번호와 좌표를 서버로 전송
                    sio.emit('move', {'player': player_number, 'position': (x, y)})

                    
        # 화면 그리기
        screen.fill((255, 255, 255))  # 배경 흰색

        if isEnd and current_turn == player_number:
            screen.blit(win_surface,((WINDOW_SIZE//2)-150,WINDOW_SIZE//2))
        elif isEnd:
            screen.blit(lose_surface,((WINDOW_SIZE//2)-150,WINDOW_SIZE//2))

        # 플레이어 입장 대기
        if not flag:
            screen.blit(text_surface,(35,150))
            sio.emit('start')

        if flag and isEnd == False:
            # 격자선 그리기
            for i in range(BOARD_SIZE+1):
                # 수직선
                start_pos = (MARGIN + i * CELL_SIZE, MARGIN)
                end_pos = (MARGIN + i * CELL_SIZE, WINDOW_SIZE - MARGIN)
                pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 1)
                # 수평선
                start_pos = (MARGIN, MARGIN + i * CELL_SIZE)
                end_pos = (WINDOW_SIZE - MARGIN, MARGIN + i * CELL_SIZE)
                pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 1)


            # 오목판에 돌 그리기
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    stone = board[row][col]
                    if stone == 1 or stone == 2:
                        # 플레이어 1: 검은 돌, 플레이어 2: 흰 돌
                        color = (0, 0, 0) if stone == 1 else (255, 255, 255)
                        center = (MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE)
                        pygame.draw.circle(screen, color, center, CELL_SIZE // 2 - 2)
                        # 흰 돌일 경우 테두리 그리기
                        if stone == 2:
                            pygame.draw.circle(screen, (0, 0, 0), center, CELL_SIZE // 2 - 2, 1)

            # 턴 알려주는 UI
            if player_number == current_turn:
                screen.blit(turn_surface, (50, WINDOW_SIZE))
            else:
                screen.blit(noturn_surface, (50, WINDOW_SIZE))

        pygame.display.flip()
        clock.tick(30)

    sio.disconnect()
    pygame.quit()

if __name__ == '__main__':
    main()
