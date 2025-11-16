import tkinter as tk
from tkinter import messagebox
from minesweeper_ai import Board, Phase1Agent, Phase2Agent

CELL_SIZE = 30


class MinesweeperGUI:
    def __init__(self, master, rows=8, cols=8, mines=10, agent_kind="phase2"):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.mines = mines

        self.board = Board(rows, cols, mines)
        AgentCls = Phase2Agent if agent_kind == "phase2" else Phase1Agent
        self.agent = AgentCls()
        self.agent_kind = agent_kind

        self.buttons = {}
        self.hint_cell = None

        self.frame = tk.Frame(master)
        self.frame.pack(padx=10, pady=10)

        self.info_label = tk.Label(self.frame, text=f"{rows}x{cols}, mines={mines}, AI={agent_kind}")
        self.info_label.grid(row=0, column=0, columnspan=cols)

        # Board buttons
        for r in range(rows):
            for c in range(cols):
                b = tk.Button(
                    self.frame, width=2, height=1,
                    command=lambda rr=r, cc=c: self.reveal_cell(rr, cc)
                )
                b.grid(row=r + 1, column=c)
                b.bind("<Button-3>", lambda e, rr=r, cc=c: self.toggle_flag(rr, cc))
                self.buttons[(r, c)] = b

        # Controls
        ctrl = tk.Frame(master)
        ctrl.pack(pady=5)

        tk.Button(ctrl, text="AI Hint", command=self.ai_hint).grid(row=0, column=0, padx=5)
        tk.Button(ctrl, text="AI Move", command=self.ai_move).grid(row=0, column=1, padx=5)
        tk.Button(ctrl, text="Reset", command=self.reset).grid(row=0, column=2, padx=5)

    def reset(self):
        self.board = Board(self.rows, self.cols, self.mines)
        self.hint_cell = None
        for (r, c), b in self.buttons.items():
            b.config(text="", state=tk.NORMAL, bg="SystemButtonFace", relief=tk.RAISED)

    def update_view(self):
        for (r, c), b in self.buttons.items():
            p = (r, c)
            if self.board.flagged(p):
                b.config(text="F", fg="orange", relief=tk.RAISED)
            elif not self.board.revealed(p):
                b.config(text="", relief=tk.RAISED)
            else:
                if self.board.is_mine(p):
                    b.config(text="*", fg="red", relief=tk.SUNKEN)
                else:
                    n = self.board.adj(p)
                    b.config(text=(str(n) if n > 0 else ""), relief=tk.SUNKEN)
        # highlight hint if exists
        if self.hint_cell is not None:
            r, c = self.hint_cell
            self.buttons[(r, c)].config(bg="lightgreen")

    def reveal_cell(self, r, c):
        if self.board.game_over():
            return
        p = (r, c)
        if self.board.flagged(p):
            return
        alive = self.board.reveal(p)
        self.hint_cell = None
        self.update_view()
        if not alive:
            self.show_game_over(False)
        elif self.board.game_over():
            self.show_game_over(True)

    def toggle_flag(self, r, c):
        if self.board.game_over():
            return
        p = (r, c)
        if self.board.revealed(p):
            return
        if self.board.flagged(p):
            self.board.unflag(p)
        else:
            self.board.flag(p)
        self.hint_cell = None
        self.update_view()

    def ai_hint(self):
        if self.board.game_over():
            return
        action = self.agent.choose_action(self.board)
        if action is None:
            messagebox.showinfo("AI Hint", "No suggestion available.")
            return
        kind, p = action
        r, c = p
        self.hint_cell = p
        text = f"AI suggests to {('FLAG' if kind == 'flag' else 'REVEAL')} cell ({r}, {c})"
        messagebox.showinfo("AI Hint", text)
        self.update_view()

    def ai_move(self):
        if self.board.game_over():
            return
        action = self.agent.choose_action(self.board)
        if action is None:
            messagebox.showinfo("AI Move", "No move available.")
            return
        kind, p = action
        if kind == "flag":
            self.board.flag(p)
        else:
            alive = self.board.reveal(p)
            if not alive:
                self.update_view()
                self.show_game_over(False)
                return
        self.hint_cell = None
        self.update_view()
        if self.board.game_over():
            self.show_game_over(self.board.won())

    def show_game_over(self, win: bool):
        # reveal mines
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board.is_mine((r, c)):
                    self.board._revealed[r][c] = True
        self.update_view()
        msg = "You WIN! 🎉" if win else "Game Over 💥"
        messagebox.showinfo("Result", msg)


def main():
    root = tk.Tk()
    root.title("Minesweeper AI Helper")
    app = MinesweeperGUI(root, rows=8, cols=8, mines=10, agent_kind="phase2")
    root.mainloop()


if __name__ == "__main__":
    main()

