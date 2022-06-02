import argparse
import os

## auxiliar script for generating ncrf_configs 
def run_encoding_script(form, enc, files_to_encode, outlbl, outmodel, outdec, default_cfg_t, default_cfg_d, disp=None, planar=None):
    filename_encoding = enc
    if planar != None:
        filename_encoding += "_"+planar
    if disp != None:
        filename_encoding += "_D"
    
    print("[*] Running for encoding",filename_encoding)

    if not os.path.exists(args.outcfg):
        os.mkdir(args.outcfg)
    
    if not os.path.exists(outlbl+"_"+filename_encoding):
        os.mkdir(args.outlbl+"_"+filename_encoding)

    out_lbl_train=outlbl+"_"+filename_encoding+"/train.labels"
    out_lbl_dev=outlbl+"_"+filename_encoding+"/dev.labels"
    out_lbl_test=outlbl+"_"+filename_encoding+"/test.labels"
    
    output_labels = [out_lbl_train, out_lbl_dev, out_lbl_test]
    output_cfg_t =  args.outcfg+"/"+filename_encoding+"_train.config"
    output_cfg_d = args.outcfg+"/"+filename_encoding+"_decode.config"


    for file_in, file_out in zip(files_to_encode,output_labels):        
        os.system("python3.8 encode.py --time --form "+form+" --enc "+enc+
            (" --disp " if disp else "")+((" --planar "+planar) if planar else "")+" --input "+file_in+" --output "+file_out)

    f_in = open(default_cfg_t)
    f_out = open(output_cfg_t,"w+")
    for line in f_in:
        f_out.write(line)
    
    f_out.write("train_dir="+out_lbl_train+'/n')
    f_out.write("dev_dir="+out_lbl_dev+'/n')
    f_out.write("test_dir="+out_lbl_test+'/n')
    f_out.write("model_dir="+outmodel+"_"+filename_encoding+'/n')

    f_in = open(default_cfg_d)
    f_out = open(output_cfg_d,"w+")
    for line in f_in:
        f_out.write(line)
    f_out.write("raw_dir="+out_lbl_test+'/n')
    f_out.write("decode_dir="+outdec+'/n')
    f_out.write("dset_dir="+outmodel+"_"+filename_encoding+".dset/n")
    f_out.write("load_model_dir="+outmodel+"_"+filename_encoding+".model/n")

    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Lineraizes tree files (dev/train/test) in folders and generates config file')
    parser.add_argument('--indir', metavar='in dir', type=str, required=True,
                        help='path of the directory where the dev/train/test files are')
    
    parser.add_argument('--t_config', metavar='default config train', type=str, required=True,
                        help='default ncrf config file to use in train')
    
    parser.add_argument('--d_config', metavar='default config decode', type=str, required=True,
                        help='default ncrf config file to use in decode')

    parser.add_argument('--form', metavar='formalism', type=str, choices=["CONST","DEPS"], required=True,
                        help='formalism used in the sentence')
    
    parser.add_argument('--outlbl', metavar='out lbl dir', type=str,  required=True,
                        help='path of the directory where to save the encoded labels')

    parser.add_argument('--outcfg', metavar='out config', type=str, required=True,
                        help='path of the directory where to save the ncrf config')

    parser.add_argument('--outmodel', metavar='out model', type=str, required=True,
                        help='path of the directory where to save the ncrf model')
    
    parser.add_argument('--outdec', metavar='out decode', type=str, required=True,
                        help='path of the directory where to save the decoded labels')

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
        for encoding in ["REL","ABS","DYN"]:
            run_encoding_script(args.form, encoding, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config)
    
    elif args.form=="DEPS":
        for encoding in ["ABS","REL","POS"]:
            run_encoding_script(args.form, encoding, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config)
        
        run_encoding_script(args.form, "BRK", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=False)
        run_encoding_script(args.form, "BRK", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=True)
        run_encoding_script(args.form, "BRK_2P", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=True,planar="GREED")
        run_encoding_script(args.form, "BRK_2P", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=True,planar="GREED")
        run_encoding_script(args.form, "BRK_2P", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=True,planar="PROPAGATE")
        run_encoding_script(args.form, "BRK_2P", files_to_encode, args.outlbl, args.outmodel, args.outdec, args.t_config, args.d_config, disp=True,planar="PROPAGATE")
        
        

