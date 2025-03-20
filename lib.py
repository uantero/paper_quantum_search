# importing Qiskit
from qiskit import transpile, assemble
from qiskit_aer import Aer
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.library import MCXGate
import os, sys
from logs import logger
from dotenv import load_dotenv
from termcolor import colored
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.circuit.library import MCMT, ZGate, XGate    


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
    cccz = MCMT('z',len(search_space),len(output_qubit))
    """Apply a diffusion circuit to the register 's' in qc"""
    

    """
    qc.h(search_space)
    qc.x(search_space)
 
    qc.mcx(search_space, output_qubit)
    qc.z(output_qubit)
 
    qc.x(search_space)
    qc.h(search_space)
    
    """
    qc.h(search_space)
    qc.x(search_space)


    MCZGate = ZGate().control(len(search_space))
    qc.append(MCZGate, search_space[0:]+[output_qubit])
    

    qc.x(search_space)
    qc.h(search_space)


def execute_on_Fake_IBM(qc, num_shots=300):     
    from qiskit_aer import AerSimulator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    # ###
    TOKEN = os.environ["IBM_TOKEN"]
    OPTIMIZATION_LEVEL=3  # the higher, the longer it will take to transpile
    instance= "ibm-q/open/main"    
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN, instance=instance)    
    #print(service.backends())
    #real_backend = service.least_busy(operational=True, simulator=False)
    real_backend=service.backends()[0]

    aer = AerSimulator.from_backend(real_backend)
    logger.info ("Sending JOB to a Fake IBM backend that simulates the noise of the devices")
    logger.info ("Simulated backend: %s" %(real_backend.name))
    # We'll try to simulate using the same backend for the noise
    pm = generate_preset_pass_manager(backend=aer, optimization_level=OPTIMIZATION_LEVEL)
    isa_qc = pm.run(qc)
    # You can use a fixed seed to get fixed results.
    sampler = Sampler(mode=aer,options={"default_shots": num_shots})
    result = sampler.run([isa_qc]).result()
    countsIBM = result[0].data.res1.get_counts()

    logger.info("Counts: %s" %countsIBM)

    return countsIBM, real_backend

def execute_on_real_IBM(qc, num_shots=False):     
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    TOKEN = os.environ["IBM_TOKEN"]
    OPTIMIZATION_LEVEL=3  # the higher, the longer it will take to transpile
    instance= "ibm-q/open/main"    
    service = QiskitRuntimeService(channel="ibm_quantum", token=TOKEN, instance=instance)    
    logger.info ("Sending real JOB to IBM")
    backend = service.least_busy(operational=True, simulator=False)

    shots = 1024
    groverCircuit_transpiled = transpile(qc, backend, optimization_level=OPTIMIZATION_LEVEL)

    """
    #pm = generate_preset_pass_manager(optimization_level=OPTIMIZATION_LEVEL, backend=backend)
    logger.info ("... transpiling...")
    isa_circuit = pm.run(qc)    
    print(f">>> Circuit ops (ISA): {isa_circuit.count_ops()}")
    #return {'01': 685, '10': 739, '11': 684, '00': 692}, backend

    logger.info(backend)
    """
    # Sampler
    sampler = Sampler(mode=backend)
    # Set default shots
    if num_shots:
        sampler.options.default_shots = num_shots
        job = sampler.run([groverCircuit_transpiled], shots=num_shots)
    else:
        job = sampler.run([groverCircuit_transpiled])


    logger.info(f"job id: {job.job_id()}")
    print(f"job id: {job.job_id()}")
    job_result = job.result()

    results=job_result
    countsIBM = results[0].data.res1.get_counts()

    logger.info("IBM Counts: %s" %countsIBM)
    return countsIBM, backend




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
        
 
    return counts, None


def execute_on_IONQ(qc, num_shots=500):
    from qiskit_ionq import IonQProvider
 
    ## Check your .env file
    TOKEN = os.environ["IONQ_TOKEN"]

    provider = IonQProvider(TOKEN)
    
    simulator_backend = provider.get_backend("ionq_simulator")

    circuit = transpile(qc, backend=simulator_backend)
 
    OPTIMIZATION_LEVEL=3
     
    print ("Sending real JOB to IONQ")
    if qc.num_qubits<26:
        job = simulator_backend.run(circuit, shots=num_shots, extra_query_params={
            "noise": {"model": "aria-1"}}
            #"noise": {"model": "ideal"}}
        )
    else:
        job = simulator_backend.run(circuit, shots=num_shots, extra_query_params={
            "noise": {"model": "ideal"}}
        )    

    print ("Job: %s" %job)

    result=job.get_counts()
 
    return result, simulator_backend  

# If both register are equal, all output qubits are switched (additional_qubits are additional checks)

def checkEqual(qc, check_list, check_temporary, output, additional_qubits):
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


    if output:
        # 
        #all_bits=[]
        #for each in used_bits + list(additional_qubits):
        #    all_bits.append(each)
        #MCZGate = ZGate().control(len(all_bits))
        #qc.append(MCZGate, all_bits[0:]+[output[0]])
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

    logger.info("Counts: %s" %result)
 
    return result, qi_backend    


def simulate(qc, num_shots=300):
    from qiskit.providers.basic_provider import BasicProvider as BasicAerProvider
    provider = BasicAerProvider()        
    backend = Aer.get_backend('qasm_simulator')
    result = backend.run(transpile(qc, backend), shots=num_shots).result()
    counts = result.get_counts()
    return counts, backend
