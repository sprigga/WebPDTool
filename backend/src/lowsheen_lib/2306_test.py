# import pyvisa
from remote_instrument import instrument_iniSetting
import sys
import ast

def get_cmd_string(channels, SetVolt, SetCurr):
    if channels == '1':
        remote_Voltcmd = f"SOUR:VOLT {SetVolt}"
        remote_Currcmd = f"SOUR:CURR:LIM {SetCurr}"
        
        check_Voltcmd = "MEAS:VOLT?"
        check_Currcmd = "MEAS:CURR?"
        
    if channels == '2':
        remote_Voltcmd = f"SOUR2:VOLT {SetVolt}"
        remote_Currcmd = f"SOUR2:CURR:LIM {SetCurr}"
        
        check_Voltcmd = "MEAS2:VOLT?"
        check_Currcmd = "MEAS2:CURR?"
    return remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd

def send_cmd_to_instrument(instrument, channels, SetVolt, SetCurr):
    remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd = get_cmd_string(channels, SetVolt, SetCurr)
    if remote_Voltcmd is None or remote_Currcmd is None:
        return "Error : remote command is wrong"
    
    errors = []
    if SetVolt == '0' and SetCurr == '0':
        if channels == '1':
            instrument.write("OUTP OFF\n")
        if channels == '2':
            instrument.write("OUTP2 OFF\n")
    else:
        instrument.write(str(remote_Voltcmd))
        instrument.write(str(remote_Currcmd))
        if channels == '1':
            instrument.write("OUTP ON")
        if channels == '2':
            instrument.write("OUTP2 ON")

        # response_Volt = round(float(instrument.query(str(check_Voltcmd))), 2)
        # response_Curr = round(float(instrument.query(str(check_Currcmd))), 2)

        # if response_Volt != float(SetVolt):
        #     print("response_Volt: "+str(response_Volt))
        #     errors.append('VOLT')
        # if response_Curr != float(SetCurr):
        #     print("response_Curr: "+str(response_Curr))
        #     errors.append('CURR')

    if not errors:
        return 1
    else:
        return f"2306 channel {channels} set {' and '.join(errors)} fail"
    

def initial(instrument):#, channels):
    # if channels == '1':
    instrument.write("OUTP OFF\n")
    # if channels == '2':
    instrument.write("OUTP2 OFF\n")
        
if __name__ == "__main__":
    
    # Instrument_value, channels, SetVolt, SetCurr = 'MODEL2306_1', '1', '5', '0'
    # sys.argv = ['2306_test.py', '2306_on', "{'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': 'MODEL2306', 'ExecuteName': 'PowerSet', 'case': 'MODEL2306', 'Instrument': 'model2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"]

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args['Instrument'] if 'Instrument' in args else ''
    channels = args['Channel'] if 'Channel' in args else ''
    SetVolt = args['SetVolt'] if 'SetVolt' in args else ''
    SetCurr = args['SetCurr'] if 'SetCurr' in args else ''
    
    instrument = instrument_iniSetting(Instrument_value)
    if instrument is None:
        sys.exit(10)
    
    # print(SetVolt, SetCurr)
    if sequence == '--final':
        response = initial(instrument)#, channels)
    elif SetVolt == '0' and SetCurr == '0':
        # print('85 elif')
        response = send_cmd_to_instrument(instrument, channels, SetVolt, SetCurr)
    else:
        # print('88 else')
        response = send_cmd_to_instrument(instrument, channels, SetVolt, SetCurr)
    print(response)