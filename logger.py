class DataLogger:
    def __init__(self, print_to_console=True):
        self.log = ""
        self.print_to_console = print_to_console

    def log_func(self, text: str, end="\n"):
        if self.print_to_console:
            print(text)
        self.log += text + end

    def print_all(self, max_length=2000):
        print("=" * 100)
        if max_length is None:
            print(self.log)
        else:
            print(self.log[:max_length])
        print("=" * 100)
        print(f"Total Length: {len(self.log)}")

    def clear(self):
        self.log = ""
