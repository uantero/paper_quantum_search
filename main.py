####
####   USE GROVER TO:
####      Find x,y in a grid
####

## Calculated in IBM
"""
 e

"""
 
 
#initialization
from dotenv import load_dotenv

import matplotlib.pyplot as plt
import sys, os
import datetime
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
from utils import show_map, create_map_search, create_positions
from logs import logger
from termcolor import colored

# our Grover libs
from lib import simulate, checkEqual, initialize_H, XNOR, XOR, toffoli_general, get_qubit_index_list, add_measurement, diffusion, set_inputs

from lib import execute_on_IONQ, execute_on_QuantumInspire, simulate, execute_on_Fake_IBM, execute_on_real_IBM, execute_on_BlueQbit

from ted_qc import *

########################################################


"""
inp_map_string = [
    ["0 0 1 1 0 0"] ,
    ["0 0 0 0 0 0"] ,
    ["1 0 0 1 0 1"] ,    
    ["1 1 0 0 0 0"] ,        
    ["0 0 0 1 0 0"] ,        
 
]

"""

#############################################
##  ----------- GLOBALS --------------------

from conf import *

# ----------------------------


#####################

#if len(inp_pattern_row)%2==0:
#    logger.error("Row pattern length has to be odd (now is even)")
#    sys.exit(1)

#if len(inp_pattern_col)%2==0:
#    logger.error("Column pattern length has to be odd (now is even)")
#    sys.exit(1)    


# Some string managing...
inp_map_string_joined = (  ("".join(["".join(each) for each in inp_map_string])).replace(" ","") )
inp_pattern_row_joined = "".join(inp_pattern_row)
inp_pattern_col_joined = "".join(inp_pattern_col)

# Byte size, measured in bits... each of them is considered a "unit"
BYTE_SIZE = len(inp_pattern_row[0]) # 1 / 2 / ... bits ?

TEST_ORACLE = CONFIG["TEST_ORACLE"]["enable"]
SEND_TO = CONFIG["SELECTED_PROVIDER"]


# Bytes are only written "in horizontal"
GRID_WIDTH = int(len(inp_map_string[0][0].replace(" ","")) / BYTE_SIZE)
GRID_HEIGHT = int(len(inp_map_string) )

# Join inp_map_string into a single string
inp_map_string="".join(["".join(item) for column in inp_map_string for item in column]).replace(" ","").replace("X","1")

logger.info("[[ STARTING MAP SEARCH]] @%s" %datetime.datetime.now())

# SHOW MAP & Output other info -------------------------
show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row=None, selected_column=None)


logger.info("Look for pattern in row: %s" %inp_pattern_row)
logger.info("Look for pattern in column: %s" %inp_pattern_col)
logger.info("BYTE SIZE: %s" %BYTE_SIZE)

search_row=QuantumRegister(len(inp_pattern_row_joined), "search_row")

if not CONFIG["REUSE_ROW_COL_QUBITS"]:
    search_col=QuantumRegister(len(inp_pattern_col_joined), "search_col")    
    check_temporary=QuantumRegister( (len(search_row) + len(search_col))  , "check_temporary")
else:
    search_col=search_row

map=QuantumRegister(len(inp_map_string_joined), "map")

# This is important... this creates the list of all available/allowed positions (and required checks)
positions=create_positions(map, search_row, inp_pattern_row, search_col, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT)
# Find the pos of the requested row & col (for checkint the oracle)
CONFIG["TEST_ORACLE"]["check_pos"]= -1
if TEST_ORACLE:
    for each_position in positions:
        if each_position["row"]==CONFIG["TEST_ORACLE"]["check_pos_row"] and each_position["col"]==CONFIG["TEST_ORACLE"]["check_pos_col"]:
            logger.debug("Looking for pos: %s" %each_position["index"])
            CONFIG["TEST_ORACLE"]["check_pos"]=each_position["index"]

logger.info("Allowed positions: %s" %len(positions))

# Create required registers 
# Search space size is equal to the length of allowed positions
num_s_bits =  math.ceil(  math.log2(  len(positions) )    )
logger.info("Num qubits in search space: %squbits " %(num_s_bits))

search_space=QuantumRegister( num_s_bits , "s")

# Has to store a qubit for each search_row and search_col qubit
check_temporary=QuantumRegister( (len(search_row) + len(search_col))  , "check_temporary")
output=QuantumRegister(1, "output")

# Output qubit
out_search=ClassicalRegister(len(search_space),"out_search")
output_c=ClassicalRegister(len(output),"output_oracle")

#qc = QuantumCircuit(search_space, map, search_row, search_col, eq_temporary, check_temporary, ancilla, output)

if CONFIG["REUSE_ROW_COL_QUBITS"]:
    qc = QuantumCircuit(search_space, output, map, search_row, check_temporary)    
else:
    qc = QuantumCircuit(search_space, output, map, search_row, search_col, check_temporary)

#print (qc.num_qubits)


# -----------
# Used for checking the ORACLE (if oracle testing is enabled)
#SEARCH SPACE:
desired_pos=CONFIG["TEST_ORACLE"]["check_pos"]

format_string = "{:0" + str(int(len(search_space))) + "b}" # /2 because we have here row and col    
formated_searchspace = "%s" %(format_string.format(desired_pos))

set_inputs(qc, inp_map_string_joined, map )

# Oracle testing enabled?
if not TEST_ORACLE:
    initialize_H(qc, search_space)
    qc.x(output)
    
else:
    try:
        set_inputs(qc, formated_searchspace, search_space)
    except:
        logger.error("There's an error with the searchspace")
        sys.exit(1)

# Set patterns to search for 
set_inputs(qc, inp_pattern_row_joined, search_row)

if not CONFIG["REUSE_ROW_COL_QUBITS"]:
    set_inputs(qc, inp_pattern_col_joined, search_col)

checklist = [{
                "reg1": map[0],
                "reg2": search_row[0],
                "reg2str": "1"
            }]

"""
XNOR(qc, map[8], search_row[0], output[0])                        
add_measurement(qc, output, "res1")
counts=simulate(qc, num_shots=600)
print (counts)
sys.exit(0)
"""

#for each_pos in positions:
#    logger.info ("POS %s (%s,%s):" %(each_pos["index"], each_pos["row"],each_pos["col"]))
#    logger.debug (" ---> %s" %each_pos["checks"])

#print (positions)


logger.info("Total number of qubits in circuit: %s" %(qc.num_qubits) )
logger.info("Map has %s possible options (N=%s)" %(len(positions), len(positions)))

#N=len(positions) # Total options
N=len(positions)
#N=math.pow(2,num_s_bits)
M=1

logger.info("N: %s, M: %s" %(N, M))

#num_repetitions = max(1, math.ceil( (math.pi/4)*(math.sqrt(N / M))  ))

#num_repetitions = 1 + max(1, math.ceil( (math.pi/4)*(math.sqrt(N / M))  ))

#num_repetitions =  math.ceil( (math.pi/4)*(math.sqrt(N / M))  )    

#num_repetitions = math.ceil((math.pi/4) * math.sqrt(2 ** (num_s_bits - 1))) 

#num_repetitions = 2+math.ceil(math.pi/(4* math.asin(math.sqrt(1/(N/M)))))

num_repetitions = math.ceil(math.pi/(4* math.asin(math.sqrt(1/(N/M)))))

# Hack for IBM / IONQ....
"""
if MAKE_IT_REAL:
    if SEND_TO in ["IBM"]:
        num_repetitions=1
"""

logger.info("Num. repetitions (Pi/4*sqrt(N/M)): %s" %num_repetitions)


#for each_pos in positions:
#    print (each_pos)
#    print (" --- ")



# The ORACLE !
def oracle(qc, search_space, positions, check_temporary, output):
    format_string = "{:0" + str(int(len(search_space))) + "b}" # /2 because we have here row and col    
    
    for each_position in positions:
        check_index=-1
        check_list = []
        flipped_s = None
        pos_in_binary = format_string.format(each_position["index"])

        #print ("POS IN BINARY: %s" %pos_in_binary)

        for each_check in each_position["checks"]:
            check_index +=1
            row = each_check.row
            col = each_check.col
            map_element = each_check.element
            compare_to_register = each_check.compare_to
            compare_to_register_str = each_check.compare_to_str
            
            binary_searchspace="%s" %(pos_in_binary)
            
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
        checkEqual(qc, check_list, check_temporary, output, search_space)        

        # Repeat for restoring state to check_temporary
        #checkEqual(qc, check_list, check_temporary, None, search_space)        
                
        # Restore search_space
        if flipped_s:
            qc.x(flipped_s)


# Should we test the Oracle? Or calculate the circuit?
backend=None
if not TEST_ORACLE: # CALCULATE
    for each in range(num_repetitions):
        oracle(qc, search_space, positions, check_temporary, output)
        diffusion(qc, search_space, output)    


    add_measurement(qc, search_space, "res1")

    logger.info("CIRCUIT SIZE: %s" %qc.size())
    logger.info("CIRCUIT DEPTH: %s" %qc.depth())
    

    if SEND_TO=="IBM":
        counts, backend=execute_on_real_IBM(qc, 4096)
    elif SEND_TO=="SIMULATE":
        counts, backend=simulate(qc, 800)
    elif SEND_TO=="FAKEIBM":
        counts, backend=execute_on_Fake_IBM(qc, 3000)            
        #counts={'00': 470, '01': 458, '11': 441, '10': 431}
    elif SEND_TO=="IONQ":
        counts, backend=execute_on_IONQ(qc, 800)
    elif SEND_TO=="BLUEQUBIT":
        counts, backend=execute_on_BlueQbit(qc, 800)             

    temp={}
    for key,value in counts.items():
        if int(key[::-1], 2)<len(positions):
            temp[key]=value 
    counts=temp
    # Order and filter elements outside available positions
    counts = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)}
    logger.info("COUNTS: %s" %counts)
    
    for key,value in counts.items():
        logger.debug("%s --> %s" %(  (int(key[::-1], 2), value  )) )
    
    top_item = int(list(counts.keys())[0][::-1], 2)
    

    # Let's find that in our positions...
    selected_row=-1
    selected_col=-1
    print ("POSITIONS:")
    for each_pos in positions:        
        print ("   · %s ROW: %s COL: %s" %(each_pos, each_pos["row"], each_pos["col"]))
        if str(each_pos["index"])==str(top_item):
            selected_row=each_pos["row"]
            selected_col=each_pos["col"]

    logger.info ("Selected ROW: %s" %selected_row)
    logger.info ("Selected COL: %s" %selected_col)

    show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row, selected_col)
    
    #qc.draw("mpl")
    plot_histogram(counts)
    plt.show()

else: # TEST THE ORACLE
    logger.info("Looking for: %s" %formated_searchspace)
    oracle(qc, search_space, positions, check_temporary, output)
    add_measurement(qc, output, "res1")
    counts=simulate(qc, num_shots=200)
    # Output should be 1 (if row and col values are correct....)
    logger.info (counts)



## COMPUTE ERRORS!
# Computing probability error
if backend:
    errors = []
    circuits = []
    layoutbackend = []

    transpiled_qc = transpile(qc, backend=backend, optimization_level=3)
    circuits.append(transpiled_qc)
    errors.append(ibm_circuit_error(transpiled_qc, backend=backend))
    layoutbackend.append(backend)
    """
    try:
        transpiled_qc = transpile(qc, backend=backend, optimization_level=3)
        circuits.append(transpiled_qc)
        errors.append(ibm_circuit_error(transpiled_qc, backend=backend))
        layoutbackend.append(backend)
    except Exception as e:
        print (e)
        print('{}: This backend has no layout\n'.format(backend))
    """

    for i, error in enumerate(errors):
        print(' ')
        print('Backend: {}'.format(layoutbackend[i]))
        print('  total_error = {}, physical qubits = {} '.format(error.total, error.qubit_list))
        if "cnot " in error.__dict__:
            print('  CX_error = {} '.format(error.cnot))
        print('  SGATE_error = {}'.format(error.sgate))
        print('  TIME_error = {} '.format(error.time))
        print('  MEASUREMENT_error = {}'.format(error.measurement))

