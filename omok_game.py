BOARD_SIZE = 15
EMPTY = "."
BLACK = "B"
WHITE = "W"


def create_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def print_board(board):
    print("   " + " ".join(f"{i+1:2}" for i in range(BOARD_SIZE)))
    for y, row in enumerate(board):
        print(f"{y+1:2} " + " ".join(f" {cell}" for cell in row))


def in_bounds(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def check_five(board, x, y, stone):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dx, dy in directions:
        count = 1
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny) and board[ny][nx] == stone:
            count += 1
            nx += dx
            ny += dy

        nx, ny = x - dx, y - dy
        while in_bounds(nx, ny) and board[ny][nx] == stone:
            count += 1
            nx -= dx
            ny -= dy

        if count >= 5:
            return True
    return False


def get_move(player):
    while True:
        try:
            raw = input(f"{player} 좌표 입력 (예: 8 8): ").strip()
            x_str, y_str = raw.split()
            x, y = int(x_str) - 1, int(y_str) - 1
            return x, y
        except ValueError:
            print("입력이 올바르지 않습니다. 숫자 2개를 입력하세요.")


def main():
    board = create_board()
    turn = BLACK
    stones_played = 0

    while True:
        print_board(board)
        x, y = get_move("흑(B)" if turn == BLACK else "백(W)")

        if not in_bounds(x, y):
            print("범위를 벗어났습니다.")
            continue
        if board[y][x] != EMPTY:
            print("이미 돌이 놓인 자리입니다.")
            continue

        board[y][x] = turn
        stones_played += 1

        if check_five(board, x, y, turn):
            print_board(board)
            print(f"{turn} 승리!")
            break

        if stones_played == BOARD_SIZE * BOARD_SIZE:
            print_board(board)
            print("무승부!")
            break

        turn = WHITE if turn == BLACK else BLACK


if __name__ == "__main__":
    main()
