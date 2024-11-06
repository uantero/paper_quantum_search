import pygame
import sys
import math
import time


BLACK = (0, 0, 0)
WHITE = (200, 200, 200)
GREY = (100,100,100)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
WINDOW_HEIGHT = 600
WINDOW_WIDTH = 600
FONT_SIZE = 80

map2 = [
    [ "XX", "00", "00", "00"],
    [ "XX", "00", "XX", "00"],
    [ "XX", "XX", "00", "00"],
    [ "00", "00", "00", "00"],
]

map = [
        [ "00", "00"],
        [ "00", "XX"]
]

NUM_BITS=1
format_string = "{:0" + str(NUM_BITS) + "b}" # 


def main():
    global SCREEN, CLOCK
    pygame.init()
    pygame.display.set_caption('Robot localization using quantum search')
    SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    CLOCK = pygame.time.Clock()
    SCREEN.fill(BLACK)

    robot_position = (1,1)


    pygame.font.init() # you have to call this at the start, 
                    # if you want to use this module.
    robot_font = pygame.font.SysFont('Arial', FONT_SIZE)

    small_font = pygame.font.SysFont('Arial', 22)



    while True:
        time.sleep(0.1)
        drawGrid(SCREEN, robot_position, robot_font, small_font)
        for event in pygame.event.get():
            if event.type== pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    robot_position= (robot_position[0], max(robot_position[1]-1,0))
                elif event.key == pygame.K_RIGHT:
                    robot_position= (robot_position[0], min(robot_position[1]+1, len(map[0])-1))
                elif event.key == pygame.K_UP:
                    robot_position= (max(robot_position[0]-1,0), robot_position[1])
                elif event.key == pygame.K_DOWN:
                    robot_position= (min(robot_position[0]+1,len(map[0])-1), robot_position[1])
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()


def drawGrid(screen, robot_position, robot_font, small_font):

    AMOUNT_OF_BLOCKS = len(map[0])

    rect_border_size = 5

    
    blockSize = int(WINDOW_WIDTH / AMOUNT_OF_BLOCKS) #Set the size of the grid block
    # Draw blocks
    for x in range(0, WINDOW_WIDTH, blockSize):
        for y in range(0, WINDOW_HEIGHT, blockSize):
            rect = pygame.Rect(x, y, blockSize, blockSize)
            pygame.draw.rect(screen, WHITE, rect, 1) # 1: not filled
            
            rect2 = pygame.Rect(x+rect_border_size, y+rect_border_size, blockSize-rect_border_size*2, blockSize-rect_border_size*2)
            pygame.draw.rect(screen, WHITE, rect2, 0) # 0: not filled

    # Draw obstacles
    obstacle_border_size = 20
    seen_obstacles=[]
    all_obstacles=[]
    global_point_map=[[0 for each in range(AMOUNT_OF_BLOCKS)] for each in range(AMOUNT_OF_BLOCKS)]
    point_map=[[0 for each in range(AMOUNT_OF_BLOCKS)] for each in range(AMOUNT_OF_BLOCKS)]

    col=-1    
    for x in range(0, WINDOW_WIDTH, blockSize):
        col+=1
        row=-1
        for y in range(0, WINDOW_HEIGHT, blockSize):     
            row+=1
            if map[row][col]=="XX":       
                rect2 = pygame.Rect(x+obstacle_border_size, y+obstacle_border_size, blockSize-obstacle_border_size*2, blockSize-obstacle_border_size*2)
                pygame.draw.rect(screen, RED, rect2, 0) # 0: not filled
                all_obstacles.append({"col": col, "row": row, "x": x, "y": y})

            # Draw robot
            if robot_position == (row,col):
                
                text_surface = robot_font.render('®', False, RED)
                screen.blit(text_surface, (x+int(blockSize/2)-FONT_SIZE/2 + 10, y+int(blockSize/2)-FONT_SIZE/2- 5 ))

                # |
                pygame.draw.line(screen, GREY, (x+int(blockSize/2), 
                    y+int(blockSize/2-FONT_SIZE/2)), (x+int(blockSize/2), y+int(blockSize/2)-row*blockSize), width=5)

                pygame.draw.line(screen, GREY, (x+int(blockSize/2), 
                    y+int(blockSize/2+FONT_SIZE/2)), (x+int(blockSize/2), y+int(blockSize/2)+(AMOUNT_OF_BLOCKS-row)*0.75*blockSize), width=5)

                # -
                pygame.draw.line(screen, GREY, (x+int(blockSize/2-FONT_SIZE/2), 
                    y+int(blockSize/2)), (x+int(blockSize/2 -row*blockSize ), y+int(blockSize/2)), width=5)

                pygame.draw.line(screen, GREY, (x+int(blockSize/2+FONT_SIZE/2), 
                    y+int(blockSize/2)), (x+int(blockSize/2)+(AMOUNT_OF_BLOCKS-col)*0.75*blockSize, y+int(blockSize/2)), width=5)

            # Calculate "points"
            if math.sqrt( math.pow(row-robot_position[0],2)+math.pow(col-robot_position[1],2)) <2:
                #obstacle_text = small_font.render('11', False, BLACK)
                #screen.blit(obstacle_text, (x + 5, y+5 ))
                if map[row][col]=="XX":
                    seen_obstacles.append({"col": col, "row": row, "x": x, "y": y})

    for each_obstacle in seen_obstacles:
        col=-1
        for x in range(0, WINDOW_WIDTH, blockSize):
            col+=1
            row=-1
            for y in range(0, WINDOW_HEIGHT, blockSize):
                row+=1  
                distance = math.sqrt( math.pow(row-each_obstacle["row"],2)+math.pow(col-each_obstacle["col"],2))  
                #print (col,row,distance)
                points = int(( int(math.pow(2,NUM_BITS)-1) ) / math.pow(2, distance))
                point_map[row][col]=min(int(math.pow(2,NUM_BITS)-1),point_map[row][col]+points)
                #for each in seen_obstacles:

    for each_obstacle in all_obstacles:
        col=-1
        for x in range(0, WINDOW_WIDTH, blockSize):
            col+=1
            row=-1
            for y in range(0, WINDOW_HEIGHT, blockSize):
                row+=1  
                distance = math.sqrt( math.pow(row-each_obstacle["row"],2)+math.pow(col-each_obstacle["col"],2))  
                #print (col,row,distance)
                points = int((  int(math.pow(2,NUM_BITS)-1)   ) / math.pow(2, distance))
                global_point_map[row][col]=min( int(math.pow(2,NUM_BITS)-1) ,global_point_map[row][col]+points)  
                #for each in seen_obstacles:

    # Draw point map
    col=-1    
    for x in range(0, WINDOW_WIDTH, blockSize):
        col+=1
        row=-1
        for y in range(0, WINDOW_HEIGHT, blockSize):     
            row+=1
            if point_map[row][col]>0:       
                obstacle_text = small_font.render("%s" %format_string.format(point_map[row][col])[:NUM_BITS], False, RED)
                screen.blit(obstacle_text, (x + 5, y+5 ))
            if global_point_map[row][col]>0:
                obstacle_text2 = small_font.render("%s" %format_string.format(global_point_map[row][col])[:NUM_BITS], False, BLUE)
                screen.blit(obstacle_text2, (x + blockSize- 20, y+5 ))                


if __name__ == "__main__":
    main()
