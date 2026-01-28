from remote_instrument import instrument_iniSetting
import sys
import ast

# [SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]
# Description        Sets or queries the voltage level in volts.
# Syntax             [SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]{<NRf>|MIN|MAX}
# Query/Syntax       [SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]?[MIN|MAX]
# Parameter/Return   <NRf> 0~105% of the rated output voltage in volts.
#                    MIN Minimum voltage level
#                    MAX Maximum voltage level
# Example            SOUR:VOLT:LEV:IMM:AMPL 10
#                    Sets the voltage level to 10 volts.

# *IDN?
# meas:curr:dc?
# meas:volt:dc?;:meas:curr:dc?

def get_cmd_string(SetVolt, SetCurr):
    remote_Voltcmd = f"VOLT {SetVolt}"
    remote_Currcmd = f"CURR {SetCurr}"
    
    check_Voltcmd = "MEAS:VOLT:DC?"
    check_Currcmd = "MEAS:CURR:DC?"
    return remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd

def send_cmd_to_instrument(instrument, SetVolt, SetCurr):
    remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd = get_cmd_string(SetVolt, SetCurr)
    if remote_Voltcmd is None or remote_Currcmd is None:
        return "Error : remote command is wrong"

    instrument.write(str(remote_Voltcmd))
    instrument.write(str(remote_Currcmd))
    instrument.write("OUTP ON")

    response_Volt = round(float(instrument.query(str(check_Voltcmd))), 2)
    response_Curr = round(float(instrument.query(str(check_Currcmd))), 2)

    errors = []

    if response_Volt != float(SetVolt):
        errors.append('volt')
    if response_Curr != float(SetCurr):
        errors.append('curr')

    if not errors:
        return 1
    else:
        return f"2260B set {' and '.join(errors)} fail"
   
def initial(instrument):
    remote_cmd = 'OUTP OFF\n'
    instrument.write(str(remote_cmd))
     

if __name__ == "__main__":
    
    # Instrument_value, item, SetValue = 'MODEL2303_1', 'VOLT', '5'

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args['Instrument'] if 'Instrument' in args else ''
    SetVolt = args['SetVolt'] if 'SetVolt' in args else ''
    SetCurr = args['SetCurr'] if 'SetCurr' in args else ''
    
    instrument = instrument_iniSetting(Instrument_value)
    if instrument is None:
        sys.exit(10)
    
    if sequence == '--final' :
        response = initial(instrument)
    else:
        response = send_cmd_to_instrument(instrument, SetVolt, SetCurr)

    print(response)