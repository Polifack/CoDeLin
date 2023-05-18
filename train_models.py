import datasets
from datasets import Sequence
from datasets import ClassLabel
from hfmtl.tasks.sequence_classification import SequenceClassification
from hfmtl.tasks.token_classification import TokenClassification
from hfmtl.utils import *
from hfmtl.models import *

from PYEVALB.scorer import Scorer
from PYEVALB.summary import summary

from codelin.models.const_tree import C_Tree
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.encs.constituent import *
from codelin.utils.constants import *

import easydict
from frozendict import frozendict
import os
import torch
import pandas as pd


# Generate datasets
ptb_path = "~/Treebanks/const/PENN_TREEBANK/"
ptb_path = os.path.expanduser(ptb_path)

with open(os.path.join(ptb_path,"test.trees")) as f:
    ptb_test = [l.rstrip() for l in f.read().splitlines()]
with open(os.path.join(ptb_path,"dev.trees")) as f:
    ptb_dev = [l.rstrip() for l in f.read().splitlines()]
with open(os.path.join(ptb_path,"train.trees")) as f:
    ptb_train = [l.rstrip() for l in f.read().splitlines()]

def generate_dataset_from_codelin(train_dset, dev_dset, test_dset=None):
    label_set = set()
    dsets = [train_dset, dev_dset, test_dset] if test_dset else [train_dset, dev_dset]
    for dset in dsets:
        for labels in dset["target"]:
            label_set.update(labels)
    label_names = sorted(list(label_set))

    train_dset = datasets.Dataset.from_dict(train_dset)
    train_dset = train_dset.cast_column("target", Sequence(ClassLabel(num_classes=len(label_names), names=label_names)))

    dev_dset = datasets.Dataset.from_dict(dev_dset)
    dev_dset = dev_dset.cast_column("target", Sequence(ClassLabel(num_classes=len(label_names), names=label_names)))

    if test_dset:
        test_dset = datasets.Dataset.from_dict(test_dset)
        test_dset = test_dset.cast_column("target", Sequence(ClassLabel(num_classes=len(label_names), names=label_names)))
    
        # Convert to Hugging Face DatasetDict format
        dataset = datasets.DatasetDict({
                "train": train_dset,
                "validation": dev_dset,
                "test": test_dset
            })
    else:
        # Convert to Hugging Face DatasetDict format
        dataset = datasets.DatasetDict({
                "train": train_dset,
                "validation": dev_dset
            })

    return dataset

def encode_dset(encoder, dset):
    encoded_trees = {"tokens":[], "target":[]}
    max_len_tree = 0
    for line in dset:
        tree = C_Tree.from_string(line)
        lin_tree = encoder.encode(tree)
        encoded_trees["tokens"].append([w for w in lin_tree.words])
        encoded_trees["target"].append([str(l) for l in lin_tree.labels])
        max_len_tree = max(max_len_tree, len(lin_tree.words))
    return encoded_trees, max_len_tree

def gen_dsets():
    encodings = []

    # naive absolute encodings
    a_enc     = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_absolute", "encoder":a_enc})
    a_br_enc  = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_absolute_br", "encoder":a_br_enc})
    a_bl_enc  = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_absolute_bl", "encoder":a_bl_enc})
    ar_enc    = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_absolute_r", "encoder":ar_enc})
    ar_br_enc = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_absolute_r_br", "encoder":ar_br_enc})
    ar_bl_enc = C_NaiveAbsoluteEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_absolute_r_bl", "encoder":ar_bl_enc})

    # naive relative encodings
    r_enc     = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_relative", "encoder":r_enc})
    r_br_enc  = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_relative_br", "encoder":r_br_enc})
    r_bl_enc  = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_relative_bl", "encoder":r_bl_enc})
    rr_enc    = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_relative_r", "encoder":rr_enc})
    rr_br_enc = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_relative_r_br", "encoder":rr_br_enc})
    rr_bl_enc = C_NaiveRelativeEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_relative_r_bl", "encoder":rr_bl_enc})

    # naive dynamic encodings
    d_enc     = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_dynamic", "encoder":d_enc})
    d_br_enc  = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_dynamic_br", "encoder":d_br_enc})
    d_bl_enc  = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=False, binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_dynamic_bl", "encoder":d_bl_enc})
    dr_enc    = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"naive_dynamic_r", "encoder":dr_enc})
    dr_br_enc = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="R",  binary_marker="[b]")
    encodings.append({"name":"naive_dynamic_r_br", "encoder":dr_br_enc})
    dr_bl_enc = C_NaiveDynamicEncoding(separator="[_]", unary_joiner="[+]", reverse=True,  binary=True,  binary_direction="L",  binary_marker="[b]")
    encodings.append({"name":"naive_dynamic_r_bl", "encoder":dr_bl_enc})

    # gaps encodings
    g_r_enc   = C_GapsEncoding(separator="[_]", unary_joiner="[+]", binary_direction="R", binary_marker="[b]")
    encodings.append({"name":"gaps_r", "encoder":g_r_enc})
    g_l_enc   = C_GapsEncoding(separator="[_]", unary_joiner="[+]", binary_direction="L", binary_marker="[b]")
    encodings.append({"name":"gaps_l", "encoder":g_l_enc})

    # tetra encodings
    t_pr_enc  = C_Tetratag(separator="[_]", unary_joiner="[+]", mode='preorder',  binary_marker="[b]")
    encodings.append({"name":"tetratag_preorder", "encoder":t_pr_enc})
    t_in_enc  = C_Tetratag(separator="[_]", unary_joiner="[+]", mode='inorder',   binary_marker="[b]")
    encodings.append({"name":"tetratag_inorder", "encoder":t_in_enc})
    
    # out of memory error
    # t_po_enc  = C_Tetratag(separator="[_]", unary_joiner="[+]", mode='postorder', binary_marker="[b]")
    # encodings.append({"name":"tetratag_postorder", "encoder":t_po_enc})

    # yuxtaposed encodings
    j_enc   = C_JuxtaposedEncoding(separator="[_]", unary_joiner="[+]", binary=False, binary_direction=None, binary_marker="[b]")
    encodings.append({"name":"juxtaposed", "encoder":j_enc})
    j_r_enc = C_JuxtaposedEncoding(separator="[_]", unary_joiner="[+]", binary=True, binary_direction='R',   binary_marker="[b]")
    encodings.append({"name":"juxtaposed_r", "encoder":j_r_enc})
    j_l_enc = C_JuxtaposedEncoding(separator="[_]", unary_joiner="[+]", binary=True, binary_direction='L',   binary_marker="[b]")
    encodings.append({"name":"juxtaposed_l", "encoder":j_l_enc})

    return encodings

# Get model hyperparameters
args = easydict.EasyDict({
    "max_seq_length": 100,
    
    "batch_size": 8,
    "per_device_train_batch_size": 8,
    "per_device_eval_batch_size": 8,

    "num_train_epochs": 20,

    "learning_rate": 1,
    "weight_decay": 0.01,
    "adam_epsilon": 1e-8,
    "adam_beta1": 0.9,
    "adam_beta2": 0.999,
    "do_eval": False,
    "do_predict": False,
    "do_train": True,
    
    "evaluation_strategy": "epoch",
    "logging_strategy": "epoch",

    "overwrite_output_dir": True,

    "include_inputs_for_metrics": False,
    "batch_truncation": True,
    "add_cls": True,
    "add_clf": True,
    "drop_probability": 0.1,
    "model_name": "roberta-base"
    })

def delete_garbage():
    gc.collect()

    for obj in gc.get_objects():
        try:
            if torch.is_tensor(obj) or (hasattr(obj, 'data') and torch.is_tensor(obj.data)):
                del obj
        except:
            pass

    torch.cuda.empty_cache()


# train and evaluate using Evalb
encodings = gen_dsets()
results = {}
train_limit = None
delete_garbage()

for enc in encodings:
    results_df = pd.DataFrame(columns=["encoding", "recall", "precision", "f1", "n_labels"])
    print("[GPU] Starting training; Allocated memory:", torch.cuda.memory_allocated()/1e6,"MB")
    print("[GPU] Starting training; Cached memory:", torch.cuda.memory_cached()/1e6,"MB")
    encoder = enc["encoder"]
    
    print("[DST] Encoding the datasets using CoDeLin")
    train_enc, mlt1 = encode_dset(encoder, ptb_train[:train_limit] if train_limit else ptb_train)
    dev_enc, mlt2   = encode_dset(encoder, ptb_dev[:train_limit]   if train_limit else ptb_dev)
    dataset  = generate_dataset_from_codelin(train_enc, dev_enc)
    
    tasks = [TokenClassification(
                dataset = dataset,
                name = enc["name"],
                tokenizer_kwargs = frozendict(padding="max_length", max_length=args.max_seq_length, truncation=True)
            )]
        
    model   = Model(tasks, args)            # list of models; by default, shared encoder, task-specific CLS token task-specific head 
    trainer = Trainer(model, tasks, args)   # tasks are uniformly sampled by default
    
    print("[GPU] Model created; Total allocated memory", torch.cuda.memory_allocated()/1e6,"MB")
    print("[GPU] Model created; Total cached memory", torch.cuda.memory_cached()/1e6,"MB")
    device = torch.device("cuda")
    trainer.train()
    # Free dataset
    del dataset
    model_memory = torch.cuda.memory_allocated()/1e6
    cached_memory = torch.cuda.memory_cached()/1e6
    print("[GPU] Model training finished; Total allocated memory",model_memory,"MB")
    print("[GPU] Model training finished; Total cached memory", cached_memory,"MB")
    
    # save
    trainer.save_model(output_dir=f"models/{enc['name']}")
    
    for i, t in enumerate(tasks):
        test_trees = ptb_test[:train_limit] if train_limit else ptb_test
        dec_trees = []
        scorer = Scorer()

        for gold_tree in test_trees:
            tree = C_Tree.from_string(gold_tree)
            
            words = tree.get_words()
            postags = tree.get_postags()
            sentence = " ".join(words)
            
            tokenized_input = trainer.tokenizer(sentence, return_tensors='pt')

            t_items = tokenized_input.items()
            for k, v in t_items:
                print(k, v)
            tokenized_input = {k: v.to(device) for k, v in tokenized_input.items()}
            
            outputs = model.task_models_list[i](**tokenized_input)
            logits = outputs.logits
            predictions = logits.argmax(-1).squeeze().tolist()
            true_predictions = [tasks[i].label_names[p] for p in predictions[1:-1]]
            
            labels = []
            for p in true_predictions:
                labels.append(C_Label.from_string(p, sep="[_]", uj="[+]"))

            lin_tree = LinearizedTree(words=words, postags=postags,
                        additional_feats=[], labels=labels, n_feats=0)
            dec_tree = encoder.decode(lin_tree).postprocess_tree(conflict_strat=C_STRAT_MAX, clean_nulls=True, default_root="S")
            dec_tree = str(dec_tree)            
            dec_trees.append(dec_tree)

            # free memory
            del tokenized_input
            del predictions
            del logits
            del outputs
        
        try:
            results = scorer.score_corpus(test_trees, dec_trees)
            s = summary(results)
            
            recall = s[4]
            fscore = s[6]
            precision = s[7]
        except:
            recall = 0
            fscore = 0
            precision = 0

        results_dict = {"encoding":enc["name"], "recall":recall, "precision": precision, "f1": fscore, "n_labels": t.num_labels,
                        "model_memory":model_memory, "cache_memory":cached_memory}
        
        print("**** Results ****")
        for k, v in results_dict.items():
            print(f"{k}: {v}")
        results_df = results_df.append(results_dict, ignore_index=True)
        print()
    
    # save decoded trees
    f_name = "test_"+enc["name"]+".trees"
    with open(f_name, "w") as f:
        for t in dec_trees:
            f.write(t+"\n")

    # free memory
    del model
    del trainer
    del tasks

    delete_garbage()

    # garbage collection
    print("[GPU] End of training total allocated memory", torch.cuda.memory_allocated()/1e6,"MB")
    print("[GPU] End of training total cached memory", torch.cuda.memory_cached()/1e6,"MB")

    # save as latex
    results_latex = results_df.to_latex()
    f_name = "results_"+enc["name"]+".tex"
    with open(f_name, "w") as f:
        f.write(results_latex)