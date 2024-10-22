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
from utils import show_map, create_map_search
from logs import logger
from termcolor import colored

# our Grover libs
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

CONFIG = {
    "TEST_ORACLE": {
        "enable": False, # Used to validate the Oracl"
        "check_row": 0, # Validate the oracle with this values (check if output=1)
        "check_col": 1  # Validate the oracle with this values (check if output=1)
    },
    "MAKE_IT_REAL": False, # Sent it to some provider? (if False: simulate locally)
    "AVAILABLE_PROVIDERS": ["IONIQ", "IBM", "QUANTUMINSPIRE"],
    "SELECTED_PROVIDER": "IBM"
}


# ----------------------------


# THE MAP
inp_map_string = [

    ["0 0 0 0 0 0 "] ,
    ["0 0 0 0 0 0 "] ,
    ["0 0 0 0 0 0 "] ,
    ["0 0 0 1 0 0 "] ,
    ["0 0 1 0 1 0 "] ,
    ["0 0 0 1 0 0 "] ,

]

inp_map_string = [

    ["10 10 10 "] ,
    ["10 10 11 "] ,
    
]


# ROBOT'S SENSORS (horizontal & vertical)
# A single data is centered in the robot
# From there... if row length is 2, each data is shown with the robot in the middle-->   1 r 2 
inp_pattern_row=  ["10",]#, "0"] # row ?
inp_pattern_col=  ["11"] # col ?

#####################

if len(inp_pattern_row)%2==0:
    logger.error("Row pattern length has to be odd (now is even)")
    sys.exit(1)

if len(inp_pattern_col)%2==0:
    logger.error("Column pattern length has to be odd (now is even)")
    sys.exit(1)    


# Some string managing...
inp_map_string_joined = (  ("".join(["".join(each) for each in inp_map_string])).replace(" ","") )
inp_pattern_row_joined = "".join(inp_pattern_row)
inp_pattern_col_joined = "".join(inp_pattern_col)

# Byte size, measured in bits... each of them is considered a "unit"
BYTE_SIZE = len(inp_pattern_row[0]) # 1 / 2 / ... bits ?

TEST_ORACLE = CONFIG["TEST_ORACLE"]["enable"]
MAKE_IT_REAL = CONFIG["MAKE_IT_REAL"]
SEND_TO = CONFIG["SELECTED_PROVIDER"]


# Bytes are only written "in horizontal"
GRID_WIDTH = int(len(inp_map_string[0][0].replace(" ","")) / BYTE_SIZE)
GRID_HEIGHT = int(len(inp_map_string) )

# Join inp_map_string into a single string
inp_map_string="".join(["".join(item) for column in inp_map_string for item in column]).replace(" ","").replace("X","1")


# SHOW MAP & Output other info -------------------------
show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row=None, selected_column=None)


logger.info("Look for pattern in row: %s" %inp_pattern_row)
logger.info("Look for pattern in column: %s" %inp_pattern_col)
logger.info("BYTE SIZE: %s" %BYTE_SIZE)

num_s_bits =  math.ceil(  math.log2(  GRID_WIDTH )    )
logger.info("Num qubits in search space: %squbits (2x %squbits)" %(2*num_s_bits, num_s_bits))


# Create required registers 
search_space=QuantumRegister(num_s_bits + num_s_bits, "s")
map=QuantumRegister(len(inp_map_string_joined), "map")
search_row=QuantumRegister(len(inp_pattern_row_joined), "search_row")
# Let's assume that row and col are equal
#search_col=QuantumRegister(len(inp_pattern_col_joined), "search_col")
search_col=search_row

eq_temporary=QuantumRegister(BYTE_SIZE  , "eq_temporary")
check_temporary=QuantumRegister( (len(search_row) + len(search_col))  , "check_temporary")
ancilla=QuantumRegister(1, "ancilla")
output=QuantumRegister(1, "output")

out_search=ClassicalRegister(len(search_space),"out_search")
output_c=ClassicalRegister(len(output),"output_oracle")

#qc = QuantumCircuit(search_space, map, search_row, search_col, eq_temporary, check_temporary, ancilla, output)
qc = QuantumCircuit(search_space, map, search_row, eq_temporary, check_temporary, ancilla, output)

# -----------
# Used for checking the ORACLE (if oracle testing is enabled)
#SEARCH SPACE:
desired_row=CONFIG["TEST_ORACLE"]["check_row"]
desired_col=CONFIG["TEST_ORACLE"]["check_col"]
format_string = "{:0" + str(int(len(search_space)/2)) + "b}" # /2 because we have here row and col    
formated_searchspace = "%s%s" %(format_string.format(desired_row), format_string.format(desired_col))
print (format_string)
print (formated_searchspace)

set_inputs(qc, inp_map_string_joined, map )

# Oracle testing enabled?
if not TEST_ORACLE:
    initialize_H(qc, search_space)
else:
    set_inputs(qc, formated_searchspace, search_space)

# Set patterns to search for 
set_inputs(qc, inp_pattern_row_joined, search_row)
#set_inputs(qc, inp_pattern_col_joined, search_col)

#checkEqual(qc, [map[0]], [search_row[0]], inp_pattern_row_joined, temporary, ancilla, output)


# Create all possible combinations, and get back what has to be checked
positions = create_map_search(map, search_row, inp_pattern_row, search_col, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT)


logger.info("Number of qubits: %s" %(qc.num_qubits) )
logger.info("Map has %s possible options (N=%s)" %(len(positions), len(positions)))

N=len(positions) # Total options
#M=1
M= 1

logger.info("N: %s, M: %s" %(N, M))

num_repetitions = max(1, math.floor( (math.pi/4)*(math.sqrt(N / M)) ))
logger.info("Num. repetitions (Pi/4*sqrt(N/M)): %s" %num_repetitions)


#for each_pos in positions:
#    print (each_pos)
#    print (" --- ")



# The ORACLE !
def oracle(qc, search_space, positions, eq_temporary, check_temporary, ancilla, output):
    format_string = "{:0" + str(int(len(search_space)/2)) + "b}" # /2 because we have here row and col    
    
    for each_position in positions:
        check_index=-1
        check_list = []
        flipped_s = None
        for each_check in each_position:
            check_index +=1
            row = each_check.row
            col = each_check.col
            map_element = each_check.element
            compare_to_register = each_check.compare_to
            compare_to_register_str = each_check.compare_to_str

            row_in_binary = format_string.format(row)
            col_in_binary = format_string.format(col)
            binary_searchspace="%s%s" %(row_in_binary, col_in_binary)
            
            # Flip search_space
            if flipped_s is None:
                flipped_s=[]
                for k, pos in enumerate(binary_searchspace):                
                    if pos == "0":
                        flipped_s.append(search_space[k])
                        qc.x(search_space[k])            
                    else:
                        pass

            check_list.append({
                "reg1": map_element,
                "reg2": compare_to_register,
                "reg2str": compare_to_register_str
            })

        # ---------
        # Perform search
        checkEqual(qc, check_list, check_temporary, ancilla, output, search_space)
                
        # Restore search_space
        if flipped_s:
            qc.x(flipped_s)


# Should we test the Oracle? Or calculate the circuit?
if not TEST_ORACLE: # CALCULATE
    #for each in range(num_repetitions):
    for each in range(num_repetitions):
        oracle(qc, search_space, positions, eq_temporary, check_temporary, ancilla, output)
        diffusion(qc, search_space, output)    


    add_measurement(qc, search_space, "res1")

    if MAKE_IT_REAL:
        if SEND_TO=="IBM":
            def show_map_info(selected_row, selected_column):
                show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row, selected_column)
            counts=execute_on_IBM(qc, 2800, show_map_info, num_s_bits)
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

else: # TEST THE ORACLE
    logger.info("Looking for: %s" %formated_searchspace)
    oracle(qc, search_space, positions, eq_temporary, check_temporary, ancilla, output)
    add_measurement(qc, output, "res1")
    counts=simulate(qc, num_shots=200)
    # Output should be 1 (if row and col values are correct....)
    print (counts)

