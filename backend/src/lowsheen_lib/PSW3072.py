# import pyvisa
from remote_instrument import instrument_iniSetting
import sys
import ast
import time

def get_cmd_string(SetVolt, SetCurr):
    remote_Voltcmd = f"VOLT {SetVolt}"
    remote_Currcmd = f"CURR {SetCurr}"
    
    return remote_Voltcmd, remote_Currcmd

def send_command(instrument, command):
    command += '\n'
    instrument.write(command.encode())
    time.sleep(0.1) 

def remote_instrument(instrument, SetVolt, SetCurr):

    instrument.timeout = 1  # set timeout for read
    remote_Voltcmd, remote_Currcmd = get_cmd_string(SetVolt, SetCurr)
    if remote_Voltcmd is None or remote_Currcmd is None:
        return "Error : remote command is wrong"
    
    if SetVolt == '0' and SetCurr == '0':
        outputoff_msg = 'OUTP OFF'
        send_command(instrument, outputoff_msg)
    else:
        send_command(instrument, remote_Voltcmd)
        send_command(instrument, remote_Currcmd)
    
        outputon_msg = 'OUTP ON'
        send_command(instrument, outputon_msg)

    errors = []
    if errors:
        return f"PSW30-72 set {' and '.join(errors)} fail"
    else:
        return 1

def initial(instrument):
    outputoff_msg = 'OUTP OFF'
    send_command(instrument, outputoff_msg)

        
if __name__ == "__main__":
    
    # sys.argv = ['PSW3072.py', '3072_on', "{'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': '1', 'ExecuteName': 'PowerSet', 'case': 'PSW3072', 'Instrument': 'PSW3072_1', 'SetVolt': '0', 'SetCurr': '0'}"]

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args['Instrument'] if 'Instrument' in args else ''
    SetVolt = args['SetVolt'] if 'SetVolt' in args else ''
    SetCurr = args['SetCurr'] if 'SetCurr' in args else ''
    
    instrument = instrument_iniSetting(Instrument_value)

    # print(SetVolt, SetCurr)
    if sequence == '--final':
        response = initial(instrument)#, channels)
    elif SetVolt == '0' and SetCurr == '0':
        # print('85 elif')
        response = remote_instrument(instrument, SetVolt, SetCurr)
    else:
        # print('88 else')
        response = remote_instrument(instrument, SetVolt, SetCurr)
    print(response)