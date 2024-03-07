import random

class Game(object):
    """
    A Sudoku game, in charge of storing the state of the board and checking
    whether the puzzle is completed.
    """
    def __init__(self, seed, debug=False):
        self.seed = seed
        self.debug = debug
        self.board = None
        self.puzzle = None
        self.game_over = False

    def generate_board(self):
        """
        Generate a random valid Sudoku board.
        """
        self.seed = self.seed + 1
        random.seed(self.seed)
        board = [[0]*9 for _ in range(9)] # create an empty board
        self.solve_sudoku(board)
        if self.debug:
            print("Sudoku board:")
            for row in board:
                print(row)
        self.remove_cells(board)
        return board
    
    def solve_sudoku(self, board):
        """
        Solve the Sudoku board using backtracking.
        """
        empty_cell = self.find_empty_cell(board)
        if not empty_cell:
            return True
        row, col = empty_cell
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for num in numbers:
            if self.is_valid_move(board, row, col, num):
                board[row][col] = num
                if self.solve_sudoku(board):
                    return True
                board[row][col] = 0
        return False
    
    def remove_cells(self, board):
        """
        Remove cells from the Sudoku board to create a puzzle.
        """
        random.seed(self.seed) 
        cells_to_remove = random.randint(40, 50)
        for _ in range(cells_to_remove):
            row, col = random.randint(0, 8), random.randint(0, 8)
            if board[row][col] != 0:
                board[row][col] = 0

    def find_empty_cell(self, board):
        """
        Find the next empty cell in the Sudoku board.
        """
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def is_valid_move(self, board, row, col, num):
        """
        Check if placing 'num' at position (row, col) is a valid move.
        """
        return (
            self.is_valid_row(board, row, num)
            and self.is_valid_col(board, col, num)
            and self.is_valid_box(board, row - row % 3, col - col % 3, num)
        )

    def is_valid_row(self, board, row, num):
        """
        Check if 'num' is valid in the given row.
        """
        return num not in board[row]

    def is_valid_col(self, board, col, num):
        """
        Check if 'num' is valid in the given column.
        """
        return num not in [board[i][col] for i in range(9)]

    def is_valid_box(self, board, row, col, num):
        """
        Check if 'num' is valid in the 3x3 box containing (row, col).
        """
        return num not in [
            board[row + i][col + j] for i in range(3) for j in range(3)
        ]

    def start(self):
        """
        Start a new game.
        """
        self.game_over = False
        self.board = self.generate_board()
        if not self.puzzle:
            self.puzzle = [[cell for cell in row] for row in self.board]

    def check_win(self):
        """
        Check if the puzzle has been completed.
        """
        for row in range(9):
            if not self.check_row(row):
                return False
        for column in range(9):
            if not self.check_column(column):
                return False
        for row in range(3):
            for column in range(3):
                if not self.check_square(row, column):
                    return False
        self.game_over = True
        return True

    def check_block(self, block):
        """
        Check if a block (row, column, or square) contains the numbers 1-9.
        """
        return set(block) == set(range(1, 10))

    def check_row(self, row):
        """
        Check if a row contains the numbers 1-9.
        """
        return self.check_block(self.puzzle[row])

    def check_column(self, column):
        """
        Check if a column contains the numbers 1-9.
        """
        return self.check_block(
            [self.puzzle[row][column] for row in range(9)]
        )

    def check_square(self, row, column):
        """
        Check if a 3x3 square contains the numbers 1-9.
        """
        return self.check_block(
            [
                self.puzzle[r][c]
                for r in range(row * 3, (row + 1) * 3)
                for c in range(column * 3, (column + 1) * 3)
            ]
        )