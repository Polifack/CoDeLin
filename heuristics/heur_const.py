from utils.constants import C_CONFLICT_SEPARATOR, C_STRAT_MAX, C_STRAT_FIRST, C_STRAT_LAST, C_NONE_LABEL
from stanza.models.constituency.parse_tree import Tree

def check_conflicts(node, conflict_strat):
    '''
    Fixes conflicts in the naming of a given node according
    to a designed strategy.
    '''
    if C_CONFLICT_SEPARATOR in node.label:
        labels=node.label.split(C_CONFLICT_SEPARATOR)
        if conflict_strat == C_STRAT_MAX:
            node.label=max(set(labels), key=labels.count)
        if conflict_strat == C_STRAT_FIRST:
            node.label=labels[0]
        if conflict_strat == C_STRAT_LAST:
            node.label=labels[len(labels)-1]
        
def clean_nulls_child(tree, tree_children, child):
    '''
    Removes NULL intermediate nodes 
    '''
    if child.label == C_NONE_LABEL:
        new_children = []
        none_child_idx = tree_children.index(child)
        # append children to the "left"
        for i in range(0, none_child_idx):
            new_children.append(tree_children[i])

        # foreach of the children of the node that has a null label
        # append them to the parent
        for nc in child.children:
            new_children.append(Tree(nc.label, nc.children))

        # append children to the "right"
        for j in range(none_child_idx+1, len(tree_children)):
            new_children.append(tree_children[j])

        tree.children=tuple(new_children)  
        
def postprocess_tree_child(tree, conflicts, nulls):
    for c in tree.children:
        if type(c) is Tree:
            postprocess_tree_child(c, conflicts, nulls)
        check_conflicts(c, conflicts)
        if nulls:
            clean_nulls_child(tree, tree.children, c)

    check_conflicts(tree, conflicts)
def postprocess_tree(tree, conflicts, nulls):
    '''
    Apply heuristics to the reconstructed Constituent Trees
    in order to ensure correctness
    '''
    # Clean Null Roots
    if (nulls):
        while len(tree.children)==1 and tree.label==C_NONE_LABEL:
            tree = tree.children[0]
    
    # Postprocess Childs
    postprocess_tree_child(tree, conflicts, nulls)

    return tree

