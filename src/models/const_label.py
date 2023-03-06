from src.utils.constants import C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING, C_NONE_LABEL
from src.utils.constants import BOS, EOS, C_NO_POSTAG_LABEL

class C_Label:
    def __init__(self, nc, lc, uc, et, sp, uj):
        self.encoding_type = et

        self.n_commons = int(nc)
        self.last_common = lc
        self.unary_chain = uc if uc != C_NONE_LABEL else None
        self.separator = sp
        self.unary_joiner = uj
    
    def __repr__(self):
        unary_str = self.unary_joiner.join([self.unary_chain]) if self.unary_chain else ""
        return (str(self.n_commons) + ("*" if self.encoding_type==C_RELATIVE_ENCODING else "")
        + self.separator + self.last_common + (self.separator + unary_str if self.unary_chain else ""))
    
    def to_absolute(self, last_label):
        self.n_commons+=last_label.n_commons
        if self.n_commons<=0:
            self.n_commons = 1
        
        self.encoding_type=C_ABSOLUTE_ENCODING
    
    @staticmethod
    def from_string(l, sep, uj):
        label_components = l.split(sep)
        
        if len(label_components)== 2:
            nc, lc = label_components
            uc = None
        else:
            nc, lc, uc = label_components
        
        et = C_RELATIVE_ENCODING if '*' in nc else C_ABSOLUTE_ENCODING
        nc = nc.replace("*","")
        return C_Label(nc, lc, uc, et, sep, uj)
    
class C_LinearizedTree:
    def __init__(self, words, postags, additional_feats, labels, n_feats):
        self.words = words
        self.postags = postags
        self.additional_feats = additional_feats
        self.labels = labels
        self.n = n_feats
        
    def get_sentence(self):
        return "".join(self.words)
    
    def get_word(self, index):
        return self.words[index]

    def get_postag(self, index):
        return self.postags[index]
    
    def get_additional_feat(self, index):
        return self.additional_feats[index] if len(self.additional_feats) > 0 else None
    
    def get_label(self, index):
        return self.labels[index]
    
    def reverse_tree(self, ignore_bos_eos=True):
        '''
        Reverses the lists of words, postags, additional_feats and labels.
        Do not reverses the first (BOS) and last (EOS) elements
        '''
        if ignore_bos_eos:
            self.words = self.words[1:-1][::-1]
            self.postags = self.postags[1:-1][::-1]
            self.additional_feats = self.additional_feats[1:-1][::-1]
            self.labels = self.labels[1:-1][::-1]
        else:
            self.words = self.words[::-1]
            self.postags = self.postags[::-1]
            self.additional_feats = self.additional_feats[::-1]
            self.labels = self.labels[::-1]

    def add_row(self, word, postag, additional_feat, label):
        self.words.append(word)
        self.postags.append(postag)
        self.additional_feats.append(additional_feat)
        self.labels.append(label)
    
    def iterrows(self):
        for i in range(len(self)):
            yield self.get_word(i), self.get_postag(i), self.get_additional_feat(i), self.get_label(i)
            

    def __len__(self):
        return len(self.words)

    def __repr__(self):        
        return self.to_string()
    
    def to_string(self, f_idx_dict=None, add_bos_eos=True):
        if add_bos_eos:
            self.words = [BOS] + self.words + [EOS]
            self.postags = [BOS] + self.postags + [EOS]
            self.additional_feats = [self.n * [BOS]] + self.additional_feats + [self.n * [EOS]]
            self.labels = [BOS] + self.labels + [EOS]
        
        tree_string = ""
        for w, p, af, l in self.iterrows():
            # create the output line of the linearized tree
            output_line = [w,p]
            
            # check for features
            if f_idx_dict:
                if w == BOS:
                    f_list = [BOS] * (self.n+1)
                elif w == EOS:
                    f_list = [EOS] * (self.n+1)
                else:
                    f_list = ["_"] * (self.n+1)
                
                if af != [None]:
                    for element in af:
                        key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                        if key in f_idx_dict.keys():
                            f_list[f_idx_dict[key]] = value
                
                # append the additional elements or the placehodler
                for element in f_list:
                    output_line.append(element)

            # add the label
            output_line.append(str(l))
            tree_string+=u"\t".join(output_line)+u"\n"
        
        if add_bos_eos:
            self.words = self.words[1:-1]
            self.postags = self.postags[1:-1]
            self.additional_feats = self.additional_feats[self.n:-self.n]
            self.labels = self.labels[1:-1]

        return tree_string

    @staticmethod
    def empty_tree(n_feats = 1):
        temp_tree = C_LinearizedTree(labels=[], words=[], postags=[], additional_feats=[], n_feats=n_feats)
        return temp_tree

    @staticmethod
    def from_string(content, separator="_", unary_joiner="|", n_features=0):
        '''
        Reads a linearized tree from a string shaped as
        -BOS- \t -BOS- \t (...) \t -BOS- \n
        word \t postag \t (...) \t label \n
        word \t postag \t (...) \t label \n
        -EOS- \t -EOS- \t (...) \t -EOS- \n
        '''
        labels = []
        words  = []
        postags = []
        additional_feats = []
        
        linearized_tree = None
        for line in content.split("\n"):
            if line=="\n":
                print("Empty line")
            # skip empty line
            if len(line) <= 1:
                continue

            # Separate the label file into columns
            line_columns = line.split("\t") if ("\t") in line else line.split(" ")
            word = line_columns[0]

            if BOS == word:
                labels = []
                words  = []
                postags = []
                additional_feats = []

                continue
            
            if EOS == word:
                linearized_tree = C_LinearizedTree(words, postags, additional_feats, labels, n_features)
                continue

            if len(line_columns) == 2:
                word, label = line_columns
                postag = C_NO_POSTAG_LABEL
                feats = "_"
            elif len(line_columns) == 3:
                word, postag, label = line_columns[0], line_columns[1], line_columns[2]
                feats = "_"
            else:
                word, postag, *feats, label = line_columns[0], line_columns[1], line_columns[1:-1], line_columns[-1]
            
            # Check for predictions with no label
            if BOS in label or EOS in label:
                label = "1"+separator+"ROOT"

            words.append(word)
            postags.append(postag)
            labels.append(C_Label.from_string(label, separator, unary_joiner))
            additional_feats.append(feats)

        return linearized_tree