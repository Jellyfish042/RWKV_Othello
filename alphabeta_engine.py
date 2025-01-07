import random
from engine import OthelloEngine
from othello import Othello
from formatter import *


class AlphaBetaEngine(OthelloEngine):
    def __init__(self, path, level=5, threads=2):
        super().__init__(path, level, threads)
        self.game = Othello()

    def get_best_move(self, input_moves, max_width=3, max_depth=3, logger_func=None):
        """
        Get the best move given the previous moves.
        Use Alpha-Beta pruning algorithm to search the game tree.
        """

        if not logger_func:
            logger_func = print

        assert max_width in list(range(1, 11)) and max_depth in list(range(1, 11)), "Invalid max_width or max_depth"

        TRACK_MOVES_PROB = 0.0
        track_moves = random.random() < TRACK_MOVES_PROB
        tarch_move_flag = "TRACK_ENABLE\n" if track_moves else ""

        self.game.play_from_start(input_moves)
        root_node_color = self.game.current_player
        possible_moves = self.get_moves(input_moves)
        possible_moves = [x for x in possible_moves if x[0] != "??"]  # sometimes Egaroucid returns '??', very rare, not sure why
        possible_moves = sort_positions(possible_moves, ascending=False)
        pruned_possible_moves = possible_moves[:max_width]  # [(move, score), ...]

        logger_func(
            f"<input>\n{format_board(self.game.board)}\n{format_color(self.game.current_player)}\n{format_args(max_width, max_depth)}\n{tarch_move_flag}</input>\n"
        )
        logger_func("<reasoning>")
        logger_func(f"Possible moves and score:{format_possible_moves(possible_moves)}")

        if not pruned_possible_moves:  # input is an end game state
            logger_func("[No possible moves]")
            logger_func("> Playing ps ")
            logger_func("</reasoning>\n")
            logger_func(f"<output>\n ps \n{format_board(self.game.board)}\n</output>\n")
            return None

        if max_depth == 1 or max_width == 1:
            move, score = pruned_possible_moves[0]
            logger_func(f"> Playing {move} ")
            logger_func("</reasoning>\n")
            self.game.play_from_start(input_moves + move)
            logger_func(f"<output>\n {move} \n{format_board(self.game.board)}\n</output>\n")
            return move

        move, score = pruned_possible_moves.pop(0)
        stack = [
            {
                "move": move,
                "score": score,
                "remaining_moves": pruned_possible_moves,
                "remaining_depth": max_depth,
                "is_max": True,
                "best_move": None,
                "alpha": float("-inf"),
                "beta": float("inf"),
            }
        ]
        logger_func(format_stack(stack))

        total_evaluated_nodes = 0  # only for debugging
        while True:

            node = stack[-1]
            prev_moves = input_moves + "".join([node["move"] for node in stack])
            self.game.play_from_start(prev_moves)
            logger_func("\n=> Search next node")

            # get possible moves from Egaroucid
            possible_moves = self.get_moves(prev_moves)
            possible_moves = [x for x in possible_moves if x[0] != "??"]  # sometimes Egaroucid returns '??', very rare, not sure why
            possible_moves = sort_positions(possible_moves, ascending=False)
            if not self.game.current_player == root_node_color:
                possible_moves = [(move, -score) for move, score in possible_moves]
            pruned_possible_moves = possible_moves[:max_width]

            if len("".join([node["move"] for node in stack])) % 4 == 0:
                current_color_shoud_be = root_node_color
            else:
                current_color_shoud_be = 3 - root_node_color
            color_is_normal = True if self.game.current_player == current_color_shoud_be else False

            if node["remaining_depth"] == 1:
                logger_func("[Depth limit reached - evaluate all leaves]")
            else:
                logger_func("[Depth limit not reached]")
                if track_moves:
                    logger_func(f"Previous moves:{format_input_moves(input_moves + ''.join([node['move'] for node in stack]))}")
                logger_func(f"<board>\n{format_board(self.game.board)}\n</board>\n{format_color(current_color_shoud_be)}")
                if color_is_normal:
                    logger_func(f"Possible moves and score:{format_possible_moves(possible_moves)}")
                else:
                    logger_func(f"Possible moves and score:")
                    logger_func(f"Opponent possible moves and score:{format_possible_moves(possible_moves)}")
                if not pruned_possible_moves:
                    logger_func("[Neither player has legal moves]")
                elif not color_is_normal:
                    logger_func("[Only opponent has legal moves]")
                else:
                    logger_func("[Current player has legal moves]")

            if not pruned_possible_moves or node["remaining_depth"] == 1:  # leaf node, evaluate

                if node["remaining_depth"] == 1:
                    if node["is_max"]:
                        lst = [(node["best_move"], node["alpha"])] + [(node["move"], node["score"])] + node["remaining_moves"]
                        node["best_move"], node["alpha"] = max(lst, key=lambda x: x[1])
                    else:
                        lst = [(node["best_move"], node["beta"])] + [(node["move"], node["score"])] + node["remaining_moves"]
                        node["best_move"], node["beta"] = min(lst, key=lambda x: x[1])
                    node["remaining_moves"] = []
                    node["move"] = None
                    node["score"] = None
                else:
                    logger_func("[Leaf node - evaluate next]")
                    if node["is_max"] and node["score"] > node["alpha"]:
                        node["best_move"] = node["move"]
                        node["alpha"] = node["score"]
                    elif not node["is_max"] and node["score"] < node["beta"]:
                        node["best_move"] = node["move"]
                        node["beta"] = node["score"]
                    node["move"] = None
                    node["score"] = None
                    if node["alpha"] >= node["beta"]:  # pruning
                        node["remaining_moves"] = []
                    if node["remaining_moves"]:
                        node["move"], node["score"] = node["remaining_moves"].pop(0)
                # logger_func(format_stack(stack))
                # logger_func(format_node(node))

                total_evaluated_nodes += 1

                # reslove stack
                for idx in range(len(stack) - 1, 0, -1):
                    son_node = stack[idx]
                    parent_node = stack[idx - 1]
                    if son_node["move"] is not None:  # no need to backtrack
                        break
                    # backtracking, update alpha/beta
                    if parent_node["is_max"]:
                        if son_node["beta"] > parent_node["alpha"]:
                            parent_node["alpha"] = son_node["beta"]
                            parent_node["best_move"] = parent_node["move"]
                    else:
                        if son_node["alpha"] < parent_node["beta"]:
                            parent_node["beta"] = son_node["alpha"]
                            parent_node["best_move"] = parent_node["move"]
                    # pruning
                    parent_node["move"] = None
                    parent_node["score"] = None
                    if parent_node["alpha"] >= parent_node["beta"]:
                        parent_node["remaining_moves"] = []
                    if parent_node["remaining_moves"]:
                        parent_node["move"], parent_node["score"] = parent_node["remaining_moves"].pop(0)
                        break

                logger_func("[Updated stack]")
                logger_func(format_stack(stack))

                for idx in range(len(stack) - 1, 0, -1):
                    if stack[idx]["move"] is not None:
                        break
                    stack.pop()
                # logger_func('[Clean up]')
                # logger_func(format_stack(stack))

                if len(stack) == 1 and not stack[0]["move"]:
                    logger_func("[End of search]")
                    logger_func(f'> Playing {stack[0]["best_move"]} ')
                    logger_func("</reasoning>\n")
                    self.game.play_from_start(input_moves + stack[0]["best_move"])
                    logger_func(f"<output>\n {stack[0]['best_move']} \n{format_board(self.game.board)}\n</output>\n")
                    # print(f'alpha-beta pruning evaluated {total_evaluated_nodes} nodes')
                    return stack[0]["best_move"]

            else:  # internal node, expand
                logger_func("[Internal node - expand]")
                move, score = pruned_possible_moves.pop(0)
                if not color_is_normal:
                    stack.append(
                        {
                            "move": "ps",
                            "score": node["score"],
                            "remaining_moves": [],
                            "remaining_depth": node["remaining_depth"] - 1,
                            "is_max": not node["is_max"],
                            "best_move": None,
                            "alpha": node["alpha"],
                            "beta": node["beta"],
                        }
                    )
                else:
                    stack.append(
                        {
                            "move": move,
                            "score": score,
                            "remaining_moves": pruned_possible_moves,
                            "remaining_depth": node["remaining_depth"] - 1,
                            "is_max": not node["is_max"],
                            "best_move": None,
                            "alpha": node["alpha"],
                            "beta": node["beta"],
                        }
                    )
                logger_func(format_stack(stack))


if __name__ == "__main__":

    LEVEL = 1
    THREADS = 1
    EGAROUCID_PATH = "Egaroucid_for_Console_7_5_1_Windows_SIMD\Egaroucid_for_Console_7_5_1_SIMD.exe"
    
    engine = AlphaBetaEngine(EGAROUCID_PATH, level=LEVEL, threads=THREADS,)

    best_move = engine.get_best_move("d3c5")

    print(f"### Best move: {best_move}")

    engine.cleanup()
