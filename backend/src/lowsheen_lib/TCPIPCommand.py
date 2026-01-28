import sys
import ast
import subprocess

import sys
import socket
import binascii
import time
 
def calculate_crc32(data):
    """
    Calculate CRC32 checksum of the data
    """
    return binascii.crc32(data)
 
def read_response(sock, buffer_size=1024, delimiter=b'\n'):
    """
    Read response from the socket until the delimiter or until no more data is received
    """
    response = b""
    while True:

        data = sock.recv(buffer_size)
        if not data:
            break
        hex_string = binascii.hexlify(data).decode('utf-8')
        hex_spaced_string = ' '.join(hex_string[i:i+2] for i in range(0, len(hex_string), 2))


        # response += hex_string
        # try:
        # print("Raw response:",hex_spaced_string)
        # except:
        # print("Raw response:"+response.decode('utf-8'))        

        if hex_spaced_string != '':
            break
        if delimiter in response:
            break
    return hex_spaced_string

def main(TCP_IP,TCP_PORT,MESSAGE):
    # # Define the IP address and port
    # TCP_IP = '192.168.1.3'
    # TCP_PORT = 12345
    
    # # Define the bytes to send
    # MESSAGE = bytes([0x31, 0x03, 0xf0, 0x00, 0x00])
    
    response = ''
    # Calculate CRC32 checksum of the message
    crc32_checksum = calculate_crc32(MESSAGE)
    
    # Append CRC32 checksum to the message
    MESSAGE_WITH_CRC = MESSAGE + crc32_checksum.to_bytes(4, byteorder='big')
    
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server
        sock.connect((TCP_IP, TCP_PORT))
    
        # Send the message with CRC32 checksum
        sock.send(MESSAGE_WITH_CRC)
        hex_string = binascii.hexlify(MESSAGE_WITH_CRC).decode('utf-8')
        hex_spaced_string = ' '.join(hex_string[i:i+2] for i in range(0, len(hex_string), 2))
        # print(hex_spaced_string)

        # print("Command:",hex_spaced_string)
        CommandText = "Command: " + hex_spaced_string + "\r\n"

        # from time import sleep
        # time.sleep(1)
        # # Read the response
        sock.settimeout(5)
        response = read_response(sock)
        # print("Response received:", response)
    
    except Exception as e:
        print("Error:", e)
    
    finally:
        # Close the socket
        sock.close()
    # return CommandText + "Response:" + response
    return  response

    
if __name__ == "__main__":

    TCP_IP = '192.168.1.3'
    TCP_PORT = 12345
    MESSAGE = bytes([0x31, 0x01, 0xf0, 0x00, 0x00])


    # sys.argv = ['ConSoleCommand.py', 'eth_test', "{'ItemKey': 'FT00-077', 'ValueType': 'string', 'LimitType': 'none', 'EqLimit': '', 'ExecuteName': 'CommandTest', 'case': 'tcpip', 'Command': '192.168.1.3 12345 31;01;f0;00;00', 'Timeout': '10'}"]

    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    console_command = args['Command']
    timeout = float(args['Timeout']) if 'Timeout' in args else 1.0

    CommandList = console_command.split(' ')
    if len(CommandList)>2:
        TCP_IP = str(CommandList[0])
        TCP_PORT = int(CommandList[1])
        MESSAGE = bytes([int(byte, 16) for byte in str(CommandList[2]).split(';')])

        response = main(TCP_IP,TCP_PORT,MESSAGE)
    else:
        response = "Parameter Lack"
    
    print(response)