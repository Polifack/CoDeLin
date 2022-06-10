from stanza.models.constituency.parse_tree import Tree
from stanza.models.constituency.tree_reader import read_trees, read_tree_file
import argparse
import re



class constituent_cleaner:
    def __init__(self, delim):
        self.delim=delim
    
    def clean_postag(self, p):
        regex=str(f'{self.delim}.*?{self.delim}')
        p.label = re.sub(regex, '', p.label)

    def clean_file(self, in_path, out_path):
        trees=read_tree_file(in_path)
        f_out=open(out_path,"w+")

        for tree in trees:
            current_words=[]
            current_postags=[]
            
            tree.visit_preorder(leaf=lambda l:current_words.append(l),
                                preterminal=self.clean_postag)
            f_out.write(str(tree))

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Preprocess constituent trees in a .trees or .ptb treebank')

    parser.add_argument('--delim', metavar='delimiter', type=str, default="##",
                        required=False, help='Separator for the fields to remove')

    parser.add_argument('--extract', action='store_true', required=False, default=False,
                        help='Extract the postags from the file')
    
    parser.add_argument('--predict', action='store_true', required=False, default=False,
                        help='Predict new postags for the selected file')

    parser.add_argument('input', metavar='in file', type=str,
                        help='Path of the file to clean (.trees file).')
    
    parser.add_argument('output', metavar='out file', type=str,
                        help='Path of the clean file (.trees file).')

    args = parser.parse_args()
    c=constituent_cleaner(args.delim)
    c.clean_file(args.input, args.output)
