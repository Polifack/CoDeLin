from src.constituent.constituent import * 
from src.dependency.dependency import *
import copy
import argparse
import time

def do_encode(t, formalism, encoding, pi, po, planar, disp, no_gold, lang):
    if t:
        start_time=time.time()

    ## encode
    n_trees=0
    if formalism == "CONST":
        if encoding not in ["ABS","REL","DYN"]:
            print("[*] Error: Encoding not alowed for selected formalism.")
            exit(1)

        n_trees=encode_constituent(pi, po, encoding)
    
    elif formalism =="DEPS":
        if encoding not in ["ABS","REL","POS","BRK","BRK_2P"]:
            print("[*] Error: Encoding not alowed for selected formalism.")
            exit(1)

        if no_gold == True and lang == None:
            print("[*] Error: If not using gold POSTAGS ust specify a language for the predictions.")
        
        n_trees=encode_dependencies(pi, po, encoding,disp,planar,no_gold,lang)
    ##

    if t:
        delta_time=time.time()-start_time
        t_str="{:.2f}".format(delta_time)
        e_str = encoding + ("_DISP" if disp!=None else "") + ("_"+planar if planar!=None else "")
        print("[*] FILE:",pi,"|| ENC:",formalism,"/",e_str,"|| T:",t_str,"|| NT",n_trees,"|| T/S",n_trees/delta_time)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Transform constituent trees or dependency trees into labels')
    parser.add_argument("--time", action='store_true', required=False, 
                        help='measure encoding/decoding time')
    
    parser.add_argument('--form', metavar='formalism', type=str, choices=["CONST","DEPS"], required=True,
                        help='formalism used in the sentence')
    
    parser.add_argument('--enc', metavar='encoding_type', type=str, choices=["ABS","REL","DYN","POS","BRK","BRK_2P"], 
                        required=True, help='encoding type for the encoding')

    parser.add_argument('--disp', action='store_true', required=False, default=None,
                        help='use displacement on bracket encoding')
    
    parser.add_argument('--planar', metavar='planar_alg', type=str, choices=['GREED','PROPAGATE'],
                        default=None, required=False, help='planar separation algorithm (only BRK_2P)')

    parser.add_argument('--nogold', action='store_true', required=False, default=False,
                        help='predict postags instead of using gold anotations')
                    
    parser.add_argument('--lang', metavar='predict_lang', type=str, required=False, default=None,
                        help='language of the model used in the pos_tag prediction')

    parser.add_argument('input', metavar='in_file', type=str,
                        help='path of the file to encode (treebank or conllu)')
    
    parser.add_argument('output', metavar='out_file', type=str,
                        help='path of the file save encoded labels')

    args = parser.parse_args()
    do_encode(args.time, args.form, args.enc, args.input, args.output, args.planar, args.disp, args.nogold, args.lang)

