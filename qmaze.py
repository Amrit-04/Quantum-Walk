"""Quantum Entanglement Manager for Quantum Maze (QuMa).
Simulates 2-qubit Bell states (|Phi+>, |Psi+>) using Qiskit.
Manages entangled wall pairs, observer wave-function collapse, and quantum gate applications.
"""

from typing import List, Tuple, Optional, Dict, Any
import random
import Qrandom

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    _qiskit_available = True
    _sim = AerSimulator()
except Exception:
    try:
        from qiskit import QuantumCircuit
        from qiskit.providers.basic_provider import BasicSimulator
        _qiskit_available = True
        _sim = BasicSimulator()
    except Exception:
        _qiskit_available = False
        _sim = None


class EntangledWallPair:
    """Represents a pair of entangled walls linked via a 2-qubit quantum circuit."""
    def __init__(self, wall_a: Tuple[int, int], wall_b: Tuple[int, int], pair_id: int = 1):
        self.pair_id = pair_id
        self.wall_a = wall_a  # (x, y)
        self.wall_b = wall_b  # (x, y)
        self.is_measured = False
        self.measured_state: Optional[Tuple[int, int]] = None  # (state_a, state_b): 0=open, 1=solid
        self.gates_applied: List[str] = []
        self._init_circuit()

    def _init_circuit(self):
        """Initializes 2-qubit Bell state |Psi+> = (|01> + |10>) / sqrt(2)."""
        self.gates_applied.clear()
        if _qiskit_available and _sim is not None:
            self.circuit = QuantumCircuit(2)
            self.circuit.h(0)
            self.circuit.cx(0, 1)
            self.circuit.x(1)  # Anti-correlated Bell state
        else:
            self.circuit = None

    def apply_gate(self, gate: str) -> str:
        """Applies a quantum gate (H, X, Z, S) to the entangled circuit."""
        gate = gate.upper()
        self.gates_applied.append(gate)

        if gate == "H":
            # Re-superpose
            self.is_measured = False
            self.measured_state = None
            self._init_circuit()
            return f"Pair #{self.pair_id} re-superposed into equal superposition state!"

        if gate == "X":
            # Bit flip (NOT)
            if self.is_measured and self.measured_state:
                # Invert measured state: (0, 1) <-> (1, 0)
                b0, b1 = self.measured_state
                self.measured_state = (1 - b0, 1 - b1)
                return f"Pair #{self.pair_id} inverted via Pauli-X: Wall A is {'OPEN' if self.measured_state[0]==0 else 'SOLID'}, Wall B is {'OPEN' if self.measured_state[1]==0 else 'SOLID'}."
            elif self.circuit is not None:
                self.circuit.x(0)
                return f"Applied Pauli-X gate to Qubit 0 of Pair #{self.pair_id}."
            else:
                return f"Pauli-X applied to Pair #{self.pair_id}."

        if gate == "Z":
            if self.circuit is not None:
                self.circuit.z(0)
            return f"Applied Pauli-Z phase flip to Pair #{self.pair_id}."

        if gate == "S":
            if self.circuit is not None:
                self.circuit.s(0)
            return f"Applied Phase S gate (pi/2) to Pair #{self.pair_id}."

        return f"Unknown gate {gate} ignored."

    def measure(self) -> Tuple[int, int]:
        """Measures the 2-qubit quantum state, collapsing it to classical bits."""
        if self.is_measured and self.measured_state is not None:
            return self.measured_state

        if _qiskit_available and _sim is not None and self.circuit is not None:
            try:
                meas_circuit = self.circuit.copy()
                meas_circuit.measure_all()
                result = _sim.run(meas_circuit, shots=1).result()
                counts = result.get_counts()
                bitstring = list(counts.keys())[0].replace(" ", "")
                # Qiskit registers bitstrings right-to-left: bitstring[-1] is q0, bitstring[-2] is q1
                b0 = int(bitstring[-1])
                b1 = int(bitstring[-2])
                self.measured_state = (b0, b1)
            except Exception:
                # Fallback to quantum random generator
                b0 = Qrandom.qrandom()
                b1 = 1 - b0
                self.measured_state = (b0, b1)
        else:
            b0 = Qrandom.qrandom()
            b1 = 1 - b0
            self.measured_state = (b0, b1)

        self.is_measured = True
        return self.measured_state


class QuantumMazeManager:
    """Controls the overall quantum state of the maze walls and player interactions."""
    def __init__(self, maze_grid: List[List[int]], start: Tuple[int, int] = (1, 1), end: Optional[Tuple[int, int]] = None):
        self.grid = maze_grid
        self.start = start
        self.end = end or (len(maze_grid[0]) - 2, len(maze_grid) - 2)
        self.pairs: List[EntangledWallPair] = []
        self.recent_events: List[str] = []
        self._setup_entangled_pairs()

    def _setup_entangled_pairs(self):
        """Finds and initializes entangled wall pairs across the maze."""
        from searchWall import find_entangled_wall_pairs
        found_pairs = find_entangled_wall_pairs(self.grid, self.start, self.end, num_pairs=4)
        self.pairs.clear()

        for idx, (w1, w2) in enumerate(found_pairs, start=1):
            pair = EntangledWallPair(w1, w2, pair_id=idx)
            self.pairs.append(pair)
            # Mark walls as in superposition (tile code 6)
            self.grid[w1[1]][w1[0]] = 6
            self.grid[w2[1]][w2[0]] = 6

        self.log_event(f"Initialized {len(self.pairs)} quantum entangled wall pairs in superposition |Psi+>.")

    def log_event(self, msg: str):
        self.recent_events.append(msg)
        if len(self.recent_events) > 8:
            self.recent_events.pop(0)

    def check_player_observation(self, player_x: int, player_y: int) -> List[str]:
        """
        If the player is adjacent to or on an unmeasured entangled wall,
        trigger observer quantum measurement and collapse the state.
        """
        messages = []
        for pair in self.pairs:
            if pair.is_measured:
                continue

            dist_a = abs(player_x - pair.wall_a[0]) + abs(player_y - pair.wall_a[1])
            dist_b = abs(player_x - pair.wall_b[0]) + abs(player_y - pair.wall_b[1])

            # Adjacent (dist <= 1) acts as an observer measurement
            if dist_a <= 1 or dist_b <= 1:
                b0, b1 = pair.measure()
                # Apply collapsed states to the maze grid
                self.grid[pair.wall_a[1]][pair.wall_a[0]] = b0  # 0: passage, 1: wall
                self.grid[pair.wall_b[1]][pair.wall_b[0]] = b1

                observed_wall = "A" if dist_a <= dist_b else "B"
                state_str = f"|{b1}{b0}>"
                msg = (
                    f"Observation at Wall {observed_wall}! Wave function collapsed: {state_str}. "
                    f"Wall A {pair.wall_a} is {'OPEN' if b0==0 else 'SOLID'}, "
                    f"Wall B {pair.wall_b} is {'OPEN' if b1==0 else 'SOLID'}."
                )
                self.log_event(msg)
                messages.append(msg)

        return messages

    def apply_gate_to_nearest(self, player_x: int, player_y: int, gate: str) -> str:
        """Applies a quantum gate to the closest entangled wall pair."""
        if not self.pairs:
            return "No entangled wall pairs in maze."

        # Find closest pair
        def pair_dist(p: EntangledWallPair):
            da = abs(player_x - p.wall_a[0]) + abs(player_y - p.wall_a[1])
            db = abs(player_x - p.wall_b[0]) + abs(player_y - p.wall_b[1])
            return min(da, db)

        closest = min(self.pairs, key=pair_dist)
        result = closest.apply_gate(gate)

        # Sync grid if measured or re-superposed
        if closest.is_measured and closest.measured_state:
            self.grid[closest.wall_a[1]][closest.wall_a[0]] = closest.measured_state[0]
            self.grid[closest.wall_b[1]][closest.wall_b[0]] = closest.measured_state[1]
        else:
            self.grid[closest.wall_a[1]][closest.wall_a[0]] = 6
            self.grid[closest.wall_b[1]][closest.wall_b[0]] = 6

        self.log_event(result)
        return result


if __name__ == "__main__":
    import MazeGenerator
    mg = MazeGenerator.MazeGenerator(19, 11)
    grid = mg.GetMaze().ToList()
    qm = QuantumMazeManager(grid)
    print("Events:")
    for ev in qm.recent_events:
        print(" ", ev)
    if qm.pairs:
        p0 = qm.pairs[0]
        print(f"Triggering observation near Wall A {p0.wall_a}...")
        qm.check_player_observation(p0.wall_a[0] + 1, p0.wall_a[1])
        print("After collapse events:")
        for ev in qm.recent_events:
            print(" ", ev)
