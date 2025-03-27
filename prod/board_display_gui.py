import chess
import tkinter as tk
from tkinter import messagebox, simpledialog
from prod.constants import colors, unicode_pieces

class ChessGUI:
    def __init__(self, root, board=None):
        self.root = root
        self.root.title("Chess Board")
        self.board = board if board is not None else chess.Board()
        self.square_size = 60
        self.selected_square = None

        # Create main frame
        self.main_frame = tk.Frame(root, bg=colors['Very dark gray (almost black)'])
        self.main_frame.pack(padx=10, pady=10)

        # Create canvas for board
        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.square_size * 8,
            height=self.square_size * 8,
            bg=colors['Very dark gray (almost black)'],
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT)

        # Create info panel
        self.info_frame = tk.Frame(self.main_frame, bg=colors['Very dark gray (almost black)'])
        self.info_frame.pack(side=tk.RIGHT, padx=10)

        self.turn_label = tk.Label(
            self.info_frame,
            text="Turn: White",
            font=("Arial", 12, "bold"),
            bg=colors['Very dark gray (almost black)'],
            fg=colors['Off-white']
        )
        self.turn_label.pack()

        self.moves_text = tk.Text(
            self.info_frame,
            height=20,
            width=30,
            bg=colors["Dark gray (moves background)"],
            fg=colors["Light gray (moves text)"],
            font=("Arial", 10),
            borderwidth=0
        )
        self.moves_text.pack(pady=5)

        # Bind click event
        self.canvas.bind("<Button-1>", self.on_square_click)

        # Draw initial board
        self.draw_board()
        self.update_moves()

    def draw_board(self):
        self.canvas.delete("all")

        last_move = self.board.move_stack[-1] if self.board.move_stack else None

        for rank in range(8):
            for file in range(8):
                x1 = file * self.square_size
                y1 = (7 - rank) * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                square = chess.square(file, rank)
                color = colors['Light beige'] if (rank + file) % 2 == 0 else colors["Brown"]

                if last_move and (square == last_move.from_square or square == last_move.to_square):
                    color = colors["Light green-yellow"]
                if self.selected_square == square:
                    color = colors["Golden yellow"]

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=colors["Dark gray"])

                piece = self.board.piece_at(square)
                if piece:
                    symbol = unicode_pieces[piece.symbol()]
                    piece_color = colors['Red'] if piece.color == chess.WHITE else colors['Very dark gray']
                    self.canvas.create_text(
                        x1 + self.square_size / 2,
                        y1 + self.square_size / 2,
                        text=symbol,
                        font=("Arial", 36),
                        fill=piece_color
                    )

        for i in range(8):
            self.canvas.create_text(
                i * self.square_size + self.square_size / 2,
                8 * self.square_size - 10,
                text=chr(97 + i),
                font=("Arial", 12, "bold"),
                fill=colors['Light gray']
            )
            self.canvas.create_text(
                10,
                (7 - i) * self.square_size + self.square_size / 2,
                text=str(i + 1),
                font=("Arial", 12, "bold"),
                fill=colors['Light gray']
            )

    def update_moves(self):
        self.moves_text.delete(1.0, tk.END)
        self.turn_label.config(text=f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}")

        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            self.moves_text.insert(tk.END, "No legal moves available!")
            if self.board.is_game_over():
                result = self.board.result()
                messagebox.showinfo("Game Over", f"Game Over! Result: {result}")
            return

        moves_by_piece = {
            chess.PAWN: [], chess.KNIGHT: [], chess.BISHOP: [],
            chess.ROOK: [], chess.QUEEN: [], chess.KING: []
        }

        for move in legal_moves:
            piece = self.board.piece_at(move.from_square)
            if piece:
                moves_by_piece[piece.piece_type].append(self.board.san(move))

        piece_names = {
            chess.PAWN: "Pawn", chess.KNIGHT: "Knight", chess.BISHOP: "Bishop",
            chess.ROOK: "Rook", chess.QUEEN: "Queen", chess.KING: "King"
        }

        self.moves_text.insert(tk.END, "Possible moves:\n\n")
        for piece_type, moves in moves_by_piece.items():
            if moves:
                self.moves_text.insert(tk.END, f"{piece_names[piece_type]}:\n")
                for move in moves:
                    self.moves_text.insert(tk.END, f"  {move}\n")

    def get_promotion_piece(self):
        """Prompt the user to select a promotion piece."""
        pieces = {
            "Queen": chess.QUEEN,
            "Rook": chess.ROOK,
            "Bishop": chess.BISHOP,
            "Knight": chess.KNIGHT,
            "q": chess.QUEEN,
            "r": chess.ROOK,
            "b": chess.BISHOP,
            "k": chess.KNIGHT,
            "Q": chess.QUEEN,
            "R": chess.ROOK,
            "B": chess.BISHOP,
            "K": chess.KNIGHT
        }
        choice = simpledialog.askstring(
            "Pawn Promotion",
            "Promote to (Queen, Rook, Bishop, Knight):",
            parent=self.root
        )
        if choice and choice.capitalize() in pieces:
            return pieces[choice.capitalize()]
        else:
            messagebox.showwarning("Invalid Choice", "Defaulting to Queen.")
            return chess.QUEEN

    def on_square_click(self, event):
        file = event.x // self.square_size
        rank = 7 - (event.y // self.square_size)
        square = chess.square(file, rank)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
                self.draw_board()  # Redraw to show selection
        else:
            piece = self.board.piece_at(self.selected_square)
            move = chess.Move(self.selected_square, square)
            is_promotion = (piece.piece_type == chess.PAWN and
                           ((rank == 7 and self.board.turn == chess.WHITE) or
                            (rank == 0 and self.board.turn == chess.BLACK)))

            if is_promotion:
                promotion_piece = self.get_promotion_piece()
                move = chess.Move(self.selected_square, square, promotion=promotion_piece)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.draw_board()
                self.update_moves()
            elif self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
                self.draw_board()  # Redraw to show new selection
            else:
                self.selected_square = None
                self.draw_board()  # Redraw to clear selection

    def make_move(self, move):
        """Method to make a move programmatically and update the GUI."""
        # Check if the move is a promotion and handle it
        if move.promotion is None:
            piece = self.board.piece_at(move.from_square)
            to_rank = chess.square_rank(move.to_square)
            if (piece and piece.piece_type == chess.PAWN and
                ((to_rank == 7 and self.board.turn == chess.WHITE) or
                 (to_rank == 0 and self.board.turn == chess.BLACK))):
                # For computer moves, default to Queen if promotion not specified
                move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.draw_board()
            self.update_moves()
        else:
            print(f"Invalid move attempted: {move.uci()} in position {self.board.fen()}")