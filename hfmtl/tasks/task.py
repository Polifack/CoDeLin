from datasets import load_dataset, Dataset
from transformers import PreTrainedTokenizerBase
from frozendict import frozendict as fdict
import datasets
from dataclasses import dataclass
from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from scipy.special import expit


def get_dataset_name(dataset):
    try:
        s="/".join(dataset.cache_files['train'][0]['filename'].split('/huggingface/datasets/')[-1].split('/')[:-3])
        return s
    except:
        return ""

def oversample(dataset, n=2):
    dataset['train']= datasets.concatenate_datasets(
        [dataset['train'].shuffle(_) for _ in range(n)]
    )
    return dataset

def sample_dataset(dataset, n=10000, n_eval=1000, oversampling=None):
    if oversampling and len(dataset['train'])<n:
        dataset=oversample(dataset, oversampling)

    for k in dataset:
        n_k=(n if k=='train' else n_eval)
        if n_k and len(dataset[k])>n_k:
            dataset[k]=dataset[k].train_test_split(train_size=n_k)['train']
    return dataset

@dataclass
class Task:
    dataset: Dataset = None
    name:str = ""
    tokenizer: PreTrainedTokenizerBase = None
    tokenizer_kwargs: dict = fdict()
    max_rows: int = None
    max_rows_eval: int = None
    oversampling: int = None
    main_split: str = "train"
    
    def __hash__(self):
        return hash(str(self.dataset.__dict__))

    def __post_init__(self):
        self.__class__.__hash__ = Task.__hash__
        if type(self.dataset) == str:
            name = self.dataset
            self.dataset = load_dataset(self.dataset)
        elif type(self.dataset) == tuple:
            name = "/".join(self.dataset)
            self.dataset = load_dataset(*self.dataset)
        else:
            name = get_dataset_name(self.dataset)

        if not self.name:
            self.name = name
        self.results = []
        self.dataset = sample_dataset(self.dataset, self.max_rows, self.max_rows_eval, self.oversampling)
    
    def check():
        return True

    def set_tokenizer(self, tokenizer):
        self.tokenizer = tokenizer

    def get_labels(self):
        try:
            for key in 'label','labels':
                return self.dataset[self.main_split].features[key].names
        except:
            pass
        try:
            for key in 'label','labels':
                return sorted(set(self.dataset[self.main_split]["labels"]))
        except:
            return []