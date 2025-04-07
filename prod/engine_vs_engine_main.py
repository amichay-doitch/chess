import chess
import random

from prod.constants import move_time_for_engine, max_depth_for_engine
from prod.engine import get_random_engine_move, get_best_move_async
from prod.engine_second import get_best_move_async_second
from prod.board_display import print_board
from prod.engine_third import get_best_move_async_third
from prod.game_logic import print_outcome
from prod.board_display_gui import ChessGUI  # Import GUI
import time
from queue import Queue
import tkinter as tk
from tkinter import messagebox

def get_greedy_engine_move(board):
    """A simple greedy engine that prioritizes capturing the highest-value piece."""
    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    if capture_moves:
        def capture_value(move):
            victim = board.piece_at(move.to_square)
            return piece_value(victim) if victim else 0

        return max(capture_moves, key=capture_value)  # Simplified, no default needed

    # Fallback to Minimax, but extract the move from the Queue
    result_queue = get_best_move_async(board, max_time=1, max_depth=7)
    move = None
    start_time = time.time()
    while time.time() - start_time < 20 and move is None:
        if not result_queue.empty():
            move = result_queue.get()
            break
        time.sleep(0.01)  # Wait briefly to avoid busy-waiting
    if move is None:
        print("Greedy engine Minimax fallback timed out, selecting random move.")
        move = random.choice(legal_moves) if legal_moves else None
    return move

# Define available engines
ENGINES = {
    "1": ("Minimax", lambda board: get_best_move_async(board,
                                                       max_time=move_time_for_engine,
                                                       max_depth=max_depth_for_engine)),
    "2": ("Random", get_random_engine_move),
    "3": ("Greedy", get_greedy_engine_move),
    "4": ("Minimax Second", lambda board: get_best_move_async_second(board,
                                                                     max_time=move_time_for_engine,
                                                                     max_depth=max_depth_for_engine)),
    "5": ("Minimax mistral", lambda board: get_best_move_async_third(board,
                                                                     max_time=move_time_for_engine,
                                                                     max_depth=max_depth_for_engine)),
    # Add more engines here as needed (e.g., greedy)
}





def piece_value(piece):
    """Helper function for greedy engine."""
    values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
              chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 100000}
    return values.get(piece.piece_type, 0)


def play_game(white_engine_func, black_engine_func, white_name, black_name, game_num, gui=None, root=None):
    """Play a single game between two engines and return the result, with optional GUI."""
    board = chess.Board()
    print(f"\nStarting Game {game_num}: {white_name} (White) vs {black_name} (Black)")
    print_board(board)
    if gui:
        gui.board = board  # Sync GUI board with game board
        gui.draw_board()
        gui.update_moves()
        root.update()  # Force initial GUI update

    # Control variables for GUI interaction
    paused = [False]  # List to allow modification in nested function
    game_over = [False]

    def next_move():
        if game_over[0] or paused[0]:
            return None  # Return None if paused or game over

        if board.is_game_over():
            game_over[0] = True
            result = "White" if board.is_checkmate() and board.turn == chess.BLACK else "Black" if board.is_checkmate() else "Draw"
            print(f"Game {game_num} result: {result}")
            if gui:
                gui.moves_text.delete(1.0, tk.END)
                gui.moves_text.insert(tk.END, f"Game Over: {result}")
                gui.draw_board()  # Ensure final position is drawn
                root.update()  # Force GUI update
            return result

        current_engine = white_engine_func if board.turn == chess.WHITE else black_engine_func
        engine_name = white_name if board.turn == chess.WHITE else black_name

        # Handle engine move
        move_result = current_engine(board)

        if engine_name in ("Minimax","Minimax Second"):  # Minimax returns a Queue
            result_queue = move_result
            move = None
            start_time = time.time()
            while time.time() - start_time < move_time_for_engine and move is None:  # Wait up to 2 seconds
                if not result_queue.empty():
                    move = result_queue.get()
                    break
                time.sleep(0.01)  # Shorter sleep to avoid blocking GUI
                if gui:
                    root.update()  # Keep GUI responsive while waiting
            if move is None:
                print(f"{engine_name} timed out, selecting random move.")
                move = random.choice(list(board.legal_moves)) if board.legal_moves else None
        else:  # Random or Greedy returns a Move directly
            move = move_result

        if move and move in board.legal_moves:
            san_move = board.san(move)
            board.push(move)
            print(f"{engine_name} plays {san_move}")
            print_board(board)
            if gui:
                gui.make_move(move)  # Update GUI with the move
                gui.draw_board()  # Redraw the board explicitly
                gui.update_moves()  # Update move list
                root.update()  # Force GUI to refresh after each move
            if not paused[0] and root:
                root.after(1000, next_move)  # Schedule next move after 1 second
        else:
            print(f"{engine_name} failed to provide a valid move. Forfeiting.")
            game_over[0] = True
            return "Black" if board.turn == chess.WHITE else "White"

        # Check game outcome
        if print_outcome(board):
            game_over[0] = True
            return "White" if board.is_checkmate() and board.turn == chess.BLACK else "Black" if board.is_checkmate() else "Draw"
        return None


    def toggle_pause():
        paused[0] = not paused[0]
        pause_button.config(text="Resume" if paused[0] else "Pause")
        if not paused[0] and root:
            root.after(1000, next_move)  # Resume auto-play

    def step_move():
        if not paused[0]:
            toggle_pause()  # Pause if currently running
        result = next_move()
        if result and gui:
            messagebox.showinfo("Game Over", f"Game {game_num} result: {result}")
        return result

    # Set up GUI controls if provided
    if gui and root:
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        pause_button = tk.Button(control_frame, text="Pause", command=toggle_pause)
        pause_button.pack(side=tk.LEFT, padx=5)

        step_button = tk.Button(control_frame, text="Step", command=step_move)
        step_button.pack(side=tk.LEFT, padx=5)

        # Start auto-play
        root.after(1000, next_move)

    # Run game synchronously if no GUI, or wait for GUI to finish
    if not root:
        while not game_over[0]:
            result = next_move()
            if result:
                return result
    else:
        return None  # Result will be handled via GUI callbacks


def engine_vs_engine_comparison():
    """Main function to run multiple games and display statistics, with optional GUI."""
    print("Engine vs Engine Comparison Tool")
    print("Available engines:")
    for key, (name, _) in ENGINES.items():
        print(f"{key}: {name}")

    # Get user input
    white_engine_key = input("Select White engine (1-4): ") or "1"
    black_engine_key = input("Select Black engine (1-4): ") or "1"
    num_games = int(input("Number of games to play: ") or 10)
    use_gui = input("Use GUI to explore games? (y/n): ").lower() == 'y'

    if white_engine_key not in ENGINES or black_engine_key not in ENGINES:
        print("Invalid engine selection!")
        return

    white_name, white_engine_func = ENGINES[white_engine_key]
    black_name, black_engine_func = ENGINES[black_engine_key]

    # Initialize statistics
    results = {"White": 0, "Black": 0, "Draw": 0}
    start_time = time.time()

    if use_gui:
        root = tk.Tk()
        root.title(f"Engine vs Engine: {white_name} vs {black_name}")
        board = chess.Board()
        gui = ChessGUI(root, board)

        def run_game(game_num):
            result = play_game(white_engine_func, black_engine_func, white_name, black_name, game_num, gui, root)
            if result:
                results[result] += 1
                if game_num < num_games:
                    gui.board = chess.Board()  # Reset board for next game
                    gui.draw_board()
                    gui.update_moves()
                    root.after(2000, lambda: run_game(game_num + 1))
                else:
                    show_final_stats()

        def show_final_stats():
            elapsed_time = time.time() - start_time
            stats = (f"Games played: {num_games}\n"
                     f"White ({white_name}) wins: {results['White']} ({results['White'] / num_games * 100:.1f}%)\n"
                     f"Black ({black_name}) wins: {results['Black']} ({results['Black'] / num_games * 100:.1f}%)\n"
                     f"Draws: {results['Draw']} ({results['Draw'] / num_games * 100:.1f}%)\n"
                     f"Total time: {elapsed_time:.2f} seconds")
            messagebox.showinfo("Final Statistics", stats)
            root.quit()

        root.after(1000, lambda: run_game(1))
        root.mainloop()
    else:
        # Run games without GUI
        for game_num in range(1, num_games + 1):
            winner = play_game(white_engine_func, black_engine_func, white_name, black_name, game_num)
            results[winner] += 1
            print(f"Game {game_num} result: {winner}")

        # Display statistics
        elapsed_time = time.time() - start_time
        print("\n--- Final Statistics ---")
        print(f"Games played: {num_games}")
        print(f"White ({white_name}) wins: {results['White']} ({results['White'] / num_games * 100:.1f}%)")
        print(f"Black ({black_name}) wins: {results['Black']} ({results['Black'] / num_games * 100:.1f}%)")
        print(f"Draws: {results['Draw']} ({results['Draw'] / num_games * 100:.1f}%)")
        print(f"Total time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    engine_vs_engine_comparison()