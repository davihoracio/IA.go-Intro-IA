# IA.go — Sudoku Solver

Projeto acadêmico desenvolvido para a disciplina de **Introdução à Inteligência Artificial**.

**Autores:**
- Anna Letícia Fernandes Barbosa
- Davi Horácio de Souza
- Maria Luiza Santos da Silva

---

Implementa e compara dois agentes de busca para resolver puzzles de Sudoku: **CSP com Backtracking + AC-3 + MRV** e **Hill Climbing com Reinício Aleatório**. Conta com interface gráfica animada (Pygame) e modo terminal para análise comparativa.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura do Projeto](#arquitetura-do-projeto)
- [Algoritmos](#algoritmos)
  - [CSP — Constraint Satisfaction Problem](#csp--constraint-satisfaction-problem)
  - [Hill Climbing com Reinício Aleatório](#hill-climbing-com-reinício-aleatório)
- [Métricas Coletadas](#métricas-coletadas)
- [Interface Gráfica](#interface-gráfica)
- [Modo Terminal](#modo-terminal)
- [Puzzles Disponíveis](#puzzles-disponíveis)
- [Instalação e Execução](#instalação-e-execução)
- [Estrutura de Arquivos](#estrutura-de-arquivos)

---

## Visão Geral

O **IA.go-Sudoku** resolve puzzles de Sudoku utilizando dois paradigmas distintos de IA:

| Agente | Paradigma | Garante solução? |
|--------|-----------|-----------------|
| CSP | Busca com satisfação de restrições | Sim (se existir) |
| Hill Climbing | Busca local estocástica | Não garantido |

O objetivo é permitir a comparação direta de desempenho — tempo, nós expandidos, backtracks — entre as abordagens, tanto visualmente (GUI animada) quanto numericamente (modo terminal).

---

## Arquitetura do Projeto

```
IA.go-Sudoku/
├── main.py                     # Ponto de entrada (GUI ou terminal)
├── environment/
│   └── board.py                # Representação do tabuleiro e regras do Sudoku
├── agents/
│   ├── csp_agent.py            # Agente CSP (Backtracking + AC-3 + MRV)
│   └── hill_climbing_agent.py  # Agente Hill Climbing com reinício aleatório
├── metrics/
│   └── tracker.py              # Rastreamento de métricas de desempenho
└── interface/
    └── gui.py                  # Interface gráfica com Pygame
```

### Responsabilidades por módulo

**`environment/board.py` — SudokuBoard**
- Mantém o puzzle original (`initial`) separado do grid em edição (`grid`)
- Fornece células vazias, vizinhos (linha + coluna + bloco) e validação de valores
- Não resolve nada — é um ambiente passivo que os agentes consultam

**`metrics/tracker.py` — Tracker**
- Cronometra a execução (`start` / `stop`)
- Conta nós expandidos e backtracks
- Grava snapshots de cada estado para animação na GUI
- Exporta dicionário de métricas via `summary()`

**`agents/csp_agent.py` — CSPAgent**
- Implementa o pipeline: AC-3 → Backtracking com MRV

**`agents/hill_climbing_agent.py` — HillClimbingAgent**
- Busca local com geração de estado inicial por blocos e reinícios aleatórios

**`interface/gui.py` — rodar_interface()**
- Interface completa em Pygame com seleção de dificuldade, agente e animação passo a passo

---

## Algoritmos

### CSP — Constraint Satisfaction Problem

Implementado em `agents/csp_agent.py`, o agente CSP trata o Sudoku como um problema de satisfação de restrições onde cada célula vazia é uma variável com domínio `{1..9}` e as restrições são as regras do Sudoku (unicidade em linha, coluna e bloco 3×3).

#### Pipeline de resolução

```
Puzzle → AC-3 (redução de domínios) → Backtracking + MRV → Solução
```

**1. AC-3 — Arc Consistency 3**

Antes do backtracking, o AC-3 propaga restrições entre variáveis vizinhas para reduzir domínios. Para cada arco `(Xi, Xj)`, remove de `domain[Xi]` os valores que não têm suporte em `domain[Xj]`. Se algum domínio ficar vazio, o puzzle não tem solução.

```python
def ac3(self) -> bool:
    queue = deque((xi, xj) for xi in self.variables
                            for xj in self.constraints[xi]
                            if xj in self.variables)
    while queue:
        xi, xj = queue.popleft()
        if self._revise(xi, xj):
            if len(self.domains[xi]) == 0:
                return False
            for xk in self.constraints[xi]:
                if xk != xj and xk in self.variables:
                    queue.append((xk, xi))
    return True
```

**2. Backtracking Recursivo**

Percorre as variáveis não atribuídas tentando valores do domínio. Ao detectar inconsistência, volta (backtrack) e tenta o próximo valor.

**3. MRV — Minimum Remaining Values**

Heurística de seleção de variável: escolhe sempre a célula com o menor número de valores ainda consistentes com o estado atual do assignment. Em caso de empate, desempata pela maior quantidade de vizinhos não atribuídos (grau).

```
MRV: min(variáveis não atribuídas, key= domínio disponível atual)
Desempate: max(vizinhos não atribuídos) — heurística de grau
```

**4. LCV — Least Constraining Value**

Ao ordenar os valores do domínio, prioriza os que eliminam menos opções dos vizinhos, melhorando a performance média do backtracking.

---

### Hill Climbing com Reinício Aleatório

Implementado em `agents/hill_climbing_agent.py`, é uma busca local que opera diretamente no espaço de estados completos, sem backtracking global.

#### Estratégia

**1. Geração do estado inicial**

Cada bloco 3×3 é preenchido com os números faltantes, embaralhados aleatoriamente. Isso garante que **nenhum bloco tenha conflitos internos** desde o início — apenas linhas e colunas podem conter conflitos, reduzindo o espaço de busca efetivo.

**2. Função heurística — contagem de conflitos**

```
conflitos = Σ (9 - valores_únicos_na_linha) + Σ (9 - valores_únicos_na_coluna)
```

Zero conflitos = solução perfeita. Blocos nunca são contados pois, por construção e pelas trocas, sempre permanecem sem conflito.

**3. Geração de vizinhos**

A cada iteração, percorre **todos os blocos 3×3** e avalia **todas as trocas possíveis** entre células livres dentro de cada bloco. Aceita o vizinho de menor custo global.

**4. Movimentos laterais e reinícios**

| Situação | Ação |
|----------|------|
| Vizinho melhora custo | Aceita e continua |
| Vizinho tem custo igual + `sideways < max_sideways` | Aceita (escape de platô) |
| Ótimo local atingido | Reinício aleatório |
| Todos os restarts esgotados | Retorna melhor estado encontrado |

**Parâmetros padrão:**

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `max_restarts` | 150 | Número máximo de reinícios |
| `max_iterations` | 3000 | Iterações por reinício |
| `max_sideways` | 50 | Movimentos laterais permitidos antes de reiniciar |

---

## Métricas Coletadas

O `Tracker` coleta as seguintes métricas para cada execução:

| Métrica | CSP | Hill Climbing | Descrição |
|---------|:---:|:-------------:|-----------|
| Solução encontrada | ✅ | ✅ | Se o puzzle foi resolvido perfeitamente |
| Conflitos finais | — | ✅ | Conflitos restantes (0 = perfeito) |
| Nós expandidos | ✅ | ✅ | Total de estados avaliados |
| Backtracks | ✅ | — | Retrocessos no backtracking |
| Passos gravados | ✅ | ✅ | Snapshots para animação |
| Tempo (s) | ✅ | ✅ | Tempo total de execução |

---

## Interface Gráfica

A GUI é construída com **Pygame** e oferece:

- **Seleção de dificuldade:** Fácil, Médio, Difícil
- **Seleção de agente:** CSP, Hill Climbing, ou Ambos (side-by-side)
- **Animação passo a passo** da resolução, com velocidade adaptativa (até 100 frames de snapshot)
- **Painel lateral** com botões interativos, estado atual e métricas pós-resolução
- **Cores diferenciadas:** números originais em azul escuro, números resolvidos em azul claro

### Modo "Ambos"

Ao selecionar "Ambos", os dois agentes rodam em paralelo (threads separadas) e os dois grids são animados simultaneamente lado a lado, permitindo comparação visual direta.

```
┌─────────────────────────────┬─────────────────┐
│   CSP          Hill Climbing│   Dificuldade   │
│  [grid]          [grid]     │  [Fácil][Médio] │
│                             │  [Difícil]      │
│  métricas      métricas     │   Algoritmo     │
│                             │  [CSP][HC]      │
│                             │  [Ambos]        │
│                             │  [RESOLVER]     │
└─────────────────────────────┴─────────────────┘
```

---

## Modo Terminal

Roda os três puzzles sequencialmente e imprime uma tabela comparativa:

```
$ python main.py --terminal
```

Saída exemplo:

```
──────────────────────────────────────────────────────────
  COMPARAÇÃO — Puzzle: Fácil
──────────────────────────────────────────────────────────
  Métrica                            CSP  Hill Climbing
  ──────────────────────────── ──────────── ──────────────
  Solução encontrada              Sim ✅        Sim ✅
  Conflitos finais                     0             0
  Nós expandidos                     127         8.432
  Backtracks                           3             —
  Passos gravados                    130         8.432
  Tempo (s)                       0.0021        0.3841
──────────────────────────────────────────────────────────
  → CSP foi 182.9x mais rápido.
```

---

## Puzzles Disponíveis

| Nível | Células preenchidas | Células vazias | Descrição |
|-------|:------------------:|:--------------:|-----------|
| **Fácil** | 36 / 81 (44.4%) | 45 / 81 (55.6%) | Mais dicas, restrições mais diretas |
| **Médio** | 30 / 81 (37.0%) | 51 / 81 (63.0%) | Menos dicas, busca mais extensa |
| **Difícil** | 23 / 81 (28.4%) | 58 / 81 (71.6%) | Puzzle próximo do mínimo de dicas |

Os puzzles estão definidos em `main.py` (modo terminal) e `interface/gui.py` (modo GUI) e são idênticos entre os dois arquivos.

---

## Instalação e Execução

### Pré-requisitos

- Python 3.10+
- Pygame

```bash
pip install pygame
```

### Executar a interface gráfica (padrão)

```bash
python main.py
```

### Executar no terminal com comparativo

```bash
python main.py --terminal
```

---

## Estrutura de Arquivos

```
IA.go-Sudoku/
├── main.py
├── environment/
│   ├── __init__.py
│   └── board.py
├── agents/
│   ├── __init__.py
│   ├── csp_agent.py
│   └── hill_climbing_agent.py
├── metrics/
│   ├── __init__.py
│   └── tracker.py
└── interface/
    ├── __init__.py
    └── gui.py
```
