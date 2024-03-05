from tkinter import Tk, Canvas, Frame, Button
import random

class SudokuUI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """
    def __init__(self, parent, game):
        self.game = game
        Frame.__init__(self, parent)
        self.parent = parent
        self.row, self.col = -1, -1
        self.margin = 20
        self.side = 50
        self.width = self.height = self.margin * 2 + self.side * 9

        self.initUI()

    def initUI(self):
        self.parent.title("Sudoku")
        self.pack()
        self.canvas = Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()

        self.draw_grid()
        self.draw_puzzle()

        self.canvas.bind("<Button-1>", self.cell_clicked)
        self.canvas.bind("<Key>", self.key_pressed)

    def draw_grid(self):
        """
        Draws grid divided with blue lines into 3x3 squares
        """
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"

            x0 = self.margin + i * self.side
            y0 = self.margin
            x1 = self.margin + i * self.side
            y1 = self.height - self.margin
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = self.margin
            y0 = self.margin + i * self.side
            x1 = self.width - self.margin
            y1 = self.margin + i * self.side
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def draw_puzzle(self):
        """
        Fill the grid with numbers from the puzzle
        """
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = self.game.puzzle[i][j]
                if answer != 0:
                    x = self.margin + j * self.side + self.side / 2
                    y = self.margin + i * self.side + self.side / 2
                    original = self.game.board[i][j]
                    color = "black" if answer == original else "sea green"
                    self.canvas.create_text(x, y, text=answer, tags="numbers", fill=color)

    def draw_cursor(self):
        """
        Draw a red cursor around the current selected cell.
        """
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = self.margin + self.col * self.side + 1
            y0 = self.margin + self.row * self.side + 1
            x1 = self.margin + (self.col + 1) * self.side - 1
            y1 = self.margin + (self.row + 1) * self.side - 1
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", tags="cursor")

    def draw_victory(self):
        """
        Draw a 'victory' text to the canvas.
        """
        x0 = y0 = self.margin + self.side * 2
        x1 = y1 = self.margin + self.side * 7
        self.canvas.create_oval(x0, y0, x1, y1, tags="victory", fill="dark orange", outline="orange")
        x = y = self.margin + 4 * self.side + self.side / 2
        self.canvas.create_text(x, y, text="You win!", tags="victory", fill="white", font=("Arial", 32))

        self.after(5000, self.clear_answers)

    def cell_clicked(self, event):
        """
        Called when the user clicks a cell.
        """
        if self.game.game_over:
            return
        x, y = event.x, event.y
        if self.margin < x < self.width - self.margin and self.margin < y < self.height - self.margin:
            self.canvas.focus_set()
            self.row, self.col = int((y - self.margin) / self.side), int((x - self.margin) / self.side)
        else:
            self.row, self.col = -1, -1

        self.draw_cursor()

    def key_pressed(self, event):
        """
        Called when the user presses a key.
        """
        if self.game.game_over:
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            original_number = self.game.board[self.row][self.col]
            if original_number == 0:
                self.game.puzzle[self.row][self.col] = int(event.char)
                self.col, self.row = -1, -1
                self.draw_puzzle()
                self.draw_cursor()
                if self.game.check_win():
                    self.draw_victory()
        elif event.keysym == "BackSpace":
            original_number = self.game.board[self.row][self.col]
            if original_number == 0:
                self.game.puzzle[self.row][self.col] = 0
                self.draw_puzzle()

    def clear_answers(self):
        """
        Clear all user answers.
        """
        self.game.start()
        self.canvas.delete("victory")
        self.draw_puzzle()

class SudokuGame(object):
    """
    A Sudoku game, in charge of storing the state of the board and checking
    whether the puzzle is completed.
    """
    def __init__(self, seed, debug=False):
        self.seed = seed
        self.debug = debug
        self.board = None

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

if __name__ == '__main__':
    game = SudokuGame(1, debug=False)
    game.start()

    root = Tk()
    ui = SudokuUI(root, game)
    root.geometry("%dx%d" % (ui.width, ui.height))
    root.resizable(False,False)
    root.mainloop()
