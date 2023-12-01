import os
from codelin.models.deps_tree import D_Tree

treebank_path = "/home/poli/Treebanks/20ag"
fix_projectivity = True

for lang in os.listdir(treebank_path):
    current_path = os.path.join(treebank_path, lang)
    for file in os.listdir(current_path):
        try:
            #print(os.path.join(current_path,file))
            # output file check
            if not 'output' in file:
                continue
            # encoding check
            if "Hexatag" not in file:
                continue
            
            # extension check
            if not file.endswith(".labels"):
                continue
            
            file = os.path.join(current_path, file)
            file_out = file.replace(".labels", ".conllu")

            cmd = "python main.py DEPS DEC 6TG "+file+" "+file_out+" --multitask --sep [_] --time --count_heur"
            print(cmd)
            exit_code = os.system(cmd)
            if exit_code != 0:
                print("ERROR: ", cmd)
                exit(1)
        except Exception as e:
            print(e)

    # # file_evalb_out = file_out.replace(".trees", ".evalb")
    # cmd = "python evalud/evalud.py "+file_out+" "+file_test
    # print(cmd)
    # exit_code = os.system(cmd)
    # print("Exit code:", exit_code)

    # # run command and take output text
    # output = os.popen(cmd).read()
    # # search for the Bracketing FMeasure = xxxx line
    # fmeasure = output.split("Bracketing FMeasure")[1].split("=")[1].split()[0]


    # print("FMeasure:", fmeasure)
    #break