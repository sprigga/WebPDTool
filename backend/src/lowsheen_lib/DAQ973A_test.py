from remote_instrument import instrument_iniSetting
import time
import sys
import ast


def check_channel_list(cmd, channels):
    channel_no = str(channels).strip("()").split(", ")
    channel_check = []
    if cmd == 'CURR':
        for i in channel_no:            
            if i[-2:] == '21' or i[-2:] == '22':
                channel_check.append(i)
            else:
                print("Error : channel input is wrong! (21/22)")
                return None
    else:
        for i in channel_no:
            channel_check.append(i)            
            # if i[-2:] in [str(num).zfill(2) for num in range(1, 21)]:
            #     channel_check.append(i)
            # else:
            #     print("Error : channel input is wrong! (01~20)")
            #     return None
    return channel_check

def get_cmd_string(cmd, channels, type_ = None):
    channel_check = check_channel_list(cmd, channels)
    if channel_check is not None:
        if cmd == 'OPEN' or cmd == 'CLOS':
            remote_cmd = f"ROUT:{cmd} (@{','.join(channel_check)})"
            check_cmd = f"ROUT:{cmd}? (@{','.join(channel_check)})"
            return remote_cmd, check_cmd
        else:
            if cmd == 'VOLT' or cmd == 'CURR':
                if type_ is None :
                    print("Error : no type setting!(AC/DC)")
                    return
                remote_cmd = f"MEAS:{cmd}:{type_}? (@{','.join(channel_check)})"
                return remote_cmd
            else:
                if type_ is None or type_ == "":
                    type_ = 'DEF'
                remote_cmd = f"MEAS:{cmd}? (@{','.join(channel_check)})"
                return remote_cmd
    else:
        return None

function_mapping = {
    'OPEN','CLOS',
    'DIOD','CAP','FREQ','PER','FRES','RES','TEMP',
    'CURR','VOLT',
}

def send_cmd_to_instrument(instrument, cmd, channels, type_):

    if cmd in function_mapping:
        # SETTING function
        if cmd == 'OPEN' or cmd == 'CLOS':
            remote_cmd, check_cmd = get_cmd_string(cmd, channels, type_)
            if remote_cmd == None:
                print("Error : remote command is wrong")
            else:
                instrument.write(str(remote_cmd))
                time.sleep(0.1)
                response = instrument.query(str(check_cmd))
                return response
        # MEASURE function
        else:
            remote_cmd = get_cmd_string(cmd, channels, type_)
            if remote_cmd == None:
                print("Error : remote command is wrong")
            else:
                if cmd == 'TEMP':
                    instrument.query(str(remote_cmd))
                    time.sleep(2)
                response = '{:.3f}'.format(float(instrument.query(str(remote_cmd))))
                return response
    else:
        print("Invalid command:", str(cmd))
        
def initial(instrument):
    remote_cmd = '*RST\n'
    instrument.write(str(remote_cmd))
     
if __name__ == "__main__":

    # Instrument_value, item, channels, type_ = 'DAQ973A_1', 'CLOS', '101', ''

    # Instrument_value = 'DAQ973A_1'
    # item = 'FREQ'
    # channels = '101'
    # type_ = ''
    # sequence = 'test'

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args['Instrument'] if 'Instrument' in args else ''
    instrument = instrument_iniSetting(Instrument_value)
    if instrument is None:
        print("instrument is None")
        sys.exit(10)
    
    if sequence == '--final':
        response = initial(instrument)
    else:
        item = args['Item'].upper()
        channels = args['Channel'] if 'Channel' in args else None
        type_ = args['Type'] if 'Type' in args else None
        response = send_cmd_to_instrument(instrument, item, channels, type_=type_)
    print(response)
    