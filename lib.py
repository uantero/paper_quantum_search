# importing Qiskit
from qiskit import transpile, transpile
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate
import os, sys
from logs import logger
from dotenv import load_dotenv



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
 

 

def execute_on_IBM(qc, num_shots=500, show_results=None):
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
 
    # ###
    TOKEN = os.environ["IBM_TOKEN"]
 
    OPTIMIZATION_LEVEL=3
 
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN)    
    logger.info ("Sending real JOB to IBM")
    backend = service.least_busy(operational=True, simulator=False)
    sampler = Sampler(backend)
    job = sampler.run([transpile(qc, backend, optimization_level=OPTIMIZATION_LEVEL)], shots=num_shots)
    logger.info(f"job id: {job.job_id()}")
    results = job.result()

    logger.info (results)
 
    row = results[0].data.cbit_row_result.get_counts()
    column = results[0].data.cbit_column_result.get_counts()
    selected_row=None
    selected_column=None
    logger.debug ("COLUMN:")
    logger.debug  (column)
    answers = {k: v for k, v in sorted(column.items(), key=lambda item: item[1], reverse=True)}
    selected_column = sorted(column.items(), key=lambda item: item[1], reverse=True)[0]
    logger.info ("COLUMN Results")
    for each in answers:
        bits = each[::-1]
        if not selected_column:
            selected_column = int(bits, 2)        
        logger.debug ("b'%s' [Columna: %s] --> %s" %(each, int(bits, 2), answers[each]))    

    logger.debug ("ROW:")
    logger.debug  (row)
    answers = {k: v for k, v in sorted(row.items(), key=lambda item: item[1], reverse=True)}
    selected_row = sorted(row.items(), key=lambda item: item[1], reverse=True)[0]
    logger.info ("ROW Results")
    for each in answers:
        bits = each[::-1]
        if not selected_row:
            selected_row = int(bits, 2)        
        logger.debug ("b'%s' [Fila: %s] --> %s" %(each, int(bits, 2), answers[each]))    

    if show_results:
        show_results(selected_row, selected_column)    

    logger.info ("-- FINISHED --")
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

def execute_on_QuantumInspire(qc, num_shots=500):
    from quantuminspire.qiskit import QI

    from quantuminspire.api import QuantumInspireAPI
    from quantuminspire.credentials import get_authentication, enable_account
    from quantuminspire.credentials import enable_account
    
    QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

    QI.set_authentication(get_authentication(), QI_URL, project_name="Paper2024")

    qi_backend = QI.get_backend('QX single-node simulator')  
    shot_count = 512

    circuit = transpile(qc, backend=qi_backend)
    qi_job = qi_backend.run(circuit, shots=num_shots)
    qi_result = qi_job.result()
    result = qi_result.get_counts(circuit)
 
    return result        