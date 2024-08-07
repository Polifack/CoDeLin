from codelin.encs.abstract_encoding import ADEncoding
from codelin.models.deps_label import D_Label
from codelin.models.deps_tree import D_Tree
from codelin.encs.constituent import C_Tetratag
from codelin.models.const_tree import C_Tree
from codelin.utils.constants import D_NONE_LABEL, D_2P_GREED, D_2P_PROP, C_NONE_LABEL
from codelin.models.linearized_tree import LinearizedTree

class D_HexatagEncoding(ADEncoding):
    
    def __init__(self, separator:str = "_"):
        super().__init__(separator)

    def __str__(self):
        return "Dependency Hexa-Tags Encoding"

    def encode(self, dep_tree):
        # to encode hexatags we employ tetratagging into a bht converted dependency tree
        # the reltype encoding will be dealt by the unary chain encoding mechanism
        bht_tree = D_Tree.to_bht(dep_tree, include_reltype=True)
        print(bht_tree)
        tagger = C_Tetratag(separator=self.separator, unary_joiner="[+]", mode="inorder", binary_marker="[b]")
        lin_tree = tagger.encode(bht_tree)

        # resort the words of the linearized tree to match the original order
        # this is necessary because the tetratagging process may change the order
        # of the words in the tree
        lin_tree = LinearizedTree.sort_words(lin_tree, dep_tree)

        return lin_tree
        
    def decode(self, lin_tree):
        tagger = C_Tetratag(separator=self.separator, unary_joiner="[+]", mode="inorder", binary_marker="[b]")
        bht_tree = tagger.decode(lin_tree)
        dectree = D_Tree.from_bht(bht_tree)

        # remove first node if id = 0 and form = '-ROOT-'
        if dectree.nodes[0].id == 0 and dectree.nodes[0].form == "-ROOT-":
            dectree.nodes.pop(0)

        # remove -NONE- nodes
        for node in dectree.nodes:
            if node.form == "-NONE-":
                dectree.nodes.remove(node)
        
        # fix ids starting in 0
        if dectree.nodes[0].id == 0:
            for node in dectree.nodes:
                node.id += 1

        return dectree