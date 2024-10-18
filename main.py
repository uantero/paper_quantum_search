####
####   USE GROVER TO:
####      Find x,y in a grid
####
 
"""
  RESULTADOS IBM (18-oct-2024):
  -----------------
      MAP:
        ========
        1010
        0000
        0110 
        0000

        Looking in rows for: 11 
        Looking in cols for: 10
        Number of qubits in search space: 4 (2x 2)
        =================================
        Estimated Grover repetitions: 3
        SENDING TO REAL IBM COMPUTER
        Sending real JOB to IBM
        job id: cw902hj2802g0081k5sg
        PrimitiveResult([SamplerPubResult(data=DataBin(cbit_row_result=BitArray(<shape=(), num_shots=5500, num_bits=2>), cbit_column_result=BitArray(<shape=(), num_shots=5500, num_bits=2>)), metadata={'circuit_metadata': {}})], metadata={'execution': {'execution_spans': ExecutionSpans([SliceSpan(<start='2024-10-18 06:33:50', stop='2024-10-18 06:34:26', size=5500>)])}, 'version': 2})
        COLUMN:
        {'11': 1363, '10': 1355, '00': 1372, '01': 1410}
        COLUMN Results
        b'01' [Columna: 2] --> 1410
        b'00' [Columna: 0] --> 1372
        b'11' [Columna: 3] --> 1363
        b'10' [Columna: 1] --> 1355
        ROW:
        {'11': 1834, '01': 1874, '00': 906, '10': 886}
        ROW Results
        b'01' [Fila: 2] --> 1874
        b'11' [Fila: 3] --> 1834
        b'00' [Fila: 0] --> 906
        b'10' [Fila: 1] --> 886
        . . . . . . . . . . . . 
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
from logs import logger
from termcolor import colored

# our Grover libs
from oracles import create_column_oracle, create_row_oracle
from lib import initialize_H, XNOR, XOR, toffoli_general, get_qubit_index_list, add_measurement, diffusion, set_inputs
from lib import execute_on_IONQ, execute_on_IBM, execute_on_QuantumInspire


########################################################


"""
inp_map_string = [
    ["0 0 0 0 0 0 0 0"] ,
    ["0 0 X 0 0 0 0 0"] ,
    ["0 0 0 0 0 0 0 0"] ,
    ["0 0 0 0 0 0 0 0"] ,
    ["0 0 0 X 0 0 0 0"] ,
    ["0 0 X 0 X 0 0 0"] ,
    ["0 0 0 X 0 0 0 0"] ,
    ["0 0 0 0 0 0 0 0"]     
]
"""

#############################################
##  ----------- GLOBALS --------------------
# THE MAP
inp_map_string = [
    ["0 0 0 "] ,
    ["0 1 0 "] ,
    ["0 0 0 "] ,
]


# ROBOT'S SENSORS (horizontal & vertical)
inp_pattern_row=  "01" # row ?
inp_pattern_col=  "01" # col ?

# Send it to an external provider?
MAKE_IT_REAL = False

# Which external provider?
#SEND_TO = "IONQ"
#SEND_TO = "IBM"
SEND_TO = "QUANTUMINSPIRE"

# ----------------------------
# Are we validating the oracle? Used to validate the Oracle
TEST_ORACLE = False

# Byte size, measured in bits... each of them is considered a "unit"
# Bytes are only written "in horizontal"
BYTE_SIZE = 1 # 2 bits
GRID_WIDTH = int(len(inp_map_string[0][0].replace(" ","")) / BYTE_SIZE)
GRID_HEIGHT = int(len(inp_map_string) )

# Join inp_map_string into a single string
inp_map_string="".join(["".join(item) for column in inp_map_string for item in column]).replace(" ","").replace("X","1")

##  ----------- /GLOBALS --------------------
#############################################


## ---------------------------------------------
## Show map
def show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE, selected_row=None, selected_column=None):
    print ("")
    print ("          %s" %" ".join([str(each) for each in range(GRID_WIDTH)]))
    print ("         %s" %"--".join(["" for each in range(GRID_WIDTH+1)]))
    index=-1
    for each_map_line in wrap(inp_map_string, GRID_WIDTH*BYTE_SIZE ):
        index+=1
        if index==selected_row:
            print (  colored("       %s| %s  | " %(index, " ".join(each_map_line)) , 'red', attrs=['bold'] ) )
        else:
            line=""
            col_index=-1
            for each_column_item in each_map_line:
                col_index+=1
                if col_index==selected_column:
                    line = line + colored(each_column_item, "red", attrs=['bold']) + " "
                else:
                    line = line + each_column_item + " "

            print ("       %s| %s | " %(index, line))
    print ("         %s" %"--".join(["" for each in range(GRID_WIDTH+1)]))

## ---------------------------------------------
## Initialize the circuit and set some registers
def init_circuit():
    logger.info ("STARTING FOR:")
    logger.info ("MAP:")
    logger.debug ("========> MAP ")

    show_map(inp_map_string, GRID_WIDTH, BYTE_SIZE)

    logger.debug ("<======== MAP ")
    logger.info ("Looking in rows for: | %s |" %" ".join(inp_pattern_row))
    logger.info ("Looking in cols for: | %s |" %" ".join(inp_pattern_col))
    
    # Output is (x,y)... we assume that GRID_WIDTH = GRID_HEIGHT
    num_s_bits =  math.ceil(  math.log2(  GRID_WIDTH )    )
    logger.info ("Number of qubits in search space: | %s | (2x %i)" %(num_s_bits * 2, num_s_bits ))
    
    # Create required registers 
    row_searchspace=QuantumRegister(num_s_bits, "cs")
    column_searchspace=QuantumRegister(num_s_bits, "rs")
    map_string=QuantumRegister(len(inp_map_string), "map_string")
    row_substring=QuantumRegister(len(inp_pattern_row), "row_substring")
    column_substring=QuantumRegister(len(inp_pattern_col), "column_substring")
    temporary=QuantumRegister(  len(row_substring) , "temporary")
    
    oracle_row_output=QuantumRegister(1, "row_output")
    oracle_column_output=QuantumRegister(1, "column_output")
    ancillary=QuantumRegister(1, "ancillary") # Used to mark that the substring was already found

    cbit_row_result = ClassicalRegister(len(row_searchspace), "cbit_row_result")
    cbit_column_result = ClassicalRegister(len(column_searchspace), "cbit_column_result")


    # Creating circuit
    qc = QuantumCircuit(row_searchspace, column_searchspace, map_string, row_substring, column_substring, temporary, oracle_row_output, oracle_column_output, ancillary, cbit_row_result, cbit_column_result)

    return {
        "qc": qc,
        "searchspace":{
            "row_searchspace": row_searchspace,
            "column_searchspace": column_searchspace
        },
        "inputs": {
            "map_string": map_string,
            "row_substring": row_substring,
            "column_substring": column_substring
        },
        "outputs": {
            "oracle_row_output": oracle_row_output,
            "oracle_column_output": oracle_column_output
        },
        "temporary": {
            "temporary": temporary,
            "ancillary": ancillary
        },
        "result": {
            "cbit_row_result": cbit_row_result,
            "cbit_column_result": cbit_column_result
        }        
    }


## ---------------------------------------------
## Main function
def main(inp_map_string, inp_pattern_row, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT):    

    results = init_circuit()

    qc = results["qc"]
    row_searchspace = results["searchspace"]["row_searchspace"]
    column_searchspace = results["searchspace"]["column_searchspace"]
    map_string = results["inputs"]["map_string"]
    row_substring = results["inputs"]["row_substring"]
    column_substring = results["inputs"]["column_substring"]
    oracle_row_output = results["outputs"]["oracle_row_output"]
    oracle_column_output = results["outputs"]["oracle_column_output"]
    temporary = results["temporary"]["temporary"]
    ancillary = results["temporary"]["ancillary"]
    cbit_row_result = results["result"]["cbit_row_result"]
    cbit_column_result = results["result"]["cbit_column_result"]


    # ------------------------
    # Used to validate the Oracle        
    # If set, it is used here to validate that the oracle works as expected
    if TEST_ORACLE: # Just to develop/debug the oracle...
        # In which row or column should we look?
        LOOK_IN_ROW = 0
        LOOK_IN_COLUMN = 0
        look_for = ["row", "column"]

        num_s_bits =  math.ceil(  math.log2(  GRID_WIDTH )    )
        format_string = "{:0"+str(num_s_bits)+"b}"
        logger.debug ("Looking in row position: %s [binary %s]" %(LOOK_IN_ROW, format_string.format(LOOK_IN_ROW)))
        logger.debug ("Looking in col position: %s [binary %s]" %(LOOK_IN_COLUMN, format_string.format(LOOK_IN_COLUMN)))

        set_inputs(qc, format_string.format(LOOK_IN_ROW), row_searchspace)
        set_inputs(qc, format_string.format(LOOK_IN_COLUMN), column_searchspace)    
        set_inputs(qc, inp_map_string, map_string)
        set_inputs(qc, inp_pattern_row, row_substring)
        set_inputs(qc, inp_pattern_col, column_substring)    

        check = "column" # "column"

        if "row" in look_for:
            # ROW
            qc.compose(create_row_oracle(qc, row_searchspace, map_string, row_substring, temporary, oracle_row_output, ancillary, BYTE_SIZE, GRID_WIDTH))
            # Measure oracle output for validation
            add_measurement(qc, oracle_row_output, "row")
            #qc.measure(oracle_row_output, cbit_row_result)
        
        if "column" in look_for:
            # COL
            qc.compose(create_column_oracle(qc, column_searchspace, map_string, column_substring, temporary, oracle_column_output, ancillary, BYTE_SIZE, GRID_WIDTH))
            # Measure oracle output for validation    
            add_measurement(qc, oracle_column_output, "vertical")
            #qc.measure(column_searchspace, list(range(num_s_bits)))
            pass

        num_shots = 100
        from qiskit.providers.basic_provider import BasicProvider as BasicAerProvider
        provider = BasicAerProvider()    
        backend = provider.get_backend()
        result = backend.run(transpile(qc, backend), shots=num_shots).result()
        counts = result.get_counts()

        logger.info (counts)

        # Exit
        sys.exit(0)

    
    # -----------------------------------------------
    # "REAL" grover search 
    # We use the grover oracle + diffussion
    else:
        initialize_H(qc, row_searchspace)
        initialize_H(qc, column_searchspace)
        set_inputs(qc, inp_map_string, map_string)
        set_inputs(qc, inp_pattern_col, row_substring)
        set_inputs(qc, inp_pattern_row, column_substring)    
            
        #N = 2 * (len(inp_map_string) )/ ((len(inp_pattern_row) + len(inp_pattern_col))/BYTE_SIZE ) # Horiz & vertical
        
        N = len(inp_map_string) / BYTE_SIZE
            
        num_repetitions = math.floor( (math.pi/4)*(math.sqrt(N)) )           
                
    
        logger.info ("Estimated Grover repetitions: %s" %num_repetitions)        
        
        look_for = ["row", "column"]

        # Repeat! -------------------------------------        
        for repetition in range(num_repetitions):
            # oracle + diffusion for rows
            if "row" in look_for:
                qc.compose(create_row_oracle(qc, row_searchspace, map_string, row_substring, temporary, oracle_row_output, ancillary, BYTE_SIZE, GRID_WIDTH))
                diffusion(qc, row_searchspace, oracle_row_output)
            
            # oracle + diffusion for columns
            if "column" in look_for:
                qc.compose(create_column_oracle(qc, column_searchspace, map_string, column_substring, temporary, oracle_column_output, ancillary, BYTE_SIZE, GRID_WIDTH))
                diffusion(qc, column_searchspace, oracle_column_output)    
        
        # Measure
        if "column" in look_for:
            qc.measure(column_searchspace, cbit_column_result)

        if "row" in look_for:
            qc.measure(row_searchspace, cbit_row_result)
        
    
        # --- Send it to external provider ------
        # -- real ---
        make_it_real = MAKE_IT_REAL    
        if make_it_real:
            if SEND_TO=="IONQ":
                logger.info ("SENDING TO IONQ")
                counts = execute_on_IONQ(qc, 500)
            elif SEND_TO=="QUANTUMINSPIRE":
                logger.info ("SENDING TO QUANTUM INSPIRE")
                counts = execute_on_QuantumInspire(qc, 500)                
            else:
                logger.info ("SENDING TO REAL IBM COMPUTER")
                counts = execute_on_IBM(qc, 3500)

        # --- simulated locally ---    
        else:
            logger.info ("SIMULATING LOCALLY")
            num_shots=300
            #from qiskit.providers.basic_provider import BasicProvider as BasicAerProvider
            #provider = BasicAerProvider()    
            #backend = provider.get_backend()
            backend = Aer.get_backend('qasm_simulator')
            tqc = transpile(
                qc, optimization_level=2
            )
            result = backend.run(tqc, shots=num_shots).result()
            counts = result.get_counts()

        #execute_on_IBM(qc, num_shots=500):

    # Get data     
    logger.debug (counts)
    logger.debug ("========================")
    answers = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)}
    logger.info ("All Results")
    rows={}
    cols={}
    for each in answers:
        bits = each[::-1]
        row,column = bits.split(" ")
        logger.debug ("b'%s' [Fila: %s, Col: %s] --> %s" %(each, int(row, 2), int(column, 2), answers[each]))

        # Store results by row & column
        if int(row, 2) not in rows:
            rows[int(row, 2)]=0
        rows[int(row, 2)]+=answers[each]

        if int(column, 2) not in cols:
            cols[int(column, 2)]=0
        cols[int(column, 2)]+=answers[each]    
    
    logger.info ("By Row and Column:")
    logger.debug ("ROWS: %s" %rows)    
    logger.debug ("COLUMNS: %s" %cols)

    proposed_row = list({k: v for k, v in sorted(rows.items(), key=lambda item: item[1], reverse=True)}.keys())[0]
    proposed_column = list({k: v for k, v in sorted(cols.items(), key=lambda item: item[1], reverse=True)}.keys())[0]
    logger.info ("PROPOSED ROW: %s" %proposed_row)
    logger.info ("PROPOSED COLUMN: %s" %proposed_column)

    show_map(inp_map_string, 
        GRID_WIDTH, BYTE_SIZE, 
        proposed_row, 
        proposed_column
    )

 
##  ------------------------- MAIN  ------------------------------------------------------------------
if __name__ == "__main__":
    logger.info(" -------------------------- STARTING ----------------------------")
    if TEST_ORACLE:
        logger.info ("In this run, we will test the oracle (no repetition or diffusion)")
        main(inp_map_string, inp_pattern_row, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT)
    else:
        logger.info ("Send to an external provider: [ %s ]" %MAKE_IT_REAL)
        main(inp_map_string, inp_pattern_row, inp_pattern_col, BYTE_SIZE, GRID_WIDTH, GRID_HEIGHT)
        logger.info ("--- 🏁 FINISHED ---")
