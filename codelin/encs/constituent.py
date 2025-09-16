from codelin.models.linearized_tree import LinearizedTree
from codelin.encs.enc_const import *
from codelin.utils.constants import C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING, C_TETRA_ENCODING, \
    C_JUXTAPOSED_ENCODING, C_LEFT_DESC_ENCODING, C_RIGHT_DESC_ENCODING
import os
import stanza.pipeline
from codelin.models.const_tree import C_Tree
from codelin.encs.abstract_encoding import ACEncoding
from tqdm import tqdm

def extract_features_const(in_path):
    file_in = open(in_path, "r")
    feats_set = set()
    for line in file_in:
        line = line.rstrip()
        tree = C_Tree.from_string(line)
        tree.extract_features()
        feats = tree.get_feature_names()
        
        feats_set = feats_set.union(feats)

    return sorted(feats_set)


def batch_encode(self, tree_list):
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            return list(executor.map(self.encode, tree_list))

def encode_constituent(in_path, out_path, encoding_type, reverse, separator, multitask, n_label_cols, unary_joiner, features, binary, binary_direction, 
                       binary_marker, traverse_dir, ignore_postags, add_bos_eos):
    '''
    Encodes the selected file according to the specified parameters.
    '''

    # Select encoder
    if encoding_type == C_ABSOLUTE_ENCODING:
        encoder = C_DepthBasedAbsolute(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_RELATIVE_ENCODING:
        encoder = C_DepthBasedRelative(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_DYNAMIC_ENCODING:
        encoder = C_DepthBasedDynamic(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_TETRA_ENCODING:
        encoder = C_Tetratag(separator, unary_joiner, traverse_dir, binary_direction, binary_marker)
    elif encoding_type == C_LEFT_DESC_ENCODING:
        encoder = C_LeftDescendant(separator, unary_joiner, binary_direction, reverse, binary_marker)
    elif encoding_type == C_RIGHT_DESC_ENCODING:
        encoder = C_RightDescendant(separator, unary_joiner, binary_direction, reverse, binary_marker)
    elif encoding_type == C_JUXTAPOSED_ENCODING:
        encoder = C_AttachJuxtapose(separator, unary_joiner, binary, binary_direction, binary_marker)
    else:
        raise Exception("Unknown encoding type")

    # Build feature index dictionary
    f_idx_dict = {}
    if features:
        if features == ["ALL"]:
            features = extract_features_const(in_path)
        for i, f in enumerate(features):
            f_idx_dict[f] = i

    # Create output directory
    out_dir = os.path.dirname(out_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    file_out = open(out_path, "w", encoding='utf-8')
    file_in = open(in_path, "r", encoding='utf-8')

    tree_counter = 0
    labels_counter = 0
    label_set = set()
    nci_set = set()
    lci_set = set()
    uci_set = set()

    # Read and parse all trees first
    parsed_trees = []
    raw_lines = []
    for line in file_in:
        line = line.rstrip()
        if not line:
            continue
        tree = C_Tree.from_string(line)
        if ignore_postags:
            tree.set_dummy_preterminals()
        parsed_trees.append(tree)
        raw_lines.append(line)

    # Batch encode trees
    try:
        linearized_trees = encoder.batch_encode(parsed_trees)
    except Exception as e:
        # Debug fallback: try sequentially to identify which tree fails
        for i, tree in enumerate(parsed_trees):
            try:
                encoder.encode(tree)
            except:
                print("[*] Error occurred while encoding the following tree:")
                print(tree)
                raise Exception(f"Tree encoding error at line {i}") from e

    # Write encoded trees to file
    for linearized_tree, line in zip(linearized_trees, raw_lines):
        file_out.write(linearized_tree.to_string(f_idx_dict, separate_columns=multitask, n_label_cols=n_label_cols, add_bos_eos=add_bos_eos))
        file_out.write("\n")
        tree_counter += 1
        labels_counter += len(linearized_tree)
        for lbl in linearized_tree.labels:
            label_set.add(str(lbl))
            lci_set.add(str(lbl.last_common))
            nci_set.add(str(lbl.n_commons))
            uci_set.add(str(lbl.unary_chain))

    return labels_counter, tree_counter, len(label_set), label_set, lci_set, nci_set, uci_set

def decode_constituent(
    in_path, out_path, encoding_type, lookbehind, separator, multitask, n_label_cols,
    unary_joiner, conflicts, nulls, postags, lang, binary, binary_marker, traverse_dir
):
    """
    Decodes a constituent treebank file using the specified encoding parameters.

    :param in_path: Path to the input labels file.
    :param out_path: Path to save the decoded tree.
    :param encoding_type: Type of encoding to decode.
    :param lookbehind: Whether to use lookbehind for the tree traversal.
    :param separator: String used to separate label fields.
    :param multitask: Whether the labels are in a multitask format.
    :param n_label_cols: Number of label columns in the input file.
    :param unary_joiner: String used to join unary chains.
    :param conflicts: Conflict resolution heuristics to apply.
    :param nulls: Null handling strategy.
    :param postags: Whether to include POS tagging.
    :param lang: Language for POS tagging.
    :param binary: Whether binary encoding was applied.
    :param binary_marker: Marker used for binary encoding.
    :param traverse_dir: Direction for tree traversal.
    """

    if encoding_type == C_ABSOLUTE_ENCODING:
        decoder = C_DepthBasedAbsolute(separator, unary_joiner, lookbehind, binary,  None, binary_marker)
    elif encoding_type == C_RELATIVE_ENCODING:
        decoder = C_DepthBasedRelative(separator, unary_joiner, lookbehind, binary,  None, binary_marker)
    elif encoding_type == C_DYNAMIC_ENCODING:
        decoder = C_DepthBasedDynamic(separator, unary_joiner, lookbehind, binary,  None, binary_marker)
    elif encoding_type == C_TETRA_ENCODING:
        decoder = C_Tetratag(separator, unary_joiner, traverse_dir, None, binary_marker)
    elif encoding_type == C_LEFT_DESC_ENCODING:
        decoder = C_LeftDescendant(separator, unary_joiner, None, lookbehind, binary_marker)
    elif encoding_type == C_RIGHT_DESC_ENCODING:
        decoder = C_RightDescendant(separator, unary_joiner, None, lookbehind, binary_marker)
    elif encoding_type == C_JUXTAPOSED_ENCODING:
        decoder = C_AttachJuxtapose(separator, unary_joiner, binary, None, binary_marker)
    else:
        raise Exception("Unknown encoding type")

    # Initialize POS tagging if required
    nlp = None
    if postags:
        stanza.download(lang=lang)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos')
    
    tree_counter, labels_counter = 0, 0
    
    with open(in_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
        tree_string = ""
        
        for line in tqdm(f_in, desc="Decoding Trees", unit=" t"):
            if line == "\n":
                tree_string = tree_string.rstrip()
                current_tree = LinearizedTree.from_string(
                    tree_string, 
                    mode="CONST", 
                    separator=separator, 
                    unary_joiner=unary_joiner,
                    separate_columns=multitask, 
                    ignore_postags=True, 
                    n_label_cols=n_label_cols
                )
                if postags and nlp:
                    c_tags = nlp(current_tree.get_sentence())
                    current_tree.set_postags([word.pos for word in c_tags.words])
                try:
                    decoded_tree : C_Tree = decoder.decode(current_tree)
                    decoded_tree = decoded_tree.postprocess_tree(conflicts, nulls)
                except Exception as e:
                    print(f"[*] Error decoding tree {tree_counter + 1}:\n{current_tree}\n{e}")
                    print(f"[*] Exiting...")
                    break
                
                f_out.write(str(decoded_tree).replace('\n', '') + '\n')
                tree_string = ""
                tree_counter += 1
            else:
                tree_string += line
            labels_counter += 1
    
    return tree_counter, labels_counter
