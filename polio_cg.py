import sys
import time
from itertools import combinations, permutations
from collections import Counter, defaultdict
import copy

# Place all polyominoes to form predefined 2D shape

ids = input()
print(ids, file=sys.stderr, flush=True)
counter_polio = Counter(ids)
ids = [x for x in ids]
h, w = [int(i) for i in input().split()]
g = []
for i in range(h):
    line = input()  # single line of board - place your polyominoes only on 'O' symbols
    print(line, file=sys.stderr, flush=True)
    g.append(line)
    if '.' in line:
        counter_polio['.'] = 1
    
# Write an action using print
# To debug: print("Debug messages...", file=sys.stderr, flush=True)


class LinkNode:
    def __init__(self):
        self.L = self.R = self.U = self.D = self
        self.C = None      # le header de colonne
        self.size = 0      # nombre de 1 dans la colonne
        self.rid = -1
        self.cid = -1


class ManageLink:
    def __init__(self, N_cols):
        self.N = N_cols

        # racine
        self.root = LinkNode()

        # colonnes
        self.colHeader = []
        last = self.root
        for i in range(N_cols):
            col = LinkNode()
            col.cid = i
            col.C = col
            col.size = 0
            col.U = col.D = col
            # lier horizontalement
            col.L = last
            col.R = last.R
            last.R.L = col
            last.R = col
            last = col
            self.colHeader.append(col)

    def addNode(self, row, col):
        node = LinkNode()
        node.rid = row
        node.cid = col

        # --- colonne ---
        colHead = self.colHeader[col]
        node.C = colHead
        node.D = colHead
        node.U = colHead.U
        colHead.U.D = node
        colHead.U = node
        colHead.size += 1

        # --- ligne : lier avec les autres n�uds de la m�me ligne ---
        # cherche � ajouter � la fin de la ligne existante
        left = node  # si premier de la ligne, se lie � lui-m�me
        # pour construire une ligne compl�te, on devra lier horizontalement tous les n�uds de cette ligne
        # c'est � faire lors de l�insertion multiple par ligne

        node.L = node.R = node  # si seul pour l'instant

        return node

    def linkRowNodes(self, nodes):
        """Recevoir une liste de n�uds appartenant � la m�me ligne et les lier horizontalement."""
        n = len(nodes)
        for i in range(n):
            nodes[i].R = nodes[(i+1)%n]
            nodes[i].L = nodes[(i-1)%n]

    def cover(self, colHead):
        # retirer la colonne
        colHead.R.L = colHead.L
        colHead.L.R = colHead.R

        # supprimer les lignes qui contiennent 1 dans cette colonne
        i = colHead.D
        while i != colHead:
            j = i.R
            while j != i:
                j.D.U = j.U
                j.U.D = j.D
                j.C.size -= 1
                j = j.R
            i = i.D

    def uncover(self, colHead):
        # restaurer les lignes
        i = colHead.U
        while i != colHead:
            j = i.L
            while j != i:
                j.C.size += 1
                j.D.U = j
                j.U.D = j
                j = j.L
            i = i.U

        # restaurer la colonne
        colHead.R.L = colHead
        colHead.L.R = colHead

    def coverp(self, col):
        col.R.L = col.L
        col.L.R = col.R
        for i in self.iter_down(col):
            for j in self.iter_right(i):
                j.D.U = j.U
                j.U.D = j.D
                j.C.size -= 1

    def uncoverp(self, col):
        for i in self.iter_up(col):
            for j in self.iter_left(i):
                j.C.size += 1
                j.D.U = j
                j.U.D = j
        col.R.L = col
        col.L.R = col

    def iter_right(self, node):
        c = node.R
        while c != node:
            yield c
            c = c.R

    def iter_left(self, node):
        c = node.L
        while c != node:
            yield c
            c = c.L

    def iter_down(self, node):
        c = node.D
        while c != node:
            yield c
            c = c.D

    def iter_up(self, node):
        c = node.U
        while c != node:
            yield c
            c = c.U

    def visualizeColumns(self):
        print("---- Visualize columns ----")
        c = self.root.R
        while c != self.root:
            nodes = []
            n = c.D
            while n != c:
                nodes.append(f"({n.rid},{n.cid})")
                n = n.D
            print(f"Col {c.cid}: ", " -> ".join(nodes))
            c = c.R
        print("---------------------------")

       

def sudokuDLX(board):
    N_cols = 9*9*4  # 324 contraintes
    dlx = ManageLink(N_cols)
    row_map = {}  # row_id -> (r,c,val)

    row_id = 0
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                val_list = [board[r][c]]
            else:
                val_list = list(range(1,10))
            for val in val_list:
                nodes = []
                # Cellule
                nodes.append(dlx.addNode(row_id, r*9 + c))
                # Ligne
                nodes.append(dlx.addNode(row_id, 81 + r*9 + val - 1))
                # Colonne
                nodes.append(dlx.addNode(row_id, 162 + c*9 + val - 1))
                # Bloc
                blk = (r//3)*3 + (c//3)
                nodes.append(dlx.addNode(row_id, 243 + blk*9 + val - 1))
                # Lier horizontalement
                dlx.linkRowNodes(nodes)
                row_map[row_id] = (r,c,val)
                row_id += 1

    solution = []

    def search():
        if dlx.root.R == dlx.root:
            return True  # toutes les colonnes couvertes

        # choisir la colonne avec le moins de 1
        c = dlx.root.R
        min_size = c.size
        col = c
        while c != dlx.root:
            if c.size < min_size:
                min_size = c.size
                col = c
            c = c.R

        dlx.cover(col)
        r = col.D
        while r != col:
            solution.append(r.rid)
            j = r.R
            while j != r:
                dlx.cover(j.C)
                j = j.R
            if search():
                return True
            # backtrack
            solution.pop()
            j = r.L
            while j != r:
                dlx.uncover(j.C)
                j = j.L
            r = r.D
        dlx.uncover(col)
        return False

    search()

    # reconstruire la grille
    solved = [[0]*9 for _ in range(9)]
    for rid in solution:
        r,c,val = row_map[rid]
        solved[r][c] = val
    return solved


polyominos_with_rot = {
    # Carré 2x2
    "A1": [(0,0),(0, 1),(1, 0),(2, 0)],
    "A2": [(0,0),(0, -1),(1, 0),(2, 0)],
    "A3": [(0,0),(0, 1),(-1, 0),(-2, 0)],
    "A4": [(0,0),(0, -1),(-1, 0),(-2, 0)],
    "A5": [(0,0),(-1,0),(0,1),(0,2)],
    "A6": [(0,0),(-1,0),(0,-1),(0,-2)],
    "A7": [(0,0),(1,0),(0,1),(0,2)],
    "A8": [(0,0),(1,0),(0,-1),(0,-2)],

    # Ligne de 3 horizontale
    "B1": [(0,0),(0,1),(1,0),(2,0),(2,1)],
    "B2": [(0,0),(0,-1),(1,0),(2,0),(2,-1)],
    "B3": [(0,0),(0,1),(0,2),(-1,0),(-1,2)],
    "B4": [(0,0),(0,1),(0,2),(1,0),(1,2)],

    # L triomino
    "C1": [(0,0),(0,1),(0,-1),(1,0), (-1,0)],

    # T tetromino
    "D1": [(0,0),(0,1),(0,-1),(-1,0)],
    "D2": [(0,0),(0,1),(0,-1),(1,0)],
    "D3": [(0,0),(-1,0),(1,0),(0,1)],
    "D4": [(0,0),(-1,0),(1,0),(0,-1)],

    # Ligne de 4 horizontale
    "E1": [(0,0),(1,0),(-1,0),(0,1),(0,2)],
    "E2": [(0,0),(1,0),(-1,0),(0,-1),(0,-2)],
    "E3": [(0,0),(0,-1),(0,1),(-1,0),(-2,0)],
    "E4": [(0,0),(0,-1),(0,1),(1,0),(2,0)],

    # Ligne de 3 verticale
    "F1": [(0,0),(0,1),(0,2), (0,3)],
    "F2": [(0,0),(1,0),(2,0), (3,0)],

    # Z tetromino
    "G1": [(0,0),(0,-1),(1,-1),(-1,0),(-1,1)],
    "G2": [(0,0),(0,1),(1,1),(-1,0),(-1,-1)],
    "G3": [(0,0),(1,0),(1,1),(0,-1),(-1,-1)],
    "G4": [(0,0),(1,0),(1,-1),(0,1),(-1,1)],
 

    # Petit L (2x2 en escalier)
    "H1": [(0,0),(-1,0),(0,1)],
    "H2": [(0,0),(-1,0),(0,-1)],
    "H3": [(0,0),(1,0),(0,-1)],
    "H4": [(0,0),(1,0),(0,1)],

    # Barre verticale de 2
    "I1": [(0,0),(-1,0),(1,0),(1,1),(-1,1),(2,1)],
    "I2": [(0,0),(-1,0),(1,0),(-1,-1),(1,-1),(2,-1)],
    "I3": [(0,0),(-1,0),(1,0),(1,1),(-1,1),(-2,1)],
    "I4": [(0,0),(-1,0),(1,0),(-1,-1),(1,-1),(-2,-1)],
    "I5": [(0,0),(0,1),(0,2),(-1,0),(-1,2),(-1,3)],
    "I6": [(0,0),(0,1),(0,2),(1,0),(1,2),(1,3)],
    "I7": [(0,0),(0,1),(0,2),(-1,0),(-1,2),(-1,-1)],
    "I8": [(0,0),(0,1),(0,2),(1,0),(1,2),(1,-1)],

    # Carré 1x2 horizontal
    "J1": [(0,0),(1,0),(2,0),(0,1),(0,2)],
    "J2": [(0,0),(1,0),(2,0),(0,-1),(0,-2)],
    "J3": [(0,0),(-1,0),(-2,0),(0,-1),(0,-2)],
    "J4": [(0,0),(-1,0),(-2,0),(0,1),(0,2)],

    # L de 4 cases
    "K1": [(0,0),(0,1),(1,0),(1,1)],

    # S tetromino
    "L1": [(0,0),(-1,0),(-1,1),(1,0),(1,-1)],
    "L2": [(0,0),(-1,0),(-1,-1),(1,0),(1,1)],
    "L3": [(0,0),(0,1),(0,-1),(-1,-1),(1,1)],
    "L4": [(0,0),(0,1),(0,-1),(1,-1),(-1,1)],

    # Petit carré 2x1 + 1 au-dessus (genre Γ)
    "M1": [(0,0),(0,-1),(1,0),(1,1)],
    "M2": [(0,0),(0,1),(1,0),(1,-1)],
    "M3": [(0,0),(0,1),(-1,1),(1,0)],
    "M4": [(0,0),(0,1),(-1,0),(1,1)],

    # Carré en escalier 2x2 (Z mini)
    "N1": [(0,0),(0,1),(1,0),(1,1),(0,-1)],
    "N2": [(0,0),(0,1),(1,0),(1,1),(1,-1)],
    "N3": [(0,0),(0,1),(1,0),(1,1),(0,2)],
    "N4": [(0,0),(0,1),(1,0),(1,1),(1,2)],
    "N5": [(0,0),(0,1),(1,0),(1,1),(-1,0)],
    "N6": [(0,0),(0,1),(1,0),(1,1),(-1,1)],
    "N7": [(0,0),(0,1),(1,0),(1,1),(2,0)],
    "N8": [(0,0),(0,1),(1,0),(1,1),(2,1)],


}

def rotationsKa(shape):
    """Retourne les 4 rotations (0°, 90°, 180°, 270°) d’un polyomino"""
    #"A0": [(0,0),(0, 1),(1, 0),(2, 0)],
    #"A1": [(0,0),(0, -1),(1, 0),(2, 0)],
    #"A2": [(0,0),(0, 1),(-1, 0),(-2, 0)],
    #"A3": [(0,0),(0, -1),(-1, 0),(-2, 0)],

    rots = []
    rots.append(shape[:])

    r2 = []
    for c in shape:
        y, x = c
        r2.append((-y, x))
    rots.append(r2)

    r3 = []
    for c in shape:
        x, y = c
        r3.append((y, -x))
    rots.append(r3)

    r4 = []
    for c in shape:
        x, y = c
        r4.append((-y, -x))
    rots.append(r4)
    
    shape2 = []
    for c in shape:
        y, x = c
        shape2.append((x, y))

    rots.append(shape2[:])

    r6 = []
    for c in shape2:
        y, x = c
        r6.append((-y, x))
    rots.append(r6)

    r7 = []
    for c in shape2:
        x, y = c
        r7.append((y, -x))
    rots.append(r7)

    r8 = []
    for c in shape2:
        x, y = c
        r8.append((-y, -x))
    rots.append(r8)

    return rots

def rotationsK2(shape):
    """
    Retourne les 8 transformations (4 rotations × miroir horizontal)
    d’un polyomino représenté par une liste de coordonnées [(y,x), ...].
    """
    def rotate90(coords):
        # rotation 90°: (y, x) → (x, -y)
        return [(x, -y) for (y, x) in coords]

    def mirror(coords):
        # miroir horizontal: (y, x) → (y, -x)
        return [(y, -x) for (y, x) in coords]

    def normalize(coords):
        # recentre pour éviter les décalages : (0,0) en haut-gauche
        miny = min(y for y, _ in coords)
        minx = min(x for _, x in coords)
        return sorted([(y - miny, x - minx) for y, x in coords])

    rots = []

    current = shape
    for _ in range(4):  # 0°, 90°, 180°, 270°
        rots.append((current))
        current = rotate90(current)

    mirrored = mirror(shape)
    current = mirrored
    for _ in range(4):
        rots.append((current))
        current = rotate90(current)

    # on retire les doublons (certaines formes symétriques ont < 8 variantes)
    unique_rots = []
    seen = set()
    for r in rots:
        t = tuple(r)
        if t not in seen:
            seen.add(t)
            unique_rots.append(r)

    return unique_rots

def rotationsK(shape):
    """
    Génère toutes les rotations (90°, 180°, 270°) et symétries (flip) 
    sans changer les signes des coordonnées (on garde les négatifs).
    """
    shapes = set()

    for flip_y in [1, -1]:  # symétrie verticale
        for flip_x in [1, -1]:  # symétrie horizontale
            current = [(y * flip_y, x * flip_x) for y, x in shape]
            for _ in range(4):  # 4 rotations
                current = [(-x, y) for y, x in current]  # rotation 90°
                shapes.add(tuple(sorted(current)))  # utiliser tuple pour set

    # retour sous forme de listes
    return [list(s) for s in shapes]


def polyominoDLX(N, M, CPolio, g):
    global polyominos_with_rot, ids
   
    #print(polyominos_with_rot, file=sys.stderr, flush=True)

    row_id = 0
    num_cells = N * M
    num_pieces = len(polyominos_with_rot)
    total_cols = num_cells + len(ids)

    row_map = {}


    N_cols = total_cols  # contraintes
    dlx = ManageLink(N_cols)
    row_map = {}  # row_id -> (r,c,val)

   
    object = {0:[(0,0),(1,0),(2,0)]}#,
              #1:[(0,0)]}

    polyominoss = {
        "cross": [(0,0), (0,-1), (0,1), (-1,0), (1,0)],
        "L": [(0,0), (1,0), (2,0), (2,1)],
        "square": [(0,0), (0,1), (1,0), (1,1)],
        "T": [(0,0), (0,-1), (0,1), (1,0)],
    }

    polyominos2 = {
        "I": [(0,0), (1,0), (2,0), (3,0)],
        "O": [(0,0), (0,1), (1,0), (1,1)],
        "T": [(0,0), (0,-1), (0,1), (1,0)],
        "L": [(0,0), (1,0), (2,0), (2,1)],
        "J": [(0,0), (1,0), (2,0), (2,-1)],
        "S": [(0,0), (0,1), (1,-1), (1,0)],
        "Z": [(0,0), (0,-1), (1,0), (1,1)],
    }

    
    row_id = 0
    idx = 0
    id_piece = []
    for name, shape in polyominos_with_rot.items():
        # trouver les positions possibles
        if name[0] not in ids:
            idx +=1
            continue
        id_piece.append(name)
        max_r = N - max(dr for dr, _ in shape )
        max_c = M - max(dc for _, dc in shape )
        min_r = -min(dr for dr, _ in shape )
        min_c = -min(dc for _, dc in shape )
        

        #print(max_r, max_c, min_r, min_c, file=sys.stderr, flush=True)
      
        for r in range(min_r, max_r):
            for c in range(min_c, max_c):
                #dlx.addNode(row_id, r*N+c)
                valid = True
                
                for dr, dc in shape:
                    nr, nc = r + dr, c + dc
                    if g[nr][nc] == '.':
                        valid = False
                        break
                
                if valid:
                    nodes = []
                    for dr, dc in shape:
                        nr, nc = r + dr, c + dc
                        col_idx = nr*M + nc
                        nodes.append(dlx.addNode(row_id, col_idx))

                    col_idx = N*M + ids.index(name[0])
                    nodes.append(dlx.addNode(row_id, col_idx))

                    dlx.linkRowNodes(nodes)
                    row_map[row_id] = (r, c, name)
                    row_id += 1

                                        
        idx +=1

                
    
    for r in range(0, N):
        for c in range(0, M):
            if g[r][c] == '.':
                nodes = []
                nr, nc = r , c
                col_idx = nr*M + nc
                nodes.append(dlx.addNode(row_id, col_idx))

                dlx.linkRowNodes(nodes)
                row_map[row_id] = (r, c, "")
                row_id += 1
    
    """
    for i in range(len(ids)):
        nodes = []
        #if 'ABCDEFGHIJKLMN'[i] in ids:
        col_idx = N*M + i
        nodes.append(dlx.addNode(row_id, col_idx))

        dlx.linkRowNodes(nodes)
        row_map[row_id] = (-1, -1, 'ABCDEFGHIJKLMN'[0])
        row_id += 1
    """
 
    solution = []
    sf = []

    """
    for forced_piece in id_piece:
        forced_idx = list(polyominos_with_rot.keys()).index(forced_piece)
        forced_col = dlx.colHeader[N*M + forced_idx]
        dlx.coverp(forced_col)
    """

    count = 0
    
    def search():
        nonlocal count, sf, solution

        if dlx.root.R == dlx.root:
            """
            piece = set()
            valid = True
            for rid in solution:
                r, c, val = row_map[rid]
                if g[r][c] == '.' :
                    valid=False
                    break
                piece.add(val[0])
            if valid and len(piece) == len(CPolio.keys()):
                sf.append(solution[:])
            """
            sf.append(solution[:])
            count +=1
            print('sol', file=sys.stderr, flush=True)
            return True  # toutes les colonnes couvertes

        # choisir la colonne avec le moins de 1
        c = dlx.root.R
        min_size = c.size
        col = c
        while c != dlx.root:
            if c.size < min_size:
                min_size = c.size
                col = c
            c = c.R

        dlx.cover(col)
        r = col.D
        while r != col:
            solution.append(r.rid)
            j = r.R
            while j != r:
                dlx.cover(j.C)
                j = j.R
            if search():
                #if count == 1:
                return True
            # backtrack
            solution.pop()
            j = r.L
            while j != r:
                dlx.uncover(j.C)
                j = j.L
            r = r.D
        dlx.uncover(col)
        return False

    search()
        
    colors = [
        ("\033[39m", "Noir"),
        ("\033[31m", "Rouge"),
        ("\033[32m", "Vert"),
        ("\033[33m", "Jaune"),
        ("\033[34m", "Bleu"),
        ("\033[35m", "Magenta"),
        ("\033[36m", "Cyan"),
        ("\033[37m", "Blanc"),
        ("\033[90m", "Gris clair"),
        ("\033[91m", "Rouge clair"),
        ("\033[92m", "Vert clair"),
        ("\033[93m", "Jaune clair"),
        ("\033[94m", "Bleu clair"),
        ("\033[95m", "Magenta clair")
    ]
    RESET = "\033[0m"

    print("nb sol=", len(sf), file=sys.stderr, flush=True)

    # reconstruction de la grille colorée
    fsolved = []
    for s in sf:
        solved = [['.'] * M for _ in range(N)]
        indcol = 0  # on réinitialise pour chaque solution

        for rid in s:
            r, c, val = row_map[rid]
            col = colors[indcol % len(colors)][0]  # couleur cyclique
            if val not in polyominos_with_rot.keys():continue
            #if val[0] != 'L': continue
            for y, x in polyominos_with_rot[val]:
                solved[r + y][c + x] = val[0]
            indcol = (indcol + 1) % len(colors)  # prochaine couleur

      
        for r in range(0, N):
            for c in range(0, M):
                if g[r][c] == '.':
                    solved[r][c] = '.'

        fsolved.append(solved)
        break

    # affichage de toutes les grilles
    for grid in fsolved:
        for row in grid:
            print("".join(row))
        print()


N = h
M = w

start = time.perf_counter()
polyominoDLX(N, M, counter_polio, g)
end = time.perf_counter()
print("time:", end-start, N, M,file=sys.stderr, flush=True)


