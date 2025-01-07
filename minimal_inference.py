import os

os.environ["RWKV_JIT_ON"] = "1"
os.environ["RWKV_CUDA_ON"] = "0"
os.environ["RWKV_V7_ON"] = "1"

from rwkv.model import RWKV
from rwkv.rwkv_tokenizer import TRIE_TOKENIZER
from rwkv.utils import PIPELINE, PIPELINE_ARGS

MODEL_PATH = 'models/rwkv7_othello_26m_L10_D448_extended'

if 'extended' in MODEL_PATH:
    print("Using extended eigenvalue model")
    from rwkv_extended import RWKV
else:
    from rwkv.model import RWKV
model = RWKV(model=MODEL_PATH, strategy="cpu fp32")
pipeline = PIPELINE(model, "rwkv_vocab_v20230424")
pipeline.tokenizer = TRIE_TOKENIZER("othello_vocab.txt")
gen_args = PIPELINE_ARGS(top_k=1, alpha_frequency=0, alpha_presence=0, token_stop=[0])

# black (●) white (○) empty (·)
input_str = """<input>
● ● ● ● ● ● ● ● 
● · ○ ○ ● ● ● ○ 
● ○ ○ ○ ○ ● ● ○ 
● ○ ○ ○ ○ ● ● ● 
● ○ ○ ○ ○ ● ● ● 
● ○ ○ ○ ○ ● ● ● 
● · · · · ● ● ● 
● · · ○ ○ ○ ○ ○ 
NEXT ● 
MAX_WIDTH-2
MAX_DEPTH-2
</input>

"""

print(f'{" Model input ":-^100}\n{input_str}\n{" Model output ":-^100}')
solution = pipeline.generate(input_str, token_count=64000, args=gen_args, callback=lambda x: print(x, end="", flush=True))
