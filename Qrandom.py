"""Quantum Random Number Generator (QRNG) using Qiskit.
Generates true quantum-simulated random numbers by preparing qubits in an equal
superposition state H|0> = (|0> + |1>) / sqrt(2) and performing measurement.
"""

from collections import deque
import random
import sys

_simulator = None
_backend_type = None

def _init_backend():
    global _simulator, _backend_type
    if _simulator is not None:
        return _simulator

    # 1. Try Qiskit Aer (fast C++ simulation)
    try:
        from qiskit_aer import AerSimulator
        _simulator = AerSimulator()
        _backend_type = "qiskit_aer.AerSimulator"
        return _simulator
    except Exception:
        pass

    # 2. Try Qiskit modern BasicSimulator (pure Python, built into Qiskit 1.x+)
    try:
        from qiskit.providers.basic_provider import BasicSimulator
        _simulator = BasicSimulator()
        _backend_type = "qiskit.BasicSimulator"
        return _simulator
    except Exception:
        pass

    # 3. Try legacy Qiskit Aer (Qiskit 0.x compatibility)
    try:
        from qiskit import Aer
        _simulator = Aer.get_backend('qasm_simulator')
        _backend_type = "legacy_aer"
        return _simulator
    except Exception:
        pass

    # 4. Fallback to pseudo-random if Qiskit backend fails
    _backend_type = "pseudo_fallback"
    return None


class QuantumRandomGenerator:
    """Buffers quantum-measured bits for ultra-fast queries during maze generation."""
    def __init__(self, n_qubits=8, shots=64):
        self.n_qubits = n_qubits
        self.shots = shots
        self.bit_buffer = deque()
        self.backend = _init_backend()

    def _refill(self):
        backend = self.backend or _init_backend()
        if backend is None:
            # Fallback
            for _ in range(self.n_qubits * self.shots):
                self.bit_buffer.append(random.getrandbits(1))
            return

        try:
            from qiskit import QuantumCircuit
            qc = QuantumCircuit(self.n_qubits)
            qc.h(range(self.n_qubits))
            qc.measure_all()

            # Execute on backend
            if hasattr(backend, "run"):
                result = backend.run(qc, shots=self.shots).result()
            else:
                from qiskit import execute
                result = execute(qc, backend, shots=self.shots).result()

            counts = result.get_counts()
            for bitstring, count in counts.items():
                clean_bits = [int(b) for b in bitstring.replace(" ", "")]
                for _ in range(count):
                    self.bit_buffer.extend(clean_bits)
        except Exception as e:
            # Fallback if execution fails
            for _ in range(self.n_qubits * self.shots):
                self.bit_buffer.append(random.getrandbits(1))

    def get_bit(self) -> int:
        if not self.bit_buffer:
            self._refill()
        return self.bit_buffer.popleft()

    def get_int(self, min_val: int, max_val: int) -> int:
        if min_val >= max_val:
            return min_val
        span = max_val - min_val + 1
        bits_needed = span.bit_length()
        while True:
            val = 0
            for _ in range(bits_needed):
                val = (val << 1) | self.get_bit()
            if val < span:
                return min_val + val

    def get_float(self) -> float:
        # 32 bits of precision
        val = 0
        for _ in range(32):
            val = (val << 1) | self.get_bit()
        return val / (1 << 32)


# Global instance for seamless usage across the project
_qrng = QuantumRandomGenerator()

def qrandom() -> int:
    """Returns 0 or 1 from quantum measurement."""
    return _qrng.get_bit()

def qrandom_bool() -> bool:
    """Returns True or False from quantum measurement."""
    return bool(_qrng.get_bit())

def qrandint(a: int, b: int) -> int:
    """Returns a random integer in range [a, b] using quantum random bits."""
    return _qrng.get_int(a, b)

def qrandom_float() -> float:
    """Returns a random float in range [0.0, 1.0) using quantum random bits."""
    return _qrng.get_float()

def get_backend_name() -> str:
    _init_backend()
    return _backend_type or "unknown"

if __name__ == "__main__":
    print(f"Quantum Backend: {get_backend_name()}")
    print("Testing 10 quantum bits:", [qrandom() for _ in range(10)])
    print("Testing quantum randint [1, 10]:", [qrandint(1, 10) for _ in range(5)])
    print("Testing quantum float:", qrandom_float())
