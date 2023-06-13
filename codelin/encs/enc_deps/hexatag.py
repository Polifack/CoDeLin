from codelin.encs.abstract_encoding import ADEncoding
from codelin.models.deps_label import D_Label
from codelin.models.deps_tree import D_Tree
from codelin.utils.constants import D_NONE_LABEL, D_2P_GREED, D_2P_PROP
from codelin.models.linearized_tree import LinearizedTree

class D_HexatagEncoding(ADEncoding):
    
    def __init__(self, separator:str = "_"):
        super().__init__(separator)

    def __str__(self):
        return "Dependency Bracketing Hexa-Tags Encoding"

    def encode(self, dep_tree):
        pass

    def decode(self, lin_tree):
        pass