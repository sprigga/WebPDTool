import sys
import serial
import ast
import time

# def get_response(ser):
#     response = ser.readline().decode().strip()
#     # if response == '':
#     #     response = 'default'

#     return response

def get_response(ser, timeout, ReslineCount):
    response = ''
    start_time = time.time()
    get_total_line = 0
    end_count = 0

    while (time.time() - start_time) < timeout:
        if ser.in_waiting > 0:
        # if ser:
            line_response = ser.readline().decode('utf-8', errors='replace').strip()
            get_total_line += 1
            # print(f'get line_response: {line_response}')

            if response:
                response += '\n'
            response += line_response
            end_count = 0
            print(f'update response: {response}')

            # if get_total_line >= ReslineCount:
            #     break
            if ReslineCount != '':
                if get_total_line >= ReslineCount:
                    break
        else:
            time.sleep(0.1) 

            if ReslineCount == '':
                end_count += 1
                # print(f'try {end_count} time: No data')

                if end_count >= 3:
                    # print('Stopping reading')
                    break

                if ReslineCount and get_total_line >= ReslineCount:
                    # print('get response, stopping reading')
                    break

    return response

def comport_send(ser, comport_command, timeout, ReslineCount):

    ser.timeout = timeout  # set timeout for read
    message = comport_command
    ser.write(message.encode())
    response = get_response(ser, timeout, ReslineCount)
    ser.close()
    return response
def smh_write_command(ser, comport_command, timeout, ReslineCount):
    if ser:
        ser.write(bytes(comport_command, encoding='utf-8'))
        ser.flush()
        #wait for the serial console to finish.(needed for correct behaviour)
        time.sleep(0.05)
    # response = smh_get_response(ser)
    # ser.close()
    # return response
    return

def smh_get_response(ser):
    received_response = None

    if ser:
    # if ser.in_waiting > 0:
        # Read the entire response from the serial device
        received_response = ser.readline().decode('utf-8')
        # received_response = ser.read(ser.in_waiting)
        # print(f"received_response: {received_response}")
    ser.close()    
    return received_response

def comport_initial(ser):
    rst_msg = '*RST\n'
    ser.write(rst_msg.encode())
    outputoff_msg = 'OUTP OFF\n'
    ser.write(outputoff_msg.encode())
    
if __name__ == "__main__":
    
    # ---- 參數說明 -----
    #   ComportWait : 等待comport開啟初始化的時間，預設為0  (依測項連線時間設定 eg.arduino需要大概2秒的時間準備/ comport儀器連線不需等待)
    #       Timeout : 等待comport讀取response的時間(依測項回復時間設定)，預設為3秒
    #  ReslineCount : comport讀取pass response的總行數，可不給
    # ---- 參數說明 -----

    # sys.argv = ['./src/lowsheen_lib/ComPortCommand.py', "['Test_TXT']", "{'ItemKey': 'FT00-000', 'ValueType': 'string', 'LimitType': 'none', 'ExecuteName': 'CommandTest', 'case': 'comport', 'Port': 'COM9', 'Baud': '115200', 'Command': '0xAA 0x06 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xAA\\\\n', 'ComportWait': '2', 'Timeout': '5', 'content': 'C:\content.txt', 'ReslineCount': '10'}"]

    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    comport_name = args['Port']
    comport_baudrate = args['Baud']
    comport_command = args['Command'] if 'Command' in args else ''
    ComportWait = float(args['ComportWait']) if 'ComportWait' in args else 0
    Timeout = float(args['Timeout']) if 'Timeout' in args else 3
    ReslineCount = int(args['ReslineCount']) if 'ReslineCount' in args else ''
    content = args['content'] if 'content' in args else ''
    response = None

    if '\\n' in comport_command:
        comport_command = comport_command.replace('\\n', '\n')
    else:
        comport_command = comport_command

    try:
        ser = serial.Serial(comport_name, comport_baudrate, timeout=1)
        time.sleep(ComportWait) #等待comport開啟初始化的時間
    except:
        print("Failed to connect to the serial port")
        sys.exit(10)
    try:
        if sequence == '--final' :
            response = comport_initial(ser)
        else:
            # response = comport_send(ser, comport_command, Timeout, ReslineCount)
            # 20240705 polo add
            smh_write_command(ser, comport_command, Timeout, ReslineCount)
            time.sleep(0.5)
            response = smh_get_response(ser)
        if content != '':
            try:
                f = open(content, 'w')
                f.write(str(response))
                f.close()
            except WindowsError as e:
                print(f"Error reading from the registry: {e}")
    except Exception as e:
        print(e)
        sys.exit()

    print(response)
    # print("123")

    