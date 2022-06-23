import argparse
import os

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Lineraizes tree files (dev/train/test) in folders and generates config file')
    parser.add_argument('--input', metavar='in dir', type=str, required=True,
                        help='Path of the directory where the dev/train/test files are')
    
    parser.add_argument('--tconfig', metavar='default config train', type=str, required=True,
                        help='Default NCRFpp config file for Training Stage')
    
    parser.add_argument('--dconfig', metavar='default config decode', type=str, required=True,
                        help='Default NCRFpp config file for Decoding Stage.')
    
    parser.add_argument('--outlbl', metavar='out lbl dir', type=str,  required=True,
                        help='Directory where to save decoded labels that will be inputed to the NCRFpp')

    parser.add_argument('--outcfg', metavar='out config', type=str, required=True,
                        help='Directory where to save the NCRFpp model.')

    parser.add_argument('--outmodel', metavar='out_model', type=str, required=True,
                        help='Directory where to save the NCRFpp model.')
    
    parser.add_argument('--outdec', metavar='out_pred', type=str, required=True,
                        help='Directory where to save predicted labels during Decoding Stage.')

    parser.add_argument('--sep', metavar='separator', type=str, default="_",
                        required=False, help='Character used to join label fields.')

    parser.add_argument('--ujoiner', metavar='unary chain jointer', type=str, default="+",
                        required=False, help='Character used to join Unary Chains.')

    parser.add_argument('--postags', action='store_true', required=False, default=False,
                        help='predict postags instead of using gold anotations')
                    
    parser.add_argument('--lang', metavar='predict_lang', type=str, required=False, default=None,
                        help='language of the model used in the pos_tag prediction')
    
    parser.add_argument('--feats',metavar="features", nargs='+', default=None,
                        help='additional features in constituent tree', required=False)

    
    args = parser.parse_args()
    
    # Encodings 
    encodings = ["ABS","REL","DYN"]

    # Get input files
    train_trees=args.input+"/train.trees"
    dev_trees=args.input+"/dev.trees"
    test_trees=args.input+"/test.trees"

    files_trees = [train_trees, dev_trees, test_trees]
    
    for enc in encodings:
        outcfg = args.outcfg
        path = ""
        for d in outcfg.split('/'):
        # handle instances of // in string
            if not d: continue 
            path += d + '/'
            if not os.path.isdir(path):
                os.mkdir(path)
                
        outlbl = args.outlbl + "_" + enc
        path = ""
        for d in outlbl.split('/'):
        # handle instances of // in string
            if not d: continue 
            path += d + '/'
            if not os.path.isdir(path):
                os.mkdir(path)

        # Get files for labels output
        labels_train = outlbl+"/train.labels"
        labels_dev = outlbl+"/dev.labels"
        labels_test = outlbl+"/test.labels"
        
        files_label = [labels_train, labels_dev, labels_test]
        
        # Get files for config files
        output_cfg_t =  outcfg+"/"+enc+"_train.config"
        output_cfg_d = outcfg+"/"+enc+"_decode.config"
    

        feats_string = ""
        if args.feats:
            feats_string = " --feats"
            for feat in args.feats:
                feats_string+=" "+feat

        for file_in, file_out in zip(files_trees, files_label):
            cmd=("python3.8 encode_const.py "+enc+" "+file_in+" "+file_out+" --sep "+args.sep+" --ujoiner "+args.ujoiner
                +(" --postags "if args.postags else "")+(" --lang " if args.lang else "")+feats_string)
            print(cmd)
            os.system(cmd)

        f_in = open(args.tconfig)
        f_out = open(output_cfg_t,"w+")
        for line in f_in:
            f_out.write(line)
        
        f_out.write("\ntrain_dir="+labels_train+'\n')
        f_out.write("dev_dir="+labels_dev+'\n')
        f_out.write("test_dir="+labels_test+'\n')
        f_out.write("model_dir="+args.outmodel+"_"+enc+'\n')

        f_in = open(args.dconfig)
        f_out = open(output_cfg_d,"w+")
        for line in f_in:
            f_out.write(line)

        f_out.write("raw_dir="+labels_test+'\n')
        f_out.write("decode_dir="+args.outdec+"_"+enc+'.labels\n')
        f_out.write("dset_dir="+args.outmodel+"_"+enc+".dset\n")
        f_out.write("load_model_dir="+args.outmodel+"_"+enc+".model\n")