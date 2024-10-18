# importing Qiskit
from qiskit import transpile, transpile
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate

from lib import initialize_H, XNOR, XOR, toffoli_general, get_qubit_index_list, add_measurement, diffusion, set_inputs

# --------------------- ORACLE --------------------------------
# Oracle that "marks" the output when a difference is found between two strings
 

# ORACLE FOR VERTICAL SEARCH
def create_column_oracle(qc, searchspace, map_string, column_substring, temporary, oracle_output, ancillary, BYTE_SIZE, GRID_WIDTH):    

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
def create_row_oracle(qc, searchspace, map_string, row_substring, temporary, oracle_output, ancillary,  BYTE_SIZE, GRID_WIDTH):
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
