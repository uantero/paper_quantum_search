####
####   USE GROVER TO:
####      Find x,y in a grid
####

## Calculated in IBM
"""

        0 1 2 3 4 5
    0 ['0 0 1 1 0 0']
    1 ['1 0 0 0 0 0']
    2 ['0 0 0 0 0 0']
    3 ['1 0 0 1 0 1']
    4 ['1 1 0 0 0 0']
    5 ['0 0 0 1 0 0']

   Job: cwb9b3wjyrs0008wyzt0
   21/10/2024:

    ROWS: {'0100': 188, '1100': 188, '1001': 186, '0101': 184, '1000': 179, '1110': 179, '0001': 179, '0010': 178, '0111': 176, '0110': 175, '1101': 174, '0011': 170, '0000': 168, '1111': 167, '1011': 157, '1010': 152}
    COLS: {'11': 804, '10': 747, '01': 646, '00': 603}

   Result: 
     · ROW: 3
     · COL: 3


"""
 
 
#initialization
from dotenv import load_dotenv

import matplotlib.pyplot as plt
import sys, os
import numpy as np
import math
import re
from textwrap import wrap

# You should have a correct .env file in the same directory as this file
# Put your tokens there...
load_dotenv()  # take environment variables from .env.

# importing Qiskit
from qiskit import transpile, transpile
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate
 
# import basic plot tools
from qiskit.visualization import plot_histogram

# Import our libraries...
from logs import logger
from termcolor import colored

# our Grover libs
from oracles import create_column_oracle, create_row_oracle
from lib import simulate, checkEqual, initialize_H, XNOR, XOR, toffoli_general, get_qubit_index_list, add_measurement, diffusion, set_inputs
from lib import execute_on_IONQ, execute_on_IBM, execute_on_QuantumInspire


########################################################


"""
inp_map_string = [
    ["0 0 1 1 0 0"] ,
    ["1 0 0 0 0 0"] ,
    ["0 0 0 0 0 0"] ,
    ["1 0 0 1 0 1"] ,    
    ["1 1 0 0 0 0"] ,        
    ["0 0 0 1 0 0"] ,        
 
]

"""

#############################################
##  ----------- GLOBALS --------------------
# THE MAP
inp_map_string = [
    ["0 0 1 0 "] ,
    ["0 1 0 1 "] ,
    ["0 0 1 0 "] ,
    ["0 0 1 0 "] ,
]

for each in inp_map_string:
    print (each)
print (" ")


# ROBOT'S SENSORS (horizontal & vertical)
# A single data is centered in the robot
# From there... if row length is 2, each data is shown with the robot in the middle-->   1 r 2 
inp_pattern_row=  ["1", "1"]#, "0"] # row ?
inp_pattern_col=  ["1"] # col ?

inp_map_string_joined = (  ("".join(["".join(each) for each in inp_map_string])).replace(" ","") )
inp_pattern_row_joined = "".join(inp_pattern_row)
inp_pattern_col_joined = "".join(inp_pattern_col)

# Byte size, measured in bits... each of them is considered a "unit"
BYTE_SIZE = len(inp_pattern_row[0]) # 1 / 2 / ... bits ?

# Send it to an external provider?
MAKE_IT_REAL = False

# Which external provider?
# OPTIONS: IONQ, IBM, QUANTUMINSPIRE

#SEND_TO = "IONQ"
SEND_TO = "IBM"
#SEND_TO = "QUANTUMINSPIRE"

# ----------------------------
# Are we validating the oracle? Used to validate the Oracle
TEST_ORACLE = False

# Bytes are only written "in horizontal"
GRID_WIDTH = int(len(inp_map_string[0][0].replace(" ","")) / BYTE_SIZE)
GRID_HEIGHT = int(len(inp_map_string) )

# Join inp_map_string into a single string
inp_map_string="".join(["".join(item) for column in inp_map_string for item in column]).replace(" ","").replace("X","1")


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


## This create a list of positions
##  inp_map_string: can be anything (string or quantum register) that could be used as a map
##  inp_pattern_row: string or quantum register that defines the substring to be found in the row
##  row_elements: STRING of the substring to be found in the row (as it is used to check .cx etc...)
##  ....
def create_map_search(inp_map_string, inp_pattern_row, row_elements, inp_pattern_col, col_elements, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT):
    from textwrap import wrap
    import numpy as np
    
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
            return " (%s|%s[%s|%s]<%s|%s>) " %(self.row, self.col, self.type, self.element, self.compare_to, self.compare_to_str)
    
    for each_row_index in range( math.floor(len(row_elements)/2),  len(rows) -  len(row_elements) +1 ):    
        #print ("ROW! %s" %each_row_index)
        if each_row_index>=len(rows):
            continue
        this_row=rows[each_row_index]                
        for each_column_index in range( math.floor(len(col_elements)/2),  len(columns) -  math.floor(len(col_elements))+1):    
            #print ("COL! %s" %each_column_index)
            temp_positions=[]            
            start_col_positions = [each for each in range(-math.floor(len(row_elements)/2), math.floor(len(row_elements)/2))]            
            for each_row_bit in range(len(row_elements)):
                if each_column_index+each_row_bit+start_col_positions[each_row_bit]>=len(rows[each_row_index]):
                    continue

                
                element=Element(
                        each_row_index, 
                        each_column_index, 
                        rows[each_row_index][each_column_index+each_row_bit+start_col_positions[each_row_bit]],
                        "row",
                        inp_pattern_row[each_row_bit],
                        row_elements[each_row_bit]
                        )
                #print("Row: %s, Col: %s --> %s" %(each_row_index, each_column_index, row_elements[each_row_bit]))
                temp_positions.append(element)

            start_row_positions = [each for each in range(-math.floor(len(col_elements)/2), math.floor(len(col_elements)/2))]            
            if len(inp_pattern_col)>1:
                for each_col_bit in range(len(col_elements)):
                    if each_row_index+each_col_bit+start_row_positions[each_col_bit]>=len(rows):
                        continue

                    #print (".....")
                    #print (each_row_index)
                    #print (each_col_bit)
                    #print (start_row_positions[each_col_bit])

                    #print("*Row: %s, Col: %s" %(each_row_index, each_column_index))
                    if each_row_index+each_col_bit>=len(rows):
                        continue
                    element=Element(
                                each_row_index, 
                                each_column_index, 
                                rows[each_row_index+each_col_bit+start_row_positions[each_col_bit]][each_column_index],
                                "col",
                                inp_pattern_col[each_col_bit],
                                col_elements[each_col_bit]
                            )
                    temp_positions.append(element)
            positions.append(temp_positions)
                #print (this_row[each_column_index])
        
    
    return positions



num_s_bits =  math.ceil(  math.log2(  GRID_WIDTH )    )
logger.info("Num qubits in search space: %squbits (2x %squbits)" %(2*num_s_bits, num_s_bits))

# Create required registers 
print (inp_map_string_joined)
search_space=QuantumRegister(num_s_bits + num_s_bits, "s")
map=QuantumRegister(len(inp_map_string_joined), "map")
search_row=QuantumRegister(len(inp_pattern_row_joined), "search_row")
search_col=QuantumRegister(len(inp_pattern_col_joined), "search_col")
temporary=QuantumRegister(len(search_row) + len(search_col), "temporary")
ancilla=QuantumRegister(1, "ancilla")
output=QuantumRegister(1, "output")
out_search=ClassicalRegister(len(search_space),"out_search")
output_c=ClassicalRegister(len(output),"output_oracle")

qc = QuantumCircuit(search_space, map, search_row, search_col, temporary, ancilla, output)

print ("JOINED MAP: %s" %inp_map_string_joined)
print ("JOINED inp_pattern_row_joined: %s" %inp_pattern_row_joined)

#SEARCH SPACE:
desired_row=1
desired_col=1
format_string = "{:0" + str(int(len(search_space)/2)) + "b}" # /2 because we have here row and col    
formated_searchspace = "%s%s" %(format_string.format(desired_row), format_string.format(desired_col))
print ("desired search_space: %s" %formated_searchspace)
print ("MAP: %s" %inp_map_string_joined)

set_inputs(qc, inp_map_string_joined, map )
if not TEST_ORACLE:
    initialize_H(qc, search_space)
else:
    set_inputs(qc, formated_searchspace, search_space)
set_inputs(qc, inp_pattern_row_joined, search_row)
set_inputs(qc, inp_pattern_col_joined, search_col)

#checkEqual(qc, [map[0]], [search_row[0]], inp_pattern_row_joined, temporary, ancilla, output)

print (len(inp_pattern_row))
positions = create_map_search(map, search_row, inp_pattern_row, search_col, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT)
N = len(positions)

logger.info("Number of qubits: %s" %(qc.num_qubits) )

logger.info("Map has %s possible options (N=%s)" %(len(positions), len(positions)))

print (positions)
#checkEqual(qc, [map[3]], [search_row[0]], "1", temporary, ancilla, output, search_space)

def oracle(qc, search_space, positions, temporary, ancilla, output):
    format_string = "{:0" + str(int(len(search_space)/2)) + "b}" # /2 because we have here row and col    

    for each_position in positions:
        for each_check in each_position:
            row = each_check.row
            col = each_check.col
            map_element = each_check.element
            compare_to_register = each_check.compare_to
            compare_to_register_str = each_check.compare_to_str

            row_in_binary = format_string.format(row)
            col_in_binary = format_string.format(col)
            binary_searchspace="%s%s" %(row_in_binary, col_in_binary)
            
            # Flip search_space
            flipped_s = []
            for k, pos in enumerate(binary_searchspace):
                if pos == "0":
                    flipped_s.append(search_space[k])
                    qc.x(search_space[k])            
                else:
                    pass

            checkEqual(qc, map_element, compare_to_register, compare_to_register_str, temporary, ancilla, output, search_space)
            
            if len(flipped_s):
                qc.x(flipped_s)


logger.info("Looking at: (%s)" %search_space)
logger.info("Looking for (row): (%s)" %inp_pattern_row)
logger.info("Looking for (col): (%s)" %inp_pattern_col)


if not TEST_ORACLE:
    N=len(positions)
    M=2

    num_repetitions = max(1,math.floor( (math.pi/4)*(math.sqrt(N / M)) ))
    logger.info("Num. repetitions: %s" %num_repetitions)

    #for each in range(num_repetitions):
    for each in range(num_repetitions):
        oracle(qc, search_space, positions, temporary, ancilla, output)
        diffusion(qc, search_space, output)    


    add_measurement(qc, search_space, "res1")

    if MAKE_IT_REAL:
        if SEND_TO=="IBM":
            counts=execute_on_IBM(qc, 2800)
    else:
        counts=simulate(qc, num_shots=600)
    row={}
    col={}
    for each in counts:
        col_value=each[:2]
        row_value=each[2:]
        if row_value not in row:
            row[row_value]=0
        if col_value not in col:
            col[col_value]=0
        row[row_value]+=counts[each]
        col[col_value]+=counts[each]


    print ("ROWS: %s" %{k: v for k, v in sorted(row.items(), key=lambda item: item[1], reverse=True)})
    print ("COLS: %s" %{k: v for k, v in sorted(col.items(), key=lambda item: item[1], reverse=True)})

    selected_row=list({k: v for k, v in sorted(row.items(), key=lambda item: item[1], reverse=True)}.keys())[0]
    selected_row=str(selected_row)[::-1]
    selected_row = int(selected_row,2)
    selected_col=list({k: v for k, v in sorted(col.items(), key=lambda item: item[1], reverse=True)})[0]
    selected_col=str(selected_col)[::-1]
    selected_col = int(selected_col,2)

    print ("Selected ROW: %s" %selected_row)
    print ("Selected COL: %s" %selected_col)

else:
    oracle(qc, search_space, positions, temporary, ancilla, output)
    add_measurement(qc, output, "res1")
    counts=simulate(qc, num_shots=200)
    print (counts)

