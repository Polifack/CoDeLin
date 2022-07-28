from utils.constants import D_POSROOT, D_EMPTYREL

class ConllNode:
    def __init__(self, wid, form, lemma, upos, xpos, feats, head, deprel, deps, misc):
        self.id = wid                           # word id
        
        self.form = form if form else "_"       # word 
        self.lemma = lemma if lemma else "_"    # word lemma/stem
        self.upos = upos if upos else "_"       # universal postag
        self.xpos = xpos if xpos else "_"       # language_specific postag
        self.feats = feats if feats else "_"    # morphological features
        
        self.head = head                        # id of the word that depends on
        self.relation = deprel                  # type of relation with head

        self.deps = deps if deps else "_"       # enhanced dependency graph
        self.misc = misc if misc else "_"       # miscelaneous data
    
    def __repr__(self):
        return '\t'.join(str(e) for e in list(self.__dict__.values()))+'\n'

    @staticmethod
    def from_string(conll_str):
        wid,form,lemma,upos,xpos,feats,head,deprel,deps,misc = conll_str.split('\t')
        return ConllNode(int(wid), form, lemma, upos, xpos, feats, int(head), deprel, deps, misc)

    @staticmethod
    def dummy_root():
        return ConllNode(0, D_POSROOT, None, D_POSROOT, None, None, 0, D_EMPTYREL, None, None)
    
    @staticmethod
    def empty_node():
        return ConllNode(0, None, None, None, None, None, 0, None, None, None)