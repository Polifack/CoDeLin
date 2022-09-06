from encs.dependency import encode_dependencies, decode_dependencies
from encs.constituent import encode_constituent, decode_constituent
from utils.constants import *

import argparse
import time

if __name__=="__main__":

    encodings = [C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING, 
                D_ABSOLUTE_ENCODING, D_RELATIVE_ENCODING, D_POS_ENCODING, D_BRACKET_ENCODING, D_BRACKET_ENCODING_2P]

    parser = argparse.ArgumentParser(description='Constituent and Dependencies Linearization System')
    parser.add_argument('formalism', metavar='formalism', type=str, choices=[F_CONSTITUENT, F_DEPENDENCY],
                        help='Grammar used for the the parse tree. Currently Constituent and Dependency Grammars are supported.')
    
    parser.add_argument('operation', metavar='op',type=str, choices=[OP_DEC, OP_ENC],
                        help='Operation mode of the system. Can Encode Bracketed Treebanks / Conll Treebanks into Labels or decode Labels back into Treebanks')

    parser.add_argument('enc', metavar='encoding type', type=str, choices=encodings, 
                        help='Encoding type for the decodification. Note that it must be the same used in encoding.')

    parser.add_argument('input', metavar='in file', type=str,
                        help='Path of the file to decode (.labels file).')

    parser.add_argument('output', metavar='out file', type=str,
                        help='Path of the file save decoded tree.')

    parser.add_argument("--time", action='store_true', required=False, 
                        help='Flag to measure decoding time.')

    parser.add_argument('--sep', metavar='labels separator', type=str, default='_',
                        required=False, help='Separator for the fields in the label')
    
    parser.add_argument('--ujoiner', metavar='unary chain jointer', type=str, default="+",
                    required=False, help='Character used to join Unary Chains.')

    parser.add_argument('--feats',metavar="features", nargs='+', default=None,
                        help='ENCODE ONLY: Set of additional features to add to the labels file', required=False)

    parser.add_argument('--disp', action='store_true', required=False, default=False,
                        help='DEPENDENCY GRAMMARS ONLY: Use displacement on bracket encoding. (Dependency Bracket Encoding Exclusive)')
    
    parser.add_argument('--planar', metavar='planar_alg', type=str, choices=['GREED','PROPAGATE'],
                        default=D_2P_GREED, required=False, 
                        help='ENCODE DEPENDENCY GRAMMARS ONLY: Planar separation algorithm. (Dependency Bracket 2Planar Encoding Exclusive)')

    parser.add_argument('--rsingle', action='store_true', required=False, default=False,
                        help='DECODE DEPENDENCY GRAMMARS ONLY: Postprocess the decoded tree to have only one root.')

    parser.add_argument('--rsearch', metavar='root search strategy', type=str, default=D_ROOT_HEAD,
                        choices=[D_ROOT_HEAD, D_ROOT_REL], required=False, 
                        help='DECODE DEPENDENCY GRAMMARS ONLY: Search for root Strategy when no root found.')

    parser.add_argument('--conflict', choices = [C_STRAT_FIRST, C_STRAT_LAST, C_STRAT_MAX, C_STRAT_NONE], required = False, default=C_STRAT_MAX,
                        help='DECODE CONSTITUENT GRAMMARS ONLY: Method of conflict resolution for conflicting tree node labels.')
    
    parser.add_argument('--nulls', required = False, action='store_true', default=False, 
                        help='DECODE CONSTITUENT GRAMMARS ONLY: Allow null nodes in the decoded tree.')

    parser.add_argument('--postags', required = False, action='store_true', default = False, 
                        help = 'Predict Part of Speech tags using Stanza tagger')
    
    parser.add_argument('--lang', required=False, type=str, default='en', 
                        help = 'Language employed in part of speech predition')

    args = parser.parse_args()

    if args.time:
        start_time=time.time()

    if args.formalism == F_CONSTITUENT:
        
        if args.operation == OP_ENC:
            n_labels, n_trees, n_diff_labels = encode_constituent(args.input, args.output, args.enc, args.sep, args.ujoiner, args.feats)
        
        elif args.operation == OP_DEC:
            n_trees, n_labels = decode_constituent(args.input, args.output, args.enc, args.sep, args.ujoiner, args.conflict, args.nulls)
    
    elif args.formalism == F_DEPENDENCY:
        
        if args.operation == OP_ENC:
            n_trees, n_labels, n_diff_labels = encode_dependencies(args.input, args.output, args.sep, args.enc, args.disp, args.planar, args.feats)
        
        elif args.operation == OP_DEC:
            n_trees, n_labels = decode_dependencies(args.input, args.output, args.sep, args.enc, args.disp, args.planar, args.rsingle, args.rsearch, args.postags, args.lang)



    if args.time:
        delta_time=time.time()-start_time
        fn_str=args.input.split("/")[-1]
        t_str="{:.2f}".format(delta_time)
        ts_str="{:2f}".format(delta_time/n_trees)
        ls_str="{:2f}".format(delta_time/n_labels)


        print("-----------------------------------------")
        print(fn_str+'@'+args.enc+':')
        print("-----------------------------------------")
        print('%10s' % ('encoded trees'),n_trees)
        print('%10s' % ('total labels'),n_labels)
        if n_diff_labels is not None:
            print('%10s' % ('unique labels'),n_diff_labels)
        print('%10s' % ('time per label'),ls_str)
        print('%10s' % ('time per tree'),ts_str)
        print('%10s' % ('total time'),t_str)
        print("-----------------------------------------")
