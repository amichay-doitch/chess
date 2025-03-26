import chess
import tkinter as tk
from tkinter import messagebox

from prod.constants import colors


class ChessGUI:
    def __init__(self, root, board=None):
        self.root = root
        self.root.title("Chess Board")
        self.board = board if board is not None else chess.Board()  # Default to a new board if none provided
        self.square_size = 60
        self.selected_square = None

        # Unicode piece symbols
        self.unicode_pieces = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }

        # Create main frame
        self.main_frame = tk.Frame(root, bg="#1e1e1e")
        self.main_frame.pack(padx=10, pady=10)

        # Create canvas for board
        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.square_size * 8,
            height=self.square_size * 8,
            bg="#1e1e1e",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT)

        # Create info panel
        self.info_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.info_frame.pack(side=tk.RIGHT, padx=10)

        self.turn_label = tk.Label(
            self.info_frame,
            text="Turn: White",
            font=("Arial", 12, "bold"),
            bg="#1e1e1e",
            fg="#f5f5f5"
        )
        self.turn_label.pack()

        self.moves_text = tk.Text(
            self.info_frame,
            height=20,
            width=30,
            bg="#2f2f2f",
            fg="#e0e0e0",
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

        # Get the last move from the board's move stack
        last_move = self.board.move_stack[-1] if self.board.move_stack else None

        # Draw squares
        for rank in range(8):
            for file in range(8):
                x1 = file * self.square_size
                y1 = (7 - rank) * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                square = chess.square(file, rank)
                # Default square color
                color = "#f5e8c7" if (rank + file) % 2 == 0 else "#a77b4e"

                # Highlight last move squares
                if last_move and (square == last_move.from_square or square == last_move.to_square):
                    color = "#d4e157"  # Light green-yellow for last move highlight
                # Highlight selected square (overrides last move highlight if applicable)
                if self.selected_square == square:
                    color = "#f0c05a"  # Selected square highlight

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#4a4a4a")

                # Draw piece
                piece = self.board.piece_at(square)
                if piece:
                    symbol = self.unicode_pieces[piece.symbol()]
                    piece_color = colors['Red'] if piece.color == chess.WHITE else colors['Very dark gray']
                    self.canvas.create_text(
                        x1 + self.square_size / 2,
                        y1 + self.square_size / 2,
                        text=symbol,
                        font=("Arial", 36),
                        fill=piece_color
                    )

        # Draw coordinates
        for i in range(8):
            self.canvas.create_text(
                i * self.square_size + self.square_size / 2,
                8 * self.square_size - 10,
                text=chr(97 + i),
                font=("Arial", 12, "bold"),
                fill="#e8e8e8"
            )
            self.canvas.create_text(
                10,
                (7 - i) * self.square_size + self.square_size / 2,
                text=str(i + 1),
                font=("Arial", 12, "bold"),
                fill="#e8e8e8"
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
            chess.PAWN: [],
            chess.KNIGHT: [],
            chess.BISHOP: [],
            chess.ROOK: [],
            chess.QUEEN: [],
            chess.KING: []
        }

        for move in legal_moves:
            piece = self.board.piece_at(move.from_square)
            if piece:
                moves_by_piece[piece.piece_type].append(self.board.san(move))

        piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }

        self.moves_text.insert(tk.END, "Possible moves:\n\n")
        for piece_type, moves in moves_by_piece.items():
            if moves:
                self.moves_text.insert(tk.END, f"{piece_names[piece_type]}:\n")
                for move in moves:
                    self.moves_text.insert(tk.END, f"  {move}\n")

    def on_square_click(self, event):
        file = event.x // self.square_size
        rank = 7 - (event.y // self.square_size)
        square = chess.square(file, rank)

        if self.selected_square is None:
            if self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None  # Reset selection after a valid move
            elif self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
            else:
                self.selected_square = None

        self.draw_board()
        self.update_moves()

    def make_move(self, move):
        """Method to make a move programmatically and update the GUI."""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.draw_board()
            self.update_moves()

