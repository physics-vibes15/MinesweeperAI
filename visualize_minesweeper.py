import argparse
from time import sleep
from minesweeper_ai import Board, Phase1Agent, Phase2Agent

def render_board(board: Board):
    """ASCII board visual."""
    chars = []
    for r in range(board.rows):
        row = []
        for c in range(board.cols):
            p = (r, c)
            if board.flagged(p):
                row.append("F")
            elif not board.revealed(p):
                row.append("#")
            else:
                if board.is_mine(p):
                    row.append("*")
                else:
                    n = board.adj(p)
                    row.append(str(n) if n > 0 else ".")
        chars.append(" ".join(row))
    print("\n".join(chars))

def play_once(agent_kind="phase2", rows=8, cols=8, mines=10, delay=0.1):
    AgentCls = Phase2Agent if agent_kind == "phase2" else Phase1Agent
    board = Board(rows, cols, mines)
    agent = AgentCls()

    # initial click
    board.reveal((0, 0))
    step = 0
    print(f"\n=== New Game ({agent_kind}) ===")
    render_board(board)
    print()

    while not board.game_over():
        step += 1
        action = agent.choose_action(board)
        if action is None:
            break
        kind, p = action
        print(f"Step {step}: {kind.upper()} {p}")
        if kind == "flag":
            board.flag(p)
        else:
            board.reveal(p)
        render_board(board)
        print()
        sleep(delay)

    if board.won():
        print("Result: WIN ✅")
    else:
        print("Result: LOSS 💥")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", type=str, default="phase2", choices=["phase1","phase2"])
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--mines", type=int, default=10)
    ap.add_argument("--delay", type=float, default=0.3)
    args = ap.parse_args()

    play_once(agent_kind=args.agent, rows=args.rows, cols=args.cols,
              mines=args.mines, delay=args.delay)

