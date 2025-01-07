import os
import random
from logger import DataLogger
from alphabeta_engine import AlphaBetaEngine
import json
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from typing import List
from tqdm import tqdm


class OthelloGeneratorPool:
    def __init__(self, engine_class, engine_path: str, level: int, threads: int, pool_size: int, save_path: str):
        if os.path.exists(save_path):
            if input(f"File {save_path} already exists. Overwrite? (y/n): ").lower() == "y":
                os.remove(save_path)
            else:
                exit(0)
        self.save_path = save_path
        self.generators = [OthelloGenerator(engine_class, engine_path, level, threads) for _ in range(pool_size)]
        self.generator_queue = Queue()
        for gen in self.generators:
            self.generator_queue.put(gen)
        self.pool = ThreadPoolExecutor(max_workers=pool_size)

    def _stream_save_result(self, result):
        with open(self.save_path, "a", encoding="utf-8") as f:
            json_line = json.dumps({"text": result}, ensure_ascii=False)
            f.write(json_line + "\n")

    def _generate_sample(self, input_moves: str, max_width: int, max_depth: int) -> str:
        # print(input_moves)
        generator = self.generator_queue.get()
        try:
            result = generator.gen_one_sample(input_moves, max_width, max_depth)
            return result
        finally:
            self.generator_queue.put(generator)

    def generate_samples_parallel(self, inputs: List[tuple[str, int, int]], timeout: int = 120, batch_size: int = 1000):
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i : i + batch_size]
            # print(batch)
            futures = [self.pool.submit(self._generate_sample, moves, width, depth) for moves, width, depth in batch]

            for f in tqdm(futures, total=len(futures), desc=f"Generating batch {i//batch_size + 1}"):
                result = f.result(timeout=timeout)
                self._stream_save_result(result)

    def __del__(self):
        self.pool.shutdown()


class OthelloGenerator:
    def __init__(self, engine_class, engine_path, level, threads):
        self.engine = engine_class(engine_path, level, threads)
        self.logger = DataLogger(print_to_console=False)

    def gen_one_sample(self, input_moves, max_width, max_depth):
        self.logger.clear()
        self.engine.get_best_move(input_moves, max_width, max_depth, logger_func=self.logger.log_func)
        return self.logger.log


def read_all_txt_files(folder_path):
    all_lines = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r") as f:
                all_lines.extend(f.readlines())
    return all_lines


# def sample_game_states(games, sample_per_game):
#     sampled_states = []

#     for game in games:
#         possible_lengths = list(range(0, len(game) + 1, 2))
#         n = min(sample_per_game, len(possible_lengths))
#         selected_lengths = sorted(random.sample(possible_lengths, n))
#         game_samples = [game[:length] for length in selected_lengths]
#         sampled_states.extend(game_samples)

#     return sampled_states


def sample_game_states(games, sample_per_game, length_weight=0, min_prob=0.01):
    sampled_states = []

    for game in games:
        possible_lengths = list(range(0, len(game) + 1, 2))
        n = min(sample_per_game, len(possible_lengths))

        total_lengths = len(possible_lengths)
        base_weights = [1.0] * total_lengths
        length_weights = [i / (total_lengths - 1) for i in range(total_lengths)]

        weights = [(1 - length_weight) * bw + length_weight * lw for bw, lw in zip(base_weights, length_weights)]

        min_weight = min(weights)
        if min_weight < min_prob:
            weights = [w + (min_prob - min_weight) for w in weights]

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        selected_lengths = sorted(random.choices(population=possible_lengths, weights=normalized_weights, k=n))

        game_samples = [game[:length] for length in selected_lengths]
        # print("\n".join(game_samples))
        sampled_states.extend(game_samples)

    return sampled_states


def parallel_generate(
    engine_path,
    engine_level,
    engine_threads,
    game_path,
    sample_per_game,
    output_file,
    num_generators,
    search_tree_settings,
    start=0,
    end=None,
    length_weight=1.0,
):

    games = read_all_txt_files(game_path)
    print(f"Loaded {len(games)} games, {sample_per_game} samples per game.")
    games = games[start:end]
    print(f"Selected {len(games)} games from {start} to {end}.")
    input_moves = sample_game_states(games, sample_per_game, length_weight)
    print(f"Sampled {len(input_moves)} states.")

    input_moves = [(move, *random.choice(search_tree_settings)) for move in input_moves]

    generator_pool = OthelloGeneratorPool(
        AlphaBetaEngine,
        engine_path,
        level=engine_level,
        threads=engine_threads,
        pool_size=num_generators,
        save_path=output_file,
    )

    generator_pool.generate_samples_parallel(input_moves)


def power_pairs(limit, max_x=10, max_y=10):
    return [(x, y) for x in range(1, max_x + 1) for y in range(1, max_y + 1) if pow(x, y) < limit]


if __name__ == "__main__":
    ENGINE_PATH = "Egaroucid_for_Console_7_5_1_Windows_SIMD\Egaroucid_for_Console_7_5_1_SIMD.exe"
    GAME_LOGS_PATH = "./0000_egaroucid_6_3_0_lv11"
    SAMPLE_PER_GAME = 1
    ENGINE_LEVEL = 5
    ENGINE_THREADS = 12
    NUM_GENERATORS = 10
    RANDOM_SEED = 42
    LENGTH_WEIGHT = 0.9  # higher value means more samples from the end of the games. 0.0 means uniform distribution.

    # generate all possible pairs of which node count is less than x.
    MAX_NODE_COUNT = 100
    SEARCH_TREE_SETTINGS = power_pairs(MAX_NODE_COUNT, 10, 10)  # [(width, depth), ...]
    print(f"Search tree settings: {SEARCH_TREE_SETTINGS}")

    START = 0
    END = 1000

    OUTPUT_FILE = f"data/DEMO_lv{ENGINE_LEVEL}_s{START}_e{END}_p{SAMPLE_PER_GAME}_node{MAX_NODE_COUNT}_seed{RANDOM_SEED}_weight{LENGTH_WEIGHT}.jsonl"

    random.seed(RANDOM_SEED)

    parallel_generate(
        ENGINE_PATH,
        ENGINE_LEVEL,
        ENGINE_THREADS,
        GAME_LOGS_PATH,
        SAMPLE_PER_GAME,
        OUTPUT_FILE,
        NUM_GENERATORS,
        SEARCH_TREE_SETTINGS,
        START,
        END,
        LENGTH_WEIGHT,
    )
