import sys
import ast
import subprocess


def console_send(command, timeout ):
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) #universal_newlines=True
    try:
        # Wait for process to terminate or timeout to expire
        stdout_data, stderr_data = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # If timeout expires, kill the process
        process.kill()
        stdout_data, stderr_data = process.communicate()

    if stdout_data:
        # return stdout_data.decode()
        return stdout_data.decode('utf-8',errors='ignore')
    else:
        return ''
    
    
if __name__ == "__main__":

    # console_command, timeout = 'python ./src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 command="gpioget gpiochip1 17"', 2
    # console_command, timeout = 'python ./src/lowsheen_lib/L6MPU/ssh_cmd.py 192.168.5.1 command:"cat /dev/ttymxc0 > /outout &"', 2
    # erase
    # sys.argv = ['ConSoleCommand.py', 'eth_test', "{'ItemKey': 'TT00-00', 'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': 'end', 'ExecuteName': 'CommandTest', 'case': 'console', 'Command': 'python ./src/lowsheen_lib/testUTF/delay.py', 'Timeout': '5000'}"]

    # args = dict(arg.split('=') for arg in sys.argv[2:])
    # console_command = args.get('Command', '321')
    # timeout = float(args.get('Timeout', '1'))

    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    console_command = args['Command']
    timeout = float(args['Timeout']) if 'Timeout' in args else 1.0

    # print(console_command)

    response = console_send(console_command, timeout)

    print(response)