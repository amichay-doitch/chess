import chess
import random
import time

# Piece-square tables for better positional evaluation (simplified)
piece_square_tables = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 5, -30,
        -30, 5, 15, 20, 20, 15, 0, -30,
        -30, 0, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 5, 5, 0, 0, 0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20
    ]
}

def piece_value(piece):
    values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
              chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 100000}
    return values.get(piece.piece_type, 0)


def evaluate_board(board):
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square, piece in board.piece_map().items():
        value = piece_value(piece)
        if piece.color == chess.WHITE:
            score += value
            if piece.piece_type in piece_square_tables:
                score += piece_square_tables[piece.piece_type][square]
        else:
            score -= value
            if piece.piece_type in piece_square_tables:
                score -= piece_square_tables[piece.piece_type][63 - square]  # Flip for Black
    return score


def evaluate_board(board):
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    undeveloped_penalty = 0

    for square, piece in board.piece_map().items():
        value = piece_value(piece)
        rank = chess.square_rank(square)

        if piece.color == chess.WHITE:
            score += value
            if piece.piece_type in piece_square_tables:
                score += piece_square_tables[piece.piece_type][square]
            # Penalty for undeveloped pieces on White's back rank (rank 0)
            if piece.piece_type != chess.PAWN and rank == 0:
                undeveloped_penalty -= 50  # Negative for White
        else:
            score -= value
            if piece.piece_type in piece_square_tables:
                score -= piece_square_tables[piece.piece_type][63 - square]
            # Penalty for undeveloped pieces on Black's back rank (rank 7)
            if piece.piece_type != chess.PAWN and rank == 7:
                undeveloped_penalty += 50  # Positive for Black (to reduce Black's score)

    # Apply the penalty to the total score
    score += undeveloped_penalty
    return score


def order_moves(board, moves):
    """Order moves to maximize alpha-beta pruning efficiency."""

    def move_priority(move):
        # Prioritize captures with a rough estimate of value (MVV-LVA: Most Valuable Victim, Least Valuable Attacker)
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_value = piece_value(victim) if victim else 0
            attacker_value = piece_value(attacker) if attacker else 0
            return victim_value - attacker_value  # Higher value for capturing high-value pieces with low-value pieces
        # Prioritize checks
        board.push(move)
        is_check = board.is_check()
        board.pop()
        return 1000 if is_check else 0  # Arbitrary high value for checks

    return sorted(moves, key=move_priority, reverse=True)


def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax with alpha-beta pruning.
    - alpha: Best score maximizing player can guarantee
    - beta: Best score minimizing player can guarantee
    - Pruning occurs when beta <= alpha, meaning the opponent has a better option earlier.
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = order_moves(board, list(board.legal_moves))

    if maximizing_player:  # White's turn (maximizing score)
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)  # Update alpha with the best option found
            if beta <= alpha:  # Pruning: Opponent won't allow this branch (they have a better beta)
                break
        return max_eval
    else:  # Black's turn (minimizing score)
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)  # Update beta with the best option found
            if beta <= alpha:  # Pruning: Maximizing player won't allow this branch (they have a better alpha)
                break
        return min_eval



def get_best_move_with_time_limitation(board, max_time=10, max_depth=10):
    print(f'Calculating best move (max time: {max_time}s)...')
    if not board.legal_moves:
        return None

    start_time = time.time()
    last_check = start_time
    best_move = None
    legal_moves = order_moves(board, list(board.legal_moves))

    is_maximizing = board.turn == chess.WHITE  # White maximizes, Black minimizes
    for depth in range(1, max_depth + 1):
        current_time = time.time()
        if current_time - last_check >= 10:
            print(f"\rElapsed time: {current_time - start_time:.2f} seconds")
            last_check = current_time

        current_best_move = None
        best_value = float('-inf') if is_maximizing else float('inf')
        alpha = float('-inf')
        beta = float('inf')

        for move in legal_moves:
            board.push(move)
            value = minimax(board, depth - 1, alpha, beta, not is_maximizing)
            board.pop()

            if is_maximizing:
                if value > best_value:
                    best_value = value
                    current_best_move = move
                alpha = max(alpha, value)
            else:
                if value < best_value:
                    best_value = value
                    current_best_move = move
                beta = min(beta, value)

            elapsed_time = time.time() - start_time
            if elapsed_time >= max_time:
                print(f"Time limit reached at depth {depth - 1}. Best move so far returned.")
                return best_move if best_move else current_best_move

        best_move = current_best_move
        print(f"Completed depth {depth} in {time.time() - start_time:.2f}s")

    return best_move

def get_random_engine_move(board):
    print('Random move!')
    legal_moves = list(board.legal_moves)
    return random.choice(legal_moves) if legal_moves else None