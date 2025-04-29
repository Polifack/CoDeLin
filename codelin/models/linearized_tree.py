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

    def index(self, label):
        return self.labels.index(label)
        
    def get_sentence(self):
        return " ".join(self.words)

    def get_word(self, index):
        return self.words[index]

    def get_postag(self, index):
        return self.postags[index]
    
    def get_additional_feat(self, index):
        # return self.additional_feats[index] if len(self.additional_feats) > 0 else None
        return None
    
    def get_label(self, index):
        return self.labels[index]
    
    def remove_dummy(self):
        if self.words[0] == C_ROOT_LABEL:
            self.words = self.words[1:]
            self.postags = self.postags[1:]
            self.additional_feats = self.additional_feats[1:]
            self.labels = self.labels[1:]

    def set_postags(self, postags):
        pass

    def reverse_tree(self):
        '''
        Reverses the lists of words, postags, additional_feats and labels.
        '''
        self.words = self.words[::-1]
        self.postags = self.postags[::-1]
        self.additional_feats = self.additional_feats[::-1]
        self.labels = self.labels[::-1]

    def add_row(self, word, postag, additional_feat, label):
        self.words.append(word)
        self.postags.append(postag)
        self.additional_feats.append(additional_feat)
        self.labels.append(label)

    def sort_words(self, d_tree):
        '''
        Sorts the nodes of the linearized tree using the words to 
        match the order of the nodes in the dependency tree.
        '''
        fixed_ltree = LinearizedTree.empty_tree()
        for i in range(len(d_tree)):
            for j in range(len(self)):
                if d_tree.nodes[i].form == self.get_word(j):
                    fixed_ltree.add_row(self.get_word(j), self.get_postag(j), self.get_additional_feat(j), self.get_label(j))
                    break
        return fixed_ltree
            
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
        return self.to_string(add_bos_eos=False)
    
    def to_string(self, f_idx_dict=None, add_bos_eos=True, separate_columns=False, n_label_cols=1, ignore_postags=False):
        
        # set the columns to split the label if needed
        n_cols = (len(f_idx_dict.keys()) + 1 + n_label_cols) if f_idx_dict else (1 + n_label_cols)
        # n_cols = n_cols-1 if ignore_postags else n_cols

        # add bos eos
        if add_bos_eos:
            self.words = [BOS] + self.words + [EOS]
            self.postags = [BOS] + self.postags + [EOS]
            if f_idx_dict:
                self.additional_feats = [len(f_idx_dict.keys()) * [BOS]] + self.additional_feats + [len(f_idx_dict.keys()) * [EOS]]
            else:
                self.additional_feats = []
            
            self.labels = [BOS] + self.labels + [EOS]
        
        tree_string = ""
        
        # creat the tree
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
                    label_split = str(l).split(l.separator)
                    if len(label_split) < n_label_cols:
                        label_split += [C_NONE_LABEL] * (n_label_cols - len(label_split))
                    output_line += label_split
            
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
    def from_string(content, mode, separator="[_]", unary_joiner="[+]", separate_columns=False, n_label_cols=1, 
                    ignore_postags=False, n_features=0, sep_bits=-1):
        '''
        Reads a linearized tree from a string shaped as:
        word \t postag \t (...) \t label \n
        This version does not rely on -BOS- or -EOS- markers.
        '''
        labels = []
        words = []
        postags = []
        additional_feats = []
        split_tree = content.strip().split("\n")

        for line in split_tree:
            # Skip empty lines
            if not line.strip():
                continue

            # Separate the label file into columns
            line_columns = line.split("\t") if "\t" in line else line.split(" ")
            word = line_columns[0]

            if separate_columns:
                if len(line_columns) == 1 + n_label_cols:
                    word, *label = line_columns
                    postag = C_NO_POSTAG_LABEL
                    feats = "_"
                    label = separator.join(label)
                elif len(line_columns) == 2 + n_label_cols:
                    word, postag, *label = line_columns
                    feats = "_"
                    label = separator.join(label)
                else:
                    label = line_columns[-n_label_cols:]
                    word, postag, *feats = line_columns[:-n_label_cols]
                    label = separator.join(label)
            else:
                if len(line_columns) == 2:
                    word, label = line_columns
                    postag = C_NO_POSTAG_LABEL
                    feats = "_"
                elif len(line_columns) == 3:
                    word, postag, label = line_columns
                    feats = "_"
                else:
                    word, postag, *feats, label = line_columns

            # Check for predictions with no label
            if not label.strip():
                label = "1" + separator + "ROOT"

            words.append(word)
            postags.append(postag)
            additional_feats.append(feats)

            if mode == "CONST":
                labels.append(C_Label.from_string(label, separator, unary_joiner))
            elif mode == "DEPS":
                if sep_bits > 0:
                    label_parts = label.split(separator)
                    deprel = label_parts[-1]
                    bits = "".join(label_parts[:-1])
                    label = separator.join([bits, deprel])
                labels.append(D_Label.from_string(label, separator))
            else:
                raise ValueError(f"[!] Unknown mode: {mode}")
        
        return LinearizedTree(words, postags, additional_feats, labels, n_features)

    @staticmethod
    def to_look_behind(lin_tree: 'LinearizedTree'):
        '''
        Returns a lookbehind version of the constituent tree. This means, the fields nc_i and lc_i are
        displaced one word forward while the uc_i is kept. For example
        
        2_B, 1_A, 2_C, 3_D, 1_A, 1_$$_E
        
        would be transformed into
        
        1_$$, 2_B, 1_A, 2_C, 3_D, 1_A_E

        This will only work on depth-based encodings for constituent trees.
        '''
        # print(type(lin_tree.labels[0]))
        if not isinstance(lin_tree.labels[0], C_Label):
            raise ValueError("Error: Applying lookbehind to a dependency tree")
        
        new_tree = LinearizedTree.empty_tree()
        for i in range(len(lin_tree)):
            word_i = lin_tree.words[i]
            postag_i = lin_tree.postags[i]
            features_i = lin_tree.additional_feats[i]
            label_i: C_Label = lin_tree.labels[i]
            label_j: C_Label = lin_tree.labels[i+1] if i+1 < len(lin_tree) else lin_tree.labels[0]
            label_lb = C_Label(label_j.n_commons, label_j.last_common, label_i.unary_chain, 
                            label_i.encoding_type, label_i.separator, label_i.unary_joiner) 
            
            new_tree.add_row(word_i, postag_i, features_i, label_lb)
        return new_tree
    
    @staticmethod
    def undo_look_behind(lin_tree: 'LinearizedTree'):
        '''
        Reverses the lookbehind transformation on a depth-based constituent tree.
        For example, the lookbehind sequence:
        
        1_$$, 2_B, 1_A, 2_C, 3_D, 1_A_E
        
        would be transformed back into:
        
        2_B, 1_A, 2_C, 3_D, 1_A, 1_$$$_E
        
        Assumes the input is the result of `to_look_behind`.
        '''
        if not isinstance(lin_tree.labels[0], C_Label):
            raise ValueError("Error: Applying undo_look_behind to a dependency tree")
        
        new_tree = LinearizedTree.empty_tree()
        for i in range(len(lin_tree)):
            word_i = lin_tree.words[i]
            postag_i = lin_tree.postags[i]
            features_i = lin_tree.additional_feats[i]
            label_i: C_Label = lin_tree.labels[i]
            label_j: C_Label = lin_tree.labels[i-1] if i > 0 else lin_tree.labels[-1]
            label_restore = C_Label(label_j.n_commons, label_j.last_common, label_i.unary_chain,
                                    label_i.encoding_type, label_i.separator, label_i.unary_joiner)

            new_tree.add_row(word_i, postag_i, features_i, label_restore)
        return new_tree
