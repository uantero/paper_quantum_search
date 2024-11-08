# importing Qiskit
from qiskit import transpile, transpile
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate
import os, sys
from logs import logger
from dotenv import load_dotenv
from termcolor import colored
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler 


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
 


def execute_on_Fake_IBM(qc, num_shots=300, show_results=None, num_s_bits=2):     
    from qiskit_aer import AerSimulator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    # ###
    TOKEN = os.environ["IBM_TOKEN"]
    OPTIMIZATION_LEVEL=3  # cuanto mayor es el nivel de optimización mas tarda en hacer la transpilacion
    instance= "ibm-q/open/main"
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN, instance=instance)    
    real_backend = service.least_busy(operational=True, simulator=False)
    aer = AerSimulator.from_backend(real_backend)
    logger.info ("Sending JOB to a Fake IBM backend")
    logger.info ("Simulated backend: %s" %(real_backend.name))
    # Mandamos a un backend simulado pero con el mismo comportamiento y ruido que el backend real
    pm = generate_preset_pass_manager(backend=aer, optimization_level=3)
    isa_qc = pm.run(qc)
    # You can use a fixed seed to get fixed results.
    sampler = Sampler(mode=aer,options={"default_shots": 20})
    result = sampler.run([isa_qc]).result()
    countsIBM = result[0].data.res1.get_counts()

    return countsIBM

def execute_on_real_IBM(qc, num_shots=500, show_results=None, num_s_bits=2):     
    TOKEN = os.environ["IBM_TOKEN"]
    OPTIMIZATION_LEVEL=3  # cuanto mayor es el nivel de optimización mas tarda en hacer la transpilacion
    instance= "ibm-q/open/main"
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN, instance=instance)    
    logger.info ("Sending real JOB to IBM")
    backend = service.least_busy(operational=True, simulator=False)
    logger.info(backend)
    sampler = Sampler(mode=backend, options={"default_shots": num_shots})
    logger.info ("... transpiling...")

    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
 
    pm = generate_preset_pass_manager(optimization_level=OPTIMIZATION_LEVEL, backend=backend)
    isa_circuit = pm.run(qc)
    print(f">>> Circuit ops (ISA): {isa_circuit.count_ops()}")
    job = sampler.run([isa_circuit])
    logger.info(f"job id: {job.job_id()}")
    print(f"job id: {job.job_id()}")
    job_result = job.result()

    results=job_result
    countsIBM = results[0].data.res1.get_counts()
    return countsIBM



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
    
        
    # Multi check....
    used_bits=[]
    temporary_check_index=-1
    for each_check in check_list:        
        reg1 = each_check["reg1"]
        reg2 = each_check["reg2"]
        reg2str = each_check["reg2str"]

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

    QI.set_authentication(get_authentication(), QI_URL, project_name="Paper2024")

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
