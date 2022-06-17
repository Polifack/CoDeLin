import nltk
import argparse

def pt(s):
    nltk.Tree.fromstring(s).pretty_print()

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Prints constituent tree in a file')
    parser.add_argument('input', metavar='in_file', type=str,
                        help='path of the file to encode (treebank or conllu)')
    args=parser.parse_args()
    for line in open(args.input):
        print(line)
        pt(line)