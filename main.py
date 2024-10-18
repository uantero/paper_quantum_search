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

 
MAKE_IT_REAL = True
SEND_TO = "IONQ"
#SEND_TO = "IBM"
# ----------------------------
# Used to validate the Oracle
test_oracle = False


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

# THE MAP
inp_map_string = [
    ["1 0 1 "] ,
    ["0 1 0 "] ,
    ["0 1 1 "] 
]

# ROBOT'S SENSORS (horizontal & vertical)
inp_pattern_row=  "11" # row 2
inp_pattern_col=  "11" # col 1


# Byte size, measured in bits... each of them is considered a "unit"
# Bytes are only written "in horizontal"
BYTE_SIZE = 1 # 2 bits
GRID_WIDTH = int(len(inp_map_string[0][0].replace(" ","")) / BYTE_SIZE)
GRID_HEIGHT = int(len(inp_map_string) )

# Join inp_map_string into a single string
inp_map_string="".join(["".join(item) for column in inp_map_string for item in column]).replace(" ","").replace("X","1")

 
print ("STARTING FOR:")
print ("MAP:")
print ("========")
for each_map_line in wrap(inp_map_string, GRID_WIDTH*BYTE_SIZE ):
    print (each_map_line)
 
print ("")
print ("Looking in rows for: %s" %inp_pattern_row)
print ("Looking in cols for: %s" %inp_pattern_col)
 
# Output is (x,y)... we assume that GRID_WIDTH = GRID_HEIGHT
num_s_bits =  math.ceil(  math.log2(  GRID_WIDTH )    )
print ("Number of qubits in search space: %s (2x %i)" %(num_s_bits * 2, num_s_bits ))
print ("=================================")
 
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
 
qc = QuantumCircuit(row_searchspace, column_searchspace, map_string, row_substring, column_substring, temporary, oracle_row_output, oracle_column_output, ancillary, cbit_row_result, cbit_column_result)

# Let's create the circuit
#if test_oracle:
#    qc = QuantumCircuit(row_searchspace, column_searchspace, map_string, row_substring, column_substring, temporary, oracle_row_output, oracle_column_output, ancillary, cbit_row_result, cbit_column_result)
#else:
#    qc = QuantumCircuit(row_searchspace, column_searchspace, map_string, row_substring, column_substring, temporary, oracle_row_output, oracle_column_output, ancillary)
 
def initialize_H(qc, qubits):
    """Apply a H-gate to 'qubits' in qc"""
    for q in qubits:
        qc.h(q)
    return qc
 
# Check for equality
def XNOR(qc,a,b,output):
    qc.cx(a,output)
    qc.cx(b,output)
    qc.x(output)
 
# Check for inequality
def XOR(qc,a,b,output):
    qc.cx(a,output)
    qc.cx(b,output)
 
def toffoli_general(qr, control, target):
    qr.append(MCXGate(num_ctrl_qubits=len(control)), control + [target])
 
def get_qubit_index_list(qc, register):
    return list([qc.find_bit(qarg)[0] for qarg in register])
 
def add_measurement2(qc, what):
    num_bits = len(what)
    meas = QuantumCircuit(num_bits, num_bits)
    meas.measure(list(range(num_bits)), list(range(num_bits)))
    qc.compose(meas, inplace=True, qubits=what)
 
def add_measurement(qc, what, name):
    num_bits = len(what)
    measuring_c = ClassicalRegister(num_bits, name)
    meas = QuantumCircuit(what, measuring_c)
    meas.measure(what, measuring_c)
    qc.compose(meas, inplace=True, qubits=what)    
 
def diffusion(qc: QuantumCircuit, search_space, output_qubit):
    """Apply a diffusion circuit to the register 's' in qc"""
    qc.h(search_space)
    qc.x(search_space)
 
    qc.mcx(search_space, output_qubit)
    qc.z(output_qubit)
 
    qc.x(search_space)
    qc.h(search_space)
 
def execute_on_IBM(qc, num_shots=500):
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
 
    # ###
    TOKEN = os.environ["IBM_TOKEN"]
 
    OPTIMIZATION_LEVEL=3
 
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN)    
    print ("Sending real JOB to IBM")
    backend = service.least_busy(operational=True, simulator=False)
    sampler = Sampler(backend)
    job = sampler.run([transpile(qc, backend, optimization_level=OPTIMIZATION_LEVEL)], shots=num_shots)
    print(f"job id: {job.job_id()}")
    results = job.result()

    print (results)
 
    row = results[0].data.cbit_row_result.get_counts()
    column = results[0].data.cbit_column_result.get_counts()
    print ("COLUMN:")
    print (column)
    answers = {k: v for k, v in sorted(column.items(), key=lambda item: item[1], reverse=True)}
    print ("COLUMN Results")
    for each in answers:
        bits = each[::-1]
        print ("b'%s' [Columna: %s] --> %s" %(each, int(bits, 2), answers[each]))    

    print ("ROW:")
    print (row)
    answers = {k: v for k, v in sorted(row.items(), key=lambda item: item[1], reverse=True)}
    print ("ROW Results")
    for each in answers:
        bits = each[::-1]
        print ("b'%s' [Fila: %s] --> %s" %(each, int(bits, 2), answers[each]))    

    sys.exit(0)
    

 
    return results

def execute_on_IONQ(qc, num_shots=500):
    from qiskit_ionq import IonQProvider
 
    ## Check your .env file
    TOKEN = os.environ["IONQ_TOKEN"]

    provider = IonQProvider(TOKEN)
    
    simulator_backend = provider.get_backend("ionq_simulator")

 
    OPTIMIZATION_LEVEL=3
     
    print ("Sending real JOB to IONQ")
    job = simulator_backend.run(qc, shots=num_shots, extra_query_params={
        "noise": {"model": "aria-1"}}
    )

    result=job.get_counts()
 
    return result    
 
# --------------------- ORACLE --------------------------------
#Oracle that "marks" the output when a difference is found between two strings
 
"""
inp_map_string = (
    "000" +
    "100" +
    "000"
)
inp_map_string = (
    "012" +
    "345" +
    "678"
)
 
  036
  147
  258
"""
 
# ORACLE FOR VERTICAL SEARCH
def create_column_oracle(qc, searchspace, map_string, column_substring, temporary, oracle_output, ancillary):    

    format_string = "{:0" + str(len(searchspace)) + "b}"
   
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

    map_in_cols =  split_in_columns(map_string, GRID_WIDTH)
    col=-1
    for each_map_col in map_in_cols:
        col = col + 1
        index=-1
        pos_in_binary = format_string.format(col)
        # Flip search space
        flipped_s = []
        for k, pos in enumerate(pos_in_binary):
            if pos == "0":
                flipped_s.append(searchspace[k])
                qc.x(searchspace[k])            

        # We should match all bits between string and substring
        
        #print ("POS IN BINARY: %s" %pos_in_binary)
        for each_map_item_index in range(len(each_map_col) - int(len(column_substring)/BYTE_SIZE)+1):
            used_bits = []
            for each_substring_bit_index in range( int(len(column_substring)/BYTE_SIZE) ):
                #print (each_map_col[each_map_item_index + each_substring_bit_index])
                #print ("%s - %s" %(each_map_item_index + each_substring_bit_index, each_substring_bit_index))
                for each_bit in range(BYTE_SIZE):
                    XNOR(qc,each_map_col[each_map_item_index + each_substring_bit_index][each_bit], column_substring[BYTE_SIZE*each_substring_bit_index+each_bit], temporary[BYTE_SIZE*each_substring_bit_index+each_bit])
                
                    # Keep track of used "temporary" bits
                    used_bits.append( temporary[BYTE_SIZE*each_substring_bit_index+each_bit] )
            #print ("...")
            # Generate output            
            qc.cx( ancillary, oracle_output[0]) # Used to reset output if it was previously set (in case we have multiple coincidences)
            qc.mcx( list(searchspace) + list(used_bits) , oracle_output[0])
            qc.cx( oracle_output[0] , ancillary)                         

            # Revert status of "temporary"
            for each_substring_bit_index in range( int(len(column_substring)/BYTE_SIZE) ):
                #print (each_map_col[each_map_item_index + each_substring_bit_index])
                #print ("%s - %s" %(each_map_item_index + each_substring_bit_index, each_substring_bit_index))
                for each_bit in range(BYTE_SIZE):
                    XNOR(qc,each_map_col[each_map_item_index + each_substring_bit_index][each_bit], column_substring[BYTE_SIZE*each_substring_bit_index+each_bit], temporary[BYTE_SIZE*each_substring_bit_index+each_bit])

        #print ("=== %s / ====" %(pos_in_binary))

        # Revert Search space
        if len(flipped_s):
            qc.x(flipped_s)


 
    # Revert things back!
 
    #toffoli_general(qc, get_qubit_index_list(qc, temporary), get_qubit_index_list(qc, oracle_output)[0])
    #toffoli_general(qc, get_qubit_index_list(qc, temporary), get_qubit_index_list(qc, oracle_output)[0])
 
    #qc.mcx(temporary, oracle_output[0])


    return qc


# ORACLE FOR HORIZONTAL SEARCH
def create_row_oracle(qc, searchspace, map_string, row_substring, temporary, oracle_output, ancillary):
    format_string = "{:0" + str(len(searchspace)) + "b}"
   
    # Ok! Let's look in rows...
    # Consider bytes...
    def split_in_rows(what, width):
        rows=[]
        each_row=[]
        for each in [what[i:i+BYTE_SIZE] for i in range(0, len(what), BYTE_SIZE)]:
            each_row.append(each)
            if len(each_row)>=width:
                rows.append(each_row)
                each_row=[]
        return rows   
    
    map_in_rows =  split_in_rows(map_string, GRID_WIDTH)
    row=-1
    for each_map_row in map_in_rows:
        row = row + 1
        index=-1
        pos_in_binary = format_string.format(row)
        # Flip search space
        flipped_s = []
        for k, pos in enumerate(pos_in_binary):
            if pos == "0":
                flipped_s.append(searchspace[k])
                qc.x(searchspace[k])            

        # We should match all bits between string and substring
        
        for each_map_item_index in range(len(each_map_row) - int(len(row_substring)/BYTE_SIZE)+1):
            used_bits = []
            for each_substring_bit_index in range( int(len(row_substring)/BYTE_SIZE) ):
                #print ("%s - %s" %(each_map_item_index + each_substring_bit_index, each_substring_bit_index))
                for each_bit in range(BYTE_SIZE):
                    XNOR(qc,each_map_row[each_map_item_index + each_substring_bit_index][each_bit], row_substring[BYTE_SIZE*each_substring_bit_index+each_bit], temporary[BYTE_SIZE*each_substring_bit_index+each_bit])
                    # Keep track of used "temporary" bits
                    used_bits.append(temporary[BYTE_SIZE*each_substring_bit_index+each_bit])
                #print ("   --> %s %s" %((each_map_item_index + each_substring_bit_index), each_substring_bit_index))
            #print ("...")

            # Generate output            
            qc.cx( ancillary, oracle_output[0]) # Used to reset output if it was previously set (in case we have multiple coincidences)
            qc.mcx( list(searchspace) + list(used_bits) , oracle_output[0])
            qc.cx( oracle_output[0] , ancillary)             
            

            # Revert status of "temporary"
            for each_substring_bit_index in range( int(len(row_substring)/BYTE_SIZE) ):
                #print ("%s - %s" %(each_map_item_index + each_substring_bit_index, each_substring_bit_index))
                for each_bit in range(BYTE_SIZE):
                    XNOR(qc,each_map_row[each_map_item_index + each_substring_bit_index][each_bit], row_substring[BYTE_SIZE*each_substring_bit_index+each_bit], temporary[BYTE_SIZE*each_substring_bit_index+each_bit])


#        print ("=== %s / ====" %(pos_in_binary))


        # Revert Search space
        if len(flipped_s):
            qc.x(flipped_s)
 
    # Revert things back!
 
    #toffoli_general(qc, get_qubit_index_list(qc, temporary), get_qubit_index_list(qc, oracle_output)[0])
    #toffoli_general(qc, get_qubit_index_list(qc, temporary), get_qubit_index_list(qc, oracle_output)[0])
 
    #qc.mcx(temporary, oracle_output[0])


    return qc


# Set inputs (the pattern and the long string)
def set_inputs(qc, inp_w, w):
    """Negate the initial |0> states of w and p corresponding to the input"""
    for i, c in enumerate(inp_w):
        if c == "1":
            qc.x(w[i])
 
    return qc


# 
# Used to validate the Oracle
#test_oracle = True
 
if test_oracle:
    LOOK_IN_ROW = 0
    LOOK_IN_COLUMN = 1
    format_string = "{:0"+str(num_s_bits)+"b}"
    print ("Looking in row: %s [%s]" %(LOOK_IN_ROW, format_string.format(LOOK_IN_ROW)))
    print ("Looking in col: %s [%s]" %(LOOK_IN_COLUMN, format_string.format(LOOK_IN_COLUMN)))

    set_inputs(qc, format_string.format(LOOK_IN_ROW), row_searchspace)
    set_inputs(qc, format_string.format(LOOK_IN_COLUMN), column_searchspace)    
    set_inputs(qc, inp_map_string, map_string)
    set_inputs(qc, inp_pattern_row, row_substring)
    set_inputs(qc, inp_pattern_col, column_substring)    
    # ROW
    qc.compose(create_row_oracle(qc, row_searchspace, map_string, row_substring, temporary, oracle_row_output, ancillary))
    # Measure oracle output for validation
    add_measurement(qc, oracle_row_output, "row")
    #qc.measure(oracle_row_output, cbit_row_result)
 
    # COL
    #qc.compose(create_column_oracle(qc, column_searchspace, map_string, column_substring, temporary, oracle_column_output, ancillary))
    # Measure oracle output for validation    
    #add_measurement(qc, oracle_column_output, "vertical")
    #qc.measure(column_searchspace, list(range(num_s_bits)))

    num_shots = 100
    from qiskit.providers.basic_provider import BasicProvider as BasicAerProvider
    provider = BasicAerProvider()    
    backend = provider.get_backend()
    result = backend.run(transpile(qc, backend), shots=num_shots).result()
    counts = result.get_counts()

    print (counts)
    sys.exit(0)

 
# "Real" grover search (if not validating)
else:
    initialize_H(qc, row_searchspace)
    initialize_H(qc, column_searchspace)
    set_inputs(qc, inp_map_string, map_string)
    set_inputs(qc, inp_pattern_col, row_substring)
    set_inputs(qc, inp_pattern_row, column_substring)    
   
    #N = len(inp_map_string)/(num_s_bits)
    N = 2 * (len(inp_map_string) )/ ((len(inp_pattern_row) + len(inp_pattern_col))/BYTE_SIZE ) # Horiz & vertical
    num_repetitions = math.floor( (math.pi/4)*(math.sqrt(N)) )           
    
   
    print ("Estimated Grover repetitions: %s" %num_repetitions)
    
    # Repeat!
    # ROWS
    for repetition in range(num_repetitions):
        qc.compose(create_row_oracle(qc, row_searchspace, map_string, row_substring, temporary, oracle_row_output, ancillary))
        diffusion(qc, row_searchspace, oracle_row_output)
        
        qc.compose(create_column_oracle(qc, column_searchspace, map_string, column_substring, temporary, oracle_column_output, ancillary))
        diffusion(qc, column_searchspace, oracle_column_output)    
        
    qc.measure(column_searchspace, cbit_column_result)
    qc.measure(row_searchspace, cbit_row_result)
    
    #add_measurement(qc, row_searchspace, name="row")
    #add_measurement(qc, column_searchspace, name="column")

    # Columns
    #for repetition in range(num_repetitions):
    #    qc.compose(create_column_oracle(qc, column_searchspace, map_string, column_substring, temporary, oracle_column_output, ancillary))
    #diffusion(qc, column_searchspace, oracle_column_output)    
    #add_measurement(qc, column_searchspace, name="vert")
    
    # Add measure for searchspace
    #add_measurement(qc, row_searchspace, name="horiz")
    #add_measurement(qc, row_searchspace, name="horiz")
    #
    #qc.measure(column_searchspace, cbit_column_result)
    #qc.measure(row_searchspace, cbit_row_result)
 
    # -- real ---
    make_it_real = MAKE_IT_REAL    
    if make_it_real:
        if SEND_TO=="IONQ":
            print ("SENDING TO IONQ")
            counts = execute_on_IONQ(qc, 4500)
        else:
            print ("SENDING TO REAL IBM COMPUTER")
            counts = execute_on_IBM(qc, 4500)
 
    else:
        print ("SIMULATING LOCALLY")
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
print (counts)
print ("========================")
answers = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)}
print ("Results")
rows={}
cols={}
for each in answers:
    bits = each[::-1]
    row,column = bits.split(" ")
    print ("b'%s' [Fila: %s, Col: %s] --> %s" %(each, int(row, 2), int(column, 2), answers[each]))
    if int(row, 2) not in rows:
        rows[int(row, 2)]=0
    rows[int(row, 2)]+=answers[each]

    if int(column, 2) not in cols:
        cols[int(column, 2)]=0
    cols[int(column, 2)]+=answers[each]    

print ("ROWS: \n%s" %rows)
print ("PROPOSED ROW: %s" %list({k: v for k, v in sorted(rows.items(), key=lambda item: item[1], reverse=True)}.keys())[0])
print ("COLUMNS: \n%s" %cols)
print ("PROPOSED COLUMN: %s" %list({k: v for k, v in sorted(cols.items(), key=lambda item: item[1], reverse=True)}.keys())[0])

