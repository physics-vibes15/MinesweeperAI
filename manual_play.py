import argparse
from minesweeper_ai import Board, Phase1Agent, Phase2Agent

# ---------- ANSI color helpers ----------

RESET = "\033[0m"
BOLD = "\033[1m"
FG_COLORS = {
    "1": "\033[34m",  # blue
    "2": "\033[32m",  # green
    "3": "\033[31m",  # red
    "4": "\033[35m",  # magenta
    "5": "\033[33m",  # yellow
    "6": "\033[36m",  # cyan
    "7": "\033[90m",  # grey
    "8": "\033[37m",  # white
    "F": "\033[33m",  # yellow for flags
    "*": "\033[31m",  # red for mines
    "#": "\033[90m",  # grey for hidden
}


def colorize(ch: str) -> str:
    code = FG_COLORS.get(ch, "")
    return f"{code}{ch}{RESET}" if code else ch


# ---------- Rendering ----------

def render_board(board: Board, show_mines: bool = False):
    """Render the board for a human player with colors."""
    print()
    header = "   " + " ".join(f"{c}" for c in range(board.cols))
    print(header)
    print("   " + "-" * (2 * board.cols - 1))
    for r in range(board.rows):
        row_chars = []
        for c in range(board.cols):
            p = (r, c)
            if board.flagged(p):
                row_chars.append(colorize("F"))
            elif not board.revealed(p):
                if show_mines and board.is_mine(p):
                    row_chars.append(colorize("*"))
                else:
                    row_chars.append(colorize("#"))
            else:
                if board.is_mine(p):
                    row_chars.append(colorize("*"))
                else:
                    n = board.adj(p)
                    ch = str(n) if n > 0 else "."
                    row_chars.append(colorize(ch))
        print(f"{r}: " + " ".join(row_chars))
    print()


def print_help():
    print("Commands:")
    print("  r row col   -> reveal cell at (row, col)")
    print("  f row col   -> flag/unflag cell at (row, col)")
    print("  ai          -> let the AI make ONE move")
    print("  hint        -> AI SUGGESTS one move (does NOT play it)")
    print("  help        -> show this help")
    print("  quit        -> exit game")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--mines", type=int, default=10)
    ap.add_argument(
        "--agent",
        type=str,
        default="phase2",
        choices=["phase1", "phase2"],
        help="AI used for the 'ai' and 'hint' commands",
    )
    args = ap.parse_args()

    board = Board(args.rows, args.cols, args.mines)
    AgentCls = Phase2Agent if args.agent == "phase2" else Phase1Agent
    agent = AgentCls()

    print(f"\nMinesweeper manual mode ({args.rows}x{args.cols}, mines={args.mines})")
    print(f"AI helper: {args.agent}")
    print_help()

    render_board(board)

    while not board.game_over():
        cmd = input("Enter command (type 'help' for options): ").strip().lower()

        if cmd in ("quit", "q"):
            print("Exiting game.")
            return

        if cmd in ("help", "h"):
            print_help()
            continue

        # ---------- HINT (does not change board) ----------
        if cmd == "hint":
            action = agent.choose_action(board)
            if action is None:
                print("AI has no suggestion (no valid move found).")
            else:
                kind, p = action
                r, c = p
                if kind == "flag":
                    print(f"AI SUGGESTS: flag cell ({r}, {c})")
                else:
                    print(f"AI SUGGESTS: reveal cell ({r}, {c})")
            continue

        # ---------- AI move (actually plays ONE move) ----------
        if cmd == "ai":
            action = agent.choose_action(board)
            if action is None:
                print("AI: No valid action found.")
            else:
                kind, p = action
                r, c = p
                if kind == "flag":
                    print(f"AI flags ({r}, {c})")
                    board.flag(p)
                else:
                    print(f"AI reveals ({r}, {c})")
                    alive = board.reveal(p)
                    if not alive:
                        print("AI hit a mine! 💥")
                        break
            render_board(board)
            continue

        # ---------- Human reveal/flag ----------
        parts = cmd.split()
        if len(parts) == 3 and parts[0] in ("r", "f"):
            try:
                r = int(parts[1])
                c = int(parts[2])
            except ValueError:
                print("Row and column must be integers.")
                continue
            if not (0 <= r < board.rows and 0 <= c < board.cols):
                print("Out of bounds.")
                continue

            if parts[0] == "r":
                if board.revealed((r, c)):
                    print("Cell already revealed.")
                    continue
                alive = board.reveal((r, c))
                if not alive:
                    print("You hit a mine! 💥")
                    break
            else:  # flag
                if board.revealed((r, c)):
                    print("Cannot flag a revealed cell.")
                    continue
                if board.flagged((r, c)):
                    print("Unflagging cell.")
                    board.unflag((r, c))
                else:
                    print("Flagging cell.")
                    board.flag((r, c))

            render_board(board)
        else:
            print("Unknown command. Type 'help' for options.")

        if board.game_over():
            break

    print("\nFinal board (mines shown):")
    render_board(board, show_mines=True)
    if board.won():
        print("Result: YOU WIN ✅")
    else:
        print("Result: GAME OVER 💥")


if __name__ == "__main__":
    main()
