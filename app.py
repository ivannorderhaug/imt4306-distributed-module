from tkinter import Entry, Label, Tk, Button
from twisted.internet import reactor
from twisted.internet import tksupport
from random import randint
from peer import Peer
from game import Game
from ui import UI

if __name__ == '__main__':
    peer = Peer()
    reactor.listenUDP(peer.port, peer)
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
            host_entry.insert(0, f"{peer.addr}:")

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

            join_button = Button(dialog, text="Join", command=on_join_game, width=10)
            join_button.pack(pady=5)

        join_game_button = Button(dialog, text="Join Game", command=on_join, width=10)
        join_game_button.pack(pady=5)

        dialog.mainloop()
    
    create_initial_dialog()
    root = Tk()
    game = Game(randint(0,9999), debug=True)
    ui = UI(root, peer, game)
    root.geometry("%dx%d" % (ui.width, ui.height+40))
    root.resizable(False,False)
    root.protocol("WM_DELETE_WINDOW", peer.stop)

    if host and port: # We either create a new game or join an existing game
        reactor.callWhenRunning(peer.send_hello, (host, port))
        reactor.callWhenRunning(reactor.callLater, 0.05, ui.ask_for_gamedata, (host, port))
        reactor.callWhenRunning(reactor.callLater, 0.1, ui.init_ui)
    else:
        game.start()
        ui.init_ui()
    tksupport.install(root)
    reactor.run()



