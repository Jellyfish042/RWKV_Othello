import copy


class Othello:
    def __init__(self):

        self.board = [[0] * 8 for _ in range(8)]
        self.board[3][3] = self.board[4][4] = 2  # white
        self.board[3][4] = self.board[4][3] = 1  # black

        self.current_player = 1  # techincally is "current color"
        self.moves = ""

    def reset(self):
        self.board = [[0] * 8 for _ in range(8)]
        self.board[3][3] = self.board[4][4] = 2
        self.board[3][4] = self.board[4][3] = 1
        self.current_player = 1
        self.moves = ""

    def _convert_position(self, pos):
        if len(pos) != 2:
            return None
        col = ord(pos[0].lower()) - ord("a")
        row = int(pos[1]) - 1
        if not (0 <= row < 8 and 0 <= col < 8):
            return None
        return row, col

    def _get_flips(self, row, col):
        if self.board[row][col] != 0:
            return []

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        opponent = 3 - self.current_player
        flips = []

        for dx, dy in directions:
            temp_flips = []
            x, y = row + dx, col + dy

            while 0 <= x < 8 and 0 <= y < 8 and self.board[x][y] == opponent:
                temp_flips.append((x, y))
                x += dx
                y += dy

            if temp_flips and 0 <= x < 8 and 0 <= y < 8 and self.board[x][y] == self.current_player:
                flips.extend(temp_flips)

        return flips

    def has_valid_moves(self, player):
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == 0 and self._get_flips(row, col, player):
                    return True
        return False

    def get_legal_moves(self):
        legal_moves = []
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == 0 and self._get_flips(row, col):
                    legal_moves.append(f"{chr(col + 97)}{row + 1}")
        return legal_moves

    def play(self, moves: str):
        # moves: f5D6 format string
        moves = moves.lower()
        original_board = copy.deepcopy(self.board)
        moves_lst = [moves[i : i + 2] for i in range(0, len(moves), 2)]

        for move in moves_lst:
            pos = self._convert_position(move)
            if not pos:
                return False

            row, col = pos
            flips = self._get_flips(row, col)

            if not flips:
                self.board = original_board
                return False

            self.board[row][col] = self.current_player
            for flip_row, flip_col in flips:
                self.board[flip_row][flip_col] = self.current_player

            self.current_player = 3 - self.current_player
            has_valid_move = False
            for r in range(8):
                for c in range(8):
                    if self._get_flips(r, c):
                        has_valid_move = True
                        break
                if has_valid_move:
                    break

            if not has_valid_move:
                self.current_player = 3 - self.current_player

        self.moves += moves
        return True

    def play_from_start(self, moves: str):
        moves = moves.replace("ps", "")
        self.reset()
        return self.play(moves)

    def get_moves(self):
        return self.moves

    def get_board_format(self):
        symbols = {0: "-", 1: "X", 2: "O"}
        current_player = " X" if self.current_player == 1 else " O"
        return "".join(symbols[self.board[row][col]] for row in range(8) for col in range(8)) + current_player

    def is_game_over(self):
        info = {
            "black": sum(row.count(1) for row in self.board),
            "white": sum(row.count(2) for row in self.board),
        }
        temp = self.current_player
        for player in [1, 2]:
            self.current_player = player
            for row in range(8):
                for col in range(8):
                    if self._get_flips(row, col):
                        self.current_player = temp
                        return False, info
        self.current_player = temp
        if info["black"] > info["white"]:
            info["winner"] = "black"
        elif info["black"] < info["white"]:
            info["winner"] = "white"
        else:
            info["winner"] = "draw"

        return True, info

    def print_board(self):
        symbols = {0: "-", 1: "X", 2: "O"}
        print("  a b c d e f g h")
        for row in range(8):
            print(row + 1, end=" ")
            for col in range(8):
                print(symbols[self.board[row][col]], end=" ")
            print()


if __name__ == "__main__":
    othello = Othello()
    othello.play_from_start("f5d6c4d3c2b3b4b5c5e2")
    print(othello.get_legal_moves())
