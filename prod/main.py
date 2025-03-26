import chess
from game_logic import random_game, human_vs_computer


def main():
    board = chess.Board()
    print("Welcome to Chess!")
    print("1. Computer vs Computer")
    print("2. Human vs Computer (White)")
    print("3. Human vs Computer (Black)")

    choice = input("Select game mode (1-3): ")

    if choice == "1":
        white_random = float(input("White randomness (0-1, 0=best moves): ") or 0.1)
        black_random = float(input("Black randomness (0-1, 0=best moves): ") or 0.1)
        random_game(board, white_random, black_random)
    elif choice == "2":
        human_vs_computer(board, chess.WHITE)
    elif choice == "3":
        human_vs_computer(board, chess.BLACK)
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()