from src.constituent.constituent import * 
from src.dependency.dependency import *
import copy
import argparse
import time

def do_encode(t, formalism, encoding, disp, remnulls, pi, po):
    if t:
        start_time=time.time()

    n_trees=0
    if formalism == "CONST":
        if encoding not in ["ABS","REL","DYN"]:
            print("[*] Error: Encoding not alowed for selected formalism")
            exit(1)
        
        n_trees=decode_constituent(pi, po, encoding, remnulls)
    
    elif formalism =="DEPS":
        if encoding not in ["ABS","REL","POS","BRK","BRK_2P"]:
            print("[*] Error: Encoding not alowed for selected formalism")
            exit(1)

        n_trees=decode_dependencies(pi, po, encoding, disp)

    if t:
        delta_time=time.time()-start_time
        t_str="{:.2f}".format(delta_time)
        e_str = encoding + ("_REMNULLS" if remnulls else "")
        print("[*] FILE:",pi,"|| ENC:",formalism,"/",e_str,"|| T:",t_str,"|| NT",n_trees,"|| T/S",n_trees/delta_time)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Transform labels back into constituent/dependency trees')
    parser.add_argument("--time", action='store_true', required=False, 
                        help='Flag to measure decoding time.')
    
    parser.add_argument('--form', metavar='formalism', type=str, choices=["CONST","DEPS"], required=True,
                        help='Formalism used in the sentence. Note that it must be the same used in encoding.')
    
    parser.add_argument('--enc', metavar='encoding type', type=str, choices=["ABS","REL","DYN","POS","BRK","BRK_2P"], 
                        required=True, help='Encoding type for the decodification. Note that it must be the same used in encoding.')

    parser.add_argument('--disp', action='store_true', required=False, default=None,
                        help='Use displacement on bracket encoding.')

    parser.add_argument('--remnulls', action='store_true', required=False, default=None,
                        help='Use displacement on bracket encoding.')

    parser.add_argument('--input', metavar='in file', type=str, required=True,
                        help='Path of the file to decode (.labels file).')
    
    parser.add_argument('--output', metavar='out file', type=str,  required=True,
                        help='Path of the file save decoded tree.')

    args = parser.parse_args()
    do_encode(args.time, args.form, args.enc, args.disp, args.remnulls, args.input, args.output)

