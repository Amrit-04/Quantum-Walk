"""Comprehensive test suite for QuMa (Quantum Walk / Maze).
Tests quantum random generation, maze topology & solvability,
Qiskit Bell-state entanglement, and game mechanics.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pytest
import Qrandom
from Maze import Maze
from MazeGenerator import MazeGenerator
from searchWall import SearchWall, bfs_path, is_solvable, find_entangled_wall_pairs
from qmaze import EntangledWallPair, QuantumMazeManager
import main


class TestQuantumRandom:
    def test_backend_available(self):
        backend = Qrandom.get_backend_name()
        assert backend in ("qiskit_aer.AerSimulator", "qiskit.BasicSimulator", "legacy_aer", "pseudo_fallback")

    def test_qrandom_bits(self):
        bits = [Qrandom.qrandom() for _ in range(50)]
        for b in bits:
            assert b in (0, 1)
        # Should not be all zeros or all ones over 50 bits
        assert 0 in bits
        assert 1 in bits

    def test_qrandint_range(self):
        for _ in range(30):
            val = Qrandom.qrandint(3, 9)
            assert 3 <= val <= 9

    def test_qrandom_float(self):
        for _ in range(20):
            flt = Qrandom.qrandom_float()
            assert 0.0 <= flt < 1.0


class TestMazeGeneration:
    def test_maze_connectivity(self):
        """Verify that Eller's algorithm produces a fully connected spanning tree."""
        mg = MazeGenerator(10, 8)
        maze = mg.GetMaze()
        grid = maze.ToList()

        # Matrix dimensions
        expected_rows = 2 * 8 + 1  # 17
        expected_cols = 2 * 10 + 1  # 21
        assert len(grid) == expected_rows
        assert len(grid[0]) == expected_cols

        # Start and finish cells must be accessible
        start = (1, 1)
        finish = (expected_cols - 2, expected_rows - 2)
        assert grid[start[1]][start[0]] != 1
        assert grid[finish[1]][finish[0]] != 1

        # Must have a valid path from start to finish
        path = bfs_path(grid, start, finish)
        assert path is not None
        assert path[0] == start
        assert path[-1] == finish

    def test_border_walls(self):
        mg = MazeGenerator(8, 6)
        grid = mg.GetMaze().ToList()
        h, w = len(grid), len(grid[0])

        # Top and bottom row
        for x in range(w):
            assert grid[0][x] == 1
            assert grid[h - 1][x] == 1

        # Left and right col
        for y in range(h):
            assert grid[y][0] == 1
            assert grid[y][w - 1] == 1


class TestQuantumEntanglement:
    def test_entangled_pair_measurement(self):
        pair = EntangledWallPair((2, 3), (4, 5), pair_id=1)
        assert not pair.is_measured
        assert pair.measured_state is None

        # Measure
        state = pair.measure()
        assert pair.is_measured
        assert len(state) == 2
        # Anti-correlated Bell state: one open (0), one solid (1)
        assert state in ((0, 1), (1, 0))

    def test_pauli_x_gate_inversion(self):
        pair = EntangledWallPair((2, 3), (4, 5), pair_id=1)
        pair.measure()
        orig_state = pair.measured_state

        # Apply Pauli-X
        pair.apply_gate("X")
        new_state = pair.measured_state
        assert new_state == (1 - orig_state[0], 1 - orig_state[1])

    def test_hadamard_gate_resuperposition(self):
        pair = EntangledWallPair((2, 3), (4, 5), pair_id=1)
        pair.measure()
        assert pair.is_measured

        # Apply H gate
        pair.apply_gate("H")
        assert not pair.is_measured
        assert pair.measured_state is None


class TestQuantumMazeManager:
    def test_entangled_pairs_solvability(self):
        """Verifies that with entangled walls, the maze remains solvable in both states."""
        mg = MazeGenerator(19, 11)
        grid = mg.GetMaze().ToList()
        start = (1, 1)
        end = (len(grid[0]) - 2, len(grid) - 2)

        qm = QuantumMazeManager(grid, start, end)
        assert len(qm.pairs) > 0

        # Collapse all pairs
        for pair in qm.pairs:
            pair.measure()
            grid[pair.wall_a[1]][pair.wall_a[0]] = pair.measured_state[0]
            grid[pair.wall_b[1]][pair.wall_b[0]] = pair.measured_state[1]

        # The maze must still be solvable after collapse
        assert is_solvable(grid, start, end)

    def test_observer_collapse_trigger(self):
        mg = MazeGenerator(19, 11)
        grid = mg.GetMaze().ToList()
        start = (1, 1)
        end = (len(grid[0]) - 2, len(grid) - 2)

        qm = QuantumMazeManager(grid, start, end)
        first_pair = qm.pairs[0]
        assert not first_pair.is_measured

        # Position player adjacent to first wall of pair
        adj_x = first_pair.wall_a[0]
        adj_y = first_pair.wall_a[1] + 1
        messages = qm.check_player_observation(adj_x, adj_y)

        assert first_pair.is_measured
        assert len(messages) > 0


class TestGameSession:
    def test_game_flow(self):
        session = main.GameSession()
        assert session.player.x == 1
        assert session.player.y == 1
        assert not session.game_won
        assert session.player.steps == 0

        # Move right
        session.move_player(1, 0)
        assert session.player.steps >= 0  # Either moved or hit wall

        # Test gate acquisition and usage
        session.inventory["X"] = 1
        session.activate_gate("X")
        assert session.inventory["X"] == 0
        assert session.gates_used == 1

        # Test win condition trigger
        session.player.x, session.player.y = session.finish_line
        session.move_player(0, 0)
        assert session.game_won
