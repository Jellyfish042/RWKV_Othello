import subprocess
import platform
import warnings


class OthelloEngine:
    def __init__(self, path, level=15, threads=2):
        self.path = path
        self.level = level
        self.threads = threads
        self._start_engine()

        self.restart_count_down = 0

    def _start_engine(self):
        if platform.system() not in ["Windows", "Linux"]:
            raise Exception("Unsupported platform.")
        if platform.system() == "Windows":
            self.sended = 20000 // 64
            warnings.warn("Do not use Windows! Microsoft ruins everything!")
        else:
            self.sended = 20000
        command = [self.path, "-level", str(self.level), "-thread", str(self.threads)]
        # print(f"Starting engine...")
        self.engine = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0
        )

        while True:
            line = self.engine.stdout.readline()
            if not line:
                continue
            # print(line.rstrip())
            if line == "\n":
                # print("Engine started.")
                return

    def restart(self):
        """Restart the engine by cleaning up existing process and starting a new one."""
        # print("Restarting engine...")
        self.cleanup()
        self._start_engine()

    def cleanup(self):
        if hasattr(self, "engine"):
            self.engine.kill()
            self.engine.stdin.close()
            self.engine.stdout.close()
            self.engine.stderr.close()

    def send_command(self, command, allow_restart=True):

        # this is a hack to prevent pipe buffer overflow, which causes the engine to hang
        # very ungraceful, but haven't found a better solution yet
        self.restart_count_down += 1
        if self.restart_count_down >= self.sended and allow_restart:
            self.restart()
            self.restart_count_down = 0

        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()
        responses = ""
        while True:
            line = self.engine.stdout.readline()
            is_end = line == "\n"
            # print(f"[DEBUG] Read line: {line!r} Exit: {is_end}")

            if is_end:
                break

            if line:
                responses += line

        # print(f"< {responses}")
        # self.engine.communicate()
        return responses

    def reset(self):
        self.send_command("reset")
        # self.send_command("init")  # same as reset

    def play(self, moves: str):
        moves = moves.replace("ps", "")
        # if moves == "":
        #     return self.send_command("\n")
        info = self.send_command(f"play {moves}")
        return info

    def set_state_by_moves(self, moves):
        self.reset()
        self.play(moves)

    def set_state_by_board(self, board):
        assert len(board) == 66
        self.send_command("setboard " + board)

    def get_moves(self, moves: str):
        self.set_state_by_moves(moves)
        engine_output = self.send_command("hint 64", allow_restart=False)
        lst = engine_output.split("\n")
        lst = [x for x in lst if x.startswith("|")]
        lst = lst[1:]
        moves = []
        for item in lst:
            item = item.split("|")
            pos, score = item[3].strip(), item[4].strip()
            moves.append((pos, float(score)))
        return moves

    def get_best_move(self, moves: str):
        moves = self.get_moves(moves)
        return moves[0][0]

    def print_board(self):
        print(self.send_command("\n"))


if __name__ == "__main__":

    LEVEL = 1
    THREADS = 1
    EGAROUCID_PATH = "Egaroucid_for_Console_7_5_1_Windows_SIMD\Egaroucid_for_Console_7_5_1_SIMD.exe"

    engine = OthelloEngine(
        EGAROUCID_PATH,
        level=LEVEL,
        threads=THREADS,
    )
    
    print(engine.get_moves("d3c3"))

    engine.cleanup()
