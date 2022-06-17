from src.models.constituent import * 
import copy
import argparse
import time


#  Python script to encode CONSTITUENT TREEBANKS into LABELS

parser = argparse.ArgumentParser(description='Transform constituent trees into labels')

parser.add_argument('enc', type=str, choices=["ABS","REL","DYN"], 
                    help='Encoding type')

parser.add_argument('input', metavar='in_file', type=str,
                    help='path of the file to encode (treebank or conllu)')

parser.add_argument('output', metavar='out_file', type=str,
                    help='path of the file save encoded labels')

parser.add_argument("--time", action='store_true', required=False, 
                    help='Measure encoding/decoding time')

parser.add_argument('--sep', metavar='separator', type=str, default="_",
                    required=False, help='Separator for the fields in the label')

parser.add_argument('--ujoiner', metavar='unary chain joiner', type=str, default="+",
                    required=False, help='Character used to join Unary Chains.')

parser.add_argument('--postags', action='store_true', required=False, default=False,
                    help='predict postags instead of using gold anotations')
                
parser.add_argument('--lang', metavar='predict_lang', type=str, required=False, default=None,
                    help='language of the model used in the pos_tag prediction')

parser.add_argument('--feats',metavar="features", nargs='+', default=None,
                    help='additional features in constituent tree', required=False)


args = parser.parse_args()

if args.postags and not args.lang:
    print("[*] Error: If postags prediction is enabled a language should be specified using --lang")
    exit(1)

if args.time:
    start_time=time.time()

n_trees, n_labels = encode_constituent(args.input, args.output, args.enc, args.sep, args.ujoiner, args.feats)

if args.time:
    delta_time=time.time()-start_time
    fn_str=args.input.split("/")[-1]
    t_str="{:.2f}".format(delta_time)
    ts_str="{:2f}".format(n_trees/delta_time)
    ls_str="{:2f}".format(n_labels/delta_time)


    print("[*] FILE:",fn_str,"\t|| ENC: CONST/"+args.enc,"\t|| T:",t_str,"\t|| NT",n_trees,"\t|| T/S",ts_str,"\t|| L/S",ls_str)

