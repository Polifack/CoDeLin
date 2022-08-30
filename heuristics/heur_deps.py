from utils.constants import D_NULLHEAD, D_ROOT_HEAD, D_ROOT_REL

def postprocess_tree(nodes, search_root_strat, multiroot):
    '''
    Postprocessing function for Dependency Trees that ensures correctness.
    It deals with loops, root outside of the sentence, ensuring that at least
    one root exists and (optional) if the root is unique
    The configurable parameters are:
        search_root_strat: decides if to look for a root we use the HEAD or the REL field
        multiroot: decides if we want to apply an extra step to ensure that the root is unique
    '''
    #1) Find root
    root = None
    for node in nodes:    
        if search_root_strat == D_ROOT_HEAD:
            if node.head == 0:
                root = node
                break
        elif search_root_strat == D_ROOT_REL:
            if node.rel == 'root' or node.rel == 'ROOT':
                root = node
                break
    
    # if no root found, take the first one
    if (root == None):
        i=0
        root = nodes[i]
        while root.head == D_NULLHEAD:
            i+=1
            root=nodes[i]
        
        root.head = 0

    # 2) Check loops
    check_loops(nodes, root)

    #3) Check heads
    check_valid_heads(nodes)
    
    
    # 4) Fix the D_NULLHEADS from other steps
    for node in nodes:
        if node == root:
            continue
        if node.head == D_NULLHEAD:
            node.head = root.id
        if not multiroot and node.head <= 0:
            node.head = root.id
    

def check_loops(nodes, root):
    '''
    Given a set of ConllNodes parses through the nodes
    and finds all cycles. Once it finds a cycle it breaks it
    by setting one of the heads to D_NULLHEAD
    '''
    for node in nodes:
        visited = []
        
        while (node.id != root.id) and (node.head !=D_NULLHEAD):
            if node in visited:
                node.head = D_NULLHEAD
            else:
                visited.append(node)
                next_node = min(max(node.head-1, 0), len(nodes)-1)
                node = nodes[next_node]

def check_valid_heads(nodes):
    '''
    Given a set of ConllNode nodes representing a dependency tree
    parses through the nodes and sets all heads outside the boundaries
    as D_NULLHEAD
    '''
    for node in nodes:
        if node.head==D_NULLHEAD:
            continue
        if int(node.head) < 0:
            node.head = D_NULLHEAD
        elif int(node.head) > (nodes[-1].id):
            node.head = D_NULLHEAD
