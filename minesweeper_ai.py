# minesweeper_ai.py
# Python 3.9+
from __future__ import annotations
import random
import argparse
from collections import deque, defaultdict
from typing import List, Tuple, Set, Dict, Optional

# -------------------------------
# Environment
# -------------------------------

Coord = Tuple[int, int]

class Board:
    """Minesweeper board + basic game mechanics."""
    def __init__(self, rows: int, cols: int, mines: int, seed: Optional[int] = None):
        assert 1 <= mines < rows * cols
        self.rows, self.cols, self.mines_count = rows, cols, mines
        self.rng = random.Random(seed)
        self._mine = [[False]*cols for _ in range(rows)]
        self._revealed = [[False]*cols for _ in range(rows)]
        self._flagged = [[False]*cols for _ in range(rows)]
        self._adj = [[0]*cols for _ in range(rows)]
        self._game_over = False
        self._win_cached = None

        # place mines
        cells = [(r,c) for r in range(rows) for c in range(cols)]
        self.rng.shuffle(cells)
        for (r,c) in cells[:mines]:
            self._mine[r][c] = True
        # precompute adj counts
        for r in range(rows):
            for c in range(cols):
                if self._mine[r][c]:
                    self._adj[r][c] = -1
                else:
                    self._adj[r][c] = sum(1 for nr,nc in self.neighbors((r,c)) if self._mine[nr][nc])

    def neighbors(self, p: Coord) -> List[Coord]:
        r, c = p
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    out.append((rr,cc))
        return out

    def is_mine(self, p: Coord) -> bool:
        r, c = p
        return self._mine[r][c]

    def adj(self, p: Coord) -> int:
        """-1 for mine, otherwise [0..8]."""
        r, c = p
        return self._adj[r][c]

    def revealed(self, p: Coord) -> bool:
        r, c = p
        return self._revealed[r][c]

    def flagged(self, p: Coord) -> bool:
        r, c = p
        return self._flagged[r][c]

    def covered_cells(self) -> List[Coord]:
        return [(r,c) for r in range(self.rows) for c in range(self.cols)
                if not self._revealed[r][c] and not self._flagged[r][c]]

    def state_for_agent(self) -> Dict[str, Set[Coord] | Dict[Coord, int]]:
        """What the agent is allowed to 'see'."""
        numbers: Dict[Coord, int] = {}
        covered: Set[Coord] = set()
        flagged: Set[Coord] = set()
        for r in range(self.rows):
            for c in range(self.cols):
                p = (r,c)
                if self._flagged[r][c]:
                    flagged.add(p)
                elif self._revealed[r][c]:
                    numbers[p] = self._adj[r][c]  # 0..8
                else:
                    covered.add(p)
        return {"numbers": numbers, "covered": covered, "flagged": flagged}

    def in_bounds(self, p: Coord) -> bool:
        r, c = p
        return 0 <= r < self.rows and 0 <= c < self.cols

    # Game actions
    def flag(self, p: Coord) -> None:
        if self._game_over or self._revealed[p[0]][p[1]]:
            return
        self._flagged[p[0]][p[1]] = True

    def unflag(self, p: Coord) -> None:
        if self._game_over:
            return
        self._flagged[p[0]][p[1]] = False

    def reveal(self, p: Coord) -> bool:
        """Reveal cell. Returns False if you hit a mine (game over), True otherwise."""
        if self._game_over or self._flagged[p[0]][p[1]]:
            return True  # ignore
        if self._revealed[p[0]][p[1]]:
            return True
        if self._mine[p[0]][p[1]]:
            self._revealed[p[0]][p[1]] = True
            self._game_over = True
            self._win_cached = False
            return False
        # flood fill for zeros
        self._reveal_region(p)
        # check win condition
        self._check_win()
        return True

    def _reveal_region(self, start: Coord) -> None:
        q = deque([start])
        while q:
            r, c = q.popleft()
            if self._revealed[r][c] or self._flagged[r][c]:
                continue
            self._revealed[r][c] = True
            if self._adj[r][c] == 0:
                for nb in self.neighbors((r,c)):
                    if not self._revealed[nb[0]][nb[1]] and not self._flagged[nb[0]][nb[1]]:
                        q.append(nb)

    def _check_win(self) -> None:
        if self._game_over:
            return
        # won if all non-mine are revealed
        for r in range(self.rows):
            for c in range(self.cols):
                if not self._mine[r][c] and not self._revealed[r][c]:
                    return
        self._game_over = True
        self._win_cached = True

    def game_over(self) -> bool:
        return self._game_over

    def won(self) -> bool:
        return bool(self._win_cached)

# -------------------------------
# Agent Base + utilities
# -------------------------------

class AgentOutcome:
    def __init__(self):
        self.logic_moves = 0
        self.guess_moves = 0
        self.flags_set = 0

class Agent:
    """Base class."""
    def choose_action(self, board: Board) -> Tuple[str, Coord] | None:
        """Return ('reveal' or 'flag', coord) or None if no action."""
        raise NotImplementedError

    def play_game(self, board: Board) -> AgentOutcome:
        out = AgentOutcome()
        # Ensure we start by revealing something (common practice)
        if not any(board.revealed((r,c)) for r in range(board.rows) for c in range(board.cols)):
            # start in a corner to reduce early mine hits, heuristic only
            board.reveal((0,0))

        while not board.game_over():
            action = self.choose_action(board)
            if action is None:
                break
            kind, p = action
            if kind == "flag":
                out.logic_moves += 1  # only flag when logically deduced
                out.flags_set += 1
                board.flag(p)
            elif kind == "reveal":
                # Heuristic: if this came from CSP or random, count as guess; if from SP rules, logic
                # We'll annotate inside subclasses and set a flag in self._last_action_kind
                pass
            else:
                raise ValueError("Unknown action")
        return out

# Helper to compute covered+flagged neighbors and counts from agent state
def neighbor_buckets(board: Board, cell: Coord, numbers: Dict[Coord,int],
                     covered: Set[Coord], flagged: Set[Coord]) -> Tuple[List[Coord], List[Coord], int]:
    """Return (covered_neighbors, flagged_neighbors, number_on_cell)."""
    cov, flg = [], []
    for nb in board.neighbors(cell):
        if nb in flagged:
            flg.append(nb)
        elif nb in covered:
            cov.append(nb)
    return cov, flg, numbers[cell]

# -------------------------------
# Phase 1 Agent: Single-point + random
# -------------------------------

class Phase1Agent(Agent):
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._last_move_was_logic = False

    def choose_action(self, board: Board) -> Tuple[str, Coord] | None:
        st = board.state_for_agent()
        numbers: Dict[Coord,int] = st["numbers"]  # revealed cells with numbers
        covered: Set[Coord] = st["covered"]
        flagged: Set[Coord] = st["flagged"]

        # Single-point strategies (SP-Mine and SP-Safe)
        # Try to find any certain flags
        for cell, num in numbers.items():
            cov, flg, n = neighbor_buckets(board, cell, numbers, covered, flagged)
            remaining = n - len(flg)
            if remaining == len(cov) and len(cov) > 0:
                # all covered neighbors must be mines -> flag them (one at a time)
                self._last_move_was_logic = True
                return ("flag", cov[0])

        # Try to find any certain safe reveals
        for cell, num in numbers.items():
            cov, flg, n = neighbor_buckets(board, cell, numbers, covered, flagged)
            if n == len(flg) and len(cov) > 0:
                # all other covered neighbors are safe -> reveal one
                self._last_move_was_logic = True
                return ("reveal", cov[0])

        # If nothing logical, pick a random covered cell (fallback)
        if covered:
            self._last_move_was_logic = False
            return ("reveal", self.rng.choice(list(covered)))
        return None

    def play_game(self, board: Board) -> AgentOutcome:
        out = AgentOutcome()
        # initial click
        if not any(board.revealed((r,c)) for r in range(board.rows) for c in range(board.cols)):
            board.reveal((0,0))
        while not board.game_over():
            action = self.choose_action(board)
            if action is None: break
            kind, p = action
            if kind == "flag":
                out.logic_moves += 1
                out.flags_set += 1
                board.flag(p)
            elif kind == "reveal":
                success = board.reveal(p)
                if self._last_move_was_logic:
                    out.logic_moves += 1
                else:
                    out.guess_moves += 1
                if not success:
                    break
        return out

# -------------------------------
# Phase 2 Agent: Single-point + CSP probability
# -------------------------------

class Phase2Agent(Phase1Agent):
    """Extends Phase1 with CSP-based intelligent guesses when single-point is stuck."""
    def __init__(self, seed: Optional[int] = None, max_component_size: int = 14):
        super().__init__(seed=seed)
        self.max_component_size = max_component_size  # to bound enumeration

    def choose_action(self, board: Board) -> Tuple[str, Coord] | None:
        # First use Phase1 single-point logic
        action = super().choose_action(board)
        if action is None:
            return None

        kind, p = action

        # If Phase1 produced a logical action (flag or safe reveal), take it
        if kind == "flag":
            return action
        if kind == "reveal" and self._last_move_was_logic:
            return action

        # Otherwise it's a fallback "random" reveal: upgrade with CSP intelligent guess
        st = board.state_for_agent()
        numbers: Dict[Coord,int] = st["numbers"]
        covered: Set[Coord] = st["covered"]
        flagged: Set[Coord] = st["flagged"]

        if not covered:
            return None

        # Build frontier: covered cells adjacent to at least one revealed number
        frontier = set()
        constraint_cells: Dict[Coord, List[Coord]] = {}
        for cell, n in numbers.items():
            cov, flg, nval = neighbor_buckets(board, cell, numbers, covered, flagged)
            if cov:
                frontier.update(cov)
                constraint_cells[cell] = cov

        if not frontier:
            # No constraints: still must guess anywhere
            self._last_move_was_logic = False
            return ("reveal", random.choice(list(covered)))

        # Build graph connectivity among frontier cells via shared constraints
        adj: Dict[Coord, Set[Coord]] = defaultdict(set)
        for cell, covs in constraint_cells.items():
            for i in range(len(covs)):
                for j in range(i+1, len(covs)):
                    a, b = covs[i], covs[j]
                    adj[a].add(b); adj[b].add(a)

        # Connected components
        components: List[Set[Coord]] = []
        visited = set()
        for v in frontier:
            if v in visited: continue
            comp = set([v])
            q = [v]
            visited.add(v)
            while q:
                x = q.pop()
                for y in adj[x]:
                    if y not in visited:
                        visited.add(y)
                        comp.add(y)
                        q.append(y)
            components.append(comp)

        # For each component, build local constraints and enumerate
        best_cell = None
        best_prob = 1.1  # choose min P(mine)
        certain_flag: Optional[Coord] = None
        certain_safe: Optional[Coord] = None

        for comp in components:
            if len(comp) > self.max_component_size:
                # too big, skip enumeration and continue
                continue

            # local constraints that touch this component
            #   each constraint: (set of vars inside comp), required_mines_after_flags
            local_constraints: List[Tuple[Set[Coord], int]] = []
            comp_set = set(comp)
            for num_cell, nval in numbers.items():
                cov, flg, nreq = neighbor_buckets(board, num_cell, numbers, covered, flagged)
                vars_in_comp = set([v for v in cov if v in comp_set])
                if not vars_in_comp:
                    continue
                required = nreq - sum(1 for f in flg)
                # Also subtract covered neighbors outside comp, but we keep them unknown.
                # We must only include constraints that fully lie in comp or we track outside vars count:
                outside = [v for v in cov if v not in comp_set]
                # If there are outside vars, we can't fix the count; so skip unless none:
                if outside:
                    continue
                local_constraints.append((vars_in_comp, required))

            if not local_constraints:
                # No usable constraints; skip
                continue

            vars_list = list(comp)
            # Enumerate all assignments of mines to vars_list that satisfy local_constraints
            # Use backtracking with pruning.
            assign = {}
            counts = {v: [0,0] for v in vars_list}  # [mine_count, total_count]

            def valid_partial() -> bool:
                # check each constraint lower/upper feasibility
                for varset, req in local_constraints:
                    assigned = [assign[v] for v in varset if v in assign]
                    if sum(1 for a in assigned if a) > req:
                        return False
                    remaining = len(varset) - len(assigned)
                    min_possible = sum(1 for a in assigned if a)  # already mines
                    max_possible = min_possible + remaining
                    if max_possible < req:
                        return False
                return True

            total_models = 0

            def dfs(i: int):
                nonlocal total_models
                if i == len(vars_list):
                    # check hard constraints
                    for varset, req in local_constraints:
                        if sum(1 for v in varset if assign[v]) != req:
                            return
                    total_models += 1
                    for v in vars_list:
                        if assign[v]:
                            counts[v][0] += 1
                        counts[v][1] += 1
                    return
                v = vars_list[i]
                # try v = mine (True)
                assign[v] = True
                if valid_partial():
                    dfs(i+1)
                # try v = safe (False)
                assign[v] = False
                if valid_partial():
                    dfs(i+1)
                del assign[v]

            dfs(0)

            if total_models == 0:
                # If inconsistent (shouldn't happen often), skip
                continue

            # compute probabilities for this component
            for v in vars_list:
                mine_count, total = counts[v]
                p = mine_count / total
                if p == 0.0:
                    certain_safe = v
                elif p == 1.0:
                    certain_flag = v
                if p < best_prob:
                    best_prob = p
                    best_cell = v

            # If we already found certainties, we can stop early
            if certain_flag or certain_safe:
                break

        if certain_flag:
            self._last_move_was_logic = True
            return ("flag", certain_flag)
        if certain_safe:
            self._last_move_was_logic = True
            return ("reveal", certain_safe)
        if best_cell is not None:
            self._last_move_was_logic = False  # it's still a guess (probabilistic), not 100% logic
            return ("reveal", best_cell)

        # If enumeration failed everywhere, fall back to random
        self._last_move_was_logic = False
        return ("reveal", random.choice(list(covered)))

# -------------------------------
# Evaluation
# -------------------------------

def run_experiments(rows=8, cols=8, mines=10, games=200, agent_kind="phase1", seed=None):
    rng = random.Random(seed)
    AgentCls = Phase1Agent if agent_kind.lower()=="phase1" else Phase2Agent
    wins = 0
    total_logic = 0
    total_guess = 0
    total_flags = 0
    for g in range(games):
        board = Board(rows, cols, mines, seed=rng.randint(0, 10**9))
        agent = AgentCls(seed=rng.randint(0, 10**9))
        out = agent.play_game(board)
        if board.won(): wins += 1
        total_logic += out.logic_moves
        total_guess += out.guess_moves
        total_flags += out.flags_set
    return {
        "wins": wins,
        "games": games,
        "win_rate": wins/games,
        "logic_ratio": total_logic / max(1,(total_logic+total_guess)),
        "avg_guess_moves": total_guess / games,
        "avg_flags": total_flags / games,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--mines", type=int, default=10)
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--agent", type=str, default="phase1", choices=["phase1","phase2"])
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    res = run_experiments(rows=args.rows, cols=args.cols, mines=args.mines,
                          games=args.games, agent_kind=args.agent, seed=args.seed)
    print(f"Agent: {args.agent}")
    print(f"Board: {args.rows}x{args.cols}, mines={args.mines}, games={args.games}")
    print(f"Win rate:      {res['win_rate']:.3f}")
    print(f"Logic ratio:   {res['logic_ratio']:.3f}")
    print(f"Avg guesses:   {res['avg_guess_moves']:.2f}")
    print(f"Avg flags:     {res['avg_flags']:.2f}")

if __name__ == "__main__":
    main()
