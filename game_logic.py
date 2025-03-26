import chess
import sys
from board_display import print_board
from engine import get_random_engine_move, get_best_move_with_time_limitation
import random

def print_outcome(board):
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
            sys.exit()
    print("Game continues...")


def count_pieces(board):
    return sum(1 for square in chess.SQUARES if board.piece_at(square) is not None)


def random_game(board, white_random, black_random):
    print("Initial position:")
    print_board(board)
    move_number = 0

    while board.legal_moves.count() > 0:
        move_number += 1
        if count_pieces(board) == 2:
            break

        if board.turn:
            move = get_best_move_with_time_limitation(board) if random.random() >= white_random else get_random_engine_move(board)
            print('White to play...')
        else:
            move = get_best_move_with_time_limitation(board) if random.random() >= black_random else get_random_engine_move(board)
            print('Black to play...')

        if move:
            print(f"Move {move_number}: Engine plays {board.san(move)}")
            board.push(move)
            print_board(board)
        else:
            print("No legal moves available!")
            break

    print_outcome(board)


def human_vs_computer(board, human_color=chess.WHITE):
    print("Initial position:")
    print_board(board)
    move_number = 0

    while board.legal_moves.count() > 0:
        move_number += 1
        if count_pieces(board) == 2:
            break

        if board.turn == human_color:
            print(f"{'White' if human_color else 'Black'} to play (your turn)...")
            legal_moves = list(board.legal_moves)
            move_str = input("Enter your move (e.g., 'e2e4'): ")
            try:
                move = board.parse_san(move_str)
                if move not in legal_moves:
                    print("Illegal move! Try again.")
                    continue
            except ValueError:
                print("Invalid move format! Try again.")
                continue
        else:
            print(f"{'Black' if human_color else 'White'} to play (computer)...")
            move = get_best_move_with_time_limitation(board)

        print(f"Move {move_number}: {board.san(move)}")
        board.push(move)
        print_board(board)

    print_outcome(board)