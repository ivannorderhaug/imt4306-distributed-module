from tkinter import Canvas, Frame, Label
import json
from twisted.internet.task import LoopingCall
from random import randint
from game import Game

class UI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """
    def __init__(self, root, peer, game):
        self.peer = peer
        self.peer.add_handler("move", self.handle_move)
        self.peer.add_handler("ask_gamedata", self.handle_ask_for_gamedata)
        self.peer.add_handler("gamedata", self.handle_gamedata)
        self.game = game
        Frame.__init__(self, root)
        self.root = root
        self.row, self.col = -1, -1
        self.margin = 20
        self.side = 50
        self.width = self.height = self.margin * 2 + self.side * 9
        self.lc_performance = LoopingCall(self.draw_performance)

    def init_ui(self):
        """
        Set up the UI elements.
        """
        self.root.title("Sudoku")
        self.pack()

        self.canvas = Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()
        self.peer_text = self.canvas.create_text(self.width/2, 10, text=f"{self.peer.addr}:{self.peer.port}", fill="black")
        self.canvas.tag_lower(self.peer_text)

        self.draw_grid()
        self.draw_puzzle()

        self.performance_canvas = Canvas(self, width=self.width, height=40)
        self.performance_canvas.pack()
        self.draw_performance()

        self.canvas.bind("<Button-1>", self.cell_clicked)
        self.canvas.bind("<Key>", self.key_pressed)
        self.canvas.focus_set()
        self.lc_performance.start(1)


    def draw_performance(self):
        """
        Draw the performance metrics to the canvas.
        """
        self.performance_canvas.delete("performance")
        self.peer.get_performance()
        if self.peer.latency > 0:
            self.performance_canvas.create_text(self.width/2, 10, text=f"Latency: {self.peer.latency:.6f}s", tags="performance", fill="black")
        else:
            self.performance_canvas.create_text(self.width/2, 10, text="Latency: N/A", tags="performance", fill="black")
        
        if self.peer.throughput > 0:
            self.performance_canvas.create_text(self.width/2, 25, text=f"Throughput: {self.peer.throughput:.2f} msg/s", tags="performance", fill="black")
        else:
            self.performance_canvas.create_text(self.width/2, 25, text="Throughput: N/A", tags="performance", fill="black")

    def draw_grid(self,):
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
        x = y = self.margin + 4 * self.side + self.side / 2
        self.canvas.create_text(x, y, text="You win!", tags="victory", fill="white", font=("Arial", 32))
        self.game.puzzle = None
        self.game.start()
        self.after(2000, self.clear_answers)

    def cell_clicked(self, event):
        """
        Called when the user clicks a cell.
        """
        if self.game.game_over:
            return
        x, y = event.x, event.y
        if self.margin < x < self.width - self.margin and self.margin < y < self.height - self.margin:
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
                self.send_move(self.row, self.col, int(event.char))
                self.col, self.row = -1, -1
                self.draw_puzzle()
                self.draw_cursor()
                if self.game.check_win():
                    self.draw_victory()
        elif event.keysym == "BackSpace":
            original_number = self.game.board[self.row][self.col]
            # dont update anything if the cell is an original number
            if self.game.puzzle[self.row][self.col] != original_number:
                if original_number == 0:
                    self.game.puzzle[self.row][self.col] = 0
                    self.send_move(self.row, self.col, 0)
                    self.draw_puzzle()
                    self.draw_cursor()

    def clear_answers(self):
        """
        Clear all user answers.
        """
        self.canvas.delete("victory")
        self.draw_puzzle()
    
    def handle_move(self, line):
        """
        Method to handle a move received from a peer.
        """
        peer, port = json.loads(line)['addr'], int(json.loads(line)['port'])
        if (peer, port) not in self.peer.peers:
            self.peer.peers.add((peer, port))
            self.send_gamedata((peer, port))
            return  
        self.peer.messages_count += 1
        move = json.loads(line)
        self.game.puzzle[move['row']][move['col']] = move['number']
        self.draw_puzzle()
        if self.game.check_win():
            self.draw_victory()
        
    def send_move(self, row, col, number):
        """
        Method to send a move to all online peers.
        """
        move = json.dumps({'row': row, 'col': col, 'number': number, 'addr':f'{self.peer.addr}','port':f'{self.peer.port}','msgtype': 'move'})
        move = move.encode('utf-8')
        try:
            for peer in self.peer.peers:
                self.peer.transport.write(move, peer)
        except:
            pass

    def ask_for_gamedata(self, addr):
        """
        Method to ask a peer for the game data.
        """
        ask = json.dumps({'addr': self.peer.addr, 'port': self.peer.port, 'msgtype': 'ask_gamedata'})
        ask = ask.encode('utf-8')
        try:
            self.peer.transport.write(ask, addr)
        except:
            pass

    def handle_ask_for_gamedata(self, line):
        """
        Method to handle the game data received from a peer.
        """
        self.peer.messages_count += 1
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
        try:
            self.peer.transport.write(gamedata, addr)
        except:
            pass

    def handle_gamedata(self, line):
        """
        Method to handle the game data received from a peer.
        """
        self.peer.messages_count += 1
        gamedata = json.loads(line)
        self.game = Game(gamedata['seed'])
        self.game.puzzle = gamedata['puzzle']
        self.game.start()
        if not hasattr(self, 'canvas'):
            self.init_ui()
        self.draw_puzzle()
        if self.game.check_win():
            self.draw_victory()
      
        