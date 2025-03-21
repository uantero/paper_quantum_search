
# ROBOT'S SENSORS (horizontal & vertical)
# A single data is centered in the robot
# From there... if row length is 2, each data is shown with the robot in the middle-->   1 r 2
inp_pattern_row=  ["1", "1"]
inp_pattern_col=  ["1", "1" ]


# THE MAP
''' Example
inp_map_string = [

    ["0 0 0 0"] ,
    ["0 0 0 0"] ,
    ["0 1 0 0"] ,
    ["0 0 0 0"] ,
]
'''

inp_map_string = [
    ["1 1 1 0  "] ,
    ["1 1 0 0  "] ,
    ["0 0 0 1  "] ,
    ["1 0 1 1  "] ,
]

CONFIG = {
    "TEST_ORACLE": {
        "enable": False, # Used to validate the Oracle
        "check_pos_row": 1, # Validate the oracle with this value (check if output=1)
        "check_pos_col": 1
    },
    "AVAILABLE_PROVIDERS": ["IONQ", "IBM", "FAKEIBM", "SIMULATE", "BLUEQUBIT"],
    "SELECTED_PROVIDER": "BLUEQUBIT",
    "USE_JOB_ID": "", # Used to recall results from an external service
    "REUSE_ROW_COL_QUBITS": inp_pattern_row==inp_pattern_col, # If set to True, Row and Col patterns are the same, so Qubits are reused
}    
    