import time

class Tracker:
    # 1. Introdução e Ciclo de Vida
    def __init__(self):
        self.nodes            = 0
        self.backtracks       = 0
        self.start_time       = None
        self.end_time         = None
        self.steps            = []
        self.solved           = False
        self.final_conflicts  = -1

    def start(self):
        self.nodes           = 0
        self.backtracks      = 0
        self.steps           = []
        self.solved          = False
        self.final_conflicts = -1
        self.start_time      = time.time()

    def stop(self, solved: bool):
        self.end_time = time.time()
        self.solved   = solved

    # 2. Coleta Contínua de Esforço Computacional
    def increment_nodes(self):
        self.nodes += 1

    def increment_backtracks(self):
        self.backtracks += 1

    # 3. Captura de Histórico Visual
    def record_step(self, grid: list[list[int]]):
        self.steps.append([row[:] for row in grid])

    # 4. Consolidação e Exportação de Dados
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return round(end - self.start_time, 4)
    
    def summary(self) -> dict:
        return {
            "solved"          : self.solved,
            "nodes"           : self.nodes,
            "backtracks"      : self.backtracks,
            "time_sec"        : self.elapsed(),
            "steps"           : len(self.steps),
            "final_conflicts" : self.final_conflicts,
        }

    def print_summary(self, agent_name: str = "Agente"):
        s  = self.summary()
        cf = s["final_conflicts"]
        cf_str = str(cf) if cf >= 0 else "—"
        print(f"\n{'='*38}")
        print(f"  Resultado — {agent_name}")
        print(f"{'='*38}")
        print(f"  Solução encontrada : {'Sim' if s['solved'] else 'Não'}")
        print(f"  Conflitos finais   : {cf_str}")
        print(f"  Nós expandidos     : {s['nodes']}")
        print(f"  Backtracks         : {s['backtracks']}")
        print(f"  Passos gravados    : {s['steps']}")
        print(f"  Tempo de execução  : {s['time_sec']}s")
        print(f"{'='*38}\n")