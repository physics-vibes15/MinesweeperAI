FINAL REPORT — Minesweeper AI Project
CS 271P: Foundations of Artificial Intelligence
Group 25 — Shubham Satish Chopade, Akshatha Srikantha
1. Introduction

Minesweeper is a classic puzzle game in which the player must uncover all safe squares without detonating hidden mines. Each revealed square shows a number representing how many mines are adjacent to it. This number provides local constraints that allow logical inference.

In this project, we implemented a two-phase Minesweeper AI system per instructor guidance:

Phase 1: Implement two single-point logic strategies and use random guessing when logic is insufficient.

Phase 2: Extend the agent with a Constraint Satisfaction Problem (CSP)–based intelligent guessing module that uses probability reasoning instead of random guesses.

The goal is to analyze how CSP-based decision-making improves win rate and reduces the need for guesses.

2. Problem Formulation

We model Minesweeper as a Constraint Satisfaction Problem (CSP).

CSP Representation:

Variables: Frontier cells (covered cells adjacent to at least one revealed numbered cell).

Domain: {mine, safe}

Constraints:
For each revealed numbered cell x with number n:

Number of mines among the covered neighbors of x
= n − (number of flagged neighbors of x)

The AI repeatedly chooses actions:

reveal(r, c) — uncover a cell (loss if it is a mine)

flag(r, c) — mark a cell as a mine

The game is won when all non-mine cells are revealed.

3. Phase 1: Single-Point Strategies + Random Guessing

Phase 1 uses two basic inference rules.

Rule 1 — SP-Mine (All remaining neighbors are mines)

If a revealed numbered cell shows n, and it has:

C = number of covered neighbors

F = number of flagged neighbors

Then if:

n − F = C

All covered neighbors must be mines → flag them.

Rule 2 — SP-Safe (All remaining neighbors are safe)

If:

n = F

Then all remaining covered neighbors must be safe → reveal them.

Fallback: Random Guessing

If neither rule applies, the agent has no certainty and performs a random reveal on any covered cell.

This is the complete Phase 1 system.

4. Phase 2: CSP-Based Intelligent Guessing

Phase 2 improves on Phase 1 by replacing random guessing with probability-based decisions derived from CSP enumeration.

Steps in Phase 2:
1. Identify Frontier Cells

These are covered cells that border at least one revealed number. Only these cells influence constraints.

2. Build CSP Constraints

For each revealed numbered cell, form a constraint relating its covered neighbors to the number on the cell.

Example:
If a cell shows 3, has 1 flagged neighbor and 4 covered neighbors:

Mines among the 4 covered neighbors = 3 − 1 = 2

3. Split Frontier into Connected Components

Cells that appear together in constraints form small independent components.
This keeps enumeration feasible.

4. Enumerate All Valid Assignments

For each component:

Try all combinations of mine/safe assignments.

Keep only those satisfying every constraint.

5. Compute Probability for Each Cell

For each frontier cell c:

Probability that c is a mine
= (number of valid assignments where c is a mine)
÷ (total valid assignments)

6. Make a Decision

If probability = 1 → flag (certain mine)

If probability = 0 → reveal (certain safe)

Otherwise → choose the cell with the lowest probability of being a mine

This removes most blind guesses from the game.

5. Experimental Setup

All experiments were run on randomly generated boards:

Board size: 8 × 8

Mines: 10

Games per agent: 200–300

Initial move: Reveal cell (0, 0)

Metrics collected:

Win rate

Logic ratio (logical moves ÷ total moves)

Average guesses

Average flags

The same random seeds were used for both agents to ensure fairness.

6. Results
Summary of Results
Metric	Phase 1	Phase 2	Improvement
Win rate	0.355	0.475	+12%
Logic ratio	0.865	0.951	+10%
Avg guesses	1.88	0.86	−54%
Avg flags	4.50	5.39	+20%

These results demonstrate that CSP reasoning significantly improves performance.

Graphical Comparison

Your plotting script (plot_results.py) generated a bar chart comparing:

Win rate

Logic ratio

Average guesses

The graph clearly shows Phase 2 outperforming Phase 1.

7. Discussion

Phase 1 is effective but limited. Its single-point strategies only use local information.
They fail whenever:

multiple numbered cells combine to form richer constraints

reasoning spans clusters of frontier cells

the board requires global inference

Phase 2 addresses these issues by:

modeling the frontier as a small CSP

enumerating valid mine configurations

estimating per-cell probabilities

making the safest possible choice instead of guessing blindly

This leads to:

fewer mistakes

more flags placed correctly

substantially higher win rates

CSP-based reasoning proves to be a powerful enhancement.

8. Conclusion

We successfully implemented a Minesweeper AI with two phases:

Phase 1: Pure logical strategies + random fallback

Phase 2: Logical strategies + CSP-based intelligent guessing

Phase 2 performs significantly better across all evaluation metrics.

This project showcases the effectiveness of classical AI techniques such as constraint reasoning and probability estimation in a real game environment.

9. Future Work

Add GUI to visualize decision-making

Try SAT solvers or AC-3 for faster constraint propagation

Apply Monte Carlo sampling for large components

Extend to larger difficulty boards (Intermediate, Expert)

Integrate machine learning for hybrid symbolic–neural play
