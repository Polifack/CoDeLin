import argparse
import os

## auxiliar script for generating ncrf_configs 
def run_encoding_script(enc, sep, files_to_encode, outlbl, outmodel, outdec, default_cfg_t, default_cfg_d, feats, disp=None, planar=None):
    filename_encoding = enc

    # planar algorithm (dependencies brk_2p)
    if planar != None:
        filename_encoding += "_"+planar
    
    # displacement (dependencies brk)
    if disp != None and disp == True:
        filename_encoding += "_D"

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


    feats_string = ""
    if args.feats:
        feats_string = " --feats"
        for feat in args.feats:
            feats_string+=" "+feat
    
    for file_in, file_out in zip(files_to_encode,output_labels):
        cmd=("taskset --cpu-list 1 python3.8 ./encode_deps.py "+enc+" "+file_in+" "+file_out
            + (" --disp " if disp else "")
            + ((" --planar " + planar) if planar else "")
            + (" --sep "+sep+" " if sep else "")
            + feats_string)
        os.system(cmd)

    f_in = open(default_cfg_t)
    f_out = open(output_cfg_t,"w+")
    for line in f_in:
        f_out.write(line)
    
    f_out.write("\ntrain_dir="+out_lbl_train+'\n')
    f_out.write("dev_dir="+out_lbl_dev+'\n')
    f_out.write("test_dir="+out_lbl_test+'\n')
    f_out.write("model_dir="+outmodel+"_"+filename_encoding+'\n')

    f_in = open(default_cfg_d)
    f_out = open(output_cfg_d,"w+")
    for line in f_in:
        f_out.write(line)
    f_out.write("raw_dir="+out_lbl_test+'\n')
    f_out.write("decode_dir="+outdec+"_"+filename_encoding+'.labels\n')
    f_out.write("dset_dir="+outmodel+"_"+filename_encoding+".dset\n")
    f_out.write("load_model_dir="+outmodel+"_"+filename_encoding+".model\n")


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Lineraizes tree files (dev/train/test) in folders and generates config file')
    parser.add_argument('--input', metavar='in dir', type=str, required=True,
                        help='path of the directory where the dev/train/test files are')
    
    parser.add_argument('--tconfig', metavar='default config train', type=str, required=True,
                        help='default ncrf config file to use in train')
    
    parser.add_argument('--dconfig', metavar='default config decode', type=str, required=True,
                        help='default ncrf config file to use in decode')

    parser.add_argument('--outlbl', metavar='out lbl dir', type=str,  required=True,
                        help='path of the directory where to save the encoded labels')

    parser.add_argument('--outcfg', metavar='out config', type=str, required=True,
                        help='path of the directory where to save the ncrf config')

    parser.add_argument('--outmodel', metavar='out model', type=str, required=True,
                        help='path of the directory where to save the ncrf model')
    
    parser.add_argument('--outdec', metavar='out decode', type=str, required=True,
                        help='path of the directory where to save the decoded labels')

    parser.add_argument('--sep', metavar='separator', type=str, required=False, default=None,
                        help='label fields separator')

    parser.add_argument('--feats',metavar="features", nargs='+', default=None,
                        help='additional features in constituent tree', required=False)

    args = parser.parse_args()
    
    trainfile=args.input+'/dev.conllu'
    devfile=args.input+'/test.conllu'
    testfile=args.input+'/train.conllu'

    files_to_encode = [trainfile, devfile, testfile]

    for encoding in ["ABS","REL","POS"]:
        run_encoding_script(encoding, args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats)
        
    run_encoding_script("BRK", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=False)
    run_encoding_script("BRK", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=True)
    run_encoding_script("BRK_2P", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=False, planar="GREED")
    run_encoding_script("BRK_2P", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=True, planar="GREED")
    run_encoding_script("BRK_2P", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=False, planar="PROPAGATE")
    run_encoding_script("BRK_2P", args.sep, files_to_encode, args.outlbl, args.outmodel, args.outdec, args.tconfig, args.dconfig, args.feats, disp=True, planar="PROPAGATE")