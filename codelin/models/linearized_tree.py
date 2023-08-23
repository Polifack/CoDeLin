from codelin.utils.constants import BOS, EOS, C_NO_POSTAG_LABEL, C_NONE_LABEL, C_ROOT_LABEL
from codelin.models.const_label import C_Label
from codelin.models.deps_label import D_Label

class LinearizedTree:
    def __init__(self, words, postags, additional_feats, labels, n_feats):
        self.words = words
        self.postags = postags
        self.additional_feats = additional_feats
        self.labels = labels
        #len(f_idx_dict.keys()) = n_feats

    def get_labels_splitted(self):
        '''
        Returns the labels split by
        their separator.
        '''
        for l in self.labels:
            spl = str(l).split(l.separator)
            if len(spl) == 2:
                yield spl[0], spl[1], C_NONE_LABEL
            elif len(spl) == 3:
                yield spl[0], spl[1], spl[2]

        
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
    
    def remove_dummy(self):
        if self.words[0] == C_ROOT_LABEL:
            self.words = self.words[1:]
            self.postags = self.postags[1:]
            self.additional_feats = self.additional_feats[1:]
            self.labels = self.labels[1:]

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
    
    def iterrows(self, dir='l2r'):
        if dir == 'l2r':
            for i in range(len(self)):
                yield self.get_word(i), self.get_postag(i), self.get_additional_feat(i), self.get_label(i)
        elif dir == 'r2l':
            for i in range(len(self)-1, -1, -1):
                yield self.get_word(i), self.get_postag(i), self.get_additional_feat(i), self.get_label(i)
            
    def __len__(self):
        return len(self.words)

    def __repr__(self):        
        return self.to_string()
    
    def to_string(self, f_idx_dict=None, add_bos_eos=True, separate_columns=False):
        n_cols = (len(f_idx_dict.keys())+1) if f_idx_dict else 1
        if separate_columns:
            n_cols += len(str(self.labels[0]).split(self.labels[0].separator))


        if add_bos_eos:
            self.words = [BOS] + self.words + [EOS]
            self.postags = [BOS] + self.postags + [EOS]
            if f_idx_dict:
                self.additional_feats = [len(f_idx_dict.keys()) * [BOS]] + self.additional_feats + [len(f_idx_dict.keys()) * [EOS]]
            else:
                self.additional_feats = []
            
            self.labels = [BOS] + self.labels + [EOS]
        
        tree_string = ""
        for w, p, af, l in self.iterrows():
            # create the output line of the linearized tree
            output_line = [w,p]
            
            # check for features
            if f_idx_dict:
                if w == BOS:
                    f_list = [BOS] * n_cols
                elif w == EOS:
                    f_list = [EOS] * n_cols
                else:
                    f_list = ["_"] *n_cols
                
                if af != [None]:
                    for element in af:
                        key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                        if key in f_idx_dict.keys():
                            f_list[f_idx_dict[key]] = value
                
                # append the additional elements or the placehodler
                for element in f_list:
                    output_line.append(element)
            
            ## add as much bos eos as there are columns
            if separate_columns:
                if l == BOS:
                    output_line += [BOS]*(n_cols-1)
                elif l == EOS:
                    output_line += [BOS]*(n_cols-1)
                else:
                    output_line += str(l).split(l.separator)
            else:
                output_line.append(str(l))
            
            tree_string+=u"\t".join(output_line)+u"\n"
        
        if add_bos_eos:
            self.words = self.words[1:-1]
            self.postags = self.postags[1:-1]
            if f_idx_dict:
                self.additional_feats = self.additional_feats[len(f_idx_dict.keys()):-len(f_idx_dict.keys())]
            self.labels = self.labels[1:-1]

        return tree_string

    @staticmethod
    def empty_tree(n_feats = 1):
        temp_tree = LinearizedTree(labels=[], words=[], postags=[], additional_feats=[], n_feats=n_feats)
        return temp_tree

    @staticmethod
    def from_string(content, mode, separator="[_]", unary_joiner="[+]", separate_columns=False, n_features=0):
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
                linearized_tree = LinearizedTree(words, postags, additional_feats, labels, n_features)
                continue
            
            if separate_columns:
                if mode=="CONST":
                    label_cols=3
                elif mode=="DEPS":
                    label_cols=2

                if len(line_columns) == 1+label_cols:
                    word, *label = line_columns
                    postag = C_NO_POSTAG_LABEL
                    feats = "_"
                    label = separator.join(label)
                elif len(line_columns) == 2+label_cols:
                    word, postag, *label = line_columns
                    feats = "_"
                    label = separator.join(label)
                else:
                    label = line_columns[-label_cols:]
                    word, postag, *feats = line_columns[:-label_cols]
                    label = separator.join(label)    
            else:
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
            if mode == "CONST":
                labels.append(C_Label.from_string(label, separator, unary_joiner))
            elif mode == "DEPS":
                labels.append(D_Label.from_string(label, separator))
            else:
                raise ValueError("[!] Unknown mode: %s" % mode)
            
            additional_feats.append(feats)
    
        return linearized_tree