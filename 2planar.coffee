{'id': 0, 'text': 'ROOT', 'head': 0, 'pos': 'ROOT', 'relation': 'ROOT'}
{'id': 1, 'text': 'w1', 'head': 0, 'pos': 'W1', 'relation': 'root'}
{'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
{'id': 3, 'text': 'w3', 'head': 1, 'pos': 'W3', 'relation': 'r13'}
{'id': 4, 'text': 'w4', 'head': 2, 'pos': 'W4', 'relation': 'r24 '}
{'id': 5, 'text': 'w5', 'head': 1, 'pos': 'W5', 'relation': 'r15 '}
{'id': 6, 'text': 'w6', 'head': 3, 'pos': 'W6', 'relation': 'r36 '}

----
i=2, j=1

node_i = nodes[i-1] = nodes[1] = {'id': 1, 'text': 'w1', 'head': 0, 'pos': 'W1', 'relation': 'root'}
head == j-1 == 0

# append a plane 1
----
i=3, j=2

node_i = nodes[i-1] = nodes[2] = {'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
head == j-1 == 1

# append a plane 1

i=3, j=1
node_i = nodes[i-1] = nodes[2] = {'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
head != j-1 != 0
node_j = nodes[j-1] = nodes[0] = {'id': 0, 'text': 'ROOT', 'head': 0, 'pos': 'ROOT', 'relation': 'ROOT'}
head != i-1 != 2

# skip
----
i=4,j=3
node_i = nodes[i-1] = nodes[3] = {'id': 3, 'text': 'w3', 'head': 1, 'pos': 'W3', 'relation': 'r13'}
head != j-1 != 2
node_j = nodes[j-1] = nodes[2] = {'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
head != i-1 != 3

# skip

i=4,j=2
node_i = nodes[i-1] = nodes[3] = {'id': 3, 'text': 'w3', 'head': 1, 'pos': 'W3', 'relation': 'r13'}
head == j-1 == 1

# append a plane 1

i=4,j=1
node_i = nodes[i-1] = nodes[3] = {'id': 3, 'text': 'w3', 'head': 1, 'pos': 'W3', 'relation': 'r13'}
head != j-1 != 0
node_j = nodes[j-1] = nodes[0] = {'id': 0, 'text': 'ROOT', 'head': 0, 'pos': 'ROOT', 'relation': 'ROOT'}
head != i-1 != 3

# skip
----
i=5, j=4
node_i = nodes[i-1] = nodes[4] = {'id': 4, 'text': 'w4', 'head': 2, 'pos': 'W4', 'relation': 'r24 '}
head != j-1 != 3
node_j = nodes[j-1] = nodes[3] = {'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
head != i-1 != 4

# skip

i=5, j=3
node_i = nodes[i-1] = nodes[4] = {'id': 4, 'text': 'w4', 'head': 2, 'pos': 'W4', 'relation': 'r24 '}
head == j-1 == 2

# check nodes in plane 1

plane_1=[
    {'id': 1, 'text': 'w1', 'head': 0, 'pos': 'W1', 'relation': 'root'},
    {'id': 2, 'text': 'w2', 'head': 1, 'pos': 'W2', 'relation': 'r12 '}
    {'id': 3, 'text': 'w3', 'head': 1, 'pos': 'W3', 'relation': 'r13'}
]

# cross criterion:
# para cada nodo 'n' del plano se compara con el nodo 'nc'
# si el nodo nc tiene la cabeza entre la cabeza y el id del nodo n y el nodo nc tiene el id fuera de ese rango, se cruzan
# si el nodo nc tiene el id entre la cabeza y el id del nodo n y el nodo nc tiene la cabeza fuera de ese rango, se cruzan

if n.id in range(p11.id, p11.head) and n.head not in range(p11.id, p11.head)

p11.id = 1 > n.head = 2 = False

# next

p12.id = 2 < n.id = 4 = True
p12.head = 1 > n.id = 4 = False

p12.id = 2 > n.head = 2 = False

# next

p13.id = 3 < n.id = 4 = True
p13.head = 1 > n.id = 4 = False
p13.head = 1 < n.head = 2 = True

p13.id = 3 > n.head = 2 = True
n.head = 2 > p13.id = 3 = True

