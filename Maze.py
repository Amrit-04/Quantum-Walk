"""2D Maze representation for Quantum Maze.
Converts graph vertex connectivity into a 2D tile grid with walls, corridors,
and distributed quantum gate pickups (X, Z, S, H).
"""

from typing import List, Dict, Optional
import Qrandom

class Maze(object):
    def __init__(self, w: int, h: int):
        self.m_W = w
        self.m_H = h 
        self.m_Maze: Dict[str, List[int]] = {}

    def SetWay(self, f: int, t: int):
        self.SetOrderedWay(f, t)
        self.SetOrderedWay(t, f)
    
    def SetOrderedWay(self, f: int, t: int):
        sf = str(f)
        if sf not in self.m_Maze:
            self.m_Maze[sf] = []
        if t not in self.m_Maze[sf]:
            self.m_Maze[sf].append(t)

    def HasPath(self, f: int, t: int) -> bool:
        sf = str(f)
        if sf not in self.m_Maze:
            return False
        return t in self.m_Maze[sf]

    def GetVertex(self, x: int, y: int) -> int:
        return self.m_W * y + x

    def Print(self):
        output = ''
        for x in range(self.m_W):
            output += ' __'
        print(output)
        for y in range(self.m_H):
            output = ''
            for x in range(self.m_W):
                if x != 0 and self.HasPath(self.GetVertex(x, y), self.GetVertex(x - 1, y)):
                    output += ' '
                else:
                    output += '|'
                if self.HasPath(self.GetVertex(x, y), self.GetVertex(x, y + 1)):
                    output += '  '
                else:
                    output += '__'
            print(output + '|')
        print('')

    def ToList(self) -> List[List[int]]:
        """
        Converts the maze topology into a 2D matrix of dimensions (2*H+1) x (2*W+1).
        0: Passage
        1: Wall
        2: Pauli-X gate tile
        3: Pauli-Z gate tile
        4: Phase-S gate tile
        5: Hadamard-H gate tile
        """
        grid_h = 2 * self.m_H + 1
        grid_w = 2 * self.m_W + 1
        maze_list = [[1 for _ in range(grid_w)] for _ in range(grid_h)]

        # Set corridor cells and connecting paths
        for y in range(self.m_H):
            for x in range(self.m_W):
                # Corridor cell
                maze_list[2 * y + 1][2 * x + 1] = 0

                # Left wall / passage
                if x > 0 and self.HasPath(self.GetVertex(x, y), self.GetVertex(x - 1, y)):
                    maze_list[2 * y + 1][2 * x] = 0
                else:
                    maze_list[2 * y + 1][2 * x] = 1

                # Down wall / passage
                if y < self.m_H - 1 and self.HasPath(self.GetVertex(x, y), self.GetVertex(x, y + 1)):
                    maze_list[2 * y + 2][2 * x + 1] = 0
                else:
                    maze_list[2 * y + 2][2 * x + 1] = 1

        # Border walls are already 1 by default initialization

        # Strategically place quantum gates on open passages (excluding start and finish)
        start_pt = (1, 1)
        finish_pt = (grid_w - 2, grid_h - 2)

        open_cells = [
            (cx, cy)
            for cy in range(1, grid_h - 1)
            for cx in range(1, grid_w - 1)
            if maze_list[cy][cx] == 0 and (cx, cy) != start_pt and (cx, cy) != finish_pt
        ]

        # Place 4 quantum gates: X (2), Z (3), S (4), H (5)
        # Using quantum random selection if enough open cells exist
        gate_types = [2, 3, 4, 5]  # X, Z, S, H
        if len(open_cells) >= len(gate_types):
            # Pick cells distributed across quarters of the list
            step = len(open_cells) // len(gate_types)
            for i, gate_code in enumerate(gate_types):
                idx = i * step + Qrandom.qrandint(0, step - 1)
                gx, gy = open_cells[idx]
                maze_list[gy][gx] = gate_code

        return maze_list
