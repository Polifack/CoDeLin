import numpy as np
import datasets as ds
from datasets import load_dataset, Dataset
from transformers import DefaultDataCollator
import evaluate
import funcy as fc
import evaluate
from dataclasses import dataclass
from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from scipy.special import expit
from .task import Task

def get_len(outputs):
    try:
        return len(outputs[fc.first(outputs)])
    except:
        return 1
    
@dataclass
class SequenceClassification(Task):
    task_type = "SequenceClassification"
    dataset: Dataset = None
    data_collator = DefaultDataCollator()
    s1: str = "sentence1"
    s2: str = "sentence2"
    y:  str = "target"
    num_labels: int = None

    def __post_init__(self):
        super().__post_init__()
        if not self.num_labels:
            target = self.dataset[self.main_split].features[self.y]
            
            if "float" in target.dtype:
                self.num_labels = 1
            
            elif hasattr(target, 'num_classes'):
                self.num_labels = target.num_classes
            
            else:
                self.num_labels = max(fc.flatten(self.dataset[self.main_split][self.y]))+1

        if type(self.dataset[self.main_split][self.y][0])==list and self.task_type=="SequenceClassification":
            self.problem_type="multi_label_classification"
            if set(fc.flatten(self.dataset[self.main_split][self.y]))!={0,1}:
                def one_hot(x):
                    x[self.y] = [float(i in x[self.y]) for i in range(self.num_labels)]
                    return x
                self.dataset=self.dataset.map(one_hot)
            
            self.num_labels=len(self.dataset[self.main_split][self.y][0])
            self.dataset=self.dataset.cast_column(self.y, ds.Sequence(feature=ds.Value(dtype='float64')))

    def check(self):
        features = self.dataset[self.main_split].features
        return self.s1 in features and self.y in features

    def preprocess_function(self, examples):
        inputs = (
            (examples[self.s1], examples[self.s2])
            if self.s2 in examples
            else (examples[self.s1],)
        )
        outputs = self.tokenizer(*inputs, **self.tokenizer_kwargs)
        outputs["task"] = [self.index] *get_len(examples)
        return outputs

    def compute_metrics(self, eval_pred):
        avg={}
        predictions, labels = eval_pred.predictions, eval_pred.label_ids
        if "int" in str(eval_pred.label_ids.dtype):
            metric = evaluate.load("super_glue", "cb")
            predictions = np.argmax(predictions, axis=1)
            
        elif getattr(self,"problem_type", None)=='multi_label_classification':
            metric=evaluate.load('f1','multilabel', average='macro')
            labels=labels.astype(int)
            predictions = (expit(predictions)>0.5).astype(int)
            avg={"average":"macro"}
        else:
            metric = evaluate.load("glue", "stsb")
        
        meta = {"name": self.name, "size": len(predictions), "index": self.index}
        metrics = metric.compute(predictions=predictions, references=labels,**avg)
        self.results+=[metrics]
        return {**metrics, **meta}
