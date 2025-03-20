import pygame
import sys
import math
import time
import json


BLACK = (0, 0, 0)
WHITE = (200, 200, 200)
GREY = (100,100,100)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
WINDOW_HEIGHT = 600
WINDOW_WIDTH = 600
FONT_SIZE = 80

DETECTION_DISTANCE = 2

grid_width = input("Grid size. Indicate grid width in cells --> ")
grid_width = int(grid_width)

SEARCH_PATTERN = input("Indicate search pattern --> ")
if SEARCH_PATTERN.replace("1","").replace("0",""):
    print ("Search pattern: only '1' or '0' sequences are allowed.")
    sys.exit(1)

MAP = [["0" for col in range(grid_width)] for row in range(grid_width)]

"""
sample:
map = [
        [ "0", "0"],
        [ "0", "X"]
]
"""

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
                    robot_position= (robot_position[0], min(robot_position[1]+1, len(MAP[0])-1))
                elif event.key == pygame.K_UP:
                    robot_position= (max(robot_position[0]-1,0), robot_position[1])
                elif event.key == pygame.K_DOWN:
                    robot_position= (min(robot_position[0]+1,len(MAP[0])-1), robot_position[1])
                elif event.key == pygame.K_s:                                        
                    save_configuration()
                elif event.key == pygame.K_q:                                        
                    sys.exit(0)
                elif event.key == pygame.K_SPACE:                    
                    if "X" in MAP[robot_position[0]][robot_position[1]]:
                        MAP[robot_position[0]][robot_position[1]]=""
                    else:
                        MAP[robot_position[0]][robot_position[1]]="X"
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()


def drawGrid(screen, robot_position, robot_font, small_font):

    AMOUNT_OF_BLOCKS = len(MAP[0])

    rect_border_size = 5

    
    blockSize = math.ceil(WINDOW_WIDTH / AMOUNT_OF_BLOCKS) #Set the size of the grid block
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
            if "X" in MAP[row][col]:
                rect2 = pygame.Rect(x+obstacle_border_size, y+obstacle_border_size, blockSize-obstacle_border_size*2, blockSize-obstacle_border_size*2)
                pygame.draw.rect(screen, RED, rect2, 0) # 0: not filled
                all_obstacles.append({"col": col, "row": row, "x": x, "y": y})

            # Draw robot
            """
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
            """
            # Calculate "points"
            if math.sqrt( math.pow(row-robot_position[0],2)+math.pow(col-robot_position[1],2)) < DETECTION_DISTANCE:
                #obstacle_text = small_font.render('11', False, BLACK)
                #screen.blit(obstacle_text, (x + 5, y+5 ))
                if "X" in MAP[row][col]:
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
                #global_point_map[row][col]=min( int(math.pow(2,NUM_BITS)-1) ,global_point_map[row][col]+points)  
                global_point_map[row][col]=global_point_map[row][col]+points
                #for each in seen_obstacles:
    
    # Draw point map
    col=-1    
    for x in range(0, WINDOW_WIDTH, blockSize):
        col+=1
        row=-1
        for y in range(0, WINDOW_HEIGHT, blockSize):     
            row+=1
            if point_map[row][col]>0 : 
                obstacle_text = small_font.render("%s" %format_string.format(point_map[row][col])[:NUM_BITS], False, RED)
                screen.blit(obstacle_text, (x + 5, y+5 ))
            if global_point_map[row][col]>0:
                obstacle_text2 = small_font.render("%s" %format_string.format(global_point_map[row][col])[:NUM_BITS], False, BLUE)
                screen.blit(obstacle_text2, (x + blockSize- 20, y+5 ))                


def save_configuration():
    print ("Saving configuration...")
    file_content="""
# ROBOT'S SENSORS (horizontal & vertical)
# A single data is centered in the robot
# From there... if row length is 2, each data is shown with the robot in the middle-->   1 r 2
inp_pattern_row=  <PATTERN>
inp_pattern_col=  <PATTERN>


# THE MAP
''' Example
inp_map_string = [

    ["1 0 0 0 "] ,
    ["1 0 1 0 "] ,
    ["1 1 0 0 "] ,
    ["0 0 0 0 "] ,
]
'''

inp_map_string = [
    <MAP_INFO>
]

CONFIG = {
    "TEST_ORACLE": {
        "enable": False, # Used to validate the Oracle
        "check_pos_row": 0, # Validate the oracle with this value (check if output=1)
        "check_pos_col": 1
    },
    "MAKE_IT_REAL": True, # Sent it to some provider? (if False: simulate locally)
    "AVAILABLE_PROVIDERS": ["IONQ", "IBM", "FAKEIBM", "SIMULATE", "BLUEQUBIT"],
    "SELECTED_PROVIDER": "SIMULATE",
    "USE_JOB_ID": "", # Used to recall results from an external service
    "REUSE_ROW_COL_QUBITS": inp_pattern_row==inp_pattern_col, # If set to True, Row and Col patterns are the same, so Qubits are reused
}    
    """
    with open("../conf.py", "w") as f:
        pattern=[]
        for each in SEARCH_PATTERN:
            pattern.append(each)
        
        map=""
        for each_row in MAP:
            map += '["'
            for each in each_row:
                map +=  "%s " %each
            map += '"],\n'
        file_content = file_content.replace("<PATTERN>", json.dumps(pattern))
        file_content = file_content.replace("<MAP_INFO>", map).replace("X","1")
        f.write(file_content)
        print (file_content)


if __name__ == "__main__":
    main()
