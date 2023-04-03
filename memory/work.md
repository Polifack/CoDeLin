
### Tetra-Tagging (preorder, postorder, in-order)
El encoding en preorder y postorder para el tetra-tagging tienen un problema y es que mientras que en in-order cada palabra encodea su direccion respecto a su terminal mas cercano y la direccion de su no-terminal 'siguiente', en preorder las palabras pueden encodear informacion de palabras anteriores (como se ve en la foto la palabra 'ended' esta encodeando la 'r' que indica que 'Year' es un hijo izquierdo). Esto se puede deber a que se está encodeando 'forzosamente' 2 etiquetas (e.g. lR, lL...) por palabra cuando se supone que esto son 'shift', 'reduce' transitions. En el paper [On Parsing as Tagging](https://aclanthology.org/2022.emnlp-main.607.pdf) cuándo hablan de el tagging para preorder y postorder mencionan un paper [A Unifying Theory of Transition-based and Sequence Labeling Parsing](https://aclanthology.org/2020.coling-main.336.pdf) junto al concepto de 'alignment function'. En el paper se convierten parsers de dependencias Arc Eager, Arc Standard etc en etiquetas de 'n' transiciones por etiqueta. <br>

![Several orders of Tetra tagging](pics/tetra_several_orders.png)

Esta idea se podria aplicar al tetra-tagging haciendo que para cada palabra $w_i$ se encodeen las $n$ etiquetas de acciones que aparecen en el recorrido pre-order/post-order hasta llegar a la palabra $w_{i+1}$. Esto consigue solucionar el problema con el recorrido pre-order, sin embargo para el recorrido post-order tenemos el problema de encodear en la primera palabra las etiquetas de toda la oracion.

![Several orders of Tetra tagging](pics/tetra_several_orders_2.png)

Una solucion a este problema podria consistir en cambiar la direccion de binarizacion del arbol. Los previos encodings usan arboles binarizados hacia la derecha, causando que los no terminales se encuentren mmayormente a la derecha del arbol y por lo tanto un post-order traversal siempre vaya hacia las hojas primero. Si binarizamos el arbol hacia la izquierda podriamos conseguir que el recorrido no pase por todas las hojas primero.

![Several orders of Tetra tagging](pics/tetra_several_orders_3.png)

Tras cambiar que el post-order sea el unico que utiliza binarizacion hacia la izquierda y hacer que las labels se guarden una vez por palabra obtenemos la siguiente linearizacion. Notar que, a pesar de todo, el numero de etiquetas queda desbalanceado con una gran carga de etiquetas en el ultimo nodo, que se lleva toda la cadena de no-terminales.

![Several orders of Tetra tagging](pics/tetra_several_orders_4.png)

Durante el decodificado se ha necesitado cambiar los operadores 'combine' y 'make-node' especificados en [Tetra-Tagging: Word-Synchronous Parsing with Linear-Time Inference](https://aclanthology.org/2020.acl-main.557.pdf) por acciones shift-reduce, debido a que la suposicion de que cada terminal va a tener un solo no-terminal no es cierta para los encodings que usan pre-order y post-order. Los operadores entonces quedan de esta forma:

- Pre-Order traversal
    - $r-(w)$: Insertar la palabra actual $w$ como hijo izquierdo del sub-arbol que este encima del stack
    - $l-(w)$: Insertar la palabra actual $w$ como hijo derecho del sub-arbol que este encima del stack y eliminar elementos del stack hasta encontrar uno que tenga un hijo vacio
    - $R-(NT)$: Crear un nuevo subarbol $nt$ con label $NT$ y dos hijos vacios, insertarlo como hijo izquierdo del top del stack y pushear $nt$ en el stack para que las siguientes inserciones se hagan sobre el
    - $L-(NT)$: Crear un nuevo subarbol $nt$ con label $NT$ y dos hijos vacios, insertarlo como hijo derecho del top del stack y pushear $nt$ en el stack para que las siguientes inserciones se hagan sobre el

- Post-Order traversal
    - $r-(w)$: Insertar un nuevo subarbol con label igual a la palabra actual $w$ en el stack.
    - $l-(w)$: Insertar un nuevo subarbol con label igual a la palabra actual $w$ en el stack o si el top del stack tiene hueco para combinar ese subarbol, combinarlo
    - $R-(NT)$: Crear un nuevo subarbol $nt$ con label $NT$ y dos hijos vacios, insertarlo como hijo izquierdo del top del stack y pushear $nt$ en el stack para que las siguientes inserciones se hagan sobre el
    - $L-(NT)$: Crear un nuevo subarbol $nt$ con label $NT$ y dos hijos vacios, insertarlo como hijo derecho del top del stack y pushear $nt$ en el stack para que las siguientes inserciones se hagan sobre el

