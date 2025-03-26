import chess
from tqdm import tk

from board_display_gui import ChessGUI


def print_board(board):
    lines = []

    # ANSI color codes
    WHITE_PIECE = '\033[97m'  # Bright white
    BLACK_PIECE = '\033[90m'  # Dark gray
    WHITE_PIECE = '\033[93m'  # Bright white
    BLACK_PIECE = '\033[94m'  # Dark gray
    RESET = '\033[0m'

    unicode_pieces = {
        'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
        'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
        '.': '·'
    }

    lines.append("\t\ta\tb\tc\td\te\tf\tg\th\t")
    lines.append("\t+\t-\t-\t-\t-\t-\t-\t-\t-\t+")

    for rank in range(7, -1, -1):
        line = f"{rank+1}\t|\t"
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            if piece:
                symbol = unicode_pieces[piece.symbol()]
                color = WHITE_PIECE if piece.color == chess.WHITE else BLACK_PIECE
            else:
                symbol = unicode_pieces['.']
                color = RESET
            line += f"{color}{symbol}{RESET}\t"
        line += f"|\t{rank + 1}"
        lines.append(line)
    lines.append("\t+\t-\t-\t-\t-\t-\t-\t-\t-\t+")
    lines.append("\t\ta\tb\tc\td\te\tf\tg\th\t")
    str_ = '\n'.join(lines)
    print(str_)

    print(f"Turn: {'White' if board.turn == chess.WHITE else 'Black'}")
    legal_moves = list(board.legal_moves)
    if legal_moves:
        print("Possible moves:")

        # Dictionary to store moves by piece type
        moves_by_piece = {
            chess.PAWN: [],
            chess.KNIGHT: [],
            chess.BISHOP: [],
            chess.ROOK: [],
            chess.QUEEN: [],
            chess.KING: []
        }

        # Group moves by piece type
        for move in legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:  # Ensure there’s a piece at the from_square
                piece_type = piece.piece_type
                moves_by_piece[piece_type].append(board.san(move))

        # Piece names for display
        piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }

        # Print moves for each piece type
        for piece_type, moves in moves_by_piece.items():
            if moves:  # Only print if there are moves for this piece
                print(f"\t\t{piece_names[piece_type]}: {', '.join(moves)}")
    else:
        print("No legal moves available!")
    import tkinter as tk
    root = tk.Tk()
    app = ChessGUI(root,board)
    root.mainloop()




# Example usage
if __name__ == "__main__":
    board = chess.Board()
    print_board(board)