from formatter import *


MODEL_PATH = "models/rwkv7_othello_26m_L10_D448_extended"


class OthelloAI:
    def __init__(self, model_path=MODEL_PATH):
        import os

        os.environ["RWKV_JIT_ON"] = "1"
        os.environ["RWKV_CUDA_ON"] = "0"
        os.environ["RWKV_V7_ON"] = "1"

        if 'extended' in model_path:
            print(f"Using extended eigenvalue model: {model_path}")
            from rwkv_extended import RWKV
        else:
            from rwkv.model import RWKV
        from rwkv.rwkv_tokenizer import TRIE_TOKENIZER
        from rwkv.utils import PIPELINE, PIPELINE_ARGS
        
        # self.model = RWKV(model=model_path, strategy="cuda fp16")
        self.model = RWKV(model=model_path, strategy="cpu fp32")
        self.pipeline = PIPELINE(self.model, "rwkv_vocab_v20230424")
        self.pipeline.tokenizer = TRIE_TOKENIZER("othello_vocab.txt")
        self.gen_args = PIPELINE_ARGS(top_k=1, alpha_frequency=0, alpha_presence=0, token_stop=[0])
        self.callback = None
        self.token_count = 0

    def callback_wrapper(self, model_output: str):
        self.token_count += 1
        self.callback({"type": "reasoning", "text": model_output, "token_count": self.token_count})
        # print(model_output, end="", flush=True)

    def think(self, board_state, current_player, move_count, callback, search_config):

        self.thinking = True
        self.callback = callback

        # print(search_config)
        if search_config['top_p'] == 0:
            self.gen_args.top_p = 0
            self.gen_args.top_k = 1
        else:
            self.gen_args.top_p = search_config['top_p']
            self.gen_args.top_k = 0
        input_str = f"<input>\n{format_board(board_state)}\n{format_color(current_player)}\n{format_args(search_config['breadth'], search_config['depth'])}\n</input>\n\n"
        # print(input_str)
        callback({"type": "reasoning", "text": input_str, "token_count": self.token_count})

        result_str = self.pipeline.generate(input_str, token_count=5000000, args=self.gen_args, callback=self.callback_wrapper)

        self.token_count = 0

        move = result_str.split("<output>")[-1].strip()
        move = move.split("\n")[0].strip()

        if search_config["depth"] == 1 or search_config["breadth"] == 1:
            score = int(result_str.split(move)[1][1:4])
        else:
            score = int(result_str.split("Alpha")[-1][2:5])
        print(f"AI move: {move}, score: {score}")

        callback(
            {
                "type": "evaluation",
                "player": current_player,
                "score": score,
            }
        )

        self.thinking = False
        return move
