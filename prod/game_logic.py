import chess
import sys
import random
import tkinter as tk
from board_display import print_board
from engine import get_random_engine_move, get_best_move_async

def print_outcome(board, gui=None):
    outcomes = {
        board.is_checkmate(): f"Checkmate! {'White' if board.turn == chess.BLACK else 'Black'} wins!",
        board.is_stalemate(): "Stalemate! It's a draw!",
        board.is_insufficient_material(): "Draw due to insufficient material!",
        board.is_seventyfive_moves(): "Draw by 75-move rule!",
        board.is_fivefold_repetition(): "Draw by fivefold repetition!"
    }
    for condition, message in outcomes.items():
        if condition:
            print(f"Game Over: {message}")
            if gui:
                gui.moves_text.delete(1.0, tk.END)
                gui.moves_text.insert(tk.END, f"Game Over: {message}")
            return True
    print("Game continues...")
    return False

def count_pieces(board):
    return sum(1 for square in chess.SQUARES if board.piece_at(square) is not None)

def random_game(board, white_random, black_random, gui=None, root=None):
    print("Initial position:")
    print_board(board, gui)
    move_number = 0

    def play_next_move():
        nonlocal move_number
        legal_move_count = board.legal_moves.count()
        piece_count = count_pieces(board)
        is_game_over = print_outcome(board, gui)
        print(f"Debug: legal_moves={legal_move_count}, pieces={piece_count}, game_over={is_game_over}")

        if legal_move_count == 0 or piece_count <= 2 or is_game_over:
            print("Game loop stopping.")
            return

        move_number += 1
        player = "White" if board.turn else "Black"
        print(f"{player} to play...")

        use_random = random.random() < (white_random if board.turn else black_random)
        if use_random:
            move = get_random_engine_move(board)
            print(f"Random move selected: {board.san(move) if move else 'None'}")
        else:
            move = None
            if gui:
                gui.moves_text.insert(tk.END, f"{player} thinking...\n")
            result_queue = get_best_move_async(board, max_time=5, max_depth=4)
            root.after(100, lambda: check_move_result(result_queue, player, move_number))
            return

        if move and move in board.legal_moves:
            print(f"Move {move_number}: {player} plays {board.san(move)}")
            board.push(move)
            print_board(board, gui)
            if gui:
                gui.make_move(move)
            root.after(1000, play_next_move)
        else:
            print("No valid move available!")
            print_outcome(board, gui)

    def check_move_result(result_queue, player, move_num):
        if not result_queue.empty():
            move = result_queue.get()
            print(f"Async result for {player}: {move.uci() if move else 'None'}")
            if move and move in board.legal_moves:
                san_move = board.san(move)  # Get SAN after validation
                board.push(move)
                print(f"Move {move_num}: {player} plays {san_move}")
                print_board(board, gui)
                if gui:
                    gui.make_move(move)
                root.after(1000, play_next_move)
            else:
                print(f"Invalid move from engine: {move.uci() if move else 'None'} in {board.fen()}")
                root.after(100, play_next_move)  # Retry next move
        else:
            print(f"Waiting for {player}'s move...")
            root.after(100, lambda: check_move_result(result_queue, player, move_num))

    if root:
        root.after(1000, play_next_move)

def human_vs_computer(board, human_color=chess.WHITE, gui=None, root=None):
    print("Initial position:")
    print_board(board, gui)
    move_number = 0
    last_move_stack_size = len(board.move_stack)

    def computer_turn():
        nonlocal move_number, last_move_stack_size
        legal_move_count = board.legal_moves.count()
        piece_count = count_pieces(board)
        is_game_over = print_outcome(board, gui)
        print(f"Debug: legal_moves={legal_move_count}, pieces={piece_count}, game_over={is_game_over}, move_stack={len(board.move_stack)}")

        if legal_move_count == 0 or piece_count <= 2 or is_game_over:
            print("Game loop stopping.")
            return

        current_move_stack_size = len(board.move_stack)
        if current_move_stack_size > last_move_stack_size and board.turn == human_color:
            last_move_stack_size = current_move_stack_size
            print("Human move detected, waiting for next turn...")
            root.after(100, computer_turn)
            return

        if board.turn != human_color:
            move_number += 1
            computer_player = "Black" if human_color else "White"
            print(f"{computer_player} to play (computer)...")
            if gui:
                gui.moves_text.insert(tk.END, "Computer thinking...\n")
            result_queue = get_best_move_async(board, max_time=5, max_depth=4)
            root.after(100, lambda: check_computer_move(result_queue, move_number))
        else:
            root.after(100, computer_turn)  # Wait for human move

    def check_computer_move(result_queue, move_num):
        nonlocal last_move_stack_size
        if not result_queue.empty():
            move = result_queue.get()
            computer_player = "Black" if human_color else "White"
            print(f"Async result for {computer_player}: {move.uci() if move else 'None'}")
            if move and move in board.legal_moves:
                san_move = board.san(move)  # Get SAN after validation
                board.push(move)
                print(f"Move {move_num}: {computer_player} plays {san_move}")
                print_board(board, gui)
                if gui:
                    gui.make_move(move)
                last_move_stack_size = len(board.move_stack)
                root.after(100, computer_turn)
            else:
                print(f"Invalid move from engine: {move.uci() if move else 'None'} in {board.fen()}")
                root.after(100, computer_turn)  # Retry or continue
        else:
            print("Waiting for computer move...")
            root.after(100, lambda: check_computer_move(result_queue, move_num))

    if root:
        root.after(100, computer_turn)