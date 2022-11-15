"""
This class is responsible for storing all information about the current state of the chess game. It will also determine the valid moves at the current state. And it will also 
maintain a log of all allowed moves. This log will allow us to undo moves, back to a previous state. 
"""

from importlib.metadata import files
import copy

from numpy import block

class GameState():
    def __init__(self):
        #Chess board is represented as an 8x8 2D matrix, each element has 2 characters.
        #First character represents color of the piece, i.e. "b" for black or "w" for white.
        #Second character represents type of the piece, i.e. "p" for pawn, "R" for rook, "N" for knight, etc.
        #"--" represents empty space (there are 4 rows of empty cells in a chess board)
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"], 
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveLog = []
        self.moveRedo = []
        self.whiteToMove = True
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.isCheck = False
        self.enpassantPossible = () #stores the coordinates of the square where an en passant capture move is possible.
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRight = CastlingRights(True, True, True, True)
        self.castlingRightsLog = [CastlingRights(self.currentCastlingRight.wks, self.currentCastlingRight.wqs, 
                                                self.currentCastlingRight.bks, self.currentCastlingRight.bqs)]
        self.pins = []
        self.checks = []
        self.checkMate = False
        self.staleMate = False
        self.moveFunctions = {'p':self.getPawnMoves, 'R':self.getRookMoves, 'N':self.getKnightMoves, 
                              'B':self.getBishopMoves, 'K':self.getKingMoves, 'Q':self.getQueenMoves}
    """
    Takes a move as a parameter and executes it. Doesn't work with en passant, castling and pawn promotion
    """

    def makeMove(self, move):
        if self.board[move.startrow][move.startcol] != "--":
            self.board[move.startrow][move.startcol] = "--"
            self.board[move.endrow][move.endcol] = move.piecemoved
            self.moveLog.append(move) #logging the move to undo it later if needed
            self.whiteToMove = not self.whiteToMove #switch to other player
            #if a piece moved is a king, update its location
            if move.piecemoved == 'wK':
                self.whiteKingLocation = (move.endrow, move.endcol)
            elif move.piecemoved == 'bK':
                self.blackKingLocation = (move.endrow, move.endcol) 

            ischeck, checks, pins = self.findPinsOrChecks()
            if ischeck:
                move.isCheckMove = True

            #pawn promotion
            if move.isPawnPromotion:
                print("Yes")
                promotePiece = 'Q'
                self.board[move.endrow][move.endcol] = move.piecemoved[0] + promotePiece
            
            #En Passant handling
            if move.isEnPassantMove:
                move.piececaptured = self.board[move.startrow][move.endcol] #for undoing en passant move, recovering the captured pawn is done using this statement
                self.board[move.startrow][move.endcol] = '--' #capturing the enemy pawn by making en passant move

            #whenever a pawn makes two square move, possible en passant square between starting and ending square needs to be tracked
            self.enpassantPossible = ((move.startrow + move.endrow) // 2, move.startcol) if move.piecemoved[1] == 'p' and abs(move.endrow - move.startrow) == 2 else  ()
            self.enpassantPossibleLog.append(self.enpassantPossible)
            
            #castle move 
            if move.isCastleMove:
                if move.endcol- move.startcol == 2: #king side castle move
                    self.board[move.endrow][move. endcol - 1] = self.board[move.endrow][move. endcol + 1] #moves the rook
                    self.board[move.endrow][move. endcol + 1] = '--'
                else: #queen side castle move
                    self.board[move.endrow][move. endcol + 1] = self.board[move.endrow][move. endcol - 2] #moves the rook
                    self.board[move.endrow][move. endcol - 2] = '--'

            #update castling rights, whenever a rook or a king moves
            self.updateCastleRights(move)
            #add the new castling rights to the log
            self.castlingRightsLog.append(CastlingRights(self.currentCastlingRight.wks, self.currentCastlingRight.wqs, 
                                                self.currentCastlingRight.bks, self.currentCastlingRight.bqs))

    """
    Undo the last move
    """
    def undoMove(self):
        if len(self.moveLog) > 0: #making sure that there is a move to undo
            move = self.moveLog.pop()
            self.board[move.startrow][move.startcol] = move.piecemoved
            self.board[move.endrow][move.endcol] = move.piececaptured
            self.whiteToMove = not self.whiteToMove #switch to other player
            #if a piece moved is a king, update its location
            if move.piecemoved == 'wK':
                self.whiteKingLocation = (move.startrow, move.startcol)
            elif move.piecemoved == 'bK':
                self.blackKingLocation = (move.startrow, move.startcol)

            #En Passant
            if move.isEnPassantMove:
                self.board[move.endrow][move.endcol] = '--'
                self.board[move.startrow][move.endcol] = move.piececaptured

            #Two square pawn moves
            if move.piecemoved[1] == 'p' and abs(move.endrow - move.startrow) == 2:
                self.enpassantPossible = ()

            #undo castle move
            if move.isCastleMove:
                if move.endcol- move.startcol == 2: #king side castle move
                    self.board[move.endrow][move.endcol + 1] = self.board[move.endrow][move.endcol - 1]
                    self.board[move.endrow][move.endcol - 1] = '--'
                else: #queen side castle move
                    self.board[move.endrow][move. endcol - 2] = self.board[move.endrow][move. endcol + 1] #moves the rook
                    self.board[move.endrow][move. endcol + 1] = '--'
            
            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            #undo castle rights
            self.castlingRightsLog.pop() #while undoing, we delete the latest castling rights object
            castle_rights = copy.deepcopy(self.castlingRightsLog[-1])
            self.currentCastlingRight = castle_rights #and set the current castling rights to the previous, now last rights from the log.

            self.moveRedo.append(move)

            self.checkMate = False
            self.staleMate = False 
    
    def updateCastleRights(self, move):
        if move.piecemoved == 'wK':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.piecemoved == 'bK':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.piecemoved == 'wR':
            if move.startrow == 7: 
                if move.startcol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.startcol == 7:
                    self.currentCastlingRight.wks = False
        elif move.piecemoved == 'bR':
            if move.startrow == 0: 
                if move.startcol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.startcol == 7:
                    self.currentCastlingRight.bks = False

        if move.piececaptured == 'wR':
            if move.endrow == 7: 
                if move.endcol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endcol == 7:
                    self.currentCastlingRight.wks = False
        if move.piececaptured == 'bR':
            if move.endrow == 0: 
                if move.endcol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endcol == 7:
                    self.currentCastlingRight.bks = False


    """
    Redo the last undoed move
    """
    def redoMove(self):
        if len(self.moveRedo) > 0: #making sure that there are previously undoed moves to redo
            move = self.moveRedo.pop()
            self.board[move.startrow][move.startcol] = "--"
            self.board[move.endrow][move.endcol] = move.piecemoved
            self.whiteToMove = not self.whiteToMove #switch to other player
            #if a piece moved is a king, update its location
            if move.piecemoved == 'wK':
                self.whiteKingLocation = (move.endrow, move.endcol)
            elif move.piecemoved == 'bK':
                self.blackKingLocation = (move.endrow, move.endcol) 

            if move.isEnPassantMove:
                move.piececaptured = self.board[move.startrow][move.endcol]
                self.board[move.startrow][move.endcol] = '--' #capturing the enemy pawn by making en passant move
                self.enpassantPossible.pop()

            #whenever a pawn makes two square move, possible en passant square between starting and ending square needs to be tracked
            if move.piecemoved[1] == 'p' and abs(move.endrow - move.startrow) == 2: 
                self.enpassantPossible.append(((move.startrow + move.endrow) // 2, move.startcol))
            
            #castle move 
            if move.isCastleMove:
                if move.endcol- move.startcol == 2: #king side castle move
                    self.board[move.endrow][move. endcol - 1] = self.board[move.endrow][move. endcol + 1] #moves the rook
                    self.board[move.endrow][move. endcol + 1] = '--'
                else:
                    self.board[move.endrow][move. endcol + 1] = self.board[move.endrow][move. endcol - 2] #moves the rook
                    self.board[move.endrow][move. endcol - 2] = '--'

            #update castling rights, whenever a rook or a king moves
            self.updateCastleRights(move)
            #add the new castling rights to the log
            self.castlingRightsLog.append(CastlingRights(self.currentCastlingRight.wks, self.currentCastlingRight.wqs, 
                                                self.currentCastlingRight.bks, self.currentCastlingRight.bqs))

            self.moveLog.append(move)
    
    """
    determine valid moves for a piece considering checks from the opponent (advanced algorithm)
    """
    def getValidMoves(self):
        moves = []
        self.isCheck, self.checks, self.pins = self.findPinsOrChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        if self.isCheck:
            if len(self.checks) == 1: #only one enemy piece is checking the king, so block the check, move king or remove attacking piece
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] #get info about the piece that's checking
                validSquares = [] #valid locations where pieces can move to block the king from being checked
                #if attacking piece is a knight, only option is to capture it or move the king
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(8):
                        validSquares.append((kingRow + check[2] * i, kingCol + check[3] * i)) #check[2] and check[3] are the check directions
                        # we have reached the checking piece and captured all possible locations where other pieces could move
                        if validSquares[0] == checkRow and validSquares[1] == checkCol: 
                            break

                #remove all moves that do not block a check or move the king    
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piecemoved[1] != 'K': #move did not change location of king 
                        if not (moves[i].endrow, moves[i].endcol) in validSquares: #moves that don't block the king
                            moves.remove(moves[i])
            else: #if double or more checks, then king has to move
                self.getKingMoves(kingRow, kingCol, moves)
        else: #no check, all moves (except pinned pieces, dealt later) are valid
                moves = self.getAllPossibleMoves()

        # #1) Generate all possible moves for a piece.
        # moves = self.getAllPossibleMoves()
        # #2) From each move, make the move.
        # for i in range(len(moves) - 1, -1, -1):
        #     self.makeMove(moves[i])
        #     #3) For each move made, generate all possible moves for your opponent.
        #     #4) For each of your opponent's moves, check if they attack your king.'
        #     #if the king is in check after we make a move from the list of possible moves,
        #     #then that move must be removed from the list of possible moves as it is invalid
        #     if self.inCheck(): 
        #         #5) If they do attack the king, not a valid move.
        #         moves.remove(moves[i])
        #     self.undoMove()
        #     self.moveRedo.pop()
        
        if len(moves) == 0: #checking for checkmate and stalemate condition.
            if self.isCheck: #if there are no valid moves and king is in check
                self.checkMate = True
            else:
                self.staleMate = True #if there are no valid moves and king is not in check
        # else:
        #     self.checkMate = False
        #     self.staleMate = False
        return moves

    # def inCheck(self):
    #     #calling makeMove() function switches turn to opponent, so we use not whiteToMove to point to current player
    #     if not self.whiteToMove:
    #         #if king is under attack, then white player is in check.
    #         return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
    #     else:
    #         #if king is under attack, then black player is in check.
    #         return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])
    
    # def squareUnderAttack(self, r, c):
    #     oppMoves = self.getAllPossibleMoves()
    #     for move in oppMoves:
    #         #checking if the ending coordinates of any move made by the opponent matches the king's location of current player
    #         if move.endrow == r and move.endcol == c: 
    #             return True
    #     return False
    
    def findPinsOrChecks(self):
        isCheck = False
        pins, checks = [], []
        if self.whiteToMove:
            allyColor = 'w'
            enemyColor = 'b'
            startrow = self.whiteKingLocation[0]
            startcol = self.whiteKingLocation[1]
        else:
            allyColor = 'b'
            enemyColor = 'w'
            startrow = self.blackKingLocation[0]
            startcol = self.blackKingLocation[1] 
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, 1), (1, -1)]
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range(1, 8):
                endrow = startrow + d[0] * i
                endcol = startcol + d[1] * i
                if 0 <= endrow <= 7 and 0 <= endcol <= 7: #inside board
                    endPiece = self.board[endrow][endcol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == (): #1st allied piece found in a given direction can become a possible pin. 
                            possiblePin = (endrow, endcol, d[0], d[1])
                        else: #another allied piece, if found in the same direction cancels the pinning effect from an attacking enemy piece along that direction
                            break
                    elif endPiece[0] == enemyColor: #if an enemy piece found in a given direction
                        type = endPiece[1] # then we need to perform operations based on type of the piece
                        #There are 5 conditions that can be applicable based on the type of enemy piece encountered in a given direction.
                        #1) If the piece is a rook and it is orthogonally away from a king
                        #2) If the piece is a bishop and diagonally away from a king
                        #3) If the piece is a pawn and one square away from a king diagonally
                        #4) If the piece is a queen attacking from any direction
                        #5) If the piece is the enemy king and 1 square away in all 8 directions.
                        if (type == 'R' and 0 <= j <= 3) or (type == 'B' and 4 <= j <= 7) or \
                            (type == 'p' and i == 1 and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                                (type == 'Q') or (type == 'K' and i == 1):
                                if possiblePin == (): #no allied pieces blocking the king and only enemy piece is present, in such a case, king is in check
                                    isCheck = True
                                    checks.append((endrow, endcol, d[0], d[1]))
                                else: #pinned piece found
                                    pins.append(possiblePin)
                        else: #enemy piece present but not attacking
                            break 
                else: #outside board
                    break

        #checks for knight pieces
        knightDirections = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, 2), (1, -2)]
        for i in range(len(knightDirections)):
            d = knightDirections[i]
            endrow = startrow + d[0]
            endcol = startcol + d[1]
            if 0 <= endrow < 8 and 0 <= endcol < 8: #inside board
                endPiece = self.board[endrow][endcol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    isCheck = True
                    checks.append((endrow, endcol, d[0], d[1]))
            else: #outside board
                break
        return isCheck, checks, pins



    """
    determine all possible moves for a piece without considering checks from the opponent.
    """
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves) #calls the appropriate move function based on piece type
        return moves
    
    """
    Get all pawn moves for a pawn at a given row and column and add these to the list of all moves
    """
    def enPassantKingChecks(self, r, enemyColor, insideRange, outsideRange):
        attack = block = False
        for i in insideRange:
            if self.board[r][i] != '--':
                block = True
                break
        for i in outsideRange:
            piece = self.board[r][i]
            if piece == enemyColor + 'R' or piece == enemyColor + 'Q':
                attack = True
                break
            elif piece != '--':
                block = True
                break
        return attack, block

    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        if self.whiteToMove:
            moveAmt = -1
            startrow = 6 
            backrow = 0
            enemyColor = 'b'
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmt = 1
            startrow = 1 
            backrow = 7
            enemyColor = 'w'
            kingRow, kingCol = self.blackKingLocation
        pawnPromotion = False
        
        if self.board[r + moveAmt][c] == '--':
            if not piecePinned or pinDirection == (moveAmt, 0):
                if r + moveAmt == backrow: # if piece gets into back rank, then pawn promotion possible
                    pawnPromotion = True
                moves.append(Move((r, c), (r + moveAmt, c), self.board, pawnPromotion = pawnPromotion))
                if r == startrow and self.board[r + (2*moveAmt)][c] == '--': #pawn two square move
                    moves.append(Move((r, c), (r + (2*moveAmt), c), self.board))
        if c != 0: #capture to left
            if not piecePinned or pinDirection == (moveAmt, -1):
                if (self.board[r + moveAmt][c - 1][0] == enemyColor):
                    if r + moveAmt == backrow: # if piece gets into back rank, then pawn promotion possible
                        pawnPromotion = True
                    moves.append(Move((r, c), (r + moveAmt, c - 1), self.board, pawnPromotion = pawnPromotion))
                elif (r + moveAmt, c - 1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        insideRange, outsideRange = (range(kingCol + 1, c - 1), range(c + 1, 8)) if kingCol < c else (range(kingCol - 1, c, -1), range(c - 2, -1, -1))
                        attackingPiece, blockingPiece = self.enPassantKingChecks(r, enemyColor, insideRange, outsideRange)
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmt, c - 1), self.board, isEnPassantMove=True)) 
        if c != 7: #capture to right
            if not piecePinned or pinDirection == (moveAmt, 1):
                if(self.board[r + moveAmt][c + 1][0] == enemyColor):
                    if r + moveAmt == backrow: # if piece gets into back rank, then pawn promotion possible
                        pawnPromotion = True
                    moves.append(Move((r, c), (r + moveAmt, c + 1), self.board, pawnPromotion = pawnPromotion))
                elif (r + moveAmt, c + 1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        insideRange, outsideRange = (range(kingCol + 1, c), range(c + 2, 8)) if kingCol < c else (range(kingCol - 1, c + 1, -1), range(c - 1, -1, -1))
                        attackingPiece, blockingPiece = self.enPassantKingChecks(r, enemyColor, insideRange, outsideRange)
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmt, c + 1), self.board, isEnPassantMove=True)) 

    """
    Get all rook moves for a rook at a given row and column and add these to the list of all moves
    """ 
    def getRookMoves(self, r, c, moves):

        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q': #cannot remove queen if pinned as a rook, can only be removed if pinned as a bishop
                    self.pins.remove(self.pins[i])
                break


        enemyPiece = 'b' if self.whiteToMove else 'w'
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)] #top, left, bottom, right
        for d in directions:
            for i in range(1, 8):
                endrow = r + d[0] * i
                endcol = c + d[1] * i
                if 0 <= endrow < 8 and 0 <= endcol < 8: #inside board
                    if not piecePinned or (pinDirection == d or pinDirection == (-d[0], -d[1])):
                        endPiece = self.board[endrow][endcol]
                        if endPiece == '--': 
                            moves.append(Move((r, c), (endrow, endcol), self.board))
                        elif endPiece[0] == enemyPiece:
                            moves.append(Move((r, c), (endrow, endcol), self.board))
                            break
                        else:
                            break 
                else: #outside board
                    break

    """
    Get all knight moves for a knight at a given row and column and add these to the list of all moves
    """
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break 

        allyPiece = 'w' if self.whiteToMove else 'b'
        #four orientations of L shaped move, each with its own reflections, so total 8 moves possible
        directions = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, 2), (1, -2)] 
        for d in directions:
            endrow = r + d[0] 
            endcol = c + d[1] 
            if 0 <= endrow < 8 and 0 <= endcol < 8: #inside board
                if not piecePinned:
                    endPiece = self.board[endrow][endcol]
                    if endPiece[0] != allyPiece:
                        moves.append(Move((r, c), (endrow, endcol), self.board))

    """
    Get all bishop moves for a bishop at a given row and column and add these to the list of all moves
    """
    def getBishopMoves(self, r, c, moves):

        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        enemyPiece = 'b' if self.whiteToMove else 'w'
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] #north-west, north-east, south-west, south-east
        for d in directions:
            for i in range(1, 8):
                endrow = r + d[0] * i
                endcol = c + d[1] * i
                if 0 <= endrow < 8 and 0 <= endcol < 8: #inside board
                    if not piecePinned or (pinDirection == d or pinDirection == (-d[0], -d[1])):
                        endPiece = self.board[endrow][endcol]
                        if endPiece == '--': 
                            moves.append(Move((r, c), (endrow, endcol), self.board))
                        elif endPiece[0] == enemyPiece:
                            moves.append(Move((r, c), (endrow, endcol), self.board))
                            break
                        else:
                            break 
                else: #outside board
                    break

    """
    Get all king moves for a king at a given row and column and add these to the list of all moves
    """
    def getKingMoves(self, r, c, moves):
        temp_moves = []
        allyPiece = 'w' if self.whiteToMove else 'b'
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)] 
        for i in range(8):
            endrow = r + directions[i][0]
            endcol = c + directions[i][1]
            if 0 <= endrow < 8 and 0 <= endcol < 8:
                endPiece = self.board[endrow][endcol]
                if endPiece[0] != allyPiece: #empty or enemy piece
                    #move king to that location
                    if allyPiece == 'w':
                        self.whiteKingLocation = (endrow, endcol)
                    else:
                        self.blackKingLocation = (endrow, endcol)
                    #determine the value of isCheck, to see if the king is in check after placing the king in the new location
                    isCheck, checks, pins = self.findPinsOrChecks()
                    if not isCheck: #if king is not in check after the movemement
                        moves.append(Move((r, c), (endrow, endcol), self.board))
                    #move the king back to its original place
                    if allyPiece == 'w':
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

        self.getCastleMoves(r, c, moves, allyPiece)
    
    '''
    Generate all valid castle moves for the king at (r, c) and add them to the list.
    '''

    def getCastleMoves(self, r, c, moves, allyPiece):
        isCheck, checks, pins = self.findPinsOrChecks()
        if isCheck:
            return #we cannot castle the king as it is in check
        #if king side is vacant
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingSideCastleMoves(r, c, moves, allyPiece)
        #if queen side is vacant
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueenSideCastleMoves(r, c, moves, allyPiece)
    
    def castleSquareChecks(self, r, c, allyPiece, moveAmt):
        if allyPiece == 'w':
            self.whiteKingLocation = (r, c + moveAmt)
            checkSqOne, ch, p = self.findPinsOrChecks()
            self.whiteKingLocation = (r, c + 2*moveAmt)
            checkSqTwo, ch, p = self.findPinsOrChecks()
            self.whiteKingLocation = (r, c)
        else:
            self.blackKingLocation = (r, c + moveAmt)
            checkSqOne, ch, p = self.findPinsOrChecks()
            self.blackKingLocation = (r, c + 2*moveAmt)
            checkSqTwo, ch, p = self.findPinsOrChecks()
            self.blackKingLocation = (r, c)
        return checkSqOne, checkSqTwo

    def getKingSideCastleMoves(self, r, c, moves, allyPiece):
        if self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--':
            checkSqOne, checkSqTwo = self.castleSquareChecks(r, c, allyPiece, 1)          
            if not checkSqOne and not checkSqTwo:
                moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove = True))

    def getQueenSideCastleMoves(self, r, c, moves, allyPiece):
        if self.board[r][c - 1] == '--' and self.board[r][c - 2] == '--' and self.board[r][c - 3] == '--':
            checkSqOne, checkSqTwo = self.castleSquareChecks(r, c, allyPiece, -1)          
            if not checkSqOne and not checkSqTwo:
                moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove = True))

    """
    Get all queen moves for a queen at a given row and column and add these to the list of all moves
    """
    def getQueenMoves(self, r, c, moves):
        #a queen moves like a rook and a bishop, so all possible moves are computed by calling bishop and rook functions
        self.getBishopMoves(r, c, moves)
        self.getRookMoves(r, c, moves)


class CastlingRights:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs



class Move:
    #maps rows and columns to chess notation for ranks and files respectively and vice versa.
    ranksToRows = {"1":7, "2":6, "3":5, "4":4, "5":3, "6":2, "7":1, "8":0}
    rowsToRanks = {v:k for k, v in ranksToRows.items()}
    filesToCols = {"a":0, "b":1, "c":2, "d":3, "e":4, "f":5, "g":6, "h":7}
    colsToFiles = {v:k for k, v in filesToCols.items()}

    #enpassantPossible is an optional parameter for making en passant move in a possible square
    #pawnMoves function passes coordinate value to this paramter, if no value is passed, by default it would be empty, set to ()
    def __init__(self, startPos, endPos, board, isEnPassantMove=False, pawnPromotion=False, isCastleMove=False, isCheckMove=False): 
        self.startcol = startPos[1]
        self.startrow = startPos[0]
        self.endcol = endPos[1]
        self.endrow = endPos[0]
        self.piecemoved = board[self.startrow][self.startcol]
        self.piececaptured = board[self.endrow][self.endcol]
        self.isCapture = self.piececaptured != '--'
        #Pawn Promotion
        self.isPawnPromotion = pawnPromotion
        #En Passant
        self.isEnPassantMove = isEnPassantMove
        #Castling
        self.isCastleMove = isCastleMove
        self.moveID = self.startrow * 1000 + self.startcol * 100 + self.endrow * 10 + self.endcol
        #Checks
        self.isCheckMove = isCheckMove
        # print(self.moveID)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
            #return self.getChessNotation() == other.getChessNotation()
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startcol, self.startrow) + self.getRankFile(self.endcol, self.endrow)

    def getRankFile(self, col, row):
        return self.colsToFiles[col] + self.rowsToRanks[row]
    
    def __str__(self):
        if self.isCastleMove:
            return "o-o" if self.endcol == 6 else "o-o-o"
        endSquare = self.getRankFile(self.endcol, self.endrow)
        if self.piecemoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startcol] + "x" + endSquare
            elif self.isPawnPromotion:
                return endSquare + "Q" 
            elif self.isCapture and self.isPawnPromotion:
                return self.colsToFiles[self.startcol] + "x" + endSquare + "Q"
            elif self.isCheckMove:
                return self.colsToFiles[self.startcol] + "+" + endSquare
            else:
                return endSquare


        elif self.isCheckMove:
                return self.piecemoved[1] + "+" + endSquare
        else:
            return self.piecemoved[1] + "x" + endSquare if self.isCapture else  self.piecemoved[1] + endSquare


