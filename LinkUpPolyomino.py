# -*- coding: latin-1 -*-
import sys
import time
from itertools import combinations, permutations
from collections import Counter, defaultdict
import copy
from colorama import Fore, Style, init
init(autoreset=True)
sys.setrecursionlimit(10**9)

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

polyominos = {
    # Carré 2x2
    "A": [(0,0),(0, 1),(1, 0),(2, 0)],
    #"A1": [(0,0),(0, -1),(1, 0),(2, 0)],
    #"A2": [(0,0),(0, 1),(-1, 0),(-2, 0)],
    #"A3": [(0,0),(0, -1),(-1, 0),(-2, 0)],

    # Ligne de 3 horizontale
    "B": [(0,0),(0,1),(1,0),(2,0),(2,1)],

    # L triomino
    "C": [(0,0),(0,1),(0,-1),(1,0), (-1,0)],

    # T tetromino
    "D": [(0,0),(0,1),(0,-1),(-1,0)],

    # Ligne de 4 horizontale
    "E": [(0,0),(1,0),(-1,0),(0,1),(0,2)],

    # Ligne de 3 verticale
    "F": [(0,0),(0,1),(0,2), (0,3)],

    # Z tetromino
    "G": [(0,0),(0,-1),(1,-1),(-1,0),(-1,1)],

    # Petit L (2x2 en escalier)
    "H": [(0,0),(-1,0),(0,1)],

    # Barre verticale de 2
    "I": [(0,0),(-1,0),(1,0),(1,1),(-1,1),(2,1)],

    # Carré 1x2 horizontal
    "J": [(0,0),(1,0),(2,0),(0,1),(0,2)],

    # L de 4 cases
    "K": [(0,0),(0,1),(1,0),(1,1)],

    # S tetromino
    "L": [(0,0),(-1,0),(-1,1),(1,0),(1,-1)],

    # Petit carré 2x1 + 1 au-dessus (genre Γ)
    "M": [(0,0),(0,-1),(1,0),(1,1)],

    # Carré en escalier 2x2 (Z mini)
    "N": [(0,0),(0,1),(1,0),(1,1),(0,-1)],
}

def rotationsK(shape):
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



def polyominoDLX(N):
    global polyominos
    N_cols = (N)*(N)  # contraintes
    dlx = ManageLink(N_cols)
    row_map = {}  # row_id -> (r,c,val)

    baseN = N*N

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

    polyominos_with_rot = defaultdict()
    
    for name, coords in polyominos.items():
        rot = rotationsK(coords)
        i = 0
        for r in rot:
            polyominos_with_rot[name+str(i)] = r
            i+=1

    #print(polyominos_with_rot)

    row_id = 0
    for name, shape in polyominos_with_rot.items():
        # trouver les positions possibles
        shape = [shape]
        max_r = N - max(dr for shape2 in shape for dr, _ in shape2 )
        max_c = N - max(dc for shape2 in shape for _, dc in shape2 )
        min_r = -min(dr for shape2 in shape for dr, _ in shape2 )
        min_c = -min(dc for shape2 in shape for _, dc in shape2 )

        #print(max_r, max_c, min_r, min_c)
      
        for r in range(min_r, max_r):
            for c in range(min_c, max_c):
                nodes = []#dlx.addNode(row_id, r*N+c)
                for comp in shape:
                    for dr, dc in comp:
                        nr, nc = r + dr, c + dc
                        col_idx = nr*N + nc
                        nodes.append(dlx.addNode(row_id, col_idx))
                    dlx.linkRowNodes(nodes)
                    row_map[row_id] = (r, c, name)
                    row_id += 1

 
    solution = []
    sf = []

    count = 0
    
    def search():
        nonlocal count

        if dlx.root.R == dlx.root:
            sf.append(solution[:])
            count +=1
            
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
                if count >= 5:
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

    # reconstruction de la grille colorée
    fsolved = []
    for s in sf:
        solved = [['.'] * N for _ in range(N)]
        indcol = 0  # on réinitialise pour chaque solution

        for rid in s:
            r, c, val = row_map[rid]
            col = colors[indcol % len(colors)][0]  # couleur cyclique
            for y, x in polyominos_with_rot[val]:
                solved[r + y][c + x] = col + val+ RESET
            indcol = (indcol + 1) % len(colors)  # prochaine couleur

        fsolved.append(solved)

    # affichage de toutes les grilles
    for grid in fsolved:
        for row in grid:
            print("".join(row))
        print()


N = 20

start = time.perf_counter()
polyominoDLX(N)
end = time.perf_counter()
print("time:", end-start)


