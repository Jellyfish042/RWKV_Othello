import os

os.environ["RWKV_JIT_ON"] = "1"
os.environ["RWKV_CUDA_ON"] = "0"
os.environ["RWKV_V7_ON"] = "1"

from rwkv.rwkv_tokenizer import TRIE_TOKENIZER
from rwkv.utils import PIPELINE, PIPELINE_ARGS
from othello import Othello
from formatter import *


class RWKVEngine:
    def __init__(self, path, print_output=False, max_width=1, max_depth=1, rwkv_version=None):
        assert max_width in list(range(1, 11)) and max_depth in list(range(1, 11)), "Invalid max_width or max_depth"
        self.max_width = max_width
        self.max_depth = max_depth
        if rwkv_version == 'v7':
            from rwkv.model import RWKV
            self.model = RWKV(model=path, strategy="cuda fp16")
        elif rwkv_version == 'v7_ee':
            from rwkv_extended import RWKV
            self.model = RWKV(model=path, strategy="cuda fp16")
        else:
            raise ValueError("Invalid rwkv_version")
        self.pipeline = PIPELINE(self.model, "rwkv_vocab_v20230424")
        self.pipeline.tokenizer = TRIE_TOKENIZER("othello_vocab.txt")
        self.gen_args = PIPELINE_ARGS(top_k=1, alpha_frequency=0, alpha_presence=0, token_stop=[0])
        self.game = Othello()
        self.print_output = print_output
        self.leagal_moves = [f'{x}{y}' for x in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] for y in range(1, 9)]
        
        self.token_counts = 0
        self.gen_counts = 0
        
    def callback(self, x):
        if self.print_output:
            print(x, end='', flush=True)
        self.token_counts += 1
        
    def clear_counts(self):
        self.token_counts = 0
        self.gen_counts = 0
        
    def get_avg_tokens(self):
        if self.gen_counts == 0:
            return 0
        return self.token_counts / self.gen_counts
        

    def get_best_move(self, input_moves, max_token_count=1000000):
        self.game.play_from_start(input_moves)
        input_str = (
            f"<input>\n{format_board(self.game.board)}\n{format_color(self.game.current_player)}\n{format_args(self.max_width, self.max_depth)}\n</input>\n\n"
        )
        if self.print_output:
            print(f'{" Model input ":-^100}\n{input_str}\n{" Model output ":-^100}')
        self.gen_counts += 1
        result = self.pipeline.generate(input_str, token_count=max_token_count, args=self.gen_args, callback=self.callback)
            
        result = result.split('<output>')[-1].strip()
        result = result.split('\n')[0].strip()
        result = result if result in self.leagal_moves else 'er'
            
        return result


if __name__ == "__main__":

    MODEL_PATH = "models/rwkv7_othello_9m_L10_D256_extended"

    rwkv_engine = RWKVEngine(MODEL_PATH, print_output=False, rwkv_version='v7_ee')
    result = rwkv_engine.get_best_move('')
    print(result)