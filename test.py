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

d_encs    = [D_ABSOLUTE_ENCODING, D_RELATIVE_ENCODING, D_POS_ENCODING, D_BRACKET_ENCODING, D_BRACKET_ENCODING_2P]
d_planalg = [D_2P_GREED, D_2P_PROP]

c_encs    = [C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_INCREMENTAL_ENCODING, C_DYNAMIC_ENCODING]


# Evaluation for English-EWT
for enc in d_encs:
    encode_dependencies(in_path = f_ewt+".conllu", out_path = f_ewt+"."+enc+".labels", 
                        encoding_type = enc, separator = "_", displacement = False, 
                        planar_alg = D_2P_GREED, root_enc = D_ROOT_HEAD, features = None)
    
    decode_dependencies(in_path = f_ewt+"."+enc+".labels", out_path = f_ewt+"."+enc+".decoded.conllu",
                        encoding_type = enc, separator = "_", displacement = False,
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = D_ROOT_HEAD, 
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
                        planar_alg = palg, root_enc = D_ROOT_HEAD, features = None)
    
    decode_dependencies(in_path = f_ewt+"."+palg+".labels", out_path = f_ewt+"."+palg+".decoded.conllu",
                        encoding_type = D_BRACKET_ENCODING_2P, separator = "_", displacement = False,
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = D_ROOT_HEAD, 
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
                        planar_alg = D_2P_GREED, root_enc = D_ROOT_HEAD, features = features)
    
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
                        multiroot = False, root_search = D_ROOT_HEAD, root_enc = D_ROOT_HEAD, 
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
                        encoding_type = enc, separator = "_", unary_joiner = "++", features = None)
    
    decode_constituent(in_path = f_ptb+"."+enc+".labels", out_path = f_ptb+"."+enc+".decoded.trees",
                        encoding_type = enc, separator = "_", unary_joiner = "++", nulls = True,
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
                        encoding_type = enc, separator = "_", unary_joiner = "++", features = feats)
    
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
                        encoding_type = enc, separator = "_", unary_joiner = "++", nulls = True,
                        conflicts=C_STRAT_MAX, postags = False, lang = "en")
    

    answ = system_call("./evalb/evalb "+f_spmrl+".trees "+f_spmrl+"."+enc+".decoded.trees -p ./evalb/COLLINS.prm")
    fmeasure = re.findall(r'\d+\.\d+', answ)[1]
    fmeasure = fmeasure.split(".")[0]
    fmeasure = bcolors.OKGREEN+fmeasure+bcolors.ENDC if int(fmeasure) == 100 else bcolors.FAIL+fmeasure+bcolors.ENDC
    print("["+fmeasure+"] EvalB for "+f_spmrl+"."+enc+".decoded.trees")
    
    os.remove(f_spmrl+"."+enc+".labels")
    os.remove(f_spmrl+"."+enc+".decoded.trees")



# Evaluation for predicted dependencies labels file



# Evaluation for predicted constituent labels file

forbidden_strings = [C_CONFLICT_SEPARATOR, C_NONE_LABEL, D_POSROOT, D_NULLHEAD]

pred_const_dyn = "./test/pred.const.dyn.labels"
pred_const_dyn_dec = "./test/pred.const.dyn.decoded.trees"

decode_constituent(in_path = pred_const_dyn, out_path = pred_const_dyn_dec,
                    encoding_type = C_DYNAMIC_ENCODING, separator = "_", unary_joiner = "+", nulls = True,
                    conflicts = C_STRAT_MAX, postags = False, lang = "en")

for line in open(pred_const_dyn_dec):
    if any(x in line for x in forbidden_strings):
        print("[!] Error: forbidden string found in decoded file: "+line)
        break
os.remove(pred_const_dyn_dec)


print("Done!")