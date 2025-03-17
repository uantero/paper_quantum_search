# Grover search for robotics

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

In the file 'conf.py', there are some variables that can be edited:

  

- inp_map_string ➜ A string (some nxn grid) that represents the map)

- inp_pattern_row ➜ A string that represents what the sensors of the robot perceive in the horizontal axis

- inp_pattern_col ➜ A string that represents what the sensors of the robot perceive in the vertical axis

And additionally, the configuration is controlled by the variable:

    

    CONFIG = {    
      "TEST_ORACLE": {    
      "enable": False, # Used to validate the Oracle"    
      "check_row": 0, # Validate the oracle with this values (check if output=1)    
      "check_col": 1 # Validate the oracle with this values (check if output=1)    
    },    
      "MAKE_IT_REAL": False, # Sent it to some provider? (if False: simulate locally)    
      "AVAILABLE_PROVIDERS": ["IONQ", "IBM", "QUANTUMINSPIRE"],    
      "SELECTED_PROVIDER": "IONQ"    
    }
  

Some example:

    inp_map_string = [
	   ["1 0 1 "] ,
	   ["0 1 0 "] ,
	   ["0 1 1 "]
	]
	inp_pattern_row= "10"
	inp_pattern_col= "10"

Additionally, a simple visualization demo has been created (using the Pygame librery). The code is under /UI

