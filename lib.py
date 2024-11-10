# importing Qiskit
from qiskit import transpile, transpile
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate
import os, sys
from logs import logger
from dotenv import load_dotenv
from termcolor import colored


def initialize_H(qc, qubits):
    """Apply a H-gate to 'qubits' in qc"""
    for q in qubits:
        qc.h(q)
    return qc
 
# Set inputs (the pattern and the long string)
def set_inputs(qc, inp_w, w):
    """Negate the initial |0> states of w and p corresponding to the input"""
    for i, c in enumerate(inp_w):
        if c == "1":
            qc.x(w[i])
 
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
 

 

def execute_on_IBM(qc, num_shots=500, show_results=None, num_s_bits=2, job_id="", conf={}):
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

    GRID_WIDTH=conf["GRID_WIDTH"]
    GRID_HEIGHT=conf["GRID_HEIGHT"]
 
    # ###
    TOKEN = os.environ["IBM_TOKEN"]
 
    OPTIMIZATION_LEVEL=3
 
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN)    
    if job_id:
        logger.info ("Using results from IBM job '%s'" %job_id)
        job = service.job(job_id)
        job_result = job.result()        
    else:
        logger.info ("Sending real JOB to IBM")
        backend = service.least_busy(operational=True, simulator=False)
        sampler = Sampler(backend)
        logger.info ("... transpiling...")
        job = sampler.run([transpile(qc, backend, optimization_level=OPTIMIZATION_LEVEL)], shots=num_shots)
        logger.info(f"job id: {job.job_id()}")

        job_result = job.result()

    results=job_result
    counts = results[0].data.res1.get_counts()
    print (counts)
    col={}
    row={}
    for each in counts:
        col_value=each[:num_s_bits]
        row_value=each[num_s_bits:]
        if row_value not in row:
            row[row_value]=0
        if col_value not in col:
            col[col_value]=0

        if int(row_value,2)>=GRID_HEIGHT or int(col_value,2)>=GRID_WIDTH:
            continue
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


    

    if show_results:
        show_results(selected_row, selected_col)    

    logger.info ("-- FINISHED --")
    sys.exit(0)
    

 
    return results


def execute_on_BlueQbit(qc, num_shots=500, show_results=None, num_s_bits=2, job_id="", conf={}):
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

    import bluequbit

    bq_client = bluequbit.init(os.environ["BLUEQUBIT_TOKEN"])

    #return {'0110': 93, '0100': 87, '1101': 88, '0101': 90, '0010': 52, '1001': 60, '1110': 76, '0000': 92, '0111': 72, '1111': 76, '1011': 85, '0011': 59, '0001': 59, '1000': 81, '1010': 59, '1100': 71}

    logger.info ("Sending real JOB to BLUEQUBIT")
    job_result = bq_client.run(qc, job_name="qiskit_job")

    counts = {}
    for each in job_result.top_128_results:
        counts[each]=int(job_result.top_128_results[each]*num_shots)
        
 
    return counts

def execute_on_IONQ(qc, num_shots=500):
    from qiskit_ionq import IonQProvider
 
    ## Check your .env file
    TOKEN = os.environ["IONQ_TOKEN"]

    provider = IonQProvider(TOKEN)
    
    simulator_backend = provider.get_backend("ionq_simulator")

 
    OPTIMIZATION_LEVEL=3
     
    print ("Sending real JOB to IONQ")
    if qc.num_qubits<26:
        job = simulator_backend.run(qc, shots=num_shots, extra_query_params={
            "noise": {"model": "aria-1"}}
            #"noise": {"model": "ideal"}}
        )
    else:
        job = simulator_backend.run(qc, shots=num_shots, extra_query_params={
            "noise": {"model": "ideal"}}
        )    

    print ("Job: %s" %job)

    result=job.get_counts()
 
    return result    

# If both register are equal, all output qubits are switched (additional_qubits are additional checks)

def checkEqual(qc, check_list, check_temporary, output, additional_qubits):
#def checkEqual(qc, reg1, reg2, reg1_literal_value, temporary, output, additional_qubits):
        
    #print ("Checking equal...")
    #print (additional_qubits)
    # Multi check....
    used_bits=[]
    temporary_check_index=-1
    for each_check in check_list:        
        reg1 = each_check["reg1"]
        reg2 = each_check["reg2"]
        reg2str = each_check["reg2str"]

        #print ("REG1: %s" %reg1)
        #print ("REG2: %s" %reg2)
        #print ("reg2str: %s" %reg2str)

        # Check qubit by qubit
        for bit_index in range(len(reg1)):
            temporary_check_index+=1
            used_bits.append(  check_temporary[temporary_check_index]  )
            XNOR(qc, reg1[bit_index], reg2[bit_index], check_temporary[temporary_check_index])            


    qc.mcx(used_bits + list(additional_qubits), output[0])    


    # Uncompute
    temporary_check_index=-1
    for each_check in check_list:
        temporary_check_index+=1
        reg1 = each_check["reg1"]
        reg2 = each_check["reg2"]
        reg2str = each_check["reg2str"]
        
        # Check qubit by qubit
        for bit_index in range(len(reg1)):
            XNOR(qc, reg1[bit_index], reg2[bit_index], check_temporary[temporary_check_index])            

    return qc



def execute_on_QuantumInspire(qc, num_shots=500):
    from quantuminspire.qiskit import QI

    from quantuminspire.api import QuantumInspireAPI
    from quantuminspire.credentials import get_authentication, enable_account
    from quantuminspire.credentials import enable_account
    
    QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

    logger.info ("Sending real JOB to QUANTUMINSPIRE")

    #QI.set_authentication(get_authentication(), QI_URL, project_name="Paper2024")
    enable_account(os.environ["QUANTUMINSPIRE_TOKEN"])
    QI.set_authentication()

    qi_backend = QI.get_backend('QX single-node simulator')  
    shot_count = 512

    circuit = transpile(qc, backend=qi_backend)
    qi_job = qi_backend.run(circuit, shots=num_shots)
    qi_result = qi_job.result()
    result = qi_result.get_counts(circuit)
 
    return result        


def simulate(qc, num_shots=300):
    from qiskit.providers.basic_provider import BasicProvider as BasicAerProvider
    provider = BasicAerProvider()        
    backend = Aer.get_backend('qasm_simulator')
    result = backend.run(transpile(qc, backend), shots=num_shots).result()
    counts = result.get_counts()

    return counts
