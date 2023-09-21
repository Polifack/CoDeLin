import os

treebank_path = "/home/poli/Treebanks/"
labels_path = "/home/poli/labels"

for file in os.listdir(labels_path):
    if "GERMAN" not in file:
         continue
    if "Relative" not in file:
        continue
    
    # remove all .trees and .evalb files
    if file.endswith(".trees") or file.endswith(".eval"):
        os.remove(os.path.join(labels_path, file))
    
    if not file.endswith(".labels"):
        continue
    lang = file.split("-")[0]
    encoding = file.split("-")[-1].split(".")[0]

    is_bin = "_bin_" in encoding
    bin_type = "_R" in encoding
    is_incr = "incr" in encoding
    
    encoding = encoding.split("_")[0]

    l_treebank = os.path.join(treebank_path, lang)
    file_test = os.path.join(l_treebank, "test.trees")
    file_labels = os.path.join(labels_path, file)
    file_out = file_labels.replace(".labels", ".trees")
    
    treebank = file_test.split("/")[-2]
    print(treebank, "=>", encoding, "bin:", is_bin, "incr:", is_incr, "bin_type:", bin_type)
    
    enc_cmd = ""
    if "NaiveAbsolute" in encoding:
        enc_cmd = "ABS"
    elif "NaiveRelative" in encoding:
        enc_cmd = "REL"
    elif "NaiveDynamic" in encoding:
        enc_cmd = "DYN"
    elif "Gaps" in encoding:
        enc_cmd = "GAP"
    elif "Tetra" in encoding:
        enc_cmd = "4EC"
    elif "Juxtaposed" in encoding:
        enc_cmd = "JUX"

    cmd = "python main.py CONST DEC "+enc_cmd+" "+file_labels+" "+file_out+" --multitask --sep [_] --ujoiner [+] --b_marker [*] "\
            +("--incremental " if is_incr else " ")\
            +("--binary "if is_bin else " ")\
            +("--b_direction R " if is_bin and bin_type=="_R" else "")\
            +("--b_direction L " if is_bin and bin_type=="_R" else "")

    # print(cmd)
    # if cmd fails, exit
    exit_code = os.system(cmd)
    if exit_code != 0:
        print("ERROR: ", cmd)
        exit(1)

    file_evalb_out = file_out.replace(".trees", ".evalb")
    cmd = "evalb/evalb -p evalb/COLLINS.prm "+file_test+" "+file_out
    # print(cmd)

    # run command and take output text
    output = os.popen(cmd).read()
    # search for the Bracketing FMeasure = xxxx line
    fmeasure = output.split("Bracketing FMeasure")[1].split("=")[1].split()[0]


    print("FMeasure:", fmeasure)
