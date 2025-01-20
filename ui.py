import tkinter as tk
from tkinter import font, messagebox, ttk
from threading import Thread
from othello import Othello
from rwkv_for_ui import OthelloAI
from typing import Dict, Any
import os


class ModernOthelloUI:
    def __init__(self, master):
        self.master = master
        self.master.title("RWKV-Othello")
        self.master.geometry("1515x780")
        self.master.resizable(False, False)

        self.fonts = {
            "title": font.Font(family="Inter SemiBold", size=24),
            "subtitle": font.Font(family="Inter SemiBold", size=16),
            "text": font.Font(family="Inter Regular", size=12),
            "mono": font.Font(family="JetBrains Mono", size=12),
        }

        self.colors = {
            "bg": "#1a2023",
            "board": "#2d4046",
            "black": "#000000",
            "white": "#ffffff",
            "text": "#ffffff",
            "valid": "#4CAF50",
            "button": "#34495e",
            "graph_bg": "#2d3436",
            "graph_grid": "#636e72",
            "graph_line": "#00b894",
        }

        self.cell_size = 60
        self.game = Othello()
        self.cells = []
        self.manual_control = True

        self.black_player = tk.StringVar(value="Human")
        self.white_player = tk.StringVar(value="AI")

        self.search_depth = tk.IntVar(value=1)
        self.search_layers = tk.IntVar(value=1)
        self.top_p = tk.DoubleVar(value=0.0)

        self.model_path = tk.StringVar(value="models/rwkv7_othello_26m_L10_D448_extended")

        self.setup_ui()
        self.new_game()

        try:
            self.ai = OthelloAI(self.model_path.get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load default model: {str(e)}")
            self.ai = None

        self.evaluation_history = {
            "black": [],
            "white": [],
        }  # [(move_count, score), ...]
        self.move_count = 0

        self.black_player.trace_add("write", lambda *args: self.on_player_change())
        self.white_player.trace_add("write", lambda *args: self.on_player_change())

        self.counter = 0

    def setup_ui(self):
        main = tk.Frame(self.master, bg=self.colors["bg"])
        main.pack(expand=True, fill="both")

        left_column = tk.Frame(main, bg=self.colors["bg"], width=450)
        left_column.pack(side="left", fill="both", padx=10, pady=10)
        left_column.pack_propagate(False)
        self.create_reasoning_area(left_column)

        center_column = tk.Frame(main, bg=self.colors["bg"])
        center_column.pack(side="left", fill="both", padx=10, pady=10)
        self.create_board_area(center_column)

        right_column = tk.Frame(main, bg=self.colors["bg"], width=450)
        right_column.pack(side="left", fill="both", padx=10, pady=10)
        right_column.pack_propagate(False)
        self.create_info_area(right_column)

    def create_info_area(self, parent):
        player_frame = tk.LabelFrame(
            parent,
            text="Players",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        player_frame.pack(fill="x", padx=10, pady=10)
        self.create_player_settings(player_frame)

        # Add standalone model selection frame
        model_frame = tk.LabelFrame(
            parent,
            text="Model",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        model_frame.pack(fill="x", padx=10, pady=10)

        # Automatically read all model files from models directory
        models_dir = "models"
        models = []
        if os.path.exists(models_dir):
            models = [os.path.join(models_dir, f) for f in os.listdir(models_dir)]
            # Filter out non-model files
            models = [m.replace(".pth", "") for m in models]

        if not models:
            messagebox.showwarning("Warning", "No models found in models directory!")

        model_menu = ttk.Combobox(
            model_frame, 
            textvariable=self.model_path,
            values=models,
            state="readonly",
            width=40
        )
        model_menu.pack(padx=10, pady=10)

        # Bind model change event
        self.model_path.trace_add("write", self.on_model_change)

        settings_frame = tk.LabelFrame(
            parent,
            text="Model Settings",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        settings_frame.pack(fill="x", padx=10, pady=10)
        self.create_model_settings(settings_frame)

        eval_frame = tk.LabelFrame(
            parent,
            text="Evaluation",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
            height=450,
        )
        eval_frame.pack(fill="x", padx=10, pady=10)
        eval_frame.pack_propagate(False)
        self.create_evaluation_graph(eval_frame)

    def create_evaluation_graph(self, parent):
        self.eval_canvas = tk.Canvas(
            parent,
            bg=self.colors["graph_bg"],
            highlightthickness=1,
            highlightbackground=self.colors["graph_grid"],
        )
        self.eval_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.eval_canvas.bind("<Configure>", self.draw_evaluation_graph)

    def create_player_settings(self, parent):
        style = ttk.Style()
        style.configure(
            "Custom.TRadiobutton",
            background=self.colors["bg"],
            foreground=self.colors["text"],
        )

        black_frame = tk.Frame(parent, bg=self.colors["bg"])
        black_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            black_frame,
            text="Black:",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack(side="left")

        ttk.Radiobutton(
            black_frame,
            text="Human",
            variable=self.black_player,
            value="Human",
            style="Custom.TRadiobutton",
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            black_frame,
            text="AI",
            variable=self.black_player,
            value="AI",
            style="Custom.TRadiobutton",
        ).pack(side="left")

        white_frame = tk.Frame(parent, bg=self.colors["bg"])
        white_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            white_frame,
            text="White:",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack(side="left")

        ttk.Radiobutton(
            white_frame,
            text="Human",
            variable=self.white_player,
            value="Human",
            style="Custom.TRadiobutton",
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            white_frame,
            text="AI",
            variable=self.white_player,
            value="AI",
            style="Custom.TRadiobutton",
        ).pack(side="left")

    def draw_evaluation_graph(self, event=None):
        self.eval_canvas.delete("all")

        width = self.eval_canvas.winfo_width()
        height = self.eval_canvas.winfo_height()

        self.draw_graph_grid(width, height)

        # print(self.evaluation_history)
        self.draw_graph_lines(width, height)

    def _calculate_value_range(self, all_values):
        if all_values:
            data_min = min(all_values)
            data_max = max(all_values)

            min_value = (data_min // 4) * 4
            if data_min < min_value:
                min_value -= 4
            min_value = min(min_value, -4)

            max_value = ((data_max + 3) // 4) * 4
            max_value = max(max_value, 4)

            if max_value > 0 and min_value == 0:
                min_value = -max_value
            elif min_value < 0 and max_value == 0:
                max_value = -min_value
        else:
            min_value = -4
            max_value = 4

        value_range = max_value - min_value
        return min_value, max_value, value_range

    def draw_graph_grid(self, width, height):
        left_margin = 46
        right_margin = 10
        top_margin = 10
        bottom_margin = 35

        plot_width = width - left_margin - right_margin
        plot_height = height - top_margin - bottom_margin

        all_values = []
        if self.evaluation_history["black"]:
            all_values.extend(value for _, value in self.evaluation_history["black"])
        if self.evaluation_history["white"]:
            all_values.extend(value for _, value in self.evaluation_history["white"])

        min_value, max_value, value_range = self._calculate_value_range(all_values)

        grid_values = set()

        current = 0
        while current >= min_value:
            grid_values.add(current)
            current -= 4

        current = 0
        while current <= max_value:
            grid_values.add(current)
            current += 4

        grid_values = sorted(grid_values)

        for value in grid_values:
            normalized_value = (value - min_value) / value_range
            y = top_margin + (plot_height * (1 - normalized_value))

            if value == 0:
                self.eval_canvas.create_line(
                    left_margin,
                    y,
                    width - right_margin,
                    y,
                    fill=self.colors["graph_grid"],
                    width=2,
                )
            else:
                self.eval_canvas.create_line(
                    left_margin,
                    y,
                    width - right_margin,
                    y,
                    fill=self.colors["graph_grid"],
                    dash=(2, 4),
                )

            self.eval_canvas.create_text(
                left_margin - 5,
                y,
                text=str(int(value)),
                anchor="e",
                fill=self.colors["text"],
            )

        max_moves = 60
        for i in range(11):
            x = left_margin + (plot_width * i / 10)
            self.eval_canvas.create_line(
                x,
                top_margin,
                x,
                height - bottom_margin,
                fill=self.colors["graph_grid"],
                dash=(2, 4),
            )
            move_num = int(i * max_moves / 10)
            self.eval_canvas.create_text(
                x,
                height - bottom_margin + 15,
                text=str(move_num),
                anchor="n",
                fill=self.colors["text"],
            )

    def draw_graph_lines(self, width, height):
        left_margin = 46
        right_margin = 10
        top_margin = 10
        bottom_margin = 35

        plot_width = width - left_margin - right_margin
        plot_height = height - top_margin - bottom_margin
        max_moves = 60

        all_values = []
        if self.evaluation_history["black"]:
            all_values.extend(value for _, value in self.evaluation_history["black"])
        if self.evaluation_history["white"]:
            all_values.extend(value for _, value in self.evaluation_history["white"])

        min_value, max_value, value_range = self._calculate_value_range(all_values)

        def transform_coordinates(move_count, eval_value):
            x = left_margin + (plot_width * move_count / max_moves)
            normalized_value = (eval_value - min_value) / value_range
            y = top_margin + (plot_height * (1 - normalized_value))
            return x, y

        if self.evaluation_history["black"]:
            points = []
            for move_count, eval_value in self.evaluation_history["black"]:
                x, y = transform_coordinates(move_count, eval_value)
                points.extend([x, y])
            if len(points) >= 4:
                self.eval_canvas.create_line(points, fill=self.colors["black"], width=2)

            for move_count, eval_value in self.evaluation_history["black"]:
                x, y = transform_coordinates(move_count, eval_value)
                dot_radius = 4
                self.eval_canvas.create_oval(
                    x - dot_radius,
                    y - dot_radius,
                    x + dot_radius,
                    y + dot_radius,
                    fill=self.colors["black"],
                    outline=self.colors["white"],
                )

        if self.evaluation_history["white"]:
            points = []
            for move_count, eval_value in self.evaluation_history["white"]:
                x, y = transform_coordinates(move_count, eval_value)
                points.extend([x, y])
            if len(points) >= 4:
                self.eval_canvas.create_line(points, fill=self.colors["white"], width=2)

            for move_count, eval_value in self.evaluation_history["white"]:
                x, y = transform_coordinates(move_count, eval_value)
                dot_radius = 4
                self.eval_canvas.create_oval(
                    x - dot_radius,
                    y - dot_radius,
                    x + dot_radius,
                    y + dot_radius,
                    fill=self.colors["white"],
                    outline=self.colors["black"],
                )

    def create_reasoning_area(self, parent):
        container = tk.Frame(parent, bg=self.colors["bg"], width=400)
        container.pack(side="left", fill="both", padx=20, pady=20)
        container.pack_propagate(False)

        tk.Label(
            container,
            text="Reasoning Process",
            font=self.fonts["subtitle"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack(pady=(0, 5))

        token_frame = tk.Frame(container, bg=self.colors["bg"])
        token_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            token_frame,
            text="Token Count",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack(side="left")

        self.token_count = tk.Label(
            token_frame,
            text="0",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.token_count.pack(side="right")

        frame = tk.Frame(container, bg=self.colors["bg"])
        frame.pack(expand=True, fill="both")

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.reasoning_text = tk.Text(
            frame,
            wrap=tk.WORD,
            bg=self.colors["board"],
            fg=self.colors["text"],
            font=("Courier", 12),
            padx=10,
            pady=10,
        )
        self.reasoning_text.pack(expand=True, fill="both")

        self.reasoning_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.reasoning_text.yview)

    def create_model_settings(self, parent):
        note_label = tk.Label(
            parent,
            text="In-context search will be activated when both breadth and depth are ≥2",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg="#8e9eb6",
            wraplength=400,
        )
        note_label.pack(pady=(0, 15))

        settings_frame = tk.Frame(parent, bg=self.colors["bg"])
        settings_frame.pack(fill="x", pady=(0, 20))

        depth_frame = tk.Frame(settings_frame, bg=self.colors["bg"])
        depth_frame.pack(side="left", expand=True)

        tk.Label(
            depth_frame,
            text="Search Depth",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack()

        depth_controls = tk.Frame(depth_frame, bg=self.colors["bg"])
        depth_controls.pack()

        self.create_spinner(
            depth_controls,
            self.search_depth,
            lambda: self.update_value(self.search_depth, -1),
            lambda: self.update_value(self.search_depth, 1),
        )

        layers_frame = tk.Frame(settings_frame, bg=self.colors["bg"])
        layers_frame.pack(side="left", expand=True)

        tk.Label(
            layers_frame,
            text="Search Breadth",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack()

        layers_controls = tk.Frame(layers_frame, bg=self.colors["bg"])
        layers_controls.pack()

        self.create_spinner(
            layers_controls,
            self.search_layers,
            lambda: self.update_value(self.search_layers, -1),
            lambda: self.update_value(self.search_layers, 1),
        )

        # Top-p
        # top_p_frame = tk.Frame(settings_frame, bg=self.colors["bg"])
        # top_p_frame.pack(side="left", expand=True)

        # tk.Label(
        #     top_p_frame,
        #     text="Top-p",
        #     font=self.fonts["text"],
        #     bg=self.colors["bg"],
        #     fg=self.colors["text"],
        # ).pack()

        # top_p_controls = tk.Frame(top_p_frame, bg=self.colors["bg"])
        # top_p_controls.pack()

        # self.create_spinner(
        #     top_p_controls,
        #     self.top_p,
        #     lambda: self.update_value(self.top_p, -0.1),
        #     lambda: self.update_value(self.top_p, 0.1),
        # )

    def create_spinner(self, parent, variable, decrease_cmd, increase_cmd):
        btn_style = {
            "width": 3,
            "font": self.fonts["text"],
            "bg": self.colors["button"],
            "fg": self.colors["text"],
            "borderwidth": 0,
            "padx": 5,
            "pady": 2,
        }

        tk.Button(parent, text="-", command=decrease_cmd, **btn_style).pack(side="left", padx=2)

        tk.Label(
            parent,
            textvariable=variable,
            width=2,
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack(side="left", padx=5)

        tk.Button(parent, text="+", command=increase_cmd, **btn_style).pack(side="left", padx=2)

    def update_value(self, variable, delta):
        current_value = variable.get()
        if isinstance(current_value, int):
            new_value = current_value + delta
            if 1 <= new_value <= 5:
                variable.set(new_value)
        else:
            new_value = round(current_value + delta, 1)
            if 0.0 <= new_value <= 0.7:
                variable.set(new_value)

    def create_board(self, parent):
        container = tk.Frame(parent, bg=self.colors["bg"])
        container.pack()

        coord_width = 2
        label_width = self.fonts["text"].measure("8") + 10

        right_padding = tk.Frame(container, width=label_width, bg=self.colors["bg"])
        right_padding.grid(row=0, column=9, rowspan=9)
        right_padding.grid_propagate(False)

        for j in range(8):
            tk.Label(
                container,
                text=chr(97 + j),
                width=4,
                height=1,
                font=self.fonts["text"],
                bg=self.colors["bg"],
                fg=self.colors["text"],
            ).grid(row=0, column=j + 1, pady=(0, 1))

        for i in range(8):
            tk.Label(
                container,
                text=str(i + 1),
                width=coord_width,
                height=2,
                font=self.fonts["text"],
                bg=self.colors["bg"],
                fg=self.colors["text"],
            ).grid(row=i + 1, column=0, padx=(0, 1))

            for j in range(8):
                canvas = tk.Canvas(
                    container,
                    width=self.cell_size,
                    height=self.cell_size,
                    bg=self.colors["board"],
                    highlightthickness=1,
                    highlightbackground="#000000",
                )
                canvas.grid(row=i + 1, column=j + 1)

                canvas.bind("<Button-1>", lambda e, r=i, c=j: self.make_move(r, c))
                canvas.bind("<Enter>", lambda e, c=canvas: self.highlight_cell(c))
                canvas.bind("<Leave>", lambda e, c=canvas: self.unhighlight_cell(c))

                self.cells.append(canvas)

    def create_board_area(self, parent):
        main_container = tk.Frame(parent, bg=self.colors["bg"])
        main_container.pack(expand=True)

        self.create_status_display(main_container)

        board_container = tk.Frame(main_container, bg=self.colors["bg"])
        board_container.pack(pady=10)

        self.create_board(board_container)

        btn_style = {
            "font": self.fonts["text"],
            "bg": self.colors["button"],
            "fg": self.colors["text"],
            "borderwidth": 0,
            "padx": 15,
            "pady": 8,
        }

        button_frame = tk.Frame(main_container, bg=self.colors["bg"])
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="New Game", command=self.new_game, **btn_style).pack()

    def create_status_display(self, parent):
        status = tk.Frame(parent, bg=self.colors["bg"])
        status.pack(fill="x", pady=(0, 20))

        status_container = tk.Frame(status, bg=self.colors["bg"])
        status_container.pack(expand=True)

        frames = [tk.Frame(status_container, bg=self.colors["bg"]) for _ in range(3)]
        for frame in frames:
            frame.pack(side="left", padx=20)

        tk.Label(
            frames[0],
            text="BLACK",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack()
        self.black_count = tk.Label(
            frames[0],
            text="2",
            font=self.fonts["subtitle"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.black_count.pack()

        tk.Label(
            frames[1],
            text="Current",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack()
        self.current_indicator = tk.Canvas(
            frames[1],
            width=self.cell_size,
            height=self.cell_size,
            bg=self.colors["bg"],
            highlightthickness=0,
        )
        self.current_indicator.pack(pady=5)

        tk.Label(
            frames[2],
            text="WHITE",
            font=self.fonts["text"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        ).pack()
        self.white_count = tk.Label(
            frames[2],
            text="2",
            font=self.fonts["subtitle"],
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.white_count.pack()

    def draw_piece(self, canvas, color, is_indicator=False):
        canvas.delete("all")

        bg_color = self.colors["bg"] if is_indicator else self.colors["board"]
        canvas.create_rectangle(
            0,
            0,
            self.cell_size,
            self.cell_size,
            fill=bg_color,
            outline="" if is_indicator else "#000000",
        )

        if not color:
            return

        margin = self.cell_size * 0.15
        size = self.cell_size - 2 * margin

        canvas.create_oval(
            margin + 3,
            margin + 3,
            margin + size + 3,
            margin + size + 3,
            fill="#1a1a1a",
            outline="",
        )

        canvas.create_oval(
            margin,
            margin,
            margin + size,
            margin + size,
            fill=color,
            outline="#666666" if color == self.colors["white"] else "#000000",
        )

        highlight_color = "#ffffff" if color == self.colors["white"] else "#333333"
        canvas.create_arc(
            margin + 3,
            margin + 3,
            margin + size - 3,
            margin + size - 3,
            start=45,
            extent=180,
            fill=highlight_color,
            outline="",
        )

    def update_board(self):
        for i in range(8):
            for j in range(8):
                canvas = self.cells[i * 8 + j]
                value = self.game.board[i][j]

                if value == 0:
                    self.draw_piece(canvas, None)
                    if self.manual_control and self.game._get_flips(i, j):
                        self.draw_valid_move(canvas)
                else:
                    self.draw_piece(
                        canvas,
                        self.colors["black"] if value == 1 else self.colors["white"],
                    )

        black = sum(row.count(1) for row in self.game.board)
        white = sum(row.count(2) for row in self.game.board)
        self.black_count.config(text=str(black))
        self.white_count.config(text=str(white))

        self.update_current_indicator()

    def draw_valid_move(self, canvas):
        dot_size = self.cell_size * 0.15
        center = self.cell_size / 2
        canvas.create_oval(
            center - dot_size,
            center - dot_size,
            center + dot_size,
            center + dot_size,
            fill=self.colors["valid"],
            outline="",
        )

    def update_current_indicator(self):
        color = self.colors["black"] if self.game.current_player == 1 else self.colors["white"]
        self.draw_piece(self.current_indicator, color, is_indicator=True)

    def show_game_result(self, info):
        winner = info["winner"].upper()
        black_count = info["black"]
        white_count = info["white"]

        messagebox.showinfo(
            "Game Over",
            f"Game Over!\n\nBlack: {black_count}\nWhite: {white_count}\nWinner: {winner}",
        )

    def highlight_cell(self, canvas):
        index = self.cells.index(canvas)
        row, col = index // 8, index % 8
        if self.manual_control and self.game._get_flips(row, col):
            canvas.configure(bg=self.colors["board"])

    def unhighlight_cell(self, canvas):
        canvas.configure(bg=self.colors["board"])

    def make_move(self, row, col):
        if not self.manual_control:
            return

        pos = chr(97 + col) + str(row + 1)
        if self.game.play(pos):
            self.move_count += 1
            self.update_board()

            is_over, info = self.game.is_game_over()
            if is_over:
                self.manual_control = False
                self.show_game_result(info)
                return

            current_player_type = self.black_player.get() if self.game.current_player == 1 else self.white_player.get()

            if current_player_type == "AI" and self.game.get_legal_moves():
                self.make_ai_move()

    def on_player_change(self):
        if not self.manual_control:
            return

        current_player_type = self.black_player.get() if self.game.current_player == 1 else self.white_player.get()

        if current_player_type == "AI" and self.game.get_legal_moves():
            self.make_ai_move()

    def make_ai_move(self):
        if not self.manual_control:
            return

        self.manual_control = False

        self.reasoning_text.configure(state="normal")
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.configure(state="disabled")

        search_config = {
            "depth": self.search_depth.get(),
            "breadth": self.search_layers.get(),
            "top_p": self.top_p.get(),
        }

        Thread(target=self._ai_think_thread, args=(search_config,), daemon=True).start()

    def _execute_ai_move(self, move: str):
        self.manual_control = True

        self.game.play(move)
        self.move_count += 1
        self.update_board()

        is_over, info = self.game.is_game_over()
        if is_over:
            self.manual_control = False
            self.show_game_result(info)
            return

        current_player_type = self.black_player.get() if self.game.current_player == 1 else self.white_player.get()
        if current_player_type == "AI" and self.game.get_legal_moves():
            self.make_ai_move()

    def _process_ai_update(self, data: Dict[str, Any]):
        update_type = data["type"]

        if update_type == "reasoning":
            self.reasoning_text.configure(state="normal")

            # self.all_text += data["text"]
            # if len(self.all_text.split('\n')[-1]) >= 30:
            #     self.all_text = ''
            #     self.reasoning_text.insert(tk.END, data["text"] + '\n')
            # else:
            #     self.reasoning_text.insert(tk.END, data["text"])

            self.reasoning_text.insert(tk.END, data["text"])
            self.reasoning_text.see(tk.END)
            self.reasoning_text.configure(state="disabled")

            if "token_count" in data:
                self.token_count.config(text=str(data["token_count"]))

        elif update_type == "evaluation":
            if data["player"] == 1:
                self.evaluation_history["black"].append((self.move_count, data["score"]))
            else:
                self.evaluation_history["white"].append((self.move_count, data["score"]))
            self.draw_evaluation_graph()

    def _ai_think_thread(self, search_config):

        def update_callback(data: Dict[str, Any]):
            self.master.after(0, self._process_ai_update, data)

        try:
            move = self.ai.think(
                self.game.board,
                self.game.current_player,
                self.move_count,
                update_callback,
                search_config=search_config,
            )

            self.master.after(0, self._execute_ai_move, move)
        except Exception as e:
            print(f"Error: {e}")
            self.manual_control = True

    def new_game(self):
        self.game.reset()
        self.manual_control = True
        self.move_count = 0

        self.evaluation_history = {"black": [], "white": []}

        self.reasoning_text.configure(state="normal")
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.configure(state="disabled")

        self.token_count.config(text="0")

        self.update_board()
        self.draw_evaluation_graph()

        if self.black_player.get() == "AI":
            self.make_ai_move()

    def on_model_change(self, *args):
        """Reinitialize AI when model changes"""
        if self.ai and hasattr(self.ai, 'thinking') and self.ai.thinking:
            messagebox.showwarning("Warning", "Please wait for AI to complete current move before switching models.")
            return
        
        try:
            self.ai = OthelloAI(self.model_path.get())
            messagebox.showinfo("Success", "Model loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
            # Fallback to extended version if loading fails
            self.model_path.set("models/rwkv7_othello_26m_L10_D448_extended")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernOthelloUI(root)
    root.mainloop()
