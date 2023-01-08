from src.models.const_tree import ConstituentTree
from src.encs.constituent import C_NaiveAbsoluteEncoding
from src.utils.constants import *

def evaluate():
    f_gold = open('test.trees', 'r')
    f_pred = open('test_dec.trees', 'r')

    for lg, lp in zip(f_gold, f_pred):
        if lg == lp:
            continue
        else:
            print("Gold: ", lg)
            print("Pred: ", lp)
            break
def playground():
    s = "(S (-LRB- -LRB-) (PP (IN In) (NP (DT a) (NN stock-index) (NN arbitrage) (NN sell) (NN program))) (, ,) (NP (NNS traders)) (VP (VP (VBP buy) (CC or)) (VP (VBP sell) (NP (NP (JJ big) (NNS baskets)) (PP (IN of) (NP (NNS stocks))))) (CC and) (VP (VBP offset) (NP (NP (DT the) (NN trade)) (PP (IN in) (NP (NNS futures)))) (-NONE- (VP (TO to) (VP (VB lock) (PP (IN in) (NP (DT a) (NN price) (NN difference)))))))) (. .) (-RRB- -RRB-))"
    t = ConstituentTree.from_string(s)
    e = C_NaiveAbsoluteEncoding("_", "+")
    w, p, l, f  = e.encode(t)
    lt = []
    for i in range(len(w)):
        lt.append((w[i], p[i], l[i]))
    dt = e.decode(lt)
    dt.postprocess_tree(C_STRAT_MAX)
    print(dt)
    

if "__main__" == __name__:
    playground()

