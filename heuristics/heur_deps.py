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
    check_loops(nodes)
    check_valid_heads(nodes)

    root = None
    # Attempt to find a root in the nodes using
    # the selected strategy
    for node in nodes:    
        if search_root_strat == D_ROOT_HEAD:
            if node.head == 0:
                root = node
                break
        elif search_root_strat == D_ROOT_REL:
            if node.rel == 'root':
                root = node
                break

    # If no root found use the default one
    # according to selected strategy
    if (root == None):
        root = nodes[0]
    
    # fix the D_NULLHEADS from other steps
    # and if asked, fix the uniqueness of the root
    for node in nodes:
        if node == root:
            continue

        if node.head == D_NULLHEAD:
            node.head = root.id
        
        if not multiroot and node.head <= 0:
            node.head = root.id
    

def check_loops(nodes):
    '''
    Given a set of ConllNodes parses through the nodes
    and finds all cycles. Once it finds a cycle it breaks it
    by setting one of the heads to D_NULLHEAD
    '''
    for node in nodes:
        visited = []
        while (node.head != 0) and (node.head!=-1):
            if node in visited:
                node.head = -1
            else:
                visited.append(node)
                next_node_id = min(max(node.head-1, 0), len(nodes)-1)

                node = nodes[next_node_id]

def check_valid_heads(nodes):
    '''
    Given a set of ConllNode nodes representing a dependency tree
    parses through the nodes and sets all heads outside the boundaries
    as D_NULLHEAD
    '''
    for node in nodes:
        if int(node.head) < 0:
            node.head = D_NULLHEAD
        elif int(node.head) > (nodes[-1].id):
            node.head = D_NULLHEAD
