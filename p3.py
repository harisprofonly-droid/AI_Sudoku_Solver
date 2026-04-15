import sys
import copy

class SudokuCSP:
    """
    Representation of the Sudoku board as a Constraint Satisfaction Problem.
    """
    def __init__(self, board):
        # Variables: list of (row, col) tuples
        self.variables = [(r, c) for r in range(9) for c in range(9)]
        
        # Domains: dictionary mapping variable to list of possible values
        self.domains = {}
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    self.domains[(r, c)] = list(range(1, 10))
                else:
                    self.domains[(r, c)] = [board[r][c]]
                    
        # Neighbors: dictionary mapping variable to set of related variables (arcs)
        self.neighbors = {v: set() for v in self.variables}
        self.setup_neighbors()
        
    def setup_neighbors(self):
        """
        Setup constraints by mapping each cell to its neighbors in the same row,
        column, and 3x3 subgrid.
        """
        for r, c in self.variables:
            # Same row
            for c2 in range(9):
                if c != c2: self.neighbors[(r, c)].add((r, c2))
            # Same col
            for r2 in range(9):
                if r != r2: self.neighbors[(r, c)].add((r2, c))
            # Same 3x3 block
            br, bc = r // 3, c // 3
            for i in range(3):
                for j in range(3):
                    r2, c2 = br * 3 + i, bc * 3 + j
                    if (r2, c2) != (r, c):
                        self.neighbors[(r, c)].add((r2, c2))

def ac3(csp, queue=None):
    """
    AC-3 Algorithm for Arc Consistency.
    If queue is None, initialize with all arcs in the CSP.
    """
    if queue is None:
        queue = [(Xi, Xj) for Xi in csp.variables for Xj in csp.neighbors[Xi]]
    
    while queue:
        (Xi, Xj) = queue.pop(0)
        if revise(csp, Xi, Xj):
            if not csp.domains[Xi]:
                return False # Domain is empty, inconsistency found
            for Xk in csp.neighbors[Xi]:
                if Xk != Xj:
                    queue.append((Xk, Xi))
    return True

def revise(csp, Xi, Xj):
    """
    Revise the domain of Xi to be consistent with Xj.
    Returns True if the domain was modified.
    """
    revised = False
    for x in csp.domains[Xi][:]:
        # If no value y in Dj allows (x,y) to satisfy the constraint Xi != Xj
        satisfies = any(x != y for y in csp.domains[Xj])
        if not satisfies:
            csp.domains[Xi].remove(x)
            revised = True
    return revised

class BacktrackSolver:
    """
    Backtracking Search solver with Forward Checking and Maintaining Arc Consistency (MAC).
    """
    def __init__(self, csp):
        self.csp = csp
        self.calls = 0
        self.failures = 0
        
    def is_complete(self):
        """Check if all variables have exactly one assigned value."""
        return all(len(self.csp.domains[v]) == 1 for v in self.csp.variables)
        
    def select_unassigned_variable(self):
        """
        Minimum Remaining Values (MRV) heuristic:
        Choose the variable with the fewest remaining valid values in its domain.
        """
        unassigned = [v for v in self.csp.variables if len(self.csp.domains[v]) > 1]
        return min(unassigned, key=lambda v: len(self.csp.domains[v]))
        
    def solve(self):
        """Initiate solving process."""
        # Initial AC-3 run to simplify the problem before search begins
        ac3(self.csp)
        return self.backtrack()
        
    def backtrack(self):
        """
        Recursive Backtracking Search algorithm.
        Returns True if successful, False otherwise.
        """
        self.calls += 1
        
        if self.is_complete():
            return True
            
        var = self.select_unassigned_variable()
        
        domain_copy = {k: list(v) for k, v in self.csp.domains.items()}
        
        for value in self.csp.domains[var]:
            # Try assigning the value to the variable
            self.csp.domains[var] = [value]
            
            # Use AC-3 for forward checking / constraint propagation
            # We add all arcs (Xk, var) for the neighbors of the assigned variable
            queue = [(Xk, var) for Xk in self.csp.neighbors[var]]
            
            if ac3(self.csp, queue):
                # If consistent, move to the next variable
                result = self.backtrack()
                if result:
                    return result
                    
            # If failed, restore the domain and try next value
            self.csp.domains = {k: list(v) for k, v in domain_copy.items()}
            
        # If no values worked, record a failure
        self.failures += 1
        return False

def print_board(csp):
    """Utility function to print the solved Sudoku board."""
    for r in range(9):
        row_str = ""
        for c in range(9):
            row_str += str(csp.domains[(r, c)][0]) + " "
        print(row_str.strip())

def solve_file(filename):
    print(f"--- Solving {filename} ---")
    try:
        with open(filename, 'r') as f:
            lines = f.read().splitlines()
            if not lines: return None, None
            board = []
            for line in lines:
                row = [int(c) for c in line.strip() if c.isdigit()]
                if not row: continue
                board.append(row)
        
        csp = SudokuCSP(board)
        solver = BacktrackSolver(csp)
        
        success = solver.solve()
        
        if success:
            print("Solution found!")
            print_board(csp)
        else:
            print("No solution exists.")
            
        print(f"BACKTRACK calls: {solver.calls}")
        print(f"BACKTRACK failures: {solver.failures}")
        print()
        return solver.calls, solver.failures
        
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None, None

if __name__ == "__main__":
    solve_file("easy.txt")
    solve_file("medium.txt")
    solve_file("hard.txt")
    solve_file("veryhard.txt")
