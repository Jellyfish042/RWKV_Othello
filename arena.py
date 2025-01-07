from engine import OthelloEngine
from othello import Othello
from tqdm import tqdm
import time


class OthelloArena:
    def __init__(self, player1, player2, opening_book=None):
        if opening_book:
            with open(opening_book, "r", encoding="utf-8") as f:
                self.opening_book = f.readlines()
        self.opening_book = [x.strip() for x in self.opening_book]
        print(f"Loaded {len(self.opening_book)} openings.")
        self.player1 = player1
        self.player2 = player2

        self.game = Othello()

    def get_move_from_player(self, player, prev_moves):
        assert player in ["player1", "player2"]
        if player == "player1":
            move = self.player1.get_best_move(prev_moves)
        else:
            move = self.player2.get_best_move(prev_moves)
        return move

    def play_one(self, player1_color, opening=None):

        assert player1_color in ["black", "white"]
        player2_color = "black" if player1_color == "white" else "white"

        self.game.reset()
        if opening:
            self.game.play(opening)

        role_mapping = {
            player1_color: "player1",
            player2_color: "player2",
        }

        while True:
            game_over, game_info = self.game.is_game_over()
            if game_over:
                winner_color = game_info["winner"]
                winner = role_mapping[winner_color] if winner_color in role_mapping else "draw"
                return {
                    "winner": winner,
                    "winner_color": winner_color,
                    "black": game_info["black"],
                    "white": game_info["white"],
                }

            current_color = "black" if self.game.current_player == 1 else "white"
            current_player = role_mapping[current_color]

            prev_moves = self.game.get_moves()

            move = self.get_move_from_player(current_player, prev_moves)

            if move not in self.game.get_legal_moves():
                print(f"Invalid move: {current_player} {move}")
                print(self.game.get_board_format())
                game_over, game_info = self.game.is_game_over()
                return {
                    "winner": "player1" if current_player == "player2" else "player2",
                    "winner_color": player1_color if current_player == "player2" else player2_color,
                    "black": game_info["black"],
                    "white": game_info["white"],
                }

            self.game.play(move)

            # print("-" * 100)
            # self.game.print_board()

    def evaluate(self):
        statistics = {
            "player1_win": 0,
            "player2_win": 0,
            "draw": 0,
        }
        for opening in tqdm(self.opening_book):

            game_info = self.play_one("black", opening)
            if game_info["winner"] == "player1":
                statistics["player1_win"] += 1
            elif game_info["winner"] == "player2":
                statistics["player2_win"] += 1
            else:
                statistics["draw"] += 1

            game_info = self.play_one("white", opening)
            if game_info["winner"] == "player1":
                statistics["player1_win"] += 1
            elif game_info["winner"] == "player2":
                statistics["player2_win"] += 1
            else:
                statistics["draw"] += 1

        return statistics


if __name__ == "__main__":

    from rwkv_engine import RWKVEngine
    
    # model_path, vaersion = 'models/rwkv7_othello_26m_L10_D448', 'v7
    model_path, version = 'models/rwkv7_othello_26m_L10_D448_extended', 'v7_ee'
    
    player1 = RWKVEngine(model_path, print_output=True, max_depth=1, max_width=1, rwkv_version=version)
    
    player2_depth, player2_width = 2, 2
    player2 = RWKVEngine(model_path, print_output=True, max_depth=player2_depth, max_width=player2_width, rwkv_version=version)

    arena = OthelloArena(player1, player2, "opening_mini.txt")

    statistics = arena.evaluate()
    print(statistics)
    print(f'Player1 tokens:{player1.get_avg_tokens()} Player2 tokens:{player2.get_avg_tokens()}')

    try:
        player1.cleanup()
    except:
        pass
    try:
        player2.cleanup()
    except:
        pass
