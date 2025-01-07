from ast import literal_eval


def format_board(board):
    """
    Format the board to a human-readable string.
    0 = empty (·)
    1 = black (●)
    2 = white (○)
    """
    symbols = {0: "·", 1: "●", 2: "○"}

    rows = []
    for row in board:
        row_str = " ".join(symbols[cell] for cell in row)
        rows.append(row_str + " ")

    return "\n".join(rows)


def format_score(score):
    """
    Format an integer score with proper sign and padding.
    Examples:
        5 -> "+05"
        -3 -> "-03"
        21 -> "+21"
        -15 -> "-15"
        0 -> "+00"
    """
    if score == float("inf"):
        return "+in"
    if score == float("-inf"):
        return "-in"
    score_int = int(score)
    abs_score = abs(score_int)
    if abs_score < 10:
        return f"+0{abs_score}" if score_int >= 0 else f"-0{abs_score}"
    else:
        return f"+{score_int}" if score_int >= 0 else str(score_int)


def format_possible_moves(moves_list, sep=" "):
    if not moves_list:
        return ""

    if isinstance(moves_list, str):
        moves_list = literal_eval(moves_list)

    def position_to_value(pos):
        col = ord(pos[0]) - ord("a")
        row = int(pos[1])
        return row * 10 + col

    sorted_moves = sorted(moves_list, key=lambda x: position_to_value(x[0]))

    formatted_lines = []
    for pos, score in sorted_moves:
        formatted_lines.append(f"{pos:2s} {format_score(score)}")

    return " " + sep.join(formatted_lines)


def format_possible_moves_no_sort(moves_list, sep=" "):
    if not moves_list:
        return ""

    if isinstance(moves_list, str):
        moves_list = literal_eval(moves_list)

    formatted_lines = []
    for pos, score in moves_list:
        formatted_lines.append(f"{pos:2s} {format_score(score)}")

    return " " + sep.join(formatted_lines)


def format_args(max_width, max_depth):
    return f"MAX_WIDTH-{max_width}\nMAX_DEPTH-{max_depth}"


def format_color(color):
    return "NEXT " + {1: "● ", 2: "○ "}[color]


def format_stack(stack):
    formatted_lines = []
    for node in stack:
        move = node["move"] if node["move"] else "--"
        score = format_score(node["score"]) if node["score"] is not None else "---"
        remaining_moves = format_possible_moves_no_sort(node["remaining_moves"], sep=" ")
        remaining_depth = "Remaining_Depth:" + str(node["remaining_depth"])
        is_max = "Max_Node" if node["is_max"] else "Min_Node"
        best_move = "--" if not node["best_move"] else node["best_move"]
        alpha = format_score(node["alpha"])
        beta = format_score(node["beta"])

        # formatted_lines.append(
        #     f"{is_max} {remaining_depth} Alpha: {alpha} Beta: {beta} Best: {best_move} Current: {move} {score} Unexplored: {remaining_moves}"
        # )
        formatted_lines.append(
            f"{is_max} Alpha: {alpha} Beta: {beta} Best: {best_move} Current: {move} {score} Unexplored:{remaining_moves}"
        )

    # filp
    formatted_lines = formatted_lines[::-1]

    # return "<stack>\n" + "\n".join(formatted_lines) + "\n</stack>"

    depth_info = "Remaining_Depth:" + str(stack[-1]["remaining_depth"]) + "\n"
    return "<stack>\n" + depth_info + "\n".join(formatted_lines) + "\n</stack>"


def format_node(node):
    move = node["move"] if node["move"] else "--"
    score = format_score(node["score"]) if node["score"] is not None else "---"
    remaining_moves = format_possible_moves_no_sort(node["remaining_moves"], sep=" ")
    remaining_depth = "Remaining_Depth:" + str(node["remaining_depth"])
    is_max = "Max_Node" if node["is_max"] else "Min_Node"
    best_move = "--" if not node["best_move"] else node["best_move"]
    alpha = format_score(node["alpha"])
    beta = format_score(node["beta"])

    return f"<node>\n{is_max} {remaining_depth} Alpha: {alpha} Beta: {beta} Best: {best_move} Current: {move} {score} Unexplored: {remaining_moves}\n</node>"


def sort_positions(positions, ascending=True):
    try:

        def get_position_value(pos):
            col = ord(pos[0]) - ord("a")
            row = int(pos[1]) - 1
            return row * 8 + col

        def sort_key(item):
            pos, score = item
            score_key = score if ascending else -score
            return (score_key, get_position_value(pos))

        return sorted(positions, key=sort_key)
    except Exception as e:
        print(e)
        print(positions)
        raise e


def format_input_moves(input_str):
    if not input_str:
        return ""
        
    if len(input_str) % 2 != 0:
        raise ValueError("Input string must have an even number of characters")
        
    pairs = [input_str[i:i+2] for i in range(0, len(input_str), 2)]
    formatted = "  ".join(pairs)
    
    return f" {formatted} "