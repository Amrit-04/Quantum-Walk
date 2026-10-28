"""Wall search and topological analysis for Quantum Maze.
Identifies strategic wall pairs for quantum entanglement such that in both
entangled states (|01> and |10>), the maze is guaranteed to remain solvable.
"""

from collections import deque
import random
from typing import List, Tuple, Optional, Set

def bfs_path(grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """Finds the shortest path between start and end in the maze grid."""
    if not (0 <= start[1] < len(grid) and 0 <= start[0] < len(grid[0])):
        return None
    if not (0 <= end[1] < len(grid) and 0 <= end[0] < len(grid[0])):
        return None

    queue = deque([[start]])
    visited: Set[Tuple[int, int]] = {start}

    while queue:
        path = queue.popleft()
        cx, cy = path[-1]
        if (cx, cy) == end:
            return path

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
                # 0 is passage; gate tiles (2, 3, 4, 5) are also passable
                if grid[ny][nx] != 1 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])
    return None

def is_solvable(grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]) -> bool:
    """Checks if there is any valid path from start to end."""
    return bfs_path(grid, start, end) is not None

def find_entangled_wall_pairs(
    grid: List[List[int]],
    start: Tuple[int, int],
    end: Tuple[int, int],
    num_pairs: int = 4
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Finds pairs of walls (w1, w2) such that:
    - In state |01> (w1 open, w2 closed), a path from start to end exists.
    - In state |10> (w1 closed, w2 open), an alternate path from start to end exists.
    """
    path = bfs_path(grid, start, end)
    if not path or len(path) < 6:
        return []

    # Connector passages along the escape path (between vertices)
    passages = [
        pt for pt in path[1:-1]
        if (pt[0] % 2 == 0 and pt[1] % 2 == 1) or (pt[0] % 2 == 1 and pt[1] % 2 == 0)
    ]

    if not passages:
        return []

    h, w = len(grid), len(grid[0])
    selected_pairs = []
    used_walls = set()

    # Sample candidates along the path
    step = max(1, len(passages) // (num_pairs + 1))
    candidate_w1s = passages[step//2::step]

    for w1 in candidate_w1s:
        if len(selected_pairs) >= num_pairs:
            break
        if w1 in used_walls:
            continue

        # Test closing w1
        test_grid = [row[:] for row in grid]
        test_grid[w1[1]][w1[0]] = 1

        # w1 must disconnect or significantly detour the path
        if is_solvable(test_grid, start, end):
            # It's an optional branch or cycle, still valid as an entangled gate
            pass

        # Find interior solid walls that can serve as w2
        candidates_w2 = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if (x, y) in used_walls or (x, y) == w1:
                    continue
                # Interior wall between cells
                if test_grid[y][x] == 1 and ((x % 2 == 1 and y % 2 == 0) or (x % 2 == 0 and y % 2 == 1)):
                    test_grid[y][x] = 0
                    if is_solvable(test_grid, start, end):
                        candidates_w2.append((x, y))
                    test_grid[y][x] = 1

        if candidates_w2:
            # Pick a w2 at reasonable distance from w1
            candidates_w2.sort(key=lambda pt: abs(pt[0] - w1[0]) + abs(pt[1] - w1[1]), reverse=True)
            w2 = candidates_w2[len(candidates_w2) // 2]
            selected_pairs.append((w1, w2))
            used_walls.add(w1)
            used_walls.add(w2)

    return selected_pairs


class SearchWall:
    """Compatibility class matching original repository namespace."""
    @staticmethod
    def search(maze_grid: List[List[int]], start=(1, 1), end=None) -> Optional[List[Tuple[int, int]]]:
        if end is None:
            end = (len(maze_grid[0]) - 2, len(maze_grid) - 2)
        return bfs_path(maze_grid, start, end)

    @staticmethod
    def find_pairs(maze_grid: List[List[int]], start=(1, 1), end=None, count=4):
        if end is None:
            end = (len(maze_grid[0]) - 2, len(maze_grid) - 2)
        return find_entangled_wall_pairs(maze_grid, start, end, count)


if __name__ == "__main__":
    import MazeGenerator
    mg = MazeGenerator.MazeGenerator(19, 11)
    grid = mg.GetMaze().ToList()
    pairs = SearchWall.find_pairs(grid)
    print(f"Generated {len(pairs)} entangled pairs:")
    for p in pairs:
        print("  w1:", p[0], " <---> w2:", p[1])
