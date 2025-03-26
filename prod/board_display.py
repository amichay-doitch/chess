import chess
from prod.constants import unicode_pieces

def print_board(board, gui=None):
    lines = []

    # ANSI color codes
    WHITE_PIECE = '\033[93m'  # Bright yellow (adjusted for visibility)
    BLACK_PIECE = '\033[94m'  # Bright blue (adjusted for visibility)
    RESET = '\033[0m'

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
        moves_by_piece = {
            chess.PAWN: [], chess.KNIGHT: [], chess.BISHOP: [],
            chess.ROOK: [], chess.QUEEN: [], chess.KING: []
        }

        for move in legal_moves:
            piece = board.piece_at(move.from_square)
            if piece:
                piece_type = piece.piece_type
                moves_by_piece[piece_type].append(board.san(move))

        piece_names = {
            chess.PAWN: "Pawn", chess.KNIGHT: "Knight", chess.BISHOP: "Bishop",
            chess.ROOK: "Rook", chess.QUEEN: "Queen", chess.KING: "King"
        }

        for piece_type, moves in moves_by_piece.items():
            if moves:
                print(f"\t\t{piece_names[piece_type]}: {', '.join(moves)}")
    else:
        print("No legal moves available!")

    # Update the GUI if provided
    if gui:
        gui.draw_board()
        gui.update_moves()