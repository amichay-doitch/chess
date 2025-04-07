import chess
import random
import time
import threading
from queue import Queue
from collections import defaultdict

from prod.constants import move_time_for_engine, max_depth_for_engine

# Piece-square tables with improved pawn promotion incentive
piece_square_tables = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,    # Rank 1
        5, 5, 5, 5, 5, 5, 5, 5,    # Rank 2
        5, -5, -10, 0, 0, -10, -5, 5,  # Rank 3
        0, 0, 0, 20, 20, 0, 0, 0,  # Rank 4
        5, 5, 10, 25, 25, 10, 5, 5,  # Rank 5
        10, 10, 20, 30, 30, 20, 10, 10,  # Rank 6
        50, 50, 50, 50, 50, 50, 50, 50,  # Rank 7
        100, 100, 100, 100, 100, 100, 100, 100  # Rank 8 (promotion)
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

# Endgame king PST for centralization
king_endgame_pst = [
    -10, -5, -5, -5, -5, -5, -5, -10,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 10, 10, 5, 0, -5,
    -5, 0, 5, 10, 10, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -10, -5, -5, -5, -5, -5, -5, -10
]

# Transposition table
transposition_table = {}

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
    undeveloped_penalty = 0
    mobility_bonus = 0
    king_safety = 0
    pawn_structure = 0

    # Material and PST
    total_material = 0
    for square, piece in board.piece_map().items():
        value = piece_value(piece)
        total_material += value if piece.color == chess.WHITE else -value
        rank = chess.square_rank(square)

        if piece.color == chess.WHITE:
            score += value
            if piece.piece_type in piece_square_tables:
                if piece.piece_type == chess.KING and abs(total_material) < 1500:  # Endgame
                    score += king_endgame_pst[square]
                else:
                    score += piece_square_tables[piece.piece_type][square]
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP) and rank == 0:
                undeveloped_penalty -= 30
        else:
            score -= value
            if piece.piece_type in piece_square_tables:
                if piece.piece_type == chess.KING and abs(total_material) < 1500:  # Endgame
                    score -= king_endgame_pst[63 - square]
                else:
                    score -= piece_square_tables[piece.piece_type][63 - square]
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP) and rank == 7:
                undeveloped_penalty += 30

    # Promotion bonus
    for move in board.legal_moves:
        if move.promotion:
            score += 500 if board.turn == chess.WHITE else -500

    # Mobility
    mobility_bonus += len(list(board.legal_moves)) * 5 if board.turn == chess.WHITE else -len(list(board.legal_moves)) * 5

    # King safety (simple pawn shield)
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk and board.ply() < 20:  # Early game
        for sq in chess.SquareSet(chess.BB_FILES[chess.square_file(wk)] & chess.BB_RANKS[1]):
            if board.piece_at(sq) == chess.Piece(chess.PAWN, chess.WHITE):
                king_safety += 20
    if bk and board.ply() < 20:
        for sq in chess.SquareSet(chess.BB_FILES[chess.square_file(bk)] & chess.BB_RANKS[6]):
            if board.piece_at(sq) == chess.Piece(chess.PAWN, chess.BLACK):
                king_safety -= 20

    # Pawn structure evaluation
    pawn_structure = evaluate_pawn_structure(board)

    score += undeveloped_penalty + mobility_bonus + king_safety + pawn_structure
    return score

def evaluate_pawn_structure(board):
    score = 0
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        for pawn in pawns:
            file = chess.square_file(pawn)
            rank = chess.square_rank(pawn)
            if any(board.piece_at(pawn + offset) == chess.Piece(chess.PAWN, color) for offset in [-1, 1]):
                score += 10 if color == chess.WHITE else -10  # Bonus for supported pawns
            if not any(board.piece_at(pawn + offset) == chess.Piece(chess.PAWN, 1 - color) for offset in [-1, 1]):
                score += 20 if color == chess.WHITE else -20  # Bonus for passed pawns
            if len([p for p in pawns if chess.square_file(p) == file]) > 1:
                score -= 10 if color == chess.WHITE else 10  # Penalty for doubled pawns
            if rank == 6 and color == chess.WHITE or rank == 1 and color == chess.BLACK:
                score += 30 if color == chess.WHITE else -30  # Bonus for advanced pawns
    return score

def order_moves(board, moves):
    """Order moves with promotions, captures, checks, and killer moves."""
    killer_moves = getattr(board, 'killer_moves', [None, None])  # Store 2 killer moves per depth

    def move_priority(move):
        if move.promotion:
            return 2000  # High priority for promotions
        if move in killer_moves:
            return 1500  # Killer moves
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_value = piece_value(victim) if victim else 0
            attacker_value = piece_value(attacker) if attacker else 0
            return victim_value - attacker_value + 1000
        board.push(move)
        is_check = board.is_check()
        board.pop()
        return 500 if is_check else 0

    return sorted(moves, key=move_priority, reverse=True)

def minimax(board, depth, alpha, beta, maximizing_player):
    # Transposition table lookup
    pos_key = board.board_fen()
    if pos_key in transposition_table:
        stored_score, stored_depth, stored_flag = transposition_table[pos_key]
        if stored_depth >= depth:
            if stored_flag == "exact":
                return stored_score
            elif stored_flag == "lower" and stored_score >= beta:
                return stored_score
            elif stored_flag == "upper" and stored_score <= alpha:
                return stored_score

    if depth == 0 or board.is_game_over():
        score = evaluate_board(board)
        transposition_table[pos_key] = (score, depth, "exact")
        return score

    legal_moves = order_moves(board, list(board.legal_moves))

    # Futility pruning
    if depth <= 2 and not board.is_check():
        static_eval = evaluate_board(board)
        if maximizing_player and static_eval + 500 < alpha:
            transposition_table[pos_key] = (static_eval, depth, "upper")
            return static_eval
        if not maximizing_player and static_eval - 500 > beta:
            transposition_table[pos_key] = (static_eval, depth, "lower")
            return static_eval

    if maximizing_player:
        max_eval = float('-inf')
        for i, move in enumerate(legal_moves):
            board.push(move)
            # Late Move Reductions
            if i > 3 and depth > 2 and not move.promotion and not board.is_check():
                eval = minimax(board, depth - 2, alpha, beta, False)
                if eval > alpha:
                    eval = minimax(board, depth - 1, alpha, beta, False)
            else:
                eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                if depth == max_depth_for_engine:  # Store killer move at root
                    board.killer_moves = [move, board.killer_moves[0]]
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[pos_key] = (max_eval, depth, "exact")
        return max_eval
    else:
        min_eval = float('inf')
        for i, move in enumerate(legal_moves):
            board.push(move)
            if i > 3 and depth > 2 and not move.promotion and not board.is_check():
                eval = minimax(board, depth - 2, alpha, beta, True)
                if eval < beta:
                    eval = minimax(board, depth - 1, alpha, beta, True)
            else:
                eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                if depth == max_depth_for_engine:
                    board.killer_moves = [move, board.killer_moves[0]]
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[pos_key] = (min_eval, depth, "exact")
        return min_eval

def get_best_move_with_time_limitation(board, max_time=move_time_for_engine, max_depth=max_depth_for_engine, result_queue=None):
    try:
        print(f'Calculating best move (max time: {max_time}s)...')
        if not board.legal_moves:
            print("No legal moves available.")
            if result_queue:
                result_queue.put(None)
            return None

        start_time = time.time()
        last_check = start_time
        best_move = None
        legal_moves = order_moves(board, list(board.legal_moves))
        board.killer_moves = [None, None]

        is_maximizing = board.turn == chess.WHITE
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
                if elapsed_time >= max_time * 0.8:
                    print(f"Time limit reached at depth {depth - 1}. Best move so far returned.")
                    if result_queue:
                        result_queue.put(best_move if best_move else current_best_move)
                    return best_move if best_move else current_best_move

            best_move = current_best_move
            print(f"Completed depth {depth} in {time.time() - start_time:.2f}s")

        if result_queue:
            result_queue.put(best_move)
        return best_move
    except Exception as e:
        print(f"Error in get_best_move_with_time_limitation: {e}")
        if result_queue:
            result_queue.put(None)
        return None


def get_best_move_async_third(board, max_time=move_time_for_engine, max_depth=max_depth_for_engine):
    """Run move calculation in a separate thread and return the result via a queue."""
    result_queue = Queue()
    thread = threading.Thread(
        target=get_best_move_with_time_limitation,
        args=(board.copy(), max_time, max_depth, result_queue)
    )
    thread.start()
    return result_queue

def get_random_engine_move(board):
    print('Random move!')
    legal_moves = list(board.legal_moves)
    return random.choice(legal_moves) if legal_moves else None
