"""Maze generator using Eller's Algorithm with Quantum Randomness (Qiskit).
Guarantees a fully connected, single-connected spanning tree maze where
every cell is reachable from every other cell.
"""

from Maze import Maze
import Qrandom
from collections import defaultdict
from typing import List

class MazeGenerator(object):
    def __init__(self, w: int, h: int):
        self.m_W = max(1, w)
        self.m_H = max(1, h)
        self.Generate()

    def Generate(self) -> Maze:
        self.m_Maze = Maze(self.m_W, self.m_H)
        last_set_number = 0
        current_sets: List[int] = [0] * self.m_W

        # Initialize first row sets
        for x in range(self.m_W):
            last_set_number += 1
            current_sets[x] = last_set_number

        for y in range(self.m_H - 1):
            # 1. Join adjacent cells in different sets with 50% quantum probability
            for x in range(self.m_W - 1):
                if current_sets[x] != current_sets[x + 1] and Qrandom.qrandom_bool():
                    self.m_Maze.SetWay(self.m_Maze.GetVertex(x, y), self.m_Maze.GetVertex(x + 1, y))
                    s_keep = current_sets[x]
                    s_replace = current_sets[x + 1]
                    for i in range(self.m_W):
                        if current_sets[i] == s_replace:
                            current_sets[i] = s_keep

            # 2. Carve vertical paths down: ensure EVERY set has at least one downward connection
            set_cells = defaultdict(list)
            for x in range(self.m_W):
                set_cells[current_sets[x]].append(x)

            down_cols = set()
            for s_id, cols in set_cells.items():
                forced_col = cols[Qrandom.qrandint(0, len(cols) - 1)]
                down_cols.add(forced_col)
                for col in cols:
                    if col != forced_col and Qrandom.qrandom_bool():
                        down_cols.add(col)

            for col in down_cols:
                self.m_Maze.SetWay(self.m_Maze.GetVertex(col, y), self.m_Maze.GetVertex(col, y + 1))

            # 3. Prepare sets for the next row
            next_sets = [0] * self.m_W
            for x in range(self.m_W):
                if x in down_cols:
                    next_sets[x] = current_sets[x]
                else:
                    last_set_number += 1
                    next_sets[x] = last_set_number
            current_sets = next_sets

        # 4. Final row: join all adjacent cells that are in different sets
        y = self.m_H - 1
        for x in range(self.m_W - 1):
            if current_sets[x] != current_sets[x + 1]:
                self.m_Maze.SetWay(self.m_Maze.GetVertex(x, y), self.m_Maze.GetVertex(x + 1, y))
                s_keep = current_sets[x]
                s_replace = current_sets[x + 1]
                for i in range(self.m_W):
                    if current_sets[i] == s_replace:
                        current_sets[i] = s_keep

        return self.m_Maze

    def GetMaze(self) -> Maze:
        return self.m_Maze


if __name__ == "__main__":
    print(f"Generating quantum maze using {Qrandom.get_backend_name()}...")
    mg = MazeGenerator(10, 6)
    maze = mg.GetMaze()
    maze.Print()
    print("Maze generated successfully!")
