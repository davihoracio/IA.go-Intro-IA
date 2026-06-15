import sys

def modo_terminal():
    from environment.board          import SudokuBoard
    from metrics.tracker            import Tracker
    from agents.csp_agent           import CSPAgent
    from agents.hill_climbing_agent import HillClimbingAgent

    from environment.puzzles import PUZZLES
    puzzles = PUZZLES

    def print_board(grid):
        for i in range(9):
            if i % 3 == 0 and i != 0:
                print("-" * 21)
            for j in range(9):
                if j % 3 == 0 and j != 0:
                    print("|", end=" ")
                print(grid[i][j] if grid[i][j] != 0 else ".", end=" ")
            print()

    def print_comparacao(nome, cs, hs):
        print(f"\n{'─'*58}")
        print(f"  COMPARAÇÃO — Puzzle: {nome}")
        print(f"{'─'*58}")
        print(f"  {'Métrica':<26} {'CSP':>14} {'Hill Climbing':>14}")
        print(f"  {'─'*26} {'─'*14} {'─'*14}")
        f = lambda v: "Sim ✅" if v else "Não ❌"
        print(f"  {'Solução encontrada':<26} {f(cs['solved']):>14} {f(hs['solved']):>14}")
        cf_c = str(cs['final_conflicts']) if cs['final_conflicts'] >= 0 else "—"
        cf_h = str(hs['final_conflicts']) if hs['final_conflicts'] >= 0 else "—"
        print(f"  {'Conflitos finais':<26} {cf_c:>14} {cf_h:>14}")
        print(f"  {'Nós expandidos':<26} {cs['nodes']:>14,} {hs['nodes']:>14,}")
        bt = f"{cs['backtracks']:,}"
        print(f"  {'Backtracks':<26} {bt:>14} {'—':>14}")
        print(f"  {'Passos gravados':<26} {cs['steps']:>14,} {hs['steps']:>14,}")
        print(f"  {'Tempo (s)':<26} {cs['time_sec']:>14.4f} {hs['time_sec']:>14.4f}")
        print(f"{'─'*58}")
        if cs['solved'] and hs['solved']:
            ratio = hs['time_sec'] / max(cs['time_sec'], 0.0001)
            print(f"  → CSP foi {ratio:.1f}x mais rápido.")
        elif cs['solved']:
            print("  → Apenas CSP encontrou solução perfeita.")
        elif hs['solved']:
            print("  → Apenas Hill Climbing encontrou solução.")
        else:
            print(f"  → Nenhum achou solução. Melhor HC: {hs['final_conflicts']} conflito(s).")

    for nome, puzzle in puzzles.items():
        print(f"\n{'#'*48}\n  {nome}\n{'#'*48}")
        print("\nPuzzle inicial:\n")
        print_board(puzzle)

        b1, t1 = SudokuBoard(puzzle), Tracker()
        print("\n[CSP] Resolvendo...")
        CSPAgent(b1, t1).solve()
        if t1.solved:
            print("[CSP] Solução:\n")
            print_board(b1.grid)

        b2, t2 = SudokuBoard(puzzle), Tracker()
        print("\n[HC]  Resolvendo...")
        HillClimbingAgent(b2, t2, max_restarts=150, max_iterations=3000).solve()
        if t2.solved:
            print("[HC]  Solução:\n")
            print_board(b2.grid)
        else:
            print(f"[HC]  Melhor resultado ({t2.final_conflicts} conflito(s)):\n")
            print_board(b2.grid)

        print_comparacao(nome, t1.summary(), t2.summary())

    print("\nTeste concluído.")


if __name__ == "__main__":
    if "--terminal" in sys.argv:
        modo_terminal()
    else:
        from interface.gui import rodar_interface
        rodar_interface()
