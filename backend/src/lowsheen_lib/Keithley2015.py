import re
import pyvisa as visa
import sys
import ast
from remote_instrument import instrument_iniSetting

class conf:
    Mode = {
        '1': 'THD',
        '2': 'THDN',
        '3': 'SINAD',
        }
    Type = {
        '1': 'DISTortion',
        '2': 'VOLTage:DC',
        '3': 'VOLTage:AC',
        '4': 'CURRent:DC',
        '5': 'CURRent:AC',
        '6': 'RESistance',
        '7': 'FRESistance',
        '8': 'PERiod',
        '9': 'FREQuency',
        '10': 'TEMPerature',
        '11': 'DIODe',
        '12': 'CONTinuity',
        }
    Impd = {
        '1': 'OHM50',
        '2': 'OHM600',
        '3': 'HIZ',
        }
    Shape = {
        '1': 'ISINE',
        '2': 'PULSE',
        }

def Parameter(command):
    global RST,MeasState,PrintHelp,Index,Address,State,Read_Mode,Read_Type,Read_Freq,Out_Mode,Out_Freq,Out_Impd,Out_AMPL,Out_Shape
    RST         = False
    PrintHelp   = False
    Index       = ''
    Address     = ''
    State       = ''
    Read_Mode   = ''
    Read_Type   = ''
    Read_Freq   = ''
    Out_Mode    = ''
    Out_Freq    = ''
    Out_Impd    = ''
    Out_AMPL    = ''
    Out_Shape   = ''

    if command[0] == "0": RST = True
    else:
        State   = command[0]
        if State == '1':    # Read Mode
            Read_Mode    = conf.Mode.get(command[1]	 , '')
            Read_Type    = conf.Type.get(command[2]	 , '')
            if command[3] == '0': 
                Read_Freq    = ':AUTO ON'
            else:   
                Read_Freq    = ' ' + command[3]
        elif State == '2':
            Out_Mode    = command[1]
            if Out_Mode =='1':
                Out_Freq    = command[2]
                Out_AMPL    = command[3]
                Out_Impd    = conf.Impd.get(command[4]	 , '') 
                if len(command) > 5:
                    Out_Shape   = conf.Shape.get(command[5] , '') 

    # print('command:',command)



def Measment():
    # Setting
    # print('Read_Mode:',Read_Mode)
    # print('Read_Type:',Read_Type)
    # print('Read_Freq:',Read_Freq)
    inst.write(":DIST:TYPE " + Read_Mode)       # THD, THDN, SINAD
    inst.write("func '"+ Read_Type +"'")    # VOLTage:DC, VOLTage:AC, DISTortion
    inst.write(":DIST:FREQ" + Read_Freq)      # (":DIST:FREQ:AUTO ON")

    inst.write('INIT')
    thd_result = inst.query('READ?')
    number = float(thd_result)
    formatted_str = format_scientific_notation(thd_result)
    formatted_str=formatted_str.replace('\n','')
    formatted_str=formatted_str.replace('\r','')
    formatted_str=formatted_str.replace('\r\n','')
    print(formatted_str,end='')
    return
def Output():
    inst.write("OUTP " + Out_Mode)               # 1 ON、0 OFF
    if '1' in Out_Mode:
        inst.write("OUTP:FREQ " + Out_Freq)       # Frequency
        inst.write("OUTP:IMP " + Out_Impd)      # OHM50 OHM600 HIZ
        inst.write("OUTP:AMPL " + Out_AMPL)      # Voltage Amplitude
        inst.write("OUTP:CHANnel2 " + Out_Shape)  # PULSE ISINE
    
    thd_result = inst.query('OUTP?')
    if '1' in thd_result:
        print('Output Mode:On')
    else:
        print('Output Mode:Off')
    print(1,end='')
    return 

def Reset():
    print(inst.query('*IDN?'),end='')
    inst.write('*RST')
def Close():    # 關閉儀器連接
    inst.close()

def format_scientific_notation(scientific_str):
    number = float(scientific_str)
    exponent = extract_exponent(str(number))
    if exponent != None and exponent < 0:
        num_exponent = int(str(exponent)[1:]) + 2 #小數點後有數字顯示的 1 + 2 碼
    elif exponent >= 0:
        num_exponent =int(str(exponent)) + 3
    else:
        num_exponent = int(3)

    # 如果指数为负数，使用较小的小数位数
    if 'e-' in scientific_str or 'E-' in scientific_str:
        formatted_str = "{:.{}f}".format(number, num_exponent)
    # 如果指数为正数，使用较大的小数位数
    else:
        formatted_str = "{:.3f}".format(number)

    return formatted_str
def extract_exponent(scientific_str):
    # 使用正则表达式匹配科学记号形式字符串
    match = False
    if 'e-' in str(scientific_str) :
        match = re.match(r'.*e(-?\d+).*', scientific_str)
    if 'E-' in str(scientific_str):
        match = re.match(r'.*E(-?\d+).*', scientific_str)

    if match:
        # 提取匹配到的指数部分
        exponent = int(match.group(1))
        return exponent
    else:
        decimal_str = format(float(scientific_str), '.15f')  # 将浮点数格式化为字符串，保留足够的位数
        # 计算小数点后有多少个零
        decimal_str = decimal_str.rstrip('0')  # 移除末尾的零
        num_trailing_zeros = len(decimal_str.split(".")[1]) - len(decimal_str.split(".")[1].lstrip("0"))
        return num_trailing_zeros
def help():
    print('**********************************************************************************')
    print('KEITHLEY 2015 API Helper')
    print('Index 1: <Index> ， Example.「GPIB0::16::INSTR」is ”0”')
    print('Index 2: <Address> ， Example.「GPIB0::16::INSTR」is ”16”')
    print('Index 3: <State> ， 0 : RST(連帶 IDN 回覆)，1 : Read，2 : Output')
    print('If Select Read State.')
    print('     Index 4: <Mode> ， 1 : THD，2 : THD+N，3 : SINAD')
    print('     Index 5: <Type> ， 1 : THD，2 : DCV，3 : ADV')
    print('     Index 6: <Measurement Freqency> ， 0 : AUTO，其餘頻率可自行輸入')
    print('     Example: 0 16 1 1 1 0')
    print('If Select Output State.')
    print('     Index 4: <Output> ， 0 : OFF，1 : ON')
    print('     Index 5: <Frequency> ， numerical，10 to 20000 Hz')
    print('     Index 6: <Amplitude> ， numerical，0 to 4V RMS for HIZ Specify，0 to 2V RMS for OHM50 and OHM600')
    print('     Index 7: <Impedance> ， 1 : 50 Ohm，2 : 600 Ohm ，3 : High Impedance')
    print('     Index 8: <Shape> ， 1 : Inverted sine，2 : Pulse waveform')
    print('     Example: 0 16 2 1 1000 0.001 1 1')
    print('**********************************************************************************')

def initial(instrument):
    instrument.write('*RST')

def send_cmd_to_instrument(instrument, command):
    global inst,Channel,MeasType
    inst   = instrument

    Parameter(command)

    if RST == True:
        res = Reset()
    elif State == '1':
        res = Measment()
    elif State == '2':
        res = Output()

    Close()
    # return res

if __name__ == "__main__":
    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    Instrument_value = args.get('Instrument', '')
    command = args.get('Command', '321')
    command = command.split()
        
    instrument = instrument_iniSetting(Instrument_value)
    if instrument is None:
        print("instrument is None")
        sys.exit(10)
    
    if sequence == '--final':
        response = initial(instrument)
    else:
        response = send_cmd_to_instrument(instrument, command)
        