import sys
import time
import ast

if __name__ == "__main__":
    
    # args = dict(arg.split('=') for arg in sys.argv[2:])
    # wait_msec = int(args.get('WaitmSec', '')) 

    args = sys.argv[2]
    args = ast.literal_eval(args) # list轉字典

    wait_msec = int(args['WaitmSec']) if 'WaitmSec' in args else ''
    wait_sec = wait_msec / 1000
    
    time.sleep(wait_sec)
    
    response = f"Waited for {wait_sec} secs"
    print(response)