from src.constituent.constituent import * 
from src.dependency.dependency import *
import copy
import argparse
import time

def do_encode(t, f, e, pi, po, g, lg):
    if t:
        start_time=time.time()

    n_trees=0
    if f == "const":
        if e not in ["abs","rel","dyn"]:
            print("[*] Error: Encoding not alowed for selected formalism")
            exit(1)
        
        if e=="abs":
            encoder = constituent_encoder(c_absolute_encoder())
        if e=="rel":
            encoder = constituent_encoder(c_relative_encoder())
        if e=="dyn":
            encoder = constituent_encoder(c_dynamic_encoder())
        
        n_trees=linearize_constituent(pi, po, encoder)
    
    elif f =="deps":
        if e not in ["abs","rel","pos","brk","brkd","brk2pg","brk2pp","brk2pgd","brk2ppd"]:
            print("[*] Error: Encoding not alowed for selected formalism")
            exit(1)

        if e=="abs":
            encoder = dependency_encoder(d_absolute_encoder())
        if e=="rel":
            encoder = dependency_encoder(d_absolute_encoder())
        if e=="pos":
            encoder = dependency_encoder(d_pos_encoder())
        if e=="brk":
            encoder = dependency_encoder(d_brk_encoder(False))
        if e=="brkd":
            encoder = dependency_encoder(d_brk_encoder(True))
        if e=="brk2pg":
            encoder = dependency_encoder(d_brk_2p_encoder(D_2P_GREED, False))
        if e=="brk2pgd":
            encoder = dependency_encoder(d_brk_2p_encoder(D_2P_GREED, True))
        if e=="brk2pp":
            encoder = dependency_encoder(d_brk_2p_encoder(D_2P_PROP, False))
        if e=="brk2ppd":
            encoder = dependency_encoder(d_brk_2p_encoder(D_2P_PROP, True))

        n_trees=linearize_dependencies(pi, po, encoder, g, lg)

    
    if t:
        delta_time=time.time()-start_time
        t_str="{:.2f}".format(delta_time)
        print("[*] FILE:",pi,"|| ENC:",f,"/",e,"|| T:",t_str,"|| NT",n_trees,"|| T/S",n_trees/delta_time)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Transform constituent trees or dependency trees into labels')
    parser.add_argument("--time", action='store_true', required=False, 
                        help='measure encoding/decoding time')
    
    parser.add_argument('--form', metavar='formalism', type=str, choices=["const","deps"], required=True,
                        help='formalism used in the sentence')
    
    parser.add_argument('--enc', metavar='encoding type', type=str, choices=["abs","rel","dyn","pos","brk","brkd","brk2pg","brk2pp",
                        "brk2pgd","brk2ppd"], required=True, help='encoding type for the encoding')
    
    parser.add_argument('--gold', action='store_true', required=False, default=True,
                        help='use gold pos_tags instead of predicting them')
                    
    parser.add_argument('--lang', metavar='prediction lang', type=str, required=False, default=None,
                        help='language of the model used in the pos_tag prediction')

    parser.add_argument('--input', metavar='in file', type=str, required=True,
                        help='path of the file to encode (treebank or conllu)')
    
    parser.add_argument('--output', metavar='out file', type=str,  required=True,
                        help='path of the file save encoded labels')

    args = parser.parse_args()
    do_encode(args.time, args.form, args.enc, args.input, args.output, args.gold, args.lang)

