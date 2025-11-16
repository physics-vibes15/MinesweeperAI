import matplotlib.pyplot as plt
from minesweeper_ai import run_experiments

def compare_agents(rows=8, cols=8, mines=10, games=300):
    # Run Phase 1
    phase1 = run_experiments(
        rows=rows, cols=cols, mines=mines,
        games=games, agent_kind="phase1", seed=42
    )

    # Run Phase 2
    phase2 = run_experiments(
        rows=rows, cols=cols, mines=mines,
        games=games, agent_kind="phase2", seed=43
    )

    print("Phase 1:", phase1)
    print("Phase 2:", phase2)

    labels = ["Win rate", "Logic ratio", "Avg guesses"]
    p1_vals = [phase1["win_rate"], phase1["logic_ratio"], phase1["avg_guess_moves"]]
    p2_vals = [phase2["win_rate"], phase2["logic_ratio"], phase2["avg_guess_moves"]]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots()
    ax.bar([i - width/2 for i in x], p1_vals, width, label="Phase 1")
    ax.bar([i + width/2 for i in x], p2_vals, width, label="Phase 2")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(p1_vals + p2_vals) * 1.2)
    ax.set_ylabel("Value")
    ax.set_title(f"Phase 1 vs Phase 2 ({rows}x{cols}, mines={mines}, games={games})")
    ax.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    compare_agents()
