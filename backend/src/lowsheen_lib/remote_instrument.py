import pyvisa
from pyvisa import constants
import sys
import configparser
import os
import serial

def instrument(instrument_name):
    rm = pyvisa.ResourceManager()
    inst_list = rm.list_resources()
    instrument_mapping = {}
    for inst_addr in inst_list:
        instrument = rm.open_resource(inst_addr)
        instrument_id = instrument.query('*IDN?').split(',')[1].strip()
        instrument_mapping[instrument_id.strip()] = inst_addr 
        instrument.close()
    
    if instrument_name is not None and instrument_name in instrument_mapping:
        inst_addr = instrument_mapping[instrument_name]
        rm = pyvisa.ResourceManager()
        instrument = rm.open_resource(inst_addr, timeout=5000)
        # instrument_initial(instrument)
    else:
        print("Error: The instrument name cannot find the corresponding port.")
        return
    
    return instrument

def instrument_initial(instrument):
    remote_cmd = '*RST'
    print("remote_cmd : "+ str(remote_cmd))
    instrument.write(str(remote_cmd))
    print('instrument reset already')

def instrument_iniSetting(instrument_name):

    config = configparser.ConfigParser()
    current_path = os.path.dirname(os.path.abspath(__file__))
    FILE_NAME = os.path.join(current_path, '../../test_xml.ini')
    config.read(FILE_NAME)

    # USB/LAN
    # SERIAL >> ASRL%u::INSTR
    # TCPIP_SOCKET >> TCPIP%u::%s::%u::SOCKET
    # TCPIP_INSTR >> TCPIP%u::%s::%s::INSTR
    # GPIB >> GPIB%u::%u::INSTR
    inst_addr = config['Setting'][instrument_name]
    
    try:

        if 'COM' in inst_addr:
            comport_name, comport_baudrate = parse_comport_address(inst_addr)
            # print(comport_name, comport_baudrate)
            instrument = serial.Serial(comport_name, comport_baudrate, timeout=1)

        else:
            # with pyvisa.ResourceManager() as rm:
            rm = pyvisa.ResourceManager()
            instrument = rm.open_resource(inst_addr, timeout=5000)

            if "ASRL" in inst_addr: # ASRL2::INSTR/baud:115200/bits:1
                inst_addr, BaudRate, StopBits = parse_serial_address(inst_addr)
                setup_serial(instrument, BaudRate, StopBits)

            elif 'TCPIP' and "SOCKET" in inst_addr:
                setup_tcpip_socket(instrument)
                # ip_address, port = parse_tcpip_address(inst_addr)
                # if "SOCKET" in inst_addr: # TCPIP0::192.168.0.1::2268::SOCKET
                #     setup_tcpip_socket(instrument)#, ip_address, port)
                # elif "INSTR" in inst_addr: # TCPIP0::192.168.0.1::2268::INSTR
                #     setup_tcpip_instrument(instrument, ip_address, port)

    # except:
    except Exception as e:
        print(f"[{instrument_name}] Instrument initialization failed: {str(e)}")
        # print("instrument_iniSetting Fail!")
        return None
    
    return instrument

def parse_comport_address(address): # 2306_1 = COM3/baud:115200
    parts = address.split('/')
    comport_name = parts[0] # COM3
    comport_baudrate = int(parts[1].split(':')[1]) # 115200
    return comport_name, comport_baudrate

def parse_serial_address(address): # 2030_1 = ASRL2::INSTR/baud:115200/bits:1
    parts = address.split('/')
    inst_addr = parts[0] # ASRL2::INSTR
    BaudRate = int(parts[1].split(':')[1]) # 115200
    StopBits = parts[2].split(':')[1] # 1
    return inst_addr, BaudRate, StopBits

def setup_serial(instrument, baud_rate, stop_bits):
    print('setup_serial')
    # BAUDRATE
    instrument.set_visa_attribute(constants.VI_ATTR_ASRL_BAUD, baud_rate)
    print('serial instrument setup BAUDRATE already')
    # STOPBITS
    if stop_bits != '0':
        stop_bits_mapping = {'1': constants.VI_ASRL_STOP_ONE,
                             '1.5': constants.VI_ASRL_STOP_ONE5,
                             '2': constants.VI_ASRL_STOP_TWO}
        stop_bits_value = stop_bits_mapping.get(stop_bits, constants.VI_ASRL_STOP_ONE)
        instrument.set_visa_attribute(constants.VI_ATTR_ASRL_STOP_BITS, stop_bits_value)
        print('serial instrument setup STOPBITS already')

# def parse_tcpip_address(address): 
#     # TCPIP0::192.168.0.1::2268::SOCKET 
#     # TCPIP0::192.168.0.1::2268::INSTR
#     parts = address.split('::')
#     ip_address, port = parts[1], parts[2] # 192.168.0.1 / 2268
#     print(ip_address, port)
#     return ip_address, port

def setup_tcpip_socket(instrument):#, ip_address, port):
    print('setup_tcpip_socket')
    # TERMCHAR
    instrument.set_visa_attribute(constants.VI_ATTR_TERMCHAR_EN, constants.VI_TRUE)
    instrument.set_visa_attribute(constants.VI_ATTR_TERMCHAR, 10)  # \n = 10(ASCII) = 0XA(HEX)
    print('socket instrument setup TERMCHAR already')
    # END ON READ
    instrument.set_visa_attribute(constants.VI_ATTR_SUPPRESS_END_EN, constants.VI_TRUE)
    print('socket instrument setup END ON READ already')
    # ip_address/port
    # instrument.set_visa_attribute(constants.VI_ATTR_TCPIP_ADDR, ip_address)
    # instrument.set_visa_attribute(constants.VI_ATTR_TCPIP_PORT, int(port))

# def setup_tcpip_instrument(instrument, ip_address, port): 
#     # ip_address/port/device name
#     instrument.set_visa_attribute(constants.VI_ATTR_TCPIP_ADDR, ip_address)
#     instrument.set_visa_attribute(constants.VI_ATTR_TCPIP_PORT, int(port))
#     # instrument.set_visa_attribute(constants.VI_ATTR_TCPIP_DEVICE_NAME, device_name)
