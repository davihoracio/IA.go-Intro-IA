import pygame
import sys
import copy
import threading

from environment.board import SudokuBoard
from environment.puzzles import PUZZLES
from metrics.tracker import Tracker
from agents.csp_agent import CSPAgent
from agents.hill_climbing_agent import HillClimbingAgent

WIDTH, HEIGHT = 1200, 700

BG_COLOR = (245, 247, 250)
SIDEBAR_BG = (255, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_LINE_COLOR = (44, 62, 80)
TEXT_ORIG = (44, 62, 80)
TEXT_NEW = (41, 128, 185)
BTN_BG = (223, 230, 233)
BTN_HOVER = (178, 190, 195)
BTN_ACTIVE = (9, 132, 227)
BTN_TEXT = (45, 52, 54)
BTN_TEXT_ACTIVE = (255, 255, 255)
SOLVE_BG = (0, 184, 148)
SOLVE_HOVER = (85, 239, 196)

class Button:
    def __init__(self, x, y, w, h, text, font, bg_color=BTN_BG, active_color=BTN_ACTIVE, hover_color=BTN_HOVER):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.active_color = active_color
        self.hover_color = hover_color
        self.is_active = False
        self.is_hovered = False

    def draw(self, surface):
        if self.is_active:
            color = self.active_color
            text_color = BTN_TEXT_ACTIVE
        elif self.is_hovered:
            color = self.hover_color
            text_color = BTN_TEXT
        else:
            color = self.bg_color
            text_color = BTN_TEXT

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 1, border_radius=8)

        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_grid(surface, x, y, size, current_grid, initial_grid, font, title_font, font_sm, title, summary=None):
    cell_size = size / 9

    pygame.draw.rect(surface, WHITE, (x, y, size, size))
    pygame.draw.rect(surface, GRID_LINE_COLOR, (x, y, size, size), 3)

    title_surf = title_font.render(title, True, TEXT_ORIG)
    surface.blit(title_surf, (x + size/2 - title_surf.get_width()/2, y - 40))

    for i in range(1, 9):
        line_width = 3 if i % 3 == 0 else 1
        pygame.draw.line(surface, GRID_LINE_COLOR, (x, y + i * cell_size), (x + size, y + i * cell_size), line_width)
        pygame.draw.line(surface, GRID_LINE_COLOR, (x + i * cell_size, y), (x + i * cell_size, y + size), line_width)

    for r in range(9):
        for c in range(9):
            val = current_grid[r][c]
            if val != 0:
                color = TEXT_ORIG if initial_grid[r][c] != 0 else TEXT_NEW
                text = font.render(str(val), True, color)
                text_rect = text.get_rect(center=(x + c * cell_size + cell_size/2, y + r * cell_size + cell_size/2))
                surface.blit(text, text_rect)

    if summary:
        stats = [
            f"Resolvido: {'Sim' if summary.get('solved') else 'Não'}",
            f"Tempo: {summary.get('time_sec', 0)}s",
            f"Nós Expandidos: {summary.get('nodes', 0)}",
            f"Backtracks/Passos: {summary.get('backtracks', 0)}"
        ]
        if summary.get('final_conflicts', -1) >= 0:
            stats.append(f"Conflitos Finais: {summary.get('final_conflicts')}")

        for idx, stat in enumerate(stats):
            stat_surf = font_sm.render(stat, True, TEXT_ORIG)
            surface.blit(stat_surf, (x, y + size + 15 + idx * 22))

def rodar_interface():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("IA.go - Sudoku Solver")
    clock = pygame.time.Clock()

    font_board_large = pygame.font.SysFont("Arial", 32, bold=True)
    font_board_small = pygame.font.SysFont("Arial", 24, bold=True)
    font_ui = pygame.font.SysFont("Arial", 18)
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_status = pygame.font.SysFont("Arial", 16)
    font_sm = pygame.font.SysFont("Arial", 16)
    font_main_title = pygame.font.SysFont("Arial", 28, bold=True)

    selected_puzzle = "Fácil"
    selected_agent = "CSP"

    panel_w = 270
    panel_x = WIDTH - panel_w
    btn_x = panel_x + 35

    btn_facil  = Button(btn_x, 100, 200, 40, "Fácil", font_ui)
    btn_medio  = Button(btn_x, 150, 200, 40, "Médio", font_ui)
    btn_dificil = Button(btn_x, 200, 200, 40, "Difícil", font_ui)

    btn_csp   = Button(btn_x, 300, 200, 40, "CSP", font_ui)
    btn_hc    = Button(btn_x, 350, 200, 40, "Hill Climbing", font_ui)
    btn_ambos = Button(btn_x, 400, 200, 40, "Ambos", font_ui)

    btn_solve = Button(btn_x, 500, 200, 50, "RESOLVER", font_ui, bg_color=SOLVE_BG, active_color=SOLVE_HOVER, hover_color=SOLVE_HOVER)

    buttons = [btn_facil, btn_medio, btn_dificil, btn_csp, btn_hc, btn_ambos, btn_solve]

    initial_grid = copy.deepcopy(PUZZLES[selected_puzzle])

    grid_1    = copy.deepcopy(initial_grid)
    steps_1   = []
    summary_1 = None
    title_1   = "CSP"

    grid_2    = copy.deepcopy(initial_grid)
    steps_2   = []
    summary_2 = None
    title_2   = ""

    animating    = False
    is_solving   = False
    thread_results = {}
    solve_event  = threading.Event()
    step_index_1 = 0
    step_index_2 = 0
    step_skip_1  = 1
    step_skip_2  = 1
    status_msg   = "Pronto. Selecione a dificuldade e o agente."

    def update_button_states():
        btn_facil.is_active  = (selected_puzzle == "Fácil")
        btn_medio.is_active  = (selected_puzzle == "Médio")
        btn_dificil.is_active = (selected_puzzle == "Difícil")
        btn_csp.is_active   = (selected_agent == "CSP")
        btn_hc.is_active    = (selected_agent == "HC")
        btn_ambos.is_active = (selected_agent == "Ambos")

    update_button_states()

    def solve_agent(agent_type, in_grid):
        board   = SudokuBoard(copy.deepcopy(in_grid))
        tracker = Tracker()
        if agent_type == "CSP":
            agent = CSPAgent(board, tracker)
        else:
            agent = HillClimbingAgent(board, tracker, max_restarts=150, max_iterations=3000)
        agent.solve()
        return tracker.steps, tracker.summary(), board.grid

    running = True
    while running:
        screen.fill(BG_COLOR)

        pygame.draw.rect(screen, SIDEBAR_BG, (panel_x, 0, panel_w, HEIGHT))
        pygame.draw.line(screen, (220, 220, 220), (panel_x, 0), (panel_x, HEIGHT), 2)

        pos = pygame.mouse.get_pos()

        for btn in buttons:
            btn.update(pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not animating and not is_solving:
                if btn_facil.is_clicked(pos):   selected_puzzle = "Fácil"
                elif btn_medio.is_clicked(pos):  selected_puzzle = "Médio"
                elif btn_dificil.is_clicked(pos): selected_puzzle = "Difícil"

                if btn_csp.is_clicked(pos):   selected_agent = "CSP"
                elif btn_hc.is_clicked(pos):  selected_agent = "HC"
                elif btn_ambos.is_clicked(pos): selected_agent = "Ambos"

                if any(btn.is_clicked(pos) for btn in buttons[:-1]):
                    initial_grid = copy.deepcopy(PUZZLES[selected_puzzle])
                    grid_1 = copy.deepcopy(initial_grid)
                    grid_2 = copy.deepcopy(initial_grid)
                    summary_1 = None
                    summary_2 = None
                    status_msg = f"Puzzle '{selected_puzzle}' selecionado."

                    if selected_agent == "Ambos":
                        title_1 = "CSP"
                        title_2 = "Hill Climbing"
                    elif selected_agent == "CSP":
                        title_1 = "CSP"
                        title_2 = ""
                    else:
                        title_1 = "Hill Climbing"
                        title_2 = ""

                update_button_states()

                if btn_solve.is_clicked(pos):
                    status_msg = "A resolver... Aguarde!"
                    steps_1 = []
                    steps_2 = []
                    summary_1 = None
                    summary_2 = None
                    thread_results.clear()
                    solve_event.clear()
                    is_solving = True

                    _agent = selected_agent
                    _grid  = copy.deepcopy(initial_grid)

                    def _solve_worker(agent=_agent, grid=_grid):
                        if agent in ["CSP", "HC"]:
                            s, d, g = solve_agent(agent, grid)
                            thread_results['1'] = (s, d, g)
                        else:
                            s1, d1, g1 = solve_agent("CSP", grid)
                            s2, d2, g2 = solve_agent("HC", grid)
                            thread_results['1'] = (s1, d1, g1)
                            thread_results['2'] = (s2, d2, g2)
                        solve_event.set()

                    threading.Thread(target=_solve_worker, daemon=True).start()

        if is_solving and solve_event.is_set():
            is_solving = False
            if selected_agent in ["CSP", "HC"]:
                steps_1, summary_1, f_grid = thread_results['1']
                if len(steps_1) > 0:
                    step_skip_1  = max(1, len(steps_1) // 100)
                    step_index_1 = 0
                    animating    = True
                    status_msg   = "A animar solução..."
                else:
                    grid_1     = f_grid
                    status_msg = "Resolvido instantaneamente."
            else:
                steps_1, summary_1, f_grid_1 = thread_results['1']
                steps_2, summary_2, f_grid_2 = thread_results['2']
                if len(steps_1) == 0:
                    grid_1 = f_grid_1
                else:
                    step_skip_1  = max(1, len(steps_1) // 100)
                    step_index_1 = 0
                if len(steps_2) == 0:
                    grid_2 = f_grid_2
                else:
                    step_skip_2  = max(1, len(steps_2) // 100)
                    step_index_2 = 0
                if len(steps_1) > 0 or len(steps_2) > 0:
                    animating  = True
                    status_msg = "A animar solução..."
                else:
                    status_msg = "Resolvido instantaneamente."

        if animating:
            if selected_agent in ["CSP", "HC"]:
                if len(steps_1) > 0:
                    grid_1       = steps_1[step_index_1]
                    step_index_1 += step_skip_1
                    if step_index_1 >= len(steps_1):
                        step_index_1 = len(steps_1) - 1
                        grid_1       = steps_1[step_index_1]
                        animating    = False
                        status_msg   = "Resolvido!"
            elif selected_agent == "Ambos":
                anim_1_done = len(steps_1) == 0
                anim_2_done = len(steps_2) == 0

                if not anim_1_done:
                    grid_1       = steps_1[step_index_1]
                    step_index_1 += step_skip_1
                    if step_index_1 >= len(steps_1):
                        step_index_1 = len(steps_1) - 1
                        grid_1       = steps_1[step_index_1]
                        anim_1_done  = True

                if not anim_2_done:
                    grid_2       = steps_2[step_index_2]
                    step_index_2 += step_skip_2
                    if step_index_2 >= len(steps_2):
                        step_index_2 = len(steps_2) - 1
                        grid_2       = steps_2[step_index_2]
                        anim_2_done  = True

                if anim_1_done and anim_2_done:
                    animating  = False
                    status_msg = "Resolução concluída!"

        title_surf = font_main_title.render("IA.go - Sudoku Solver", True, TEXT_ORIG)
        screen.blit(title_surf, (30, 20))

        lbl_puzzle = font_title.render("Dificuldade", True, BLACK)
        screen.blit(lbl_puzzle, (btn_x, 60))

        lbl_agent = font_title.render("Algoritmo", True, BLACK)
        screen.blit(lbl_agent, (btn_x, 260))

        for btn in buttons:
            btn.draw(screen)

        status_color = (200, 0, 0) if (animating or is_solving) else TEXT_ORIG

        words = status_msg.split(' ')
        lines = []
        current_line = ""
        for word in words:
            if font_status.size(current_line + word)[0] < 220:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        for i, line in enumerate(lines):
            status_surf = font_status.render(line.strip(), True, status_color)
            screen.blit(status_surf, (btn_x, 570 + i * 20))

        main_area_w = panel_x
        if selected_agent in ["CSP", "HC"]:
            g_size = 450
            gx = (main_area_w - g_size) / 2
            gy = (HEIGHT - g_size) / 2 - 20
            draw_grid(screen, gx, gy, g_size, grid_1, initial_grid, font_board_large, font_title, font_sm, title_1, summary_1 if not animating else None)
        else:
            g_size   = 380
            spacing  = 40
            total_w  = 2 * g_size + spacing
            gx1 = (main_area_w - total_w) / 2
            gx2 = gx1 + g_size + spacing
            gy  = (HEIGHT - g_size) / 2 - 40

            draw_grid(screen, gx1, gy, g_size, grid_1, initial_grid, font_board_small, font_title, font_sm, title_1, summary_1 if not animating else None)
            draw_grid(screen, gx2, gy, g_size, grid_2, initial_grid, font_board_small, font_title, font_sm, title_2, summary_2 if not animating else None)

        pygame.display.flip()

        if animating or is_solving:
            clock.tick(30)
        else:
            clock.tick(15)
