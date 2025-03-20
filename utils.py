import re
import math
from termcolor import colored

## ---------------------------------------------
## Show map
def show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row=None, selected_column=None):
    from textwrap import wrap
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    BLANK = "".join([" " for each in range(BYTE_SIZE)])
    LINE = "-"

    # Upper header
    # list of items
    column_items=""
    for index, each in enumerate(range(GRID_WIDTH)):
        if index==selected_column:
            column_items = column_items + colored(str(each), "red", attrs=['bold'])+BLANK
        else:
            column_items = column_items + str(each)+BLANK
    
    # Remove color codes for counting the width
    table_width =  len(ansi_escape.sub('', column_items))
    # Draw list and horizontal lines
    print ("")
    print ("          %s" %column_items )
    print ("         %s" %"".join([LINE for each in range(table_width+2)]))
    index=-1
    for each_map_line in wrap(inp_map_string, GRID_WIDTH*BYTE_SIZE ):
        line_items = wrap(each_map_line, BYTE_SIZE)

        index+=1
        if index==selected_row:
            print (  colored("       %s| %s  | " %(index, " ".join(line_items)) , 'red', attrs=['bold'] ) )
        else:
            line=""
            col_index=-1
            for each_column_item in line_items:                
                col_index+=1
                if col_index==selected_column:
                    line = line + colored(each_column_item, "red", attrs=['bold']) + " "
                else:
                    line = line + each_column_item + " "

            print ("       %s| %s | " %(index, line))
    print ("         %s" %"".join([LINE for each in range(table_width+2)]))    




# Create all possible combinations, and get back what has to be checked

def create_positions(map, search_row, inp_pattern_row, search_col, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT):
    positions = []
    class Element:
        def __init__(self, row, col, element, type, compare_to, compare_to_str):
            self.row=row
            self.col=col
            self.element=element
            self.type=type
            self.compare_to=compare_to
            self.compare_to_str=compare_to_str
        def __repr__(self):
            MAP_ITEMS=["%s%s" %(item._register.name, item._index) for item in self.element]
            COMPARE_ITEMS=["%s%s" %(item._register.name, item._index) for item in self.compare_to]
            return " (r:%s|c:%s[t:%s|%s]<%s|%s>) " %(self.row, self.col, self.type, MAP_ITEMS, COMPARE_ITEMS, self.compare_to_str)

    index=-1
    for base_row_index in range(GRID_HEIGHT-len(inp_pattern_col)+1):
        for base_col_index in range(GRID_WIDTH-len(inp_pattern_row)+1):        
            index+=1
            # Center the search pattern
            center_row_index = base_row_index+math.floor( len(inp_pattern_col)/2 )
            center_col_index = base_col_index+math.floor( len(inp_pattern_row)/2 )

            #print ("ROW: %s, COL: %s" %(center_row_index, center_col_index))
            position={ 
                    "index": index, 
                    "row":  center_row_index , 
                    "col": center_col_index
                }            
            checks=[]
            
            for row_index, each_row_item in enumerate(inp_pattern_row):
                row = center_row_index-math.floor( len(inp_pattern_col)/2 )+row_index
                #print ("    row: %s, col: %s" %(row, center_col_index))
                map_index=row*GRID_WIDTH + center_col_index
                check_element=Element(
                        row=center_row_index, 
                        col=center_col_index, 
                        element=[map[map_index]],
                        type="col",
                        compare_to=[search_col[row_index]],
                        compare_to_str=inp_pattern_col[row_index]
                        )                
                checks.append(check_element)
            
            # If inp_patter_col is just a single qubit, it should be equal to inp_pattern_row
            if len(inp_pattern_col)>1:
                for col_index, each_col_item in enumerate(inp_pattern_col):
                    col = center_col_index-math.floor( len(inp_pattern_row)/2 )+col_index
                    map_index=center_row_index*GRID_WIDTH + col
                    #print ("    row: %s, col: %s" %(center_row_index, col))
                    check_element=Element(
                            row=center_row_index, 
                            col=center_col_index, 
                            element=[map[map_index]],
                            type="row",
                            compare_to=[search_row[col_index]],
                            compare_to_str=inp_pattern_row[col_index]
                            )                
                    checks.append(check_element)
            
            position["checks"]=checks
            positions.append(position)


    return positions
                



## Create search map


## This create a list of positions
##  inp_map_string: can be anything (string or quantum register) that could be used as a map
##  inp_pattern_row: string or quantum register that defines the substring to be found in the row
##  row_elements: STRING of the substring to be found in the row (as it is used to check .cx etc...)
##  ....
def create_map_search(inp_map_string, inp_pattern_row, row_elements, inp_pattern_col, col_elements, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT):
    from textwrap import wrap
    import numpy as np
    

    # Ok! Let's look in columns...
    # Consider bytes...
    def split_in_columns(what, width):
        columns={}
        for each_column_index in range(width):
            columns[each_column_index]=[]
        column_index=-1
        for each in [what[i:i+BYTE_SIZE] for i in range(0, len(what), BYTE_SIZE)]:
            column_index=column_index+1
            columns[column_index].append(each)        
            if column_index+1>=width:
                column_index=-1
        return list(columns.values())

    def split_in_rows(what, width):
        rows=[]
        each_row=[]
        for each in [what[i:i+BYTE_SIZE] for i in range(0, len(what), BYTE_SIZE)]:
            each_row.append(each)
            if len(each_row)>=width:
                rows.append(each_row)
                each_row=[]
        return rows   

    
    positions=[]
    
    rows = split_in_rows(inp_map_string, GRID_WIDTH)
    columns = split_in_columns(inp_map_string, GRID_WIDTH)

    inp_pattern_row = [inp_pattern_row[i:i + BYTE_SIZE] for i in range(0, len(inp_pattern_row), BYTE_SIZE)] 
    inp_pattern_col = [inp_pattern_col[i:i + BYTE_SIZE] for i in range(0, len(inp_pattern_col), BYTE_SIZE)] 
    #print (inp_pattern_row)


    #print ("ROWS: %s" %rows)
    #print ("COLUMNS: %s" %columns)

    class Element:
        def __init__(self, row, col, element, type, compare_to, compare_to_str):
            self.row=row
            self.col=col
            self.element=element
            self.type=type
            self.compare_to=compare_to
            self.compare_to_str=compare_to_str
        def __repr__(self):
            MAP_ITEMS=["%s%s" %(item._register.name, item._index) for item in self.element]
            COMPARE_ITEMS=["%s%s" %(item._register.name, item._index) for item in self.compare_to]
            return " (%s|%s[%s|%s]<%s|%s>) " %(self.row, self.col, self.type, MAP_ITEMS, COMPARE_ITEMS, self.compare_to_str)
    
    for each_row_index in range( math.floor(len(row_elements)/2),  len(rows) -  math.floor(len(row_elements)/2-0.5)  ):    
        print ("ROW! %s" %each_row_index)
        if each_row_index!=1:
            continue

        this_row=rows[each_row_index]                
        for each_column_index in range( math.floor(len(col_elements)/2),  len(columns) - math.floor(len(col_elements)/2-0.5)  ):    
            print ("COL! %s" %each_column_index)            

            temp_positions=[]            
            start_col_positions = [each for each in range(-math.floor(len(row_elements)/2), math.ceil(len(row_elements)/2)) ]
            #print (start_col_positions)
            if each_column_index!=1:
                continue
            
            for each_row_bit in range(len(row_elements)):
                col_position = start_col_positions.pop(0)               
                element=Element(
                        each_row_index, 
                        each_column_index, 
                        rows[each_row_index][each_column_index+col_position],
                        "row",
                        inp_pattern_row[each_row_bit],
                        row_elements[each_row_bit]
                        )
                #print("Row: %s, Col: %s --> %s" %(each_row_index, each_column_index, row_elements[each_row_bit]))
                temp_positions.append(element)

            start_row_positions = [each for each in range(-math.floor(len(col_elements)/2), math.ceil(len(col_elements)/2)) ]
            if len(inp_pattern_col)>1:
                for each_col_bit in range(len(col_elements)):
                    row_positions=start_row_positions.pop(0)

                    #print (".....")
                    #print (each_row_index)
                    #print (each_col_bit)
                    #print (start_row_positions[each_col_bit])

                    #print("*Row: %s, Col: %s" %(each_row_index, each_column_index))
                    element=Element(
                                each_row_index, 
                                each_column_index, 
                                rows[each_row_index+row_positions][each_column_index],
                                "col",
                                inp_pattern_col[each_col_bit],
                                col_elements[each_col_bit]
                            )
                    temp_positions.append(element)
            positions.append(temp_positions)
                #print (this_row[each_column_index])
        
    
    return positions
