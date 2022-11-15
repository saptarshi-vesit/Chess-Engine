import random
pieceScore = {'Q':9, 'R':5, 'B':3, 'N':3, 'p':1, 'K':0}

knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScores = [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores = [[1, 1, 1, 3, 1, 1, 1, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores = [[4, 3, 4, 4, 4, 4, 3, 4],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [4, 3, 4, 4, 4, 4, 3, 4]]

whitePawnScores = [[8, 8, 8, 8, 8, 8, 8, 8],
                   [8, 8, 8, 8, 8, 8, 8, 8],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores = whitePawnScores[::-1]

piecePositionScores = {"N": knightScores, "B": bishopScores, "R": rookScores, "Q":queenScores, "wp": whitePawnScores, "bp":blackPawnScores}
                

CHECKMATE = 1000
STALEMATE = 0
MAX_DEPTH = 2
def makeRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves)-1)]
nextMove = None
'''
for black:
assuming worst possible score for black is +1000, so initially, maxScore = +1000
score < maxScore OR -score > -maxScore ..... (1)

for white:
assuming worst possible score for white is -1000, so initially, maxScore = -1000
score > maxScore ........ (2)

We can use (1) and (2) to define a common function for determining best move for AI, playing either black or white.

So, initially, setting maxScore to a large negative value(-1000 in this case) and later multiplying score with turn variable helps solve this problem.
'''
def makeBestMove(gs, validMoves):
    bestMove = None
    turn = 1 if gs.whiteToMove else -1 
    opponentMinMax = CHECKMATE
    random.shuffle(validMoves)
    for playerMove in validMoves:
        gs.makeMove(playerMove)
        opponentMoves = gs.getValidMoves()
        if gs.checkMate:
            opponentMax = -CHECKMATE
        elif gs.staleMate:
            opponentMax = STALEMATE
        else:
            opponentMax = -CHECKMATE
            for opponentMove in opponentMoves:
                gs.makeMove(opponentMove)
                gs.getValidMoves()
                if gs.checkMate:
                    score = CHECKMATE
                elif gs.staleMate:
                    score = STALEMATE
                else:
                    score = (-turn * board_score(gs.board)) 
                if opponentMax < score:
                    opponentMax = score
                gs.undoMove()
        if opponentMinMax > opponentMax:
            opponentMinMax = opponentMax
            bestMove = playerMove
        gs.undoMove()
    return bestMove

"""
Mini Max 
"""
def bestMoveMinMax(gs, validMoves):
    global nextMove
    minMaxMoveFind(gs, validMoves, MAX_DEPTH, gs.whiteToMove)
    return nextMove

def minMaxMoveFind(gs, validMoves, depth, whiteToMove):
    global nextMove
    if depth == 0:
        return board_score(gs)
    else:
        random.shuffle(validMoves)
        if whiteToMove:
            maxScore = -CHECKMATE
            for move in validMoves:
                gs.makeMove(move)
                oppMoves = gs.getValidMoves()
                score = minMaxMoveFind(gs, oppMoves, depth - 1, False)
                if score > maxScore:
                    maxScore = score
                    if depth == MAX_DEPTH:
                        nextMove = move
                gs.undoMove()
            return maxScore
        else:
            minScore = CHECKMATE
            for move in validMoves:
                gs.makeMove(move)
                oppMoves = gs.getValidMoves()
                score = minMaxMoveFind(gs, oppMoves, depth - 1, True)
                if score < minScore:
                    minScore = score
                    if depth == MAX_DEPTH:
                        nextMove = move
                gs.undoMove()
            return minScore

"""
Nega Max
"""
def bestMoveNegaMax(gs, validMoves):
    global nextMove
    turn = 1 if gs.whiteToMove else -1
    negMaxMoveFind(gs, validMoves, MAX_DEPTH, turn)
    return nextMove

def negMaxMoveFind(gs, validMoves, depth, turn):
    global nextMove, counter 
    counter += 1
    if depth == 0:
        return turn * board_score(gs)
    else:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            oppMoves = gs.getValidMoves()
            score = -negMaxMoveFind(gs, oppMoves, depth - 1, -turn)
            if score > maxScore: # if a < b then -a > -b
                maxScore = score
                if depth == MAX_DEPTH:
                    nextMove = move
            gs.undoMove()
        return maxScore


"""
Alpha Beta Pruning
"""
def bestMoveNegaMaxAplhaBeta(gs, validMoves):
    global nextMove, counter
    turn = 1 if gs.whiteToMove else -1
    random.shuffle(validMoves)
    #negMaxMoveFind(gs, validMoves, MAX_DEPTH, turn)
    negMaxMoveFindAlphaBeta(gs, validMoves, MAX_DEPTH, -CHECKMATE, CHECKMATE, turn)
    return nextMove

def negMaxMoveFindAlphaBeta(gs, validMoves, depth, alpha, beta, turn):
    global nextMove, counter
    if depth == 0:
        return turn * board_score(gs)
    else:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            oppMoves = gs.getValidMoves()
            score = -negMaxMoveFindAlphaBeta(gs, oppMoves, depth - 1, -beta, -alpha, -turn)
            if score > maxScore: # if a < b then -a > -b
                maxScore = score
                if depth == MAX_DEPTH:
                    nextMove = move
                    print(nextMove, score)
            gs.undoMove()
            alpha = max(alpha, maxScore)
            if beta <= alpha:
                break
        return maxScore

'''
Computing the score of the board, applying a zero sum game.
If white captures more pieces, we increase the score of the board by the pieceScore value, if black captures more, we decrease.
'''
def board_score(gs):
    turn = 1 if gs.whiteToMove else -1
    if gs.checkMate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE 
    elif gs.staleMate:
        return STALEMATE
    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            piece = gs.board[row][col]
            if piece != '--':
                piecePositionScore = 0
                if piece[1] != 'K': #no position table for king
                    #scoring the board positionally and piece capture wise as well
                    score += turn * (pieceScore[piece[1]] + piecePositionScores[piece][row][col] * .1) if piece[1] == 'p' else \
                        turn * (pieceScore[piece[1]] + piecePositionScores[piece[1]][row][col] * .1)
                    
    return score


# #scoring the board positionally and piece capture wise as well
#                     score += turn * (pieceScore[piece[1]] + piecePositionScores[piece][row][col] * .1) if piece[1] == 'p' else \
#                         turn * (pieceScore[piece[1]] + piecePositionScores[piece[1]][row][col] * .1)