import re
import sys
import ast
from RsSmcv import *
from remote_instrument import instrument_iniSetting
import pdb
import time 


class conf:
     Mode = {
        '0': 'auto_DAB',
        '1': 'auto_AM',
        '2': 'auto_FM',
        }
     
def Parameter(command):
    global RST,MeasState,PrintHelp,State,Out_Mode,Out_Freq,Out_Level,play_file,file_path
    RST         = False
    PrintHelp   = False
    State       = ''
    Out_Mode    = ''
    Out_Freq    = ''
    Out_Level   = ''
    play_file   = ''
    file_path = "/var/user/"
    if command[0] == "0": RST = True
    else:
        # State   = command[0]
        Out_Mode    = conf.Mode.get(command[1]	 , '')
        if Out_Mode == 'auto_DAB' or Out_Mode == 'auto_AM' or Out_Mode == 'auto_FM':
            Out_Freq    = float(command[2]) * 1e6
            Out_Level   = float(command[3])
        if Out_Mode == 'auto_DAB':
                if len(command) < 5:
                    print(0,end='')
                    return
                else:
                    # 提取播放文件名 
                    play_file = ' '.join(command[4:])
       
def dab(instr: RsSmcv, enable: bool = True) -> None:
   """
    控制 DAB 模式的開啟或關閉

    參數:
    instr: RsSmcv 儀器對象
    enable: True 表示啟用，False 表示禁用
    """
   try:
        print(f"{'啟用' if enable else '禁用'} DAB 模式...",end='')

        instr.source.bb.tdmb.set_state(state = enable)

        if enable:    
            
            print("RF 輸出已啟用")
            instr.output.state.set_value(True)
            
            # 設定頻率和功率
            instr.source.frequency.set_frequency(Out_Freq)
            instr.source.power.set_power(Out_Level)
            
            instr.source.bb.tdmb.set_source(tdmb_source = enums.CodingInputSignalSource.TSPLayer)
            # instr.source.bb.tdmb.set_source(tdmb_source = enums.CodingInputSignalSource.TESTsignal)
            instr.tsGen.configure.set_play_file(play_file = file_path + play_file)
            
 
        else:
            instr.source.bb.tdmb.set_state(state = enable)
            instr.output.state.set_value(state = enable)
            # print("RF 輸出已關閉")
        # print(1,end=' ') 
        return 1 # polo
   except Exception as e:
        print(f"控制DAB模式時出錯: {str(e)}",end='')
        # raise
        return 0 # polo
    
#    return 
def am(instr: RsSmcv, enable: bool = True) -> None:
     try:  
            # 使用 RsSmcv 直接建立連接
            # instr = RsSmcv(ip_address) 
            #   instr.source.bb.radio.am.set_state(state = True)
            if enable:
                print("連接到aduio AM...",end='')
                
                instr.source.bb.radio.am.set_state(state = enable)
                instr.output.state.set_value(enable)
                  # 設定頻率和功率
                instr.source.frequency.set_frequency(Out_Freq)
                instr.source.power.set_power(Out_Level)
                # print(1,end='')
            else:
                print("關閉aduio AM...",end='')
                instr.source.bb.radio.am.set_state(state = enable)
                instr.output.state.set_value(enable)
            # print(1,end='')
            return 1 # polo
            
     except Exception as e:
        print(f"控制AM程序執行出錯: {str(e)}",end='')
        if 'instr' in locals():
            instr.close()
        return 0 # polo
     
    #  return

def fm(instr: RsSmcv, enable: bool = True) -> None:
    try:  
        # 使用 RsSmcv 直接建立連接
        # instr = RsSmcv(ip_address)
        if enable:
            print("連接到aduio FM...",end='')
            instr.source.bb.radio.fm.set_state(state = enable)
            instr.output.state.set_value(True)
            instr.source.frequency.set_frequency(Out_Freq)
            instr.source.power.set_power(Out_Level)
            # print(1,end='')
        else:
            print("關閉aduio FM...",end='')
            instr.source.bb.radio.fm.set_state(state = enable)
            instr.output.state.set_value(enable) 
        # print(1,end='')  
        return 1 # polo
        
    except Exception as e:
        print(f"控制FM程序執行出錯: {str(e)}",end='')
        if 'instr' in locals():
            instr.close() 
        return 0 # polo

def iq(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            # instr.utilities.write_str(f'OUTPut1:IQ:STATe 1')
            instr.source.iq.set_state(state = enable)
        else:
            instr.source.iq.set_state(state = enable)
        # print(1,end='')
        return 1  # polo
    except Exception as e:
        print(f"程序執行出錯: {str(e)}",end='')
        if 'instr' in locals():
            instr.close()
        return 0 # polo

def rf(instr: RsSmcv, enable: bool = True) -> None:
    try:
        if enable:
            instr.output.state.set_value(state = enable)
        else:
            instr.output.state.set_value(state = enable)
        # print(1,end='')
        return 1 # polo
    except Exception as e:
        print(f"程序執行出錯: {str(e)}",end='')
        if 'instr' in locals():
            instr.close()
        return 0 # polo

def initial(instrument):
    
    try:
        # global inst
        inst = RsSmcv(instrument)
        # idn = inst.utilities.idn_string
        inst.utilities.reset()
    except Exception as e:
        print(f"Not connected: {str(e)}",end='')
def Reset():
    print(inst.utilities.query_str('*IDN?'), end='')
    # print(1,end='')
    # inst.utilities.write_str('*RST')
    inst.utilities.reset()
    return 1 # polo
    # RsSmcv.utilities.write_str('*IDN?')
    
def send_cmd_to_instrument(instrument, command):
    # global inst,Channel,MeasType
    global inst
    try:
        inst = RsSmcv(instrument)
        
        if not inst.utilities.is_connection_active(): 
            # print(0, end=' ')
            return 0 # polo
        
        if inst.utilities.query_str('*IDN?') == "": 
            # print(0, end=' ')
            return 0 # polo
        # inst   = instrument
        Parameter(command)

        if RST == True:
            Reset()
        elif Out_Mode == "auto_DAB":
           response_str = dab(inst, True)
        elif Out_Mode == 'auto_AM':
           response_str = am(inst, True)
        else: # Out_Mode == 'auto_FM':
           response_str = fm(inst, True)   
        
        return response_str
                      
    except Exception as e:
        print(f"程序執行出錯: {str(e)}",end='')     
    finally:
        if 'inst' in locals():
            inst.close()
            

#if __name__ == "__main__":
def smcv100b_main(test_uid, TestParams, SNIndex):    
    # sequence = sys.argv[1]
    # args = sys.argv[2]

    # # print(f"sequence: {sequence}, args1: {args}")
    # args = ast.literal_eval(args) # list轉字典
    # SNIndex = sys.argv[3]
    # print(f"args2: {args}, SNIndex: {SNIndex}")
    sequence = test_uid
    args = TestParams
    SNIndex = SNIndex


    Instrument_value = args.get('Instrument', '')
    command = args.get('Command', '321')
    command = command.split()
    
    # print(f"Instrument_value: {Instrument_value}, command: {command}, command[0]: {command[0]}")
    instrument = instrument_iniSetting(Instrument_value, SNIndex)
    if instrument is None:
        print("instrument is None")
        sys.exit(10)
    
    if sequence == '--final':
        response = initial(instrument)
    else:
        response = send_cmd_to_instrument(instrument, command)
    print(response) # polo
    return str(response)
    
