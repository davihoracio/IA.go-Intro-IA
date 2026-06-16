from collections import deque
from environment.board import SudokuBoard
from metrics.tracker import Tracker


class CSPAgent:
    def __init__(self, board: SudokuBoard, tracker: Tracker):
        self.board   = board
        self.tracker = tracker

        self.variables     = self.board.get_empty_cells()
        self._initial_cells = self.board.get_initial_cells()

        self.domains = {
            var: set(range(1, 10))
            for var in self.variables
        }

        self.constraints = {
            var: self.board.get_neighbors(var)
            for var in self.variables
        }

    def ac3(self) -> bool:
        queue = deque(
            (xi, xj)
            for xi in self.variables
            for xj in self.constraints[xi]
            if xj in self.variables
        )

        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False
                for xk in self.constraints[xi]:
                    if xk != xj and xk in self.variables:
                        queue.append((xk, xi))

        return True

    def _revise(self, xi: tuple, xj: tuple) -> bool:
        revised = False

        if xj not in self.variables:
            xj_domain = {self.board.initial[xj[0]][xj[1]]}
        else:
            xj_domain = self.domains[xj]

        for x in set(self.domains[xi]):
            if x not in xj_domain:
                self.domains[xi].discard(x)
                revised = True

        return revised

    def solve(self) -> list[list[int]] | None:
        self.tracker.start()

        if not self.ac3():
            self.tracker.stop(solved=False)
            return None

        assignment = {}

        for i in range(9):
            for j in range(9):
                if self.board.initial[i][j] != 0:
                    assignment[(i, j)] = self.board.initial[i][j]

        result = self._backtrack(assignment)

        if result:
            self.board.apply_solution(result)
            self.tracker.final_conflicts = 0
            self.tracker.stop(solved=True)
            return self.board.grid
        else:
            self.tracker.stop(solved=False)
            return None

    def _backtrack(self, assignment: dict) -> dict | None:
        self.tracker.increment_nodes()

        if len(assignment) == len(self.variables) + len(self._initial_cells):
            return assignment

        var = self._select_unassigned_variable(assignment)

        for value in self._ordered_domain(var, assignment):
            if self._is_consistent(var, value, assignment):
                assignment[var] = value
                self._record_snapshot(assignment)

                saved_domains = {v: set(d) for v, d in self.domains.items()}

                result = self._backtrack(assignment)
                if result:
                    return result

                del assignment[var]
                self.domains = saved_domains
                self.tracker.increment_backtracks()

        return None

    def _select_unassigned_variable(self, assignment: dict) -> tuple:
        unassigned = [v for v in self.variables if v not in assignment]

        return min(
            unassigned,
            key=lambda var: (
                len([
                    v for v in self.domains[var]
                    if self._is_consistent(var, v, assignment)
                ]),
                -len([
                    n for n in self.constraints[var]
                    if n not in assignment
                ])
            )
        )

    def _ordered_domain(self, var: tuple, assignment: dict) -> list:
        def count_constraints(value):
            count = 0
            for neighbor in self.constraints[var]:
                if neighbor not in assignment and neighbor in self.variables:
                    if value in self.domains[neighbor]:
                        count += 1
            return count

        return sorted(self.domains[var], key=count_constraints)

    def _is_consistent(self, var: tuple, value: int, assignment: dict) -> bool:
        for neighbor in self.constraints[var]:
            if neighbor in assignment and assignment[neighbor] == value:
                return False
        return True

    def _record_snapshot(self, assignment: dict):
        grid = [row[:] for row in self.board.initial]
        for (i, j), val in assignment.items():
            grid[i][j] = val
        self.tracker.record_step(grid)
