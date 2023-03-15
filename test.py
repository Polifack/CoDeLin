import os
import subprocess
import re

from src.utils.constants import *
from src.encs.dependency import *
from src.encs.constituent import *

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def system_call(command):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    return str(p.stdout.read())

f_spmrl = "./test/spmrl"
f_ptb   = "./test/ptb"
f_gsd   = "./test/gsd"
f_ewt   = "./test/ewt"

d_encs = [D_ABSOLUTE_ENCODING, D_RELATIVE_ENCODING, D_POS_ENCODING, D_BRACKET_ENCODING, D_BRACKET_ENCODING_2P]
d_planalg = [D_2P_GREED, D_2P_PROP]
forbidden_strings = [C_CONFLICT_SEPARATOR, C_NONE_LABEL, D_POSROOT, D_NULLHEAD]
c_encs = [C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING]


print("["+bcolors.WARNING+"-->"+bcolors.ENDC+"] Testing encoding and decoding gives the same file...")
# Evaluation for English-EWT
for enc in d_encs:
    encode_dependencies(in_path = f_ewt+".conllu", out_path = f_ewt+"."+enc+".labels", 
                        encoding_type = enc, separator = "_", displacement = False, 
                        planar_alg = D_2P_GREED, root_enc = True, features = None)
    
    decode_dependencies(in_path = f_ewt+"."+enc+".labels", out_path = f_ewt+"."+enc+".decoded.conllu",
                        encoding_type = enc, separator = "_", displacement = False,
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = True, 
                        postags = False, lang = "en")
    
    answ = system_call("python ./evalud/eval.py "+f_ewt+".conllu "+f_ewt+"."+enc+".decoded.conllu")
    las = re.findall(r'\d+', answ)[1]
    las = bcolors.OKGREEN+las+bcolors.ENDC if int(las) == 100 else bcolors.FAIL+las+bcolors.ENDC

    print("["+las+"] EvalUD for "+f_gsd+"."+enc+".decoded.conllu")

    os.remove(f_ewt+"."+enc+".labels")
    os.remove(f_ewt+"."+enc+".decoded.conllu")

# Evaluation for English-EWT with 2-planar
for palg in d_planalg:
    encode_dependencies(in_path = f_ewt+".conllu", out_path = f_ewt+"."+palg+".labels", 
                        encoding_type = D_BRACKET_ENCODING_2P, separator = "_", displacement = False, 
                        planar_alg = palg, root_enc = True, features = None)
    
    decode_dependencies(in_path = f_ewt+"."+palg+".labels", out_path = f_ewt+"."+palg+".decoded.conllu",
                        encoding_type = D_BRACKET_ENCODING_2P, separator = "_", displacement = False,
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = True, 
                        postags = False, lang = "en")
    
    answ = system_call("python ./evalud/eval.py "+f_ewt+".conllu "+f_ewt+"."+palg+".decoded.conllu")
    las = re.findall(r'\d+', answ)[1]
    las = bcolors.OKGREEN+las+bcolors.ENDC if int(las) == 100 else bcolors.FAIL+las+bcolors.ENDC

    print("["+las+"] EvalUD for "+f_gsd+"."+enc+".decoded.conllu")
    
    os.remove(f_ewt+"."+palg+".labels")
    os.remove(f_ewt+"."+palg+".decoded.conllu")

# Evaluation for English-EWT with additional features:
for enc in d_encs:
    features = ["Case", "Number", "Mood"]
    encode_dependencies(in_path = f_gsd+".conllu", out_path = f_gsd+"."+enc+".labels", 
                        encoding_type = enc, separator = "_", displacement = False, 
                        planar_alg = D_2P_GREED, root_enc = True, features = features)
    
    # Check number of columns in labels
    with open(f_gsd+"."+enc+".labels") as f:
        for line in f:
            if line=="\n":
                continue
            if len(line.split("\t")) != 4 + len(features):
                print("[!] Error: "+f_gsd+"."+enc+".labels has not the expected number of columns: ")
                print("    Expected: "+str(4 + len(features)))
                print("    Found: "+str(len(line.split("\t"))))
                break

    decode_dependencies(in_path = f_gsd+"."+enc+".labels", out_path = f_gsd+"."+enc+".decoded.conllu",
                        encoding_type = enc, separator = "_", displacement = False,
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = True, 
                        postags = False, lang = "en")
    
    answ = system_call("python ./evalud/eval.py "+f_gsd+".conllu "+f_gsd+"."+enc+".decoded.conllu")
    las = re.findall(r'\d+', answ)[1]
    las = bcolors.OKGREEN+las+bcolors.ENDC if int(las) == 100 else bcolors.FAIL+las+bcolors.ENDC

    print("["+las+"] EvalUD for "+f_gsd+"."+enc+".decoded.conllu")
    os.remove(f_gsd+"."+enc+".labels")
    os.remove(f_gsd+"."+enc+".decoded.conllu")

# Evaluation for Penn Treebank
for enc in c_encs:
    encode_constituent(in_path = f_ptb+".trees", out_path = f_ptb+"."+enc+".labels", 
                        encoding_type = enc, reverse = False,
                        separator = "_", unary_joiner = "++", features = None)
    
    decode_constituent(in_path = f_ptb+"."+enc+".labels", out_path = f_ptb+"."+enc+".decoded.trees",
                        encoding_type = enc, reverse = False, separator = "_", unary_joiner = "++", nulls = True,
                        conflicts = C_STRAT_MAX, postags = False, lang = "en")
    
    answ = system_call("./evalb/evalb "+f_ptb+".trees "+f_ptb+"."+enc+".decoded.trees -p ./evalb/COLLINS.prm")
    fmeasure = re.findall(r'\d+\.\d+', answ)[1]
    fmeasure = fmeasure.split(".")[0]
    fmeasure = bcolors.OKGREEN+fmeasure+bcolors.ENDC if int(fmeasure) == 100 else bcolors.FAIL+fmeasure+bcolors.ENDC
    print("["+fmeasure+"] EvalB for "+f_ptb+"."+enc+".decoded.trees")
    os.remove(f_ptb+"."+enc+".labels")
    os.remove(f_ptb+"."+enc+".decoded.trees")

# Evaluation for Penn Treebank Reversed
for enc in c_encs:
    encode_constituent(in_path = f_ptb+".trees", out_path = f_ptb+"."+enc+".labels", 
                        encoding_type = enc, reverse = True,
                        separator = "_", unary_joiner = "++", features = None)
    
    decode_constituent(in_path = f_ptb+"."+enc+".labels", out_path = f_ptb+"."+enc+".decoded.trees",
                        encoding_type = enc, reverse = True, separator = "_", unary_joiner = "++", nulls = True,
                        conflicts = C_STRAT_MAX, postags = False, lang = "en")
    
    answ = system_call("./evalb/evalb "+f_ptb+".trees "+f_ptb+"."+enc+".decoded.trees -p ./evalb/COLLINS.prm")
    fmeasure = re.findall(r'\d+\.\d+', answ)[1]
    fmeasure = fmeasure.split(".")[0]
    fmeasure = bcolors.OKGREEN+fmeasure+bcolors.ENDC if int(fmeasure) == 100 else bcolors.FAIL+fmeasure+bcolors.ENDC
    print("["+fmeasure+"] EvalB for "+f_ptb+"."+enc+".decoded.trees")
    os.remove(f_ptb+"."+enc+".labels")
    os.remove(f_ptb+"."+enc+".decoded.trees")

# Evaluation for German SPMRL
for enc in c_encs:
    feats = ["lem", "case", "number", "gender"]
    encode_constituent(in_path = f_spmrl+".trees", out_path = f_spmrl+"."+enc+".labels",
                        encoding_type = enc, reverse = False,
                        separator = "_", unary_joiner = "++", features = feats)
    
    # Check number of columns in labels
    with open(f_spmrl+"."+enc+".labels") as f:
        for line in f:
            if line=="\n":
                continue
            if len(line.split("\t")) != 5 + len(features):
                print("[!] Error: "+f_spmrl+"."+enc+".labels has not the expected number of columns: ")
                print("    Expected: "+str(5 + len(features)))
                print("    Found: "+str(len(line.split("\t"))))
                break
    
    decode_constituent(in_path = f_spmrl+"."+enc+".labels", out_path = f_spmrl+"."+enc+".decoded.trees",
                        encoding_type = enc, reverse = False, separator = "_", unary_joiner = "++", nulls = True,
                        conflicts=C_STRAT_MAX, postags = False, lang = "en")
    

    answ = system_call("./evalb/evalb "+f_spmrl+".trees "+f_spmrl+"."+enc+".decoded.trees -p ./evalb/COLLINS.prm")
    fmeasure = re.findall(r'\d+\.\d+', answ)[1]
    fmeasure = fmeasure.split(".")[0]
    fmeasure = bcolors.OKGREEN+fmeasure+bcolors.ENDC if int(fmeasure) == 100 else bcolors.FAIL+fmeasure+bcolors.ENDC
    print("["+fmeasure+"] EvalB for "+f_spmrl+"."+enc+".decoded.trees")
    
    os.remove(f_spmrl+"."+enc+".labels")
    os.remove(f_spmrl+"."+enc+".decoded.trees")

# Evaluation of tree binarizer
print("["+bcolors.WARNING+"-->"+bcolors.ENDC+"] Testing Binarization and de-binarization of constituent trees...")
for enc in c_encs:
    pred_const = "./test/pred.const."+enc+".labels"
    pred_const_dec = "./test/pred.const."+enc+".decoded.trees"

    decode_constituent(in_path = pred_const, out_path = pred_const_dec,
                        encoding_type = enc,reverse = False,separator = "_", unary_joiner = "+", nulls = True,
                        conflicts = C_STRAT_MAX, postags = False, lang = "en")

    for line in open(pred_const_dec):
        line = line.rstrip()
        ct = C_Tree.from_string(line)
        bt = C_Tree.to_binary_right(ct)
        dt = C_Tree.restore_from_binary(bt)
        assert ct == dt
        bt = C_Tree.to_binary_left(ct)
        dt = C_Tree.restore_from_binary(bt)
    os.remove(pred_const_dec)

# Evaluation for predicted dependencies labels file
print("["+bcolors.WARNING+"-->"+bcolors.ENDC+"] Testing decoding of predicted dependency labels file (oob heads and cycles)...")
for enc in d_encs:
    pred_deps = "./test/pred.deps."+enc+".labels"
    pred_deps_dec = "./test/pred.deps."+enc+".decoded.trees"

    decode_dependencies(in_path = pred_deps, out_path = pred_deps_dec, encoding_type = enc, 
                        separator = "_", multiroot = False, root_search = D_ROOT_HEAD, 
                        displacement = False, root_enc = True,  postags = False, lang = "en")

    dependency_trees = D_Tree.read_conllu_file(pred_deps_dec)
    for tree in dependency_trees:
        # remove root node
        tree.remove_dummy()
        
        # check oob heads
        for node in tree.nodes:
            if node.head > len(tree.nodes):
                print("[!] Error: oob head found in dependency decoded file: "+pred_deps_dec)
                break
        
        # check cycles
        tree_root = tree.root_search(D_ROOT_HEAD)
        for node in tree.nodes:
            visited = []    
            while (node.id != tree_root) and (node.head !=D_NULLHEAD):
                if node in visited:
                    print("[!] Error: cycle found in dependency decoded file: "+pred_deps_dec)
                    print("=>",node)
                    print("=>",visited)
                    print(tree)
                    exit(1)
                else:
                    visited.append(node)
                    next_node = min(max(node.head-1, 0), len(tree.nodes)-1)
                    node = tree.nodes[next_node]

    for line in open(pred_deps_dec):
        if any(x in line for x in forbidden_strings):
            print("[!] Error: forbidden string found in dependency decoded file: "+pred_deps_dec)
            print(line)
            break
    os.remove(pred_deps_dec)

# Evaluation for predicted constituent labels file
print("["+bcolors.WARNING+"-->"+bcolors.ENDC+"] Testing decoding of predicted constituent labels file (nulls and conflicts)...")
for enc in c_encs:
    pred_const = "./test/pred.const."+enc+".labels"
    pred_const_dec = "./test/pred.const."+enc+".decoded.trees"

    decode_constituent(in_path = pred_const, out_path = pred_const_dec,
                        encoding_type = enc, reverse = False, separator = "_", unary_joiner = "+", nulls = True,
                        conflicts = C_STRAT_MAX, postags = False, lang = "en")

    for line in open(pred_const_dec):
        if any(x in line for x in forbidden_strings):
            print("[!] Error: forbidden string found in constituent decoded file: "+pred_const_dec)
            print(line)
            break
    os.remove(pred_const_dec)


print("Done!")