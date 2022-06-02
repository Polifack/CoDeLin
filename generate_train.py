import argparse
import os

## auxiliar script for generating ncrf_configs 

def run_encoding_script(form, enc, files_to_encode, outlbl, outmodel, default_cfg):
    print("[*] Running for encoding",enc)

    if not os.path.exists(args.outcfg):
        os.mkdir(args.outcfg)
    
    if not os.path.exists(outlbl+"_"+enc):
        os.mkdir(args.outlbl+"_"+enc)

    out_lbl_train=outlbl+"_"+enc+"/train.labels"
    out_lbl_dev=outlbl+"_"+enc+"/dev.labels"
    out_lbl_test=outlbl+"_"+enc+"/test.labels"
    
    output_labels = [out_lbl_train, out_lbl_dev, out_lbl_test]
    output_cfg =  args.outcfg+"/"+enc+"_train.config"

    for file_in, file_out in zip(files_to_encode,output_labels):
        # for bracketing encoding use displacement/not use it
        if enc == "BRK":
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --input "+file_in+" --output "+file_out)
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --disp --input "+file_in+" --output "+file_out)
        # for bracketing 2-planar encoding use both algorithms with and without displacement
        if enc == "BRK_2P":        
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --planar GREED --input "+file_in+" --output "+file_out)
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --planar GREED --disp --input "+file_in+" --output "+file_out)
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --planar PROPAGATE --input "+file_in+" --output "+file_out)
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --planar PROPAGATE --disp --input "+file_in+" --output "+file_out)
        else:
            os.system("python3.8 main.py --time --form "+form+" --enc "+enc+" --input "+file_in+" --output "+file_out)

    f_in = open(default_cfg)
    f_out = open(output_cfg,"w+")
    for line in f_in:
        f_out.write(line)
    
    f_out.write("train_dir="+out_lbl_train+'/n')
    f_out.write("dev_dir="+out_lbl_dev+'/n')
    f_out.write("test_dir="+out_lbl_test+'/n')
    f_out.write("model_dir="+outmodel+"_"+enc+'/n')

    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Lineraizes tree files (dev/train/test) in folders and generates config file')
    parser.add_argument('--indir', metavar='in dir', type=str, required=True,
                        help='path of the directory where the dev/train/test files are')
    
    parser.add_argument('--config', metavar='default config', type=str, required=True,
                        help='default ncrf config file to use')

    parser.add_argument('--form', metavar='formalism', type=str, choices=["const","deps"], required=True,
                        help='formalism used in the sentence')
    
    parser.add_argument('--outlbl', metavar='out lbl dir', type=str,  required=True,
                        help='path of the directory where to save the encoded labels')

    parser.add_argument('--outcfg', metavar='out config', type=str, required=True,
                        help='path of the directory where to save the ncrf config')

    parser.add_argument('--outmodel', metavar='out model', type=str, required=True,
                        help='path of the directory where to save the ncrf model')
    
    args = parser.parse_args()

    print("[*]",args.indir)
    
    trainfile=None
    devfile=None
    testfile=None

    for file in os.listdir(args.indir):
        if "train" in file:
            trainfile=args.indir+"/"+file
        if "dev" in file:
            devfile=args.indir+"/"+file
        if "test" in file:
            testfile=args.indir+"/"+file
    
    if trainfile == None or devfile == None or testfile == None:
        print("[*] Error: missing files")
        exit(1)

    files_to_encode = [trainfile, devfile, testfile]

    # get set of encodings

    if args.form=="CONST":
        encodings = ["REL","ABS","DYN"]
    
    elif args.form=="DEPS":
        encodings = ["ABS","REL","POS","BRK","BRK_2P"]

    # encode
    for encoding in encodings:
        run_encoding_script(args.form, encoding, files_to_encode, args.outlbl, args.outmodel, args.config)
