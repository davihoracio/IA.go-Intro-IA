import random
import copy
from environment.board import SudokuBoard
from metrics.tracker   import Tracker


class HillClimbingAgent:

    def __init__(
        self,
        board         : SudokuBoard,
        tracker       : Tracker,
        max_restarts  : int = 150,
        max_iterations: int = 3000,
        max_sideways  : int = 50,
    ):
        self.board          = board
        self.tracker        = tracker
        self.max_restarts   = max_restarts
        self.max_iterations = max_iterations
        self.max_sideways   = max_sideways

    def solve(self) -> list[list[int]]:
        self.tracker.start()

        best_overall_grid      = None
        best_overall_conflicts = float("inf")

        for restart in range(self.max_restarts):

            grid = self._generate_initial_state()
            cost = self._count_conflicts(grid)

            self.tracker.record_step(copy.deepcopy(grid))

            sideways_count = 0

            for _ in range(self.max_iterations):

                self.tracker.increment_nodes()

                if cost < best_overall_conflicts:
                    best_overall_conflicts = cost
                    best_overall_grid      = copy.deepcopy(grid)

                if cost == 0:
                    self.board.apply_solution(
                        {(i, j): grid[i][j]
                         for i in range(9)
                         for j in range(9)}
                    )
                    self.tracker.stop(solved=True)
                    return self.board.grid

                neighbor, neighbor_cost = self._best_neighbor(grid, cost)

                if neighbor_cost < cost:
                    grid           = neighbor
                    cost           = neighbor_cost
                    sideways_count = 0
                    self.tracker.record_step(copy.deepcopy(grid))

                elif neighbor_cost == cost and sideways_count < self.max_sideways:
                    grid           = neighbor
                    sideways_count += 1
                    self.tracker.record_step(copy.deepcopy(grid))

                else:
                    break

        if best_overall_grid is not None:
            self.board.apply_solution(
                {(i, j): best_overall_grid[i][j]
                 for i in range(9)
                 for j in range(9)}
            )

        self.tracker.stop(solved=False)
        self.tracker.final_conflicts = best_overall_conflicts
        return self.board.grid

    def _generate_initial_state(self) -> list[list[int]]:
        grid = copy.deepcopy(self.board.initial)

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):

                present = {
                    grid[box_r + r][box_c + c]
                    for r in range(3)
                    for c in range(3)
                    if grid[box_r + r][box_c + c] != 0
                }

                missing = list(set(range(1, 10)) - present)
                random.shuffle(missing)

                idx = 0
                for r in range(3):
                    for c in range(3):
                        if grid[box_r + r][box_c + c] == 0:
                            grid[box_r + r][box_c + c] = missing[idx]
                            idx += 1

        return grid

    def _count_conflicts(self, grid: list[list[int]]) -> int:
        conflicts = 0

        for i in range(9):
            row = [grid[i][j] for j in range(9)]
            col = [grid[j][i] for j in range(9)]
            conflicts += 9 - len(set(row))
            conflicts += 9 - len(set(col))

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                box = [grid[box_r + r][box_c + c] for r in range(3) for c in range(3)]
                conflicts += 9 - len(set(box))

        return conflicts

    def _best_neighbor(
        self,
        grid        : list[list[int]],
        current_cost: int,
    ) -> tuple[list[list[int]], int]:
        best_grid    = grid
        best_cost    = current_cost
        lateral_grid = None
        lateral_cost = current_cost

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):

                free = [
                    (box_r + r, box_c + c)
                    for r in range(3)
                    for c in range(3)
                    if self.board.initial[box_r + r][box_c + c] == 0
                ]

                for i in range(len(free)):
                    for j in range(i + 1, len(free)):
                        r1, c1 = free[i]
                        r2, c2 = free[j]

                        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
                        cost = self._count_conflicts(grid)

                        if cost < best_cost:
                            best_cost = cost
                            best_grid = copy.deepcopy(grid)

                        elif cost == lateral_cost and lateral_grid is None:
                            lateral_cost = cost
                            lateral_grid = copy.deepcopy(grid)

                        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]

        if best_cost < current_cost:
            return best_grid, best_cost

        if lateral_grid is not None:
            return lateral_grid, lateral_cost

        return grid, current_cost
