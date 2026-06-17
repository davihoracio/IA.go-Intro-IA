class SudokuBoard:
    # 1. Representação Matricial e a Regra de Imutabilidade
    def __init__(self, puzzle: list[list[int]]):
        self.initial = [row[:] for row in puzzle]
        self.grid    = [row[:] for row in puzzle]

    # 2. Mapeamento do Espaço de Estados
    def get_empty_cells(self) -> list[tuple[int, int]]:
        return [
            (i, j)
            for i in range(9)
            for j in range(9)
            if self.initial[i][j] == 0
        ]

    def get_initial_cells(self) -> list[tuple[int, int]]:
        return [
            (i, j)
            for i in range(9)
            for j in range(9)
            if self.initial[i][j] != 0
        ]

    def get_neighbors(self, var: tuple[int, int]) -> set[tuple[int, int]]:
        i, j = var
        neighbors = set()

        for k in range(9):
            if k != j:
                neighbors.add((i, k))
            if k != i:
                neighbors.add((k, j))

        box_i = (i // 3) * 3
        box_j = (j // 3) * 3
        for r in range(box_i, box_i + 3):
            for c in range(box_j, box_j + 3):
                if (r, c) != var:
                    neighbors.add((r, c))

        return neighbors

    # 3. Validação Regrada vs. Heurística de Custo
    def is_valid_value(self, row: int, col: int, num: int) -> bool:
        if num in self.grid[row]:
            return False

        if num in [self.grid[r][col] for r in range(9)]:
            return False

        box_r = (row // 3) * 3
        box_c = (col // 3) * 3
        for r in range(box_r, box_r + 3):
            for c in range(box_c, box_c + 3):
                if self.grid[r][c] == num:
                    return False

        return True

    def is_solved(self) -> bool:
        for i in range(9):
            row = [self.grid[i][j] for j in range(9)]
            col = [self.grid[j][i] for j in range(9)]
            if sorted(row) != list(range(1, 10)):
                return False
            if sorted(col) != list(range(1, 10)):
                return False

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                block = [
                    self.grid[box_r + r][box_c + c]
                    for r in range(3)
                    for c in range(3)
                ]
                if sorted(block) != list(range(1, 10)):
                    return False

        return True

    @staticmethod
    def count_conflicts(grid: list[list[int]]) -> int:
        conflicts = 0

        for i in range(9):
            row = [grid[i][j] for j in range(9)]
            col = [grid[j][i] for j in range(9)]
            conflicts += (9 - len(set(row)))
            conflicts += (9 - len(set(col)))

        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                box = [grid[box_r + r][box_c + c] for r in range(3) for c in range(3)]
                conflicts += (9 - len(set(box)))

        return conflicts

    # 4. Interface de Modificação e Estado
    def apply_solution(self, assignment: dict[tuple[int, int], int]):
        for (i, j), val in assignment.items():
            self.grid[i][j] = val

    def reset(self):
        self.grid = [row[:] for row in self.initial]

    def print_board(self, grid: list[list[int]] | None = None):
        board = grid if grid is not None else self.grid

        for i in range(9):
            if i % 3 == 0 and i != 0:
                print("-" * 21)

            for j in range(9):
                if j % 3 == 0 and j != 0:
                    print("|", end=" ")
                print(board[i][j] if board[i][j] != 0 else ".", end=" ")
            print()