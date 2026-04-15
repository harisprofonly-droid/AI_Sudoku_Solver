# sudoku_csp.py

# Global variables to track performance as required by Deliverable 3
backtrack_calls = 0
backtrack_failures = 0

def get_neighbors(row, col):
    """Finds all the intersecting cells for a given cell (row, col, and 3x3 box)."""
    neighbors = []
    
    # 1. Check row
    for c in range(9):
        if c != col:
            neighbors.append((row, c))
            
    # 2. Check column
    for r in range(9):
        if r != row:
            neighbors.append((r, col))
            
    # 3. Check 3x3 grid
    start_r = (row // 3) * 3
    start_c = (col // 3) * 3
    for r in range(start_r, start_r + 3):
        for c in range(start_c, start_c + 3):
            if r != row or c != col:
                # Avoid adding duplicates that we already found in the row/col check
                if (r, c) not in neighbors:
                    neighbors.append((r, c))
                    
    return neighbors

def read_board(filename):
    """Reads the 9x9 board from a text file."""
    board = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line != "": # Ignore any accidental empty lines
                row = []
                for char in line:
                    row.append(int(char))
                board.append(row)
    return board

def print_board(board):
    """Prints the board in a clean format."""
    for r in range(9):
        for c in range(9):
            print(board[r][c], end=" ")
        print()
    print()

def setup_domains(board):
    """Creates a dictionary mapping every (row, col) to its valid remaining values."""
    domains = {}
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                # Empty cells can potentially be any number 1-9
                domains[(r, c)] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            else:
                # Fixed cells only have one option
                domains[(r, c)] = [board[r][c]]
    return domains

def ac3(domains):
    """AC-3 algorithm to narrow down domains before we start guessing."""
    queue = []
    
    # Add all binary constraints (arcs) to the queue
    for r in range(9):
        for c in range(9):
            for nr, nc in get_neighbors(r, c):
                queue.append(((r, c), (nr, nc)))
                
    while len(queue) > 0:
        (r1, c1), (r2, c2) = queue.pop(0)
        
        revised = False
        
        # If the neighboring cell is fixed to a single value
        if len(domains[(r2, c2)]) == 1:
            val = domains[(r2, c2)][0]
            # If that exact value is in our cell's domain, remove it
            if val in domains[(r1, c1)] and len(domains[(r1, c1)]) > 1:
                domains[(r1, c1)].remove(val)
                revised = True
                
        # If we changed the domain, we have to re-evaluate its neighbors
        if revised:
            if len(domains[(r1, c1)]) == 0:
                return False # A cell has 0 valid options (Contradiction)
                
            for nr, nc in get_neighbors(r1, c1):
                if (nr, nc) != (r2, c2):
                    queue.append(((nr, nc), (r1, c1)))
                    
    return True

def forward_check(domains, row, col, value):
    """Creates a new state of domains by removing 'value' from neighbors."""
    # Make a manual copy of domains so we don't ruin the original if we have to backtrack
    new_domains = {}
    for key in domains:
        new_domains[key] = list(domains[key])
        
    for nr, nc in get_neighbors(row, col):
        if value in new_domains[(nr, nc)]:
            new_domains[(nr, nc)].remove(value)
            
            # If a neighbor has no valid options left, this path is a dead end
            if len(new_domains[(nr, nc)]) == 0:
                return False
                
    return new_domains

def solve(board, domains):
    """Backtracking search using the MRV heuristic."""
    global backtrack_calls
    global backtrack_failures
    
    backtrack_calls += 1

    # Heuristic: MRV (Minimum Remaining Values)
    # Find the empty cell with the fewest possible valid options left
    min_options = 10
    best_r = -1
    best_c = -1
    
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                if len(domains[(r, c)]) < min_options:
                    min_options = len(domains[(r, c)])
                    best_r = r
                    best_c = c
                    
    # If we didn't find any empty cells, the board is completely filled!
    if best_r == -1:
        return True
        
    # Try all valid values for the best cell we found
    for value in domains[(best_r, best_c)]:
        board[best_r][best_c] = value
        
        # Run forward checking
        new_domains = forward_check(domains, best_r, best_c, value)
        
        if new_domains != False:
            # Lock in the value in the new domain state
            new_domains[(best_r, best_c)] = [value]
            
            # Recursively try to solve the rest of the board
            if solve(board, new_domains):
                return True
                
        # If it didn't work, reset the cell (undo)
        board[best_r][best_c] = 0
        
    # If no values worked, this entire branch fails and we step backward
    backtrack_failures += 1
    return False

def main():
    global backtrack_calls
    global backtrack_failures
    
    # The text files provided in the assignment format
    files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]
    
    for filename in files:
        print("========================================")
        print("Solving:", filename)
        
        try:
            board = read_board(filename)
            domains = setup_domains(board)
            
            # Reset the counters for each individual puzzle
            backtrack_calls = 0
            backtrack_failures = 0
            
            # Step 1: Pre-process with AC-3
            if ac3(domains):
                # Step 2: Start Backtracking Search
                if solve(board, domains):
                    print("Solution found!")
                    print_board(board)
                else:
                    print("Failed to find a solution.")
            else:
                print("AC-3 found a contradiction in the initial board.")
                
            print("BACKTRACK calls:", backtrack_calls)
            print("BACKTRACK returned failure:", backtrack_failures)
            print()
            
        except FileNotFoundError:
            print(f"Error: Make sure '{filename}' is in the same folder as this script!")

if __name__ == "__main__":
    main()