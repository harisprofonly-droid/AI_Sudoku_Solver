import tkinter as tk
from tkinter import ttk
import copy
import time
import sys

# -------- CSP SOLVER --------

class SudokuCSP:
    def __init__(self, board):
        self.variables = [(r, c) for r in range(9) for c in range(9)]
        self.domains = {}
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    self.domains[(r, c)] = list(range(1, 10))
                else:
                    self.domains[(r, c)] = [board[r][c]]
        self.neighbors = {v: set() for v in self.variables}
        self.setup_neighbors()
        
    def setup_neighbors(self):
        for r, c in self.variables:
            for c2 in range(9):
                if c != c2: self.neighbors[(r, c)].add((r, c2))
            for r2 in range(9):
                if r != r2: self.neighbors[(r, c)].add((r2, c))
            br, bc = r // 3, c // 3
            for i in range(3):
                for j in range(3):
                    r2, c2 = br * 3 + i, bc * 3 + j
                    if (r2, c2) != (r, c):
                        self.neighbors[(r, c)].add((r2, c2))

def ac3(csp, queue=None):
    if queue is None:
        queue = [(Xi, Xj) for Xi in csp.variables for Xj in csp.neighbors[Xi]]
    
    while queue:
        (Xi, Xj) = queue.pop(0)
        if revise(csp, Xi, Xj):
            if not csp.domains[Xi]:
                return False
            for Xk in csp.neighbors[Xi]:
                if Xk != Xj:
                    queue.append((Xk, Xi))
    return True

def revise(csp, Xi, Xj):
    revised = False
    for x in csp.domains[Xi][:]:
        satisfies = any(x != y for y in csp.domains[Xj])
        if not satisfies:
            csp.domains[Xi].remove(x)
            revised = True
    return revised

class BacktrackSolver:
    def __init__(self, csp, update_gui_callback=None):
        self.csp = csp
        self.calls = 0
        self.failures = 0
        self.update_gui = update_gui_callback
        
    def is_complete(self):
        return all(len(self.csp.domains[v]) == 1 for v in self.csp.variables)
        
    def select_unassigned_variable(self):
        unassigned = [v for v in self.csp.variables if len(self.csp.domains[v]) > 1]
        return min(unassigned, key=lambda v: len(self.csp.domains[v]))
        
    def solve(self):
        # Initial AC-3
        ac3(self.csp)
        if self.update_gui:
            self.update_gui(self.csp.domains, self.calls, self.failures)
        return self.backtrack()
        
    def backtrack(self):
        self.calls += 1
        
        if self.is_complete():
            if self.update_gui:
                self.update_gui(self.csp.domains, self.calls, self.failures)
            return True
            
        var = self.select_unassigned_variable()
        domain_copy = {k: list(v) for k, v in self.csp.domains.items()}
        
        for value in self.csp.domains[var]:
            self.csp.domains[var] = [value]
            
            queue = [(Xk, var) for Xk in self.csp.neighbors[var]]
            
            if ac3(self.csp, queue):
                # Optionally update GUI on every assignment, but it slows down extremely
                # For basic visual tracking of big steps:
                if self.update_gui and self.calls % 50 == 0:
                    self.update_gui(self.csp.domains, self.calls, self.failures)

                result = self.backtrack()
                if result:
                    return result
                    
            self.csp.domains = {k: list(v) for k, v in domain_copy.items()}
            
        self.failures += 1
        return False


# -------- GRAPHICS --------

class SudokuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSP Sudoku Solver")
        self.geometry("600x700")
        
        # UI Elements
        self.header_label = tk.Label(self, text="CSP Based Sudoku Solver (AC-3 + Backtrack)", font=("Helvetica", 16, "bold"))
        self.header_label.pack(pady=10)
        
        self.stats_label = tk.Label(self, text="File: None | Calls: 0 | Failures: 0", font=("Helvetica", 12))
        self.stats_label.pack(pady=5)
        
        self.canvas = tk.Canvas(self, width=450, height=450, bg='white')
        self.canvas.pack(pady=10)
        
        self.btn_frame = tk.Frame(self)
        self.btn_frame.pack(pady=10)
        
        self.files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]
        self.current_idx = 0
        
        self.btn_solve = tk.Button(self.btn_frame, text="Solve Current", command=self.start_solve, font=("Helvetica", 12), width=15)
        self.btn_solve.grid(row=0, column=0, padx=10)
        
        self.btn_next = tk.Button(self.btn_frame, text="Next Board", command=self.load_next, font=("Helvetica", 12), width=15)
        self.btn_next.grid(row=0, column=1, padx=10)

        self.cell_size = 50
        self.current_board = []
        self.load_board(self.files[self.current_idx])

    def draw_grid(self, domains=None):
        self.canvas.delete("all")
        for i in range(10):
            width = 3 if i % 3 == 0 else 1
            self.canvas.create_line(0, i * self.cell_size, 450, i * self.cell_size, width=width)
            self.canvas.create_line(i * self.cell_size, 0, i * self.cell_size, 450, width=width)
            
        for r in range(9):
            for c in range(9):
                text = ""
                color = "black"
                
                # Check original value
                if self.current_board[r][c] != 0:
                    text = str(self.current_board[r][c])
                    color = "blue"
                elif domains and len(domains[(r, c)]) == 1:
                    text = str(domains[(r, c)][0])
                    color = "black"
                elif domains and len(domains[(r, c)]) > 1:
                    pass # Don't display anything if uncertain, or show domain size?
                
                x = c * self.cell_size + self.cell_size // 2
                y = r * self.cell_size + self.cell_size // 2
                self.canvas.create_text(x, y, text=text, font=("Helvetica", 18, "bold"), fill=color)

    def update_stats(self, filename, calls, failures):
        self.stats_label.config(text=f"File: {filename} | Backtrack Calls: {calls} | Failures: {failures}")
        self.update()

    def update_gui_callback(self, domains, calls, failures):
        self.draw_grid(domains)
        self.update_stats(self.files[self.current_idx], calls, failures)

    def load_board(self, filename):
        self.current_board = []
        try:
            with open(filename, 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    row = [int(c) for c in line.strip() if c.isdigit()]
                    if row:
                        self.current_board.append(row)
            self.draw_grid()
            self.update_stats(filename, 0, 0)
        except Exception as e:
            self.stats_label.config(text=f"Error loading {filename}: {e}")

    def load_next(self):
        self.current_idx = (self.current_idx + 1) % len(self.files)
        self.load_board(self.files[self.current_idx])

    def start_solve(self):
        self.btn_solve.config(state="disabled")
        self.btn_next.config(state="disabled")
        
        filename = self.files[self.current_idx]
        if not self.current_board:
            return
            
        csp = SudokuCSP(self.current_board)
        solver = BacktrackSolver(csp, update_gui_callback=self.update_gui_callback)
        
        success = solver.solve()
        
        # Final update
        self.update_gui_callback(csp.domains, solver.calls, solver.failures)
        
        if success:
            self.stats_label.config(text=f"File: {filename} | SOLVED! Calls: {solver.calls} | Failures: {solver.failures}")
        else:
            self.stats_label.config(text=f"File: {filename} | NO SOLUTION. Calls: {solver.calls}")
            
        self.btn_solve.config(state="normal")
        self.btn_next.config(state="normal")


if __name__ == "__main__":
    app = SudokuGUI()
    app.mainloop()
