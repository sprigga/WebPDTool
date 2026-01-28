import re
import pyvisa as visa
import sys
import pyvisa
import time
from remote_instrument import instrument_iniSetting
import ast

class conf:
    MeasType = {
        '1': 'AMPlitude',
        '2': 'AREa',
        '3': 'BURst',
        '4': 'CARea',
        '5': 'CMEan',
        '6': 'CRMs',
        '7': 'DELay',
        '8': 'FALL',
        '9': 'FREQuency',
        '10': 'HIGH',
        '11': 'HITS',
        '12': 'LOW',
        '13': 'MAXimum',
        '14': 'MEAN',
        '15': 'MEDian',
        '16': 'MINImum',
        '17': 'NDUty',
        '18': 'NEDGECount',
        '19': 'NOVershoot',
        '20': 'NPULSECount',
        '21': 'NWIdth',
        '22': 'PEAKHits',
        '23': 'PDUty',
        '24': 'PEDGECount',
        '25': 'PERIod',
        '26': 'PHAse',
        '27': 'PK2Pk',
        '28': 'POVershoot',
        '29': 'PPULSECount',
        '30': 'PWIdth',
        '31': 'RISe',
        '32': 'RMS',
        '33': 'SIGMA1',
        '34': 'SIGMA2',
        '35': 'SIGMA3',
        '36': 'STDdev',
        '37': 'TOVershoot',
        '38': 'WAVEFORMS',
        }

def Measurement():
    try:
        IDN = inst.query(':*IDN?')
        # IDN = IDN.replace('\n','')
        # print(IDN)
        
        ## Close other channel
        closeChannel = ['1','2','3','4']
        closeChannel.remove(Channel)
        for i in range(len(closeChannel)):
            inst.write('SELECT:CH' + closeChannel[i] +' OFF')
        inst.write('SELECT:CH' + Channel + ' ON')
        
        ## print select channel in log
        selected_port = inst.query('SELECT:CH' + Channel + '?')
        # selected_port = selected_port.replace('\n','')
        # print(selected_port)

        ## Auto set
        inst.write(':AUTOSet EXECute')

        ## Wait for AutoSet program
        while(True):
            BUSY = inst.query('BUSY?')
            time.sleep(0.01)
            if '0' in BUSY:
                break
        
        ## 設定要從示波器讀取的命令。這裡是讀取頻率，但需根據實際操作手冊來調整命令
        inst.write('MEASUrement:MEAS4:SOURCE1 CH' + Channel)
        inst.write('MEASUrement:MEAS4:STATE ON')
        inst.write('MEASUrement:MEAS4:TYPE ' + MeasType)
        
        ## wait change type and read data
        while(True):
            queryType = inst.query('MEASUrement:MEAS4:TYPE?')
            # queryType = queryType.replace('\n','')
            # print(queryType)
            time.sleep(1)
            if MeasType.upper() in  queryType:
                break

        queryValue = inst.query('MEASUrement:MEAS4:VALue?')
        queryValue = queryValue.replace('\n','')
        queryValue = queryValue.replace('\r','')
        queryValue = queryValue.replace(':MEASUREMENT:MEAS4:VALUE ','')
        queryValue = float(queryValue)

        # print('Value=' + queryValue)
        return queryValue

    except:
        inst.close()

    return

def Close():    # 關閉儀器連接
    inst.close()

def send_cmd_to_instrument(instrument, cmd, channels, type_):
    global inst,Channel,MeasType
    MeasType    =   conf.MeasType.get(cmd , '')
    Channel     = channels
    inst   = instrument
    return Measurement()


def help():
    print('**********************************************************************************')
    print('API Helper')
    print('Index 1: <Index> ， Example."USB0::0x0699::0x052C::C051741::INSTR"')
    print('Index 2: <Channel> ， 1-4')
    print('Index 3: <Type> ， 1:AMPlitude. 2:AREa. 3:BURst. 4:CARea. 5:CMEan. 6:CRMs.\n' \
    '    7:DELay. 8:FALL. 9:FREQuency. 10:HIGH. 11:HITS. 12:LOW. 13:MAXimum. 14:MEAN. 15:MEDian. \n' \
    '    16:MINImum. 17:NDUty. 18:NEDGECount. 19:NOVershoot. 20:NPULSECount. 21:NWIdth. 22:PEAKHits. \n' \
    '    23:PDUty. 24:PEDGECount. 25:PERIod. 26:PHAse. 27:PK2Pk. 28:POVershoot. 29:PPULSECount. 30:PWIdth. \n' \
    '    31:RISe. 32:RMS. 33:SIGMA1. 34:SIGMA2. 35:SIGMA3. 36:STDdev. 37:TOVershoot. 38:WAVEFORMS')
    print('Example: USB0::0x0699::0x052C::C051741::INSTR 2 1')

    print('**********************************************************************************')
def initial(instrument):
    remote_cmd = '*RST\n'
    instrument.write(str(remote_cmd))

if __name__ == "__main__":
    
    # Instrument_value, item, channels  = '', '', ''

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args['Instrument'] if 'Instrument' in args else ''
    item = args['Item'] if 'Item' in args else ''
    channels = args['Channel'] if 'Channel' in args else ''
    type_ = args['Type'] if 'Type' in args else None
        
    instrument = instrument_iniSetting(Instrument_value)
    if instrument is None:
        print("instrument is None")
        sys.exit(10)
    
    if sequence == '--final':
        response = initial(instrument)
    else:
        response = send_cmd_to_instrument(instrument, item, channels, type_=type_)
    # response = send_cmd_to_instrument(instrument, item, channels, type_=type_)
        
    print(response)
