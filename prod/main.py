import chess
import tkinter as tk
from game_logic import  human_vs_computer
from board_display_gui import ChessGUI
from engine import get_random_engine_move, get_best_move_async
from engine_second import  get_best_move_async_second
from prod.engine_third import get_best_move_async_third


def main():
    root = tk.Tk()
    board = chess.Board()
    gui = ChessGUI(root, board)

    print("Welcome to Chess!")
    print("1. Computer vs Computer")
    print("2. Human vs Computer (White)")
    print("3. Human vs Computer (Black)")

    choice = input("Select game mode (1-3): ")

    if choice == "1":
        white_random = float(input("White randomness (0-1, 0=best moves): ") or 0.1)
        black_random = float(input("Black randomness (0-1, 0=best moves): ") or 0.1)
        random_game(board, white_random, black_random, gui, root)
    elif choice == "2":
        print("1. Play engine 1")
        print("2. Play engine 2")
        print("3. Play engine 3")
        choice = input("Select game mode (1-3): ")
        if choice == '1':
            human_vs_computer(get_best_move_async ,board, chess.WHITE, gui, root)
        elif choice == '2':
            human_vs_computer(get_best_move_async_second ,board, chess.WHITE, gui, root)
        elif choice == '3':
            human_vs_computer(get_best_move_async_third, board, chess.WHITE, gui, root)
        else:
            print("Invalid choice!")
            root.destroy()
            return

    elif choice == "3":
        print("1. Play engine 1")
        print("2. Play engine 2")
        print("3. Play engine 3")
        choice = input("Select game mode (1-3): ")
        if choice == '1':
            human_vs_computer(get_best_move_async ,board, chess.BLACK, gui, root)
        elif choice == '2':
            human_vs_computer(get_best_move_async_second ,board, chess.BLACK, gui, root)
        elif choice == '3':
            human_vs_computer(get_best_move_async_third, board, chess.BLACK, gui, root)
        else:
            print("Invalid choice!")
            root.destroy()
            return
    else:
        print("Invalid choice!")
        root.destroy()
        return

    root.mainloop()

if __name__ == "__main__":
    main()