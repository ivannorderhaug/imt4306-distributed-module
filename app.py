import time
from tkinter import Entry, Label, Tk, Canvas, Frame, Button
import random
import json
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall
from twisted.internet import tksupport
from random import randint
import netifaces

class SudokuGame(object):
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
        cells_to_remove = random.randint(1, 2)
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

class SudokuUI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """
    def __init__(self, parent, peer):
        self.peer = peer
        Frame.__init__(self, parent)
        self.parent = parent
        self.row, self.col = -1, -1
        self.margin = 20
        self.side = 50
        self.width = self.height = self.margin * 2 + self.side * 9

        self.initUI()

    def initUI(self):
        """
        Set up the UI elements.
        """
        self.parent.title("Sudoku")
        self.pack()

        self.canvas = Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()
        self.peer_text = self.canvas.create_text(self.width/2, 10, text=f"{peer.addr}:{peer.port}", fill="black")
        self.canvas.tag_lower(self.peer_text)

        self.draw_grid(offset=(0, 20))
        self.draw_puzzle( offset=(0, 20))

        self.canvas.bind("<Button-1>", self.cell_clicked)
        self.canvas.bind("<Key>", self.key_pressed)

    def draw_grid(self, offset=(0, 0)):
        """
        Draws grid divided with blue lines into 3x3 squares
        """
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"

            x0 = self.margin + i * self.side + offset[0]
            y0 = self.margin + offset[1]
            x1 = self.margin + i * self.side + offset[0]
            y1 = self.height - self.margin + offset[1]
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = self.margin + offset[0]
            y0 = self.margin + i * self.side + offset[1]
            x1 = self.width - self.margin + offset[0]
            y1 = self.margin + i * self.side + offset[1]
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def draw_puzzle(self, offset=(0, 0)):
        """
        Fill the grid with numbers from the puzzle
        """
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = peer.game.puzzle[i][j]
                if answer != 0:
                    x = self.margin + j * self.side + self.side / 2 + offset[0]
                    y = self.margin + i * self.side + self.side / 2 + offset[1]
                    original = peer.game.board[i][j]
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
        peer.game.start()
        self.after(2000, self.clear_answers)

    def cell_clicked(self, event):
        """
        Called when the user clicks a cell.
        """
        if peer.game.game_over:
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
        if peer.game.game_over:
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            original_number = peer.game.board[self.row][self.col]
            if original_number == 0:
                peer.game.puzzle[self.row][self.col] = int(event.char)
                peer.send_move(self.row, self.col, int(event.char))
                self.col, self.row = -1, -1
                self.draw_puzzle()
                self.draw_cursor()
                if peer.game.check_win():
                    self.draw_victory()
        elif event.keysym == "BackSpace":
            original_number = peer.game.board[self.row][self.col]
            # dont update anything if the cell is an original number
            if peer.game.puzzle[self.row][self.col] != original_number:
                if original_number == 0:
                    peer.game.puzzle[self.row][self.col] = 0
                    peer.send_move(self.row, self.col, 0)
                    self.draw_puzzle()
                    self.draw_cursor()

    def clear_answers(self):
        """
        Clear all user answers.
        """
        self.canvas.delete("victory")
        self.draw_puzzle()

class Peer(DatagramProtocol):
    def __init__(self):
        """
        Initialize the client with the given address and port for the discovery server. If no address and port are given, the client will not connect to a discovery server.
        """
        self.peers = set()
        self.commands = {
            "hello": self.handle_hello,
            "bye": self.handle_bye,
            "ping": self.handle_ping,
            "pong": self.handle_pong,
            "ask_gamedata": self.handle_ask_for_gamedata,
            "gamedata": self.handle_gamedata,
            "move": self.handle_move,
        }
        self.addr = next((netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr'] for interface in netifaces.interfaces()[1:] if netifaces.AF_INET in netifaces.ifaddresses(interface)), None)
        self.port = randint(49152, 65535)
        self.lc_ping = LoopingCall(self.send_ping)
        self.lc_ping.start(15)
        self.last_pings = {}
        self.moves = []
        self.game = None

    def datagramReceived(self, data, addr):
        """
        Method called when a datagram is received.
        """
        data = data.decode('utf-8')
        if not data:
            return
                
        try:
            for line in data.splitlines():
                line = line.strip()
                print(line)
                msgtype = json.loads(line)['msgtype']
                if msgtype in self.commands:
                    self.commands[msgtype](line)
        except json.JSONDecodeError:
            print(data)
        except KeyError:
            print("Invalid message type received.")

    def handle_hello(self, line):
        """
        Method to handle a hello message received from a peer.
        """
        hello = json.loads(line)
        peer = (hello['addr'], hello['port'])
        if peer not in self.peers:
            self.peers.add(peer)
            self.send_hello(peer, include_peers=True)
            if not self.game:
                time.sleep(0.5)
                self.ask_for_gamedata(peer)
        if 'peers' in hello:
            for peer in hello['peers']:
                if (peer['addr'], peer['port']) != (self.addr, self.port):
                    self.send_hello((peer['addr'], peer['port']))
    
    def handle_move(self, line):
        """
        Method to handle a move received from a peer.
        """
        move = json.loads(line)
        self.moves.append(move)
        self.game.puzzle[move['row']][move['col']] = move['number']
        on_move_received(self)

    def send_move(self, row, col, number):
        """
        Method to send a move to all online peers.
        """
        move = json.dumps({'row': row, 'col': col, 'number': number, 'msgtype': 'move'})
        move = move.encode('utf-8')
        for peer in self.peers:
            self.transport.write(move, peer)

    def ask_for_gamedata(self, addr):
        """
        Method to ask a peer for the game data.
        """
        ask = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'ask_gamedata'})
        ask = ask.encode('utf-8')
        self.transport.write(ask, addr)

    def handle_ask_for_gamedata(self, line):
        """
        Method to handle the game data received from a peer.
        """
        ask = json.loads(line)
        peer = (ask['addr'], ask['port'])
        self.send_gamedata(peer)

    def send_gamedata(self, addr):
        """
        Method to send the game data to a peer.
        """
        gamedata = json.dumps({
            'msgtype': 'gamedata',
            'seed': self.game.seed-1,
            'puzzle': self.game.puzzle,
        })
        
        gamedata = gamedata.encode('utf-8')
        self.transport.write(gamedata, addr)

    def handle_gamedata(self, line):
        """
        Method to handle the game data received from a peer.
        """
        gamedata = json.loads(line)
        self.game = SudokuGame(gamedata['seed'])
        self.game.puzzle = gamedata['puzzle']
        self.game.start()
        on_gamedata_received(self)
    

    def send_hello(self, addr, include_peers=False):
        """
        Method to send a hello message to a peer.
        """
        if addr == (self.addr, self.port):
            return

        hello = {
            'addr': self.addr,
            'port': self.port,
            'msgtype': 'hello',
        }
        
        if include_peers:
            peers = []
            for peer in self.peers:
                if peer != addr:
                    peers.append({'addr': peer[0], 'port': peer[1]})
            hello['peers'] = peers

        hello = json.dumps(hello)
        hello = hello.encode('utf-8')
        self.transport.write(hello, addr)


    def send_bye(self, addr):
        """
        Method to send a bye message to a peer.
        """
        bye = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'bye'})
        bye = bye.encode('utf-8')
        self.transport.write(bye, addr)
    
    def handle_bye(self, line):
        """
        Method to handle a bye message from a peer.
        """
        print(f"{line}")
        bye = json.loads(line)
        self.peers.remove((bye['addr'], bye['port']))

    def send_ping(self):
        """
        Method to send a ping message to all online peers.
        """
        ping = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'ping'})
        ping = ping.encode('utf-8')
        for peer in self.peers.copy():
            self.transport.write(ping, peer)
            if peer in self.last_pings and reactor.seconds() - self.last_pings[peer] > 120:
                print(f"No response from {peer}. It appears to have gone offline.")
                self.peers.remove(peer)
                del self.last_pings[peer]
    
    def handle_ping(self, line):
        """
        Method to handle a ping message from a peer.
        """
        ping = json.loads(line)
        self.send_pong((ping['addr'], ping['port']))
    
    def send_pong(self, addr):
        """
        Method to send a pong message to a peer.
        """
        pong = json.dumps({'addr': self.addr, 'port': self.port, 'msgtype': 'pong'})
        pong = pong.encode('utf-8')
        self.transport.write(pong, addr)

    def handle_pong(self, line):
        """
        Method to handle a pong message from a peer.
        """
        pong = json.loads(line)
        self.last_pings[(pong['addr'], pong['port'])] = reactor.seconds()

    def send(self, message):
        """
        Method to send a message to all online peers.
        """
        message = message.strip()
        if not message:
            return
        
    def stop(self):
        """
        Method to stop the client.
        """
        for peer in self.peers:
            self.send_bye(peer)

        self.lc_ping.stop()
        self.transport.stopListening()
        reactor.stop()


########################
#    MAIN PROGRAM      # 
########################

def on_gamedata_received(peer):
    """
        Helper function to create the UI when the game data is received.
    """
    global shared_ui_ref
    root = Tk()    
    shared_ui_ref = SudokuUI(root, peer)
    root.geometry("%dx%d" % (shared_ui_ref.width, shared_ui_ref.height))
    root.resizable(False,False)
    root.protocol("WM_DELETE_WINDOW", peer.stop)
    tksupport.install(root)

def on_move_received(peer):
    """
        Helper function to update the UI when a move is received.
    """
    global shared_ui_ref
    if shared_ui_ref:
        shared_ui_ref.draw_puzzle()
        if peer.game.check_win():
            shared_ui_ref.draw_victory()


"""
    Main function to start the client.
"""
if __name__ == '__main__':
    shared_ui_ref = None
    peer = Peer()
    host, port = None, None
    def create_initial_dialog():
        """
            Method to create the initial dialog.
        """
        dialog = Tk()
        dialog.title("P2P Sudoku")
        dialog.geometry("200x100")
        dialog.resizable(False,False)
        def on_close():
            dialog.destroy()
            exit()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

        # create new game or join game buttons
        new_game_button = Button(dialog, text="New Game", command=dialog.destroy, width=10)
        new_game_button.pack(pady=5)

        def on_join():
            """
                Method to create the join game dialog.
            """
            # unpack the buttons
            new_game_button.pack_forget()
            join_game_button.pack_forget()

            # entry for the host address and port
            host_label = Label(dialog, text="Host Address (ip:port)")
            host_label.pack(pady=5)
            host_entry = Entry(dialog)
            host_entry.pack(pady=5)

            def on_join_game():
                """
                    Method to join a game.
                """
                global host, port
                try:
                    h, p = host_entry.get().split(":")
                    if (h, p) == (peer.addr, str(peer.port)):
                        return
                except ValueError:
                    return
                
                if not h or not p or not p.isdigit() or int(p) < 0 or int(p) > 65535 or len(h.split(".")) != 4:
                    return
                host, port = h, int(p)
                dialog.destroy()

            # join game button
            join_button = Button(dialog, text="Join", command=on_join_game, width=10)
            join_button.pack(pady=5)


        join_game_button = Button(dialog, text="Join Game", command=on_join, width=10)
        join_game_button.pack(pady=5)

        dialog.mainloop()
    
    create_initial_dialog()

    reactor.listenUDP(peer.port, peer)
    if host and port: # We either create a new game or join an existing game
        reactor.callWhenRunning(peer.send_hello, (host, port))
    else:
        peer.game = SudokuGame(1, debug=True)
        peer.game.start()
        root = Tk()    
        shared_ui_ref = SudokuUI(root, peer)
        root.geometry("%dx%d" % (shared_ui_ref.width, shared_ui_ref.height+40))
        root.resizable(False,False)
        root.protocol("WM_DELETE_WINDOW", peer.stop)
        tksupport.install(root)

    reactor.run()



