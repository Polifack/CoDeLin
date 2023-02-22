from conllu import parse_tree_incr
from src.models.conll_node import ConllNode
from src.models.constituent_label import ConstituentLabel
from src.utils.constants import C_NO_POSTAG_LABEL, BOS, EOS

def parse_conllu(in_file):
    '''
    Given an input CONLL file parses it and returns the Dependency Trees
    in the form of a list of ConllNodes
    '''
    conll_node_list=[]
    
    for token_tree in parse_tree_incr(in_file):
        nodes = []
        postags = []
        words = []
        
        nodes.append(ConllNode.dummy_root())
        data = token_tree.serialize().split('\n')
        dependency_start_idx = 0
        for line in data:
            if line[0]!="#":
                break
            if "# text" in line:
                sentence = line.split("# text = ")[1]
            dependency_start_idx+=1
        
        data = data[dependency_start_idx:]

        for line in data:
            # check if not valid line
            if (len(line)<=1) or len(line.split('\t'))<10 or line[0] == "#":
                continue
            
            conll_node = ConllNode.from_string(line)
            nodes.append(conll_node)
        
        conll_node_list.append(nodes)
    
    return conll_node_list

def parse_constituent_labels(in_file, separator, ujoiner):
    '''
    Given a input labels file, a label field separator and a unary joiner
    returns a set of linearized constituent trees as a list of ConstituentLabels
    '''

    f_in=open(in_file)
    
    linearized_trees = []
    current_tree = []
    
    for line in f_in:
        # skip empty line
        if len(line)<=1:
            continue

        # Separate the label file into columns
        line_columns = line.split("\t") if ("\t") in line else line.split(" ")
        word = line_columns[0]

        if BOS == word:
            current_tree=[]
            continue
        
        if EOS == word:
            linearized_trees.append(current_tree)
            continue

        if len(line_columns) == 2:
            word, label = line_columns
            postag = C_NO_POSTAG_LABEL
        else:
            word, postag, label = line_columns[0], line_columns[1], line_columns[-1]
        
        # check for bad predictions. hang from root.
        if BOS in label or EOS in label:
            label = "1"+separator+"ROOT"

        current_tree.append([word, postag, ConstituentLabel.from_string(label, separator, ujoiner)])

    return linearized_trees
