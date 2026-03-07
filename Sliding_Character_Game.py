import tkinter as tk
from tkinter import simpledialog
import random
import time
import json
import os

LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_score(name, difficulty, moves, time_taken):
    lb = load_leaderboard()
    if difficulty not in lb:
        lb[difficulty] = []
    
    lb[difficulty].append({"name": name, "moves": moves, "time": time_taken})
    lb[difficulty].sort(key=lambda x: (x["moves"], x["time"]))
    lb[difficulty] = lb[difficulty][:10]
    
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(lb, f, indent=4)

class PuzzleLogic:
    def __init__(self, size=4):
        self.size = size
        self.reset()

    def reset(self, difficulty="Medium"):
        n = self.size * self.size
        self.board = list(range(1, n)) + [0]
        self.moves = 0
        self.history = []
        self.shuffle(difficulty)

    def shuffle(self, difficulty):
        moves_map = {
            "Easy": 15,
            "Medium": 40,
            "Hard": 100,
            "Ultra Promax": 500
        }
        num_moves = moves_map.get(difficulty, 40)
        
        last_moved = None
        for _ in range(num_moves):
            neighbors = self.get_valid_moves()
            if last_moved in neighbors and len(neighbors) > 1:
                neighbors.remove(last_moved)
            
            tile = random.choice(neighbors)
            self._slide(tile)
            last_moved = tile
            
        self.moves = 0
        self.history = []

    def find(self, value):
        idx = self.board.index(value)
        return divmod(idx, self.size)

    def get_valid_moves(self):
        er, ec = self.find(0)
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = er + dr, ec + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                neighbors.append(self.board[r * self.size + c])
        return neighbors

    def _slide(self, tile):
        empty_idx = self.board.index(0)
        tile_idx  = self.board.index(tile)
        self.board[empty_idx], self.board[tile_idx] = tile, 0

    def try_move(self, tile):
        if tile in self.get_valid_moves():
            self.history.append(self.board.copy()) 
            self._slide(tile)
            self.moves += 1
            return True
        return False

    def undo_move(self):
        if self.history:
            self.board = self.history.pop()
            self.moves -= 1
            return True
        return False

    def is_solved(self):
        n = self.size * self.size
        return self.board == list(range(1, n)) + [0]

class PuzzleGame(tk.Tk):
    # ── Styling ──
    BG_MAIN      = "#1F232D"
    BG_BOARD     = "#2A303C"
    BG_EMPTY     = "#191D26"
    
    BAR_WHITE    = "#F8F9FA"
    BAR_DARK     = "#343B4A"
    TEXT_LIGHT   = "#E2E8F0"
    TEXT_DARK    = "#111827"
    
    FONT_TITLE   = ("Helvetica", 28, "bold")
    FONT_INFO    = ("Helvetica", 12)
    FONT_BTN     = ("Helvetica", 11, "bold")
    FONT_TILE    = ("Georgia", 36, "bold")

    TILE_SIZE    = 110
    PAD          = 10

    TILE_COLORS = {
        1: "#1849B8",  2: "#5A229F",  3: "#090909",  4: "#BA1C1B",
        5: "#257C2A",  6: "#F4C500",  7: "#147D7F",  8: "#641423",
        9: "#DE8E97", 10: "#E5541E", 11: "#2AB7A9", 12: "#00AAB6", 
       13: "#1C1A5E", 14: "#80CCA5", 15: "#F4B18F"
    }
    
    DIFF_COLORS = {
        "Easy": "#2ECC71",         # Bright Green
        "Medium": "#F39C12",       # Vibrant Orange
        "Hard": "#E74C3C",         # Bold Red
        "Ultra Promax": "#9B59B6"  # Deep Purple
    }

    def __init__(self):
        super().__init__()
        self.title("Sliding Puzzle Game")
        
        self.attributes('-fullscreen', True)
        self.configure(bg=self.BG_MAIN)
        self.bind("<Escape>", lambda e: self.attributes('-fullscreen', False))

        self.size = 4
        self.logic = PuzzleLogic(self.size)
        self.start_time = time.time()
        self.running = True

        self._build_ui()
        self._draw_board()
        self._tick()

    def _build_ui(self):
        main_container = tk.Frame(self, bg=self.BG_MAIN)
        main_container.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(main_container, text="🧩 SLIDING PUZZLE GAME", font=self.FONT_TITLE, bg=self.BG_MAIN, fg="#FFFFFF").pack(pady=(0, 20))
        white_bar = tk.Frame(main_container, bg=self.BAR_WHITE, padx=20, pady=10)
        white_bar.pack(fill="x", pady=(0, 5))
        tk.Label(white_bar, text="Player:", font=self.FONT_INFO, bg=self.BAR_WHITE, fg=self.TEXT_DARK).pack(side="left")
        self.name_entry = tk.Entry(white_bar, font=self.FONT_INFO, width=12, relief="flat", highlightbackground="#CCC", highlightthickness=1)
        self.name_entry.insert(0, "Guest")
        self.name_entry.pack(side="left", padx=(5, 20), ipady=3, ipadx=5)
        tk.Label(white_bar, text="Difficulty:", font=self.FONT_INFO, bg=self.BAR_WHITE, fg=self.TEXT_DARK).pack(side="left", padx=(10, 5))
        self.difficulty_var = tk.StringVar(value="Medium")
        self.diff_buttons = {}
        
        for level in ["Easy", "Medium", "Hard", "Ultra Promax"]:
            btn = tk.Button(white_bar, text=level, font=("Helvetica", 10, "bold"),
                            relief="flat", padx=12, pady=4, cursor="hand2",
                            command=lambda l=level: self._set_difficulty(l))
            btn.pack(side="left", padx=4)
            self.diff_buttons[level] = btn
            
        self._update_diff_buttons()

        dark_bar = tk.Frame(main_container, bg=self.BAR_DARK, padx=20, pady=8)
        dark_bar.pack(fill="x", pady=(0, 20))

        self.timer_var = tk.StringVar(value="Time: 0s")
        self.moves_var = tk.StringVar(value="Moves: 0")

        tk.Label(dark_bar, textvariable=self.moves_var, font=self.FONT_INFO, bg=self.BAR_DARK, fg=self.TEXT_LIGHT).pack(side="left")
        tk.Label(dark_bar, text="Press Esc to exit fullscreen", font=("Helvetica", 9, "italic"), bg=self.BAR_DARK, fg="#A0AEC0").pack(side="left", expand=True)
        tk.Label(dark_bar, textvariable=self.timer_var, font=self.FONT_INFO, bg=self.BAR_DARK, fg=self.TEXT_LIGHT).pack(side="right")

        canvas_width = self.size * (self.TILE_SIZE + self.PAD) + self.PAD
        self.canvas = tk.Canvas(main_container, width=canvas_width, height=canvas_width, bg=self.BG_MAIN, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        self.status_var = tk.StringVar(value="Slide tiles to arrange!")
        tk.Label(main_container, textvariable=self.status_var, font=("Helvetica", 12), bg=self.BG_MAIN, fg="#A0AEC0").pack(pady=(15, 10))

        taskbar = tk.Frame(main_container, bg="#000000", padx=15, pady=10)
        taskbar.pack(pady=(5, 0))

        buttons = [
            ("🔀 Shuffle", self._new_game),
            ("↩ Undo",   self._undo),
            ("💡 Hint",    self._hint),
            ("🏆 Leaderboard", self._show_leaderboard),
            ("✅ Solve",   self._auto_solve)
        ]

        for text, cmd in buttons:
            btn = tk.Button(taskbar, text=text, font=self.FONT_BTN, bg="#FFFFFF", fg="#000000",
                            activebackground="#E2E8F0", activeforeground="#000000",
                            relief="flat", padx=15, pady=6, cursor="hand2", command=cmd)
            btn.pack(side="left", padx=6)

        self.bind("<Left>",  lambda e: self._keyboard_move("left"))
        self.bind("<Right>", lambda e: self._keyboard_move("right"))
        self.bind("<Up>",    lambda e: self._keyboard_move("up"))
        self.bind("<Down>",  lambda e: self._keyboard_move("down"))

    def _set_difficulty(self, level):
        """Sets the new difficulty, updates button colors, and restarts game."""
        self.difficulty_var.set(level)
        self._update_diff_buttons()
        self._new_game()
        
    def _update_diff_buttons(self):
        """Highlights the active difficulty button and grays out the rest."""
        current = self.difficulty_var.get()
        for level, btn in self.diff_buttons.items():
            if level == current:
                btn.config(bg=self.DIFF_COLORS[level], fg="#FFFFFF", activebackground=self.DIFF_COLORS[level], activeforeground="#FFFFFF")
            else:
                btn.config(bg="#CBD5E1", fg="#475569", activebackground="#94A3B8", activeforeground="#FFFFFF")

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=15, **kwargs):
        self.canvas.create_oval(x1, y1, x1+radius*2, y1+radius*2, **kwargs, outline="")
        self.canvas.create_oval(x2-radius*2, y1, x2, y1+radius*2, **kwargs, outline="")
        self.canvas.create_oval(x1, y2-radius*2, x1+radius*2, y2, **kwargs, outline="")
        self.canvas.create_oval(x2-radius*2, y2-radius*2, x2, y2, **kwargs, outline="")
        self.canvas.create_rectangle(x1+radius, y1, x2-radius, y2, **kwargs, outline="")
        self.canvas.create_rectangle(x1, y1+radius, x2, y2-radius, **kwargs, outline="")

    def _draw_board(self):
        self.canvas.delete("all")
        width = int(self.canvas['width'])
        height = int(self.canvas['height'])
        
        self._draw_rounded_rect(0, 0, width, height, radius=20, fill=self.BG_BOARD)

        for idx, value in enumerate(self.logic.board):
            r, c = divmod(idx, self.size)
            x1 = self.PAD + c * (self.TILE_SIZE + self.PAD)
            y1 = self.PAD + r * (self.TILE_SIZE + self.PAD)
            x2 = x1 + self.TILE_SIZE
            y2 = y1 + self.TILE_SIZE
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

            if value == 0:
                self._draw_rounded_rect(x1, y1, x2, y2, radius=12, fill=self.BG_EMPTY)
            else:
                color = self.TILE_COLORS.get(value, "#333333")
                self._draw_rounded_rect(x1, y1, x2, y2, radius=12, fill=color)
                self.canvas.create_text(cx, cy, text=str(value), font=self.FONT_TILE, fill="#FFFFFF")

        self.moves_var.set(f"Moves: {self.logic.moves}")

    # ── Interactions ──
    def _on_click(self, event):
        if not self.running: return
        col = event.x // (self.TILE_SIZE + self.PAD)
        row = event.y // (self.TILE_SIZE + self.PAD)
        if 0 <= row < self.size and 0 <= col < self.size:
            tile = self.logic.board[row * self.size + col]
            if tile != 0: self._make_move(tile)

    def _keyboard_move(self, direction):
        if not self.running: return
        er, ec = self.logic.find(0)
        
        delta = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        dr, dc = delta[direction]
        tr, tc = er + dr, ec + dc
        if 0 <= tr < self.size and 0 <= tc < self.size:
            self._make_move(self.logic.board[tr * self.size + tc])

    def _make_move(self, tile):
        if self.logic.try_move(tile):
            self.status_var.set("Playing...")
            self._draw_board()
            if self.logic.is_solved(): self._win()

    def _undo(self):
        if not self.running: return
        if self.logic.undo_move():
            self._draw_board()
            self.status_var.set("Move undone.")
        else:
            self.status_var.set("Nothing to undo.")

    def _hint(self):
        if not self.running: return
        moves = self.logic.get_valid_moves()
        self.status_var.set(f"💡 You can slide: {', '.join(map(str, moves))}")

    def _auto_solve(self):
        self.running = False
        n = self.size * self.size
        self.logic.board = list(range(1, n)) + [0]
        self._draw_board()
        self.status_var.set("✅ Puzzle Solved automatically.")

    def _new_game(self):
        difficulty = self.difficulty_var.get()
        self.logic.reset(difficulty)
        self.start_time = time.time()
        self.running = True
        self.status_var.set("Slide tiles to arrange!")
        self._draw_board()

    def _win(self):
        self.running = False
        elapsed = int(time.time() - self.start_time)
        self._draw_board()
        
        current_name = self.name_entry.get().strip()
        if not current_name or current_name.lower() == "guest":
            current_name = "Player"

        player_name = simpledialog.askstring(
            "🎉 Puzzle Solved!", 
            f"Amazing!\n\nDifficulty: {self.difficulty_var.get()}\nMoves: {self.logic.moves}\nTime: {elapsed}s\n\nEnter your name for the Leaderboard:",
            initialvalue=current_name
        )

        if not player_name or player_name.strip() == "":
            player_name = "Anonymous"
            
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, player_name)

        save_score(player_name, self.difficulty_var.get(), self.logic.moves, elapsed)
        
        self.status_var.set(f"🎉 {player_name} won in {self.logic.moves} moves!")
        self._show_leaderboard()

    def _show_leaderboard(self):
        lb_win = tk.Toplevel(self)
        lb_win.title("🏆 Leaderboard")
        lb_win.geometry("380x450")
        lb_win.configure(bg=self.BG_MAIN)
        
        diff = self.difficulty_var.get()
        tk.Label(lb_win, text=f"Top 10 - {diff}", font=("Helvetica", 20, "bold"), bg=self.BG_MAIN, fg="#FFFFFF").pack(pady=15)
        
        lb_data = load_leaderboard()
        scores = lb_data.get(diff, [])
        
        if not scores:
            tk.Label(lb_win, text="No scores yet. Be the first!", font=self.FONT_INFO, bg=self.BG_MAIN, fg="#A0AEC0").pack(pady=20)
        else:
            frame = tk.Frame(lb_win, bg=self.BG_MAIN)
            frame.pack(fill="x", padx=20)
            
            # Headers
            tk.Label(frame, text="Rank", font=self.FONT_BTN, bg=self.BG_MAIN, fg="#A0AEC0", width=5, anchor="w").grid(row=0, column=0)
            tk.Label(frame, text="Name", font=self.FONT_BTN, bg=self.BG_MAIN, fg="#A0AEC0", width=12, anchor="w").grid(row=0, column=1)
            tk.Label(frame, text="Moves", font=self.FONT_BTN, bg=self.BG_MAIN, fg="#A0AEC0", width=6, anchor="w").grid(row=0, column=2)
            tk.Label(frame, text="Time", font=self.FONT_BTN, bg=self.BG_MAIN, fg="#A0AEC0", width=6, anchor="w").grid(row=0, column=3)
            
            for i, score in enumerate(scores):
                tk.Label(frame, text=f"#{i+1}", font=self.FONT_INFO, bg=self.BG_MAIN, fg="#FFFFFF", anchor="w").grid(row=i+1, column=0, pady=4)
                tk.Label(frame, text=score['name'][:10], font=self.FONT_INFO, bg=self.BG_MAIN, fg="#FFFFFF", anchor="w").grid(row=i+1, column=1, pady=4)
                tk.Label(frame, text=str(score['moves']), font=self.FONT_INFO, bg=self.BG_MAIN, fg="#FFFFFF", anchor="w").grid(row=i+1, column=2, pady=4)
                tk.Label(frame, text=f"{score['time']}s", font=self.FONT_INFO, bg=self.BG_MAIN, fg="#FFFFFF", anchor="w").grid(row=i+1, column=3, pady=4)

        tk.Button(lb_win, text="Close", font=self.FONT_BTN, bg="#E74C3C", fg="#FFFFFF", relief="flat", padx=10, pady=5, command=lb_win.destroy).pack(pady=20)

    def _tick(self):
        if self.running:
            elapsed = int(time.time() - self.start_time)
            self.timer_var.set(f"Time: {elapsed}s")
        self.after(500, self._tick)

if __name__ == "__main__":
    app = PuzzleGame()
    app.mainloop()