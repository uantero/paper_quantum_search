# paper_quantum_search
Use Grover algorithm for quantum robot localization

Quick start:

 - Create virtual env
 - Create .env file (use .env_sample as a guide)
 - Run 'python main.py'

Steps:

    python3 -m venv env
    source ./env/bin/activate
    pip install -r requirements.txt
    cp .env_sample .env 
    (edit .env)
    python main.py

 

### Internal configuration
In the file 'main.py', there are some variables that can be edited:

 - inp_map_string ➜ A string (some nxn grid) that represents the map)
 - inp_pattern_row ➜ A string that represents what the sensors of the robot perceive in the horizontal axis
 - inp_pattern_col ➜ A string that represents what the sensors of the robot perceive in the vertical axis
 
 And additionally:
 - MAKE_IT_REAL ➜ If 'True', the simulation is sent to an external provider
 - SEND_TO ➜ Should be: "IBM" or "IONQ"  (only used if MAKE_IT_REAL is 'True')
 - TEST_ORACLE ➜ Used for debugging... if set to 'True', the oracle is checked
 - BYTE_SIZE: how many bits are 'stored' in a single cell of the map


Some example:

    inp_map_string = [
		    ["1 0 1 "] ,
		    ["0 1 0 "] ,
		    ["0 1 1 "] 
		  ]
	inp_pattern_row=  "10" 
	inp_pattern_col=  "10" 
