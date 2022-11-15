"""
This is our main driver file. Its responsible for handling user input and displaying current GameState object.
"""
"""
Day 1: Draw a chess board with static pieces.
Day 2: Handle user input to move the pieces around the board.
"""
import math
from shutil import move
import pygame as pg
import ChessEngine, AutomatedMoveFinder #To get reference to the state of the board

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_DISPLAY_PANEL_WIDTH = 300
MOVE_DISPLAY_PANEL_HEIGHT = BOARD_HEIGHT
WHITE = (255,255,255)
GREY = (128,128,128)
DIMENSION = 8 #dimensions of a chess board are 8x8
SQ_SIZE = BOARD_WIDTH // DIMENSION
MAX_FPS = 15 #for animations later on
IMAGES = {}

'''
Initialize a global dictionary of images. This will be called exactly once in main function.
'''

def loadImages():
    pieces = ["bR", "bN", "bB", "bQ", "bK", "bp", "wR", "wN", "wB", "wQ", "wK", "wp"]
    for piece in pieces:
        IMAGES[piece] = pg.transform.scale(pg.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

'''
Main driver code. This will handle user inputs and updating of graphics.
'''
"""Possible improvements: 
1) dialog nox popup at engine startup asking user to choose from among two player mode, playing with AI, playing with oneself.
2) dialog box popup for confirmation when a player wishes to resign by pressing "r" key.
3) dialog box popup for pawn promotion choices to user.
3) move analysis after the game
"""
def main():
    pg.init()
    #Creating the 2D canvas/board
    screen = pg.display.set_mode((BOARD_WIDTH + MOVE_DISPLAY_PANEL_WIDTH, BOARD_HEIGHT))
    clock = pg.time.Clock()
    #Filling the screen with default white color
    screen.fill(pg.Color("white"))
    #Creating an object of GameState class defined inside ChessEngine file
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveLogFont  = pg.font.SysFont("Arial", 14, False, False)
    # for i in range(len(validMoves)):
    #     print((validMoves[i].startrow, validMoves[i].startcol), (validMoves[i].endrow, validMoves[i].endcol))
    # print("\n\n")
    # print(len(validMoves))

    moveMade = False
    gameOver = False
    animate = False
    loadImages() #done only once before the while loop is finished
    running = True
    sqSelected = ()
    clicksMade = []
    playerWhite = True #if its white's turn and a human is playing it, then set to true  if AI plays it, then set to false.
    playerBlack = False #if its black's turn and a human is playing it, then set to true  if AI plays it, then set to false.
    while running:
        isHumanTurn = (gs.whiteToMove and playerWhite) or (not gs.whiteToMove and playerBlack)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                if not gameOver and isHumanTurn:
                    position = pg.mouse.get_pos()
                    y = position[0] // SQ_SIZE
                    x = position[1] // SQ_SIZE
                    if sqSelected == (x, y) or y > 7: # player has clicked on the same square again or clicked on the side panel
                        sqSelected = () #deselecting
                        clicksMade = [] #no valid clicks made, so not updating the clicksMade list
                    else:
                        sqSelected = (x, y) # coordinates of the clicked location
                        clicksMade.append(sqSelected) #updating the log with current click location
                    if len(clicksMade) == 2: #player has made the 2nd click
                        move = ChessEngine.Move(clicksMade[0], clicksMade[1], gs.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]: #move is made only if it is present in the list of valid moves                  
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                clicksMade = [] 
                        if not moveMade:
                            clicksMade = [sqSelected]
            
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_z:
                    if playerWhite and playerBlack:
                        gs.undoMove()
                    elif playerWhite or playerBlack:
                        gs.undoMove()
                        gs.undoMove()
                    moveMade = True #moves undoed or redoed also changes the gamestate
                    animate = False
                elif event.key == pg.K_y:
                    gs.redoMove()
                    moveMade = True
                elif event.key == pg.K_r:
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    clicksMade = []
                    gameOver = False
                    moveMade = False
                    animate = False
        #AI move finder
        if not gameOver and not isHumanTurn:
            AI_moves = AutomatedMoveFinder.bestMoveNegaMaxAplhaBeta(gs, validMoves)
            print(AI_moves.getChessNotation())
            if AI_moves is None:
                AI_moves = AutomatedMoveFinder.makeRandomMove(validMoves)
            gs.makeMove(AI_moves)
            moveMade = True 
            animate = True

        if moveMade: #since the gamestate changes after a valid move is made, so we must retrieve the list of new valid moves
            if animate:
                animateMove(screen, gs.board, gs.moveLog[-1], clock)
            validMoves = gs.getValidMoves() #get valid moves for the opponent who is set to play next turn
            moveMade = False
        
        drawGameState(screen, gs, sqSelected, validMoves, moveLogFont)

        if gs.checkMate or gs.staleMate:
            gameOver = True
            drawGameOverText(screen, 'Stalemate' if gs.staleMate else "Black wins by checkmate" if gs.whiteToMove else "White wins by checkmate")
        
        clock.tick(MAX_FPS)
        pg.display.flip()

'''
Responsible for all graphics on the chess board, including chess pieces, square colors and even move suggestions and piece highlighting.
'''
def drawGameState(screen, gs, sqSelected, validMoves, moveLogFont):
    drawMovesMadeText(screen, gs, moveLogFont)
    drawBoard(screen)
    highlightSquares(screen, gs, sqSelected, validMoves)
    drawPieces(screen, gs.board)

'''
Draw squares on the board
'''
def drawBoard(screen):
    global colors
    colors = [WHITE, GREY]
    for x in range(DIMENSION):
        for y in range(DIMENSION):
            rect = pg.Rect(y*SQ_SIZE, x*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            if (x + y) % 2:
                pg.draw.rect(screen, GREY, rect) 
            else:
                pg.draw.rect(screen, WHITE, rect)    

'''
Add chess pieces to the board
'''
def drawPieces(screen, board):
    for x in range(DIMENSION):
        for y in range(DIMENSION):
            piece = board[x][y]
            if piece != '--':  
                screen.blit(IMAGES[piece], (y*SQ_SIZE, x*SQ_SIZE))
'''
Displaying all the moves made on a right hand side panel
'''
def drawMovesMadeText(screen, gs, font):
    moveRect = pg.Rect(BOARD_WIDTH, 0, MOVE_DISPLAY_PANEL_WIDTH, MOVE_DISPLAY_PANEL_HEIGHT)
    pg.draw.rect(screen, pg.Color("black"), moveRect)
    moveLog = gs.moveLog #grab the movelog
    moveText = []
    for i in range(0, len(moveLog), 2):
        movePair = str(i // 2 + 1) + ") " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog): #ensuring that other player has also made a move
            movePair += str(moveLog[i + 1])
        moveText.append(movePair)
    padding = 5
    lineHeight = 2
    down = lineHeight
    textPerRow = 4
    for i in range(0, len(moveText), textPerRow):
        text = ""
        for j in range(textPerRow):
            if i + j < len(moveText):
                text += moveText[i + j] + " "
        textObject = font.render(text, 1, pg.Color('white'))
        textLocation = moveRect.move(padding, down)
        screen.blit(textObject, textLocation) 
        down += textObject.get_height() + lineHeight

        
def highlightSquares(screen, gs, sqSelected, validMoves):
    #highlight selected square
    s = pg.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(150) #transparency value, 0 --> transparent, 255 --> opaque
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            s.fill(pg.Color('purple'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            #highlighting valid moves from the selected square
            s.fill(pg.Color('green'))
            for move in validMoves:
                if move.startrow == r and move.startcol == c:
                    endcolor = gs.board[move.endrow][move.endcol]
                    if endcolor != '--' and endcolor[0] != gs.board[r][c][0]:
                        s.fill(pg.Color('red')) #capture possible
                    else:
                        s.fill(pg.Color('green')) 
                    screen.blit(s, (move.endcol*SQ_SIZE, move.endrow*SQ_SIZE))

    #highlighting starting and ending square of move made by opponent.
    s.fill(pg.Color('yellow'))
    if len(gs.moveLog) > 0:
        move = gs.moveLog[-1]
        screen.blit(s, (move.endcol*SQ_SIZE, move.endrow*SQ_SIZE))
        screen.blit(s, (move.startcol*SQ_SIZE, move.startrow*SQ_SIZE))


def animateMove(screen, board, move, clock):
    dR = move.endrow - move.startrow
    dC = move.endcol - move.startcol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startrow + dR*frame/frameCount, move.startcol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        #erase piece moved from the ending square
        color = colors[(move.endrow + move.endcol) % 2]
        endSquare = pg.Rect(move.endcol*SQ_SIZE, move.endrow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pg.draw.rect(screen, color, endSquare)
        #draw the captured piece back in that square
        if move.piececaptured != '--':
            if move.isEnPassantMove:
                enPassantRow = move.endrow + 1 if move.piecemoved[0] == 'w' else move.endrow - 1
                endSquare = pg.Rect(move.endcol*SQ_SIZE, enPassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.piececaptured], endSquare)
        #draw the moving piece
        screen.blit(IMAGES[move.piecemoved], pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        pg.display.flip()
        clock.tick((frameCount * 1200) // 30) if frameCount > 30 else clock.tick(120)

def drawGameOverText(screen, text):
    font  = pg.font.SysFont("Verdana", 32, True, False)
    textObject = font.render(text, 0, pg.Color('Gray'))
    textLocation = pg.Rect(BOARD_WIDTH/2 - textObject.get_width()/2, BOARD_HEIGHT/2 - textObject.get_height()/2, BOARD_WIDTH, BOARD_HEIGHT)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, pg.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))


if __name__ == "__main__":
    main()