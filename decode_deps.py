from src.dependency.dependency import *
import copy
import argparse
import time


#  Python script to decode DEPENDENCY LABELS back into CONLLU format

parser = argparse.ArgumentParser(description='Python script to decode DEPENDENCY LABELS back into CONLLU format')

parser.add_argument('input', metavar='in file', type=str,
                    help='Path of the file to decode (.labels file).')

parser.add_argument('output', metavar='out file', type=str,
                    help='Path of the file save decoded tree.')

parser.add_argument('enc', metavar='encoding type', type=str, choices=["ABS","REL","POS", "BRK", "BRK_2P"], 
                    help='Encoding type for the decodification. Note that it must be the same used in encoding.')

parser.add_argument("--time", action='store_true', required=False, 
                    help='Flag to measure decoding time.')

parser.add_argument('--sep', metavar='labels separator', type=str, default="_",
                    required=False, help='Separator for the fields in the label')

parser.add_argument('--disp', action='store_true', required=False, default=False,
                    help='Use displacement on bracket encoding.')

parser.add_argument('--postags', action='store_true', required=False, default=False,
                    help='Predict the postags using STANZA tagger.')

parser.add_argument('--lang', metavar='postags prediction language', required=False, default=False,
                    help='Language for the prediction of the postags using STANZA tagger')

args = parser.parse_args()

if args.postags and not args.lang:
    print("[*] Error: If postags prediction is enabled a language should be specified using --lang")
    exit(1)

if args.time:
    start_time=time.time()

n_trees,n_labels=decode_dependencies(args.input, args.output, args.sep, args.enc, args.disp, args.postags, args.lang)

if args.time:
    delta_time=time.time()-start_time
    fn_str=args.input.split("/")[-1]
    t_str="{:.2f}".format(delta_time)
    ts_str="{:2f}".format(n_trees/delta_time)
    ls_str="{:2f}".format(n_labels/delta_time)


    print("[*] FILE:",fn_str,"\t|| ENC: CONST/"+args.enc,"\t|| T:",t_str,"\t|| NT",n_trees,"\t|| T/S",ts_str,"\t|| L/S",ls_str)

