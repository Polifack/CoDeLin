import json
import argparse
from codelin.models.const_tree import C_Tree
from codelin.encs.enc_const import *
from codelin.utils.constants import *

def entities_to_tree(words, tags, entities):
    '''
    Converts a list of entities into a tree
    '''
    t = C_Tree("ROOT")
    for i in range(len(words)):
        w = words[i].rstrip()
        p = tags[i] if tags else "POSTAG"
        e = entities[i]

        terminal_tree = C_Tree(p, C_Tree(w))

        # No Entity
        if e == "NONE":
            t.add_child(terminal_tree)
        
        # Has entity
        else:
            if type(e) is list:
                # decend through the rightmost branch of the tree
                # until we find a branch with different entity name
                # or we reach the end of the tree
                cl = t
                idx = 0
                while cl.children and cl.children[-1].label == e[idx]:
                    cl = cl.children[-1]
                    idx += 1
                    
                    # check if we reached the end of the entity
                    if idx == (len(e)-1):
                        break

                # add the rest of the entities as children
                t1 = C_Tree(e[idx])
                cl.add_child(t1)
                cl = t1
                for j in range(idx+1, len(e)):
                    t1 = C_Tree(e[j])
                    cl.add_child(t1)
                    cl = t1
                
                cl.add_child(terminal_tree)
            
            # Single Entity
            else:
                # if rightmost branch of the tree has the same entity
                # add it as a child
                if t.children and t.children[-1].label == e:
                    t.children[-1].add_child(terminal_tree)
                # otherwise add a new branch
                else:
                    t.add_child(C_Tree(e, terminal_tree))
    return t

def parse_genia(e):
    name = e['entity_type']
    start, end = e['start'], e['end']+1
    entity_range = range(int(start), int(end)-1)

    return entity_range, name

def parse_nne(e):
    idxs, name = e.split(" ")
    name = name.rstrip()
    start, end = idxs.split(",")
    entity_range = range(int(start), int(end)-1) 

    return entity_range, name

def entities_to_bio(es, l, extractor=None):
    '''
    Bio Schema:
    B-<entity_name> - Beginning of an entity
    I-<entity_name> - Inside an entity
    O - Outside an entity

    BIO is the standard for NER
    '''
    if extractor is None:
        raise ValueError("Extractor function not provided")
    
    entities = ["O"]*l
    for e in es:
        entity_range, name = extractor(e)
        for j in entity_range:
            
            # get if we are inside, outside or inside an entity
            letter = "B" if j == entity_range[0] else "I"

            e_r = (letter, name, len(entity_range))
            if "O" in entities[j]:
                entities[j] = e_r
            else:
                entities[j] = [entities[j], e_r] if type(entities[j]) is not list else [*entities[j], e_r]
                entities[j] = sorted(entities[j], key=lambda x: x[2], reverse=True)
    
    # return only the entity name
    for i in range(len(entities)):
        if type(entities[i]) is list:
            entities[i] = "|".join(e[0]+"-"+e[1] for e in entities[i])
        elif type(entities[i]) is tuple:
            entities[i] = entities[i][0]+"-"+entities[i][1]
    return entities

def entities_to_bilou(es, l, extractor=None):
    '''
    Bilou Schema:
    
    B-<entity_name> - Beginning of an entity
    I-<entity_name> - Inside an entity
    L-<entity_name> - Last of an entity
    U-<entity_name> - Unitary of an entity
    O - Outside an entity
    
    https://aclanthology.org/W09-1119.pdf
    
    BILOU is the standard for NNER
    '''
    if extractor is None:
        raise ValueError("Extractor function not provided")
    
    entities = ["O"]*l
    for e in es:
        entity_range, name = extractor(e)
        for j in entity_range:
            
            # get if we are inside, outside or inside an entity
            letter = "B" if j == entity_range[0] else "I"
            letter = "L" if j == entity_range[-1] else letter
            letter = "U" if len(entity_range) == 1 else letter

            e_r = (letter, name, len(entity_range))
            if "O" in entities[j]:
                entities[j] = e_r
            else:
                entities[j] = [entities[j], e_r] if type(entities[j]) is not list else [*entities[j], e_r]
                entities[j] = sorted(entities[j], key=lambda x: x[2], reverse=True)
    
    # return only the entity name
    for i in range(len(entities)):
        if type(entities[i]) is list:
            entities[i] = "|".join(e[0]+"-"+e[1] for e in entities[i])
        elif type(entities[i]) is tuple:
            entities[i] = entities[i][0]+"-"+entities[i][1]
    return entities

def entities_to_biohd(es, l, extractor=None):
    '''
    BIOHD is employed in Discontinous-NER
    
    BIOHD file:///home/droca1/Downloads/17513-Article%20Text-21007-1-2-20210518.pdf
    '''


def parse_entities(es, l, extractor=None):
    '''
    Parse entitties from NNE and returns 
    a list of entities for each word in the sentence 
    or NONE if there is no entity
    '''
    if extractor is None:
        raise ValueError("Extractor function not provided")
    
    entities = ["NONE"]*l
    for e in es:
        entity_range, name = extractor(e)
        for j in entity_range:
            e_r = (name, len(entity_range))
            if "NONE" in entities[j]:
                entities[j] = e_r
            else:
                entities[j] = [entities[j], e_r] if type(entities[j]) is not list else [*entities[j], e_r]
                entities[j] = sorted(entities[j], key=lambda x: x[1], reverse=True)
    
    # return only the entity name
    for i in range(len(entities)):
        if type(entities[i]) is list:
            entities[i] = [e[0] for e in entities[i]]
        elif type(entities[i]) is tuple:
            entities[i] = entities[i][0]

    return entities

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='CoDeLin Ner to Trees')
    parser.add_argument('input', metavar='in file', type=str,help='Input NER file')
    parser.add_argument('output', metavar='out file', type=str, help='Output .trees file')
    parser.add_argument('--mode', type=str, default='genia', help='type of data to parse')
    parser.add_argument('--out', type=str, default='tree', help='type of data to output')

    args = parser.parse_args()

    file = open(args.input, 'r')
    mode = args.mode
    out  = args.out
    output_file = open(args.output, 'w+')

    if mode == 'nne':
        for s in file.read().split('\n\n')[:-1]:
            # Get words, postags and entities
            if s[0] == '\n':
                s=s[1:]
            lines = s.split('\n')
            w, p, e = lines[:3] + [None]*(3-len(lines))
            w = w.split(' ')
            p = p.split(' ')

            if out == 'tree':
                words, postags, entities = w, p, parse_entities(e.split("|"), len(w), extractor=parse_nne) if e else ["NONE"]*len(w)
                t = entities_to_tree(words, postags, entities)
                output_file.write(str(t) + '\n')
            
            if out == 'bio':
                entities = entities_to_bio(e.split("|"), len(w), extractor=parse_nne)
                for i in range(len(w)):
                    print(w[i],'\t\t',entities[i])

            if out =='bilou':
                entities = entities_to_bilou(e.split("|"), len(w), extractor=parse_nne)
                for i in range(len(w)):
                    print(w[i],'\t\t',entities[i])


    if mode =='genia':
        for line in file.readlines():
            # Get words, postags and entities
            s = json.loads(line)

            if out == 'tree':
                words, postags, entities = s['tokens'], ["NONE"]*len(s['tokens']), parse_entities(s['entity_mentions'], len(s['tokens']),  extractor=parse_genia)
                t = entities_to_tree(words, postags, entities)
                output_file.write(str(t) + '\n')
            
            if out == 'bio':
                words = s['tokens']
                bio_ent = entities_to_bio(s['entity_mentions'], len(words), extractor=parse_genia)
                for i in range(len(words)):
                    output_file.write(words[i] + '\t\t' + bio_ent[i] + '\n')
                output_file.write('\n')

            if out == 'bilou':
                words = s['tokens']
                bilou_ent = entities_to_bilou(s['entity_mentions'], len(words), extractor=parse_genia)
                for i in range(len(words)):
                    output_file.write(words[i] + '\t\t' + bilou_ent[i] + '\n')
                output_file.write('\n')