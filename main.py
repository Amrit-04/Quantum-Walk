"""QuMa: Quantum Maze
8-Bit Retro Maze Game featuring IBM Qiskit-simulated Quantum Entanglement.
"""

import sys
import os
import math
import time
from typing import Dict, List, Tuple, Optional
import pygame
from pygame.locals import *

import Qrandom
from MazeGenerator import MazeGenerator
from qmaze import QuantumMazeManager

# Window & Tile configuration
TILE_SIZE = 28
GRID_SIZE = (19, 11)  # 39 columns x 23 rows in tile matrix
MAZE_COLS = 2 * GRID_SIZE[0] + 1  # 39
MAZE_ROWS = 2 * GRID_SIZE[1] + 1  # 23

MAZE_PIXEL_W = MAZE_COLS * TILE_SIZE  # 1092 px
MAZE_PIXEL_H = MAZE_ROWS * TILE_SIZE  # 644 px

SIDEBAR_W = 340
WINDOW_W = MAZE_PIXEL_W + SIDEBAR_W + 40  # ~1472 px
WINDOW_H = max(720, MAZE_PIXEL_H + 40)   # 720 px

MAZE_OFFSET_X = 20
MAZE_OFFSET_Y = (WINDOW_H - MAZE_PIXEL_H) // 2

# Gate code mappings
GATE_MAP = {
    2: "X",
    3: "Z",
    4: "S",
    5: "H"
}

class Player:
    def __init__(self, x: int = 1, y: int = 1):
        self.x = x
        self.y = y
        self.steps = 0


class GameSession:
    """Manages the full state of a single play session."""
    def __init__(self):
        self.player = Player(1, 1)
        self.finish_line = (MAZE_COLS - 2, MAZE_ROWS - 2)
        self.generator = MazeGenerator(*GRID_SIZE)
        self.maze_grid = self.generator.GetMaze().ToList()
        self.quantum_mgr = QuantumMazeManager(self.maze_grid, (1, 1), self.finish_line)
        self.inventory: Dict[str, int] = {"X": 0, "Z": 0, "S": 0, "H": 0}
        self.game_won = False
        self.start_time = time.time()
        self.gates_collected = 0
        self.gates_used = 0

        # Initial check in case starting cell is adjacent to an entangled wall
        self.quantum_mgr.check_player_observation(self.player.x, self.player.y)

    def move_player(self, dx: int, dy: int):
        if self.game_won:
            return

        nx = self.player.x + dx
        ny = self.player.y + dy

        # Boundary check
        if not (0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS):
            return

        target_cell = self.maze_grid[ny][nx]

        # Solid wall
        if target_cell == 1:
            return

        # Entangled wall in superposition
        if target_cell == 6:
            # Approaching it triggers observation
            self.quantum_mgr.check_player_observation(nx, ny)
            # Re-read state after collapse
            target_cell = self.maze_grid[ny][nx]
            if target_cell == 1:
                return  # Collapsed into solid wall!

        # Check for quantum gate pickup
        if target_cell in GATE_MAP:
            gate_name = GATE_MAP[target_cell]
            self.inventory[gate_name] += 1
            self.gates_collected += 1
            self.maze_grid[ny][nx] = 0  # Clear pickup
            self.quantum_mgr.log_event(f"Acquired Pauli/Phase Gate: [{gate_name}]! Press key [{gate_name}] to activate.")

        # Execute move
        self.player.x = nx
        self.player.y = ny
        self.player.steps += 1

        # Check if adjacent to any unmeasured entangled walls
        self.quantum_mgr.check_player_observation(nx, ny)

        # Check win condition
        if (self.player.x, self.player.y) == self.finish_line:
            self.game_won = True
            elapsed = int(time.time() - self.start_time)
            self.quantum_mgr.log_event(f"VICTORY! Escaped the Quantum Labyrinth in {self.player.steps} steps ({elapsed}s)!")

    def activate_gate(self, gate: str):
        if self.game_won:
            return
        gate = gate.upper()
        if self.inventory.get(gate, 0) > 0:
            self.inventory[gate] -= 1
            self.gates_used += 1
            self.quantum_mgr.apply_gate_to_nearest(self.player.x, self.player.y, gate)
        else:
            self.quantum_mgr.log_event(f"No [{gate}] gates remaining in inventory.")


def load_scaled_sprite(filename: str, size: Tuple[int, int]) -> pygame.Surface:
    """Loads and scales a BMP sprite, creating a fallback surface if missing."""
    if os.path.exists(filename):
        try:
            surf = pygame.image.load(filename)
            return pygame.transform.scale(surf, size)
        except Exception:
            pass
    # Fallback colored rect
    surf = pygame.Surface(size)
    surf.fill((120, 120, 120))
    return surf


def main():
    pygame.init()
    pygame.font.init()

    # Configure window
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("QuMa: Quantum Maze - Qiskit Entanglement Simulation")
    clock = pygame.time.Clock()

    # Load and scale sprites
    spr_size = (TILE_SIZE, TILE_SIZE)
    spr_player = load_scaled_sprite("player.bmp", spr_size)
    spr_block = load_scaled_sprite("block.bmp", spr_size)
    spr_finish = load_scaled_sprite("wall.bmp", spr_size)
    spr_x = load_scaled_sprite("x.bmp", spr_size)
    spr_z = load_scaled_sprite("z.bmp", spr_size)
    spr_s = load_scaled_sprite("s.bmp", spr_size)
    spr_h = load_scaled_sprite("h.bmp", spr_size)

    # Fonts
    font_title = pygame.font.SysFont("segoeui", 20, bold=True)
    font_bold = pygame.font.SysFont("segoeui", 14, bold=True)
    font_regular = pygame.font.SysFont("segoeui", 12)
    font_log = pygame.font.SysFont("consolas", 11)
    font_large = pygame.font.SysFont("segoeui", 28, bold=True)

    session = GameSession()
    running = True

    while running:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()

        # Handle Events
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                break
            elif event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    running = False
                    break
                elif event.key == K_r:
                    # Reset with fresh quantum maze
                    session = GameSession()
                elif event.key in (K_w, K_UP):
                    session.move_player(0, -1)
                elif event.key in (K_s, K_DOWN):
                    session.move_player(0, 1)
                elif event.key in (K_a, K_LEFT):
                    session.move_player(-1, 0)
                elif event.key in (K_d, K_RIGHT):
                    session.move_player(1, 0)
                # Gate activation hotkeys
                elif event.key == K_x:
                    session.activate_gate("X")
                elif event.key == K_h:
                    session.activate_gate("H")
                elif event.key == K_z:
                    session.activate_gate("Z")
                elif event.key == K_s and not (pygame.key.get_mods() & KMOD_CTRL):
                    # Only trigger if not a movement key intention
                    session.activate_gate("S")

        # Rendering
        screen.fill((14, 18, 30))  # Deep cosmic navy

        # Draw Maze Boundary
        maze_rect = pygame.Rect(
            MAZE_OFFSET_X - 2,
            MAZE_OFFSET_Y - 2,
            MAZE_PIXEL_W + 4,
            MAZE_PIXEL_H + 4
        )
        pygame.draw.rect(screen, (35, 45, 75), maze_rect, border_radius=4)

        # Draw Tiles
        pulse_alpha = int(127 + 127 * math.sin(current_time / 200.0))
        for row in range(MAZE_ROWS):
            for col in range(MAZE_COLS):
                tx = MAZE_OFFSET_X + col * TILE_SIZE
                ty = MAZE_OFFSET_Y + row * TILE_SIZE
                cell_val = session.maze_grid[row][col]

                # Background corridor color
                corridor_color = (22, 28, 46) if (row % 2 == 1 and col % 2 == 1) else (18, 22, 36)
                pygame.draw.rect(screen, corridor_color, (tx, ty, TILE_SIZE, TILE_SIZE))

                if cell_val == 1:
                    screen.blit(spr_block, (tx, ty))
                elif cell_val == 2:
                    screen.blit(spr_x, (tx, ty))
                elif cell_val == 3:
                    screen.blit(spr_z, (tx, ty))
                elif cell_val == 4:
                    screen.blit(spr_s, (tx, ty))
                elif cell_val == 5:
                    screen.blit(spr_h, (tx, ty))
                elif cell_val == 6:
                    # Entangled wall in superposition: pulsing cyan/magenta glow
                    glow_surf = pygame.Surface(spr_size, pygame.SRCALPHA)
                    glow_color = (0, 220, 255, pulse_alpha)
                    pygame.draw.rect(glow_surf, glow_color, (0, 0, TILE_SIZE, TILE_SIZE), border_radius=3)
                    screen.blit(glow_surf, (tx, ty))
                    # Draw quantum superposition marker
                    psi_text = font_bold.render("Ψ", True, (255, 255, 255))
                    psi_rect = psi_text.get_rect(center=(tx + TILE_SIZE // 2, ty + TILE_SIZE // 2))
                    screen.blit(psi_text, psi_rect)

        # Draw Finish Line Goal
        fx = MAZE_OFFSET_X + session.finish_line[0] * TILE_SIZE
        fy = MAZE_OFFSET_Y + session.finish_line[1] * TILE_SIZE
        screen.blit(spr_finish, (fx, fy))

        # Finish tile indicator aura
        goal_aura = pygame.Surface(spr_size, pygame.SRCALPHA)
        pygame.draw.rect(goal_aura, (50, 255, 120, 90), (0, 0, TILE_SIZE, TILE_SIZE), 2, border_radius=3)
        screen.blit(goal_aura, (fx, fy))

        # Draw Player
        px = MAZE_OFFSET_X + session.player.x * TILE_SIZE
        py = MAZE_OFFSET_Y + session.player.y * TILE_SIZE
        screen.blit(spr_player, (px, py))

        # ------------------- DRAW SIDEBAR HUD -------------------
        sb_x = MAZE_OFFSET_X + MAZE_PIXEL_W + 20
        sb_y = MAZE_OFFSET_Y
        sb_w = SIDEBAR_W
        sb_h = MAZE_PIXEL_H

        # Sidebar background card
        pygame.draw.rect(screen, (20, 26, 44), (sb_x, sb_y, sb_w, sb_h), border_radius=8)
        pygame.draw.rect(screen, (40, 52, 85), (sb_x, sb_y, sb_w, sb_h), width=1, border_radius=8)

        # Title Header
        title_surf = font_title.render("QuMa: Quantum Maze", True, (0, 230, 255))
        screen.blit(title_surf, (sb_x + 16, sb_y + 14))

        backend_name = Qrandom.get_backend_name()
        backend_surf = font_regular.render(f"Simulation Engine: {backend_name}", True, (140, 160, 200))
        screen.blit(backend_surf, (sb_x + 16, sb_y + 38))

        # Section: Player Status
        pygame.draw.line(screen, (35, 45, 75), (sb_x + 16, sb_y + 60), (sb_x + sb_w - 16, sb_y + 60))
        lbl_status = font_bold.render("PLAYER METRICS", True, (255, 200, 80))
        screen.blit(lbl_status, (sb_x + 16, sb_y + 68))

        stat_pos = font_regular.render(f"Coordinates:  ({session.player.x}, {session.player.y})", True, (220, 230, 245))
        stat_steps = font_regular.render(f"Steps Taken:  {session.player.steps}", True, (220, 230, 245))
        stat_finish = font_regular.render(f"Target Exit:  ({session.finish_line[0]}, {session.finish_line[1]})", True, (120, 230, 140))
        screen.blit(stat_pos, (sb_x + 16, sb_y + 90))
        screen.blit(stat_steps, (sb_x + 16, sb_y + 108))
        screen.blit(stat_finish, (sb_x + 16, sb_y + 126))

        # Section: Quantum Register & Pairs
        pygame.draw.line(screen, (35, 45, 75), (sb_x + 16, sb_y + 152), (sb_x + sb_w - 16, sb_y + 152))
        lbl_pairs = font_bold.render("ENTANGLED BELL PAIRS", True, (255, 120, 200))
        screen.blit(lbl_pairs, (sb_x + 16, sb_y + 160))

        superposed_count = sum(1 for p in session.quantum_mgr.pairs if not p.is_measured)
        collapsed_count = len(session.quantum_mgr.pairs) - superposed_count
        stat_pairs = font_regular.render(f"Total: {len(session.quantum_mgr.pairs)}  |  Ψ Superposed: {superposed_count}  |  Collapsed: {collapsed_count}", True, (200, 210, 235))
        screen.blit(stat_pairs, (sb_x + 16, sb_y + 182))

        # Section: Quantum Gate Inventory
        pygame.draw.line(screen, (35, 45, 75), (sb_x + 16, sb_y + 208), (sb_x + sb_w - 16, sb_y + 208))
        lbl_inv = font_bold.render("QUANTUM GATE INVENTORY", True, (100, 220, 255))
        screen.blit(lbl_inv, (sb_x + 16, sb_y + 216))

        gates_list = [
            ("X", "Pauli-X (NOT Flip)", session.inventory["X"], (255, 100, 100)),
            ("H", "Hadamard (Superpose)", session.inventory["H"], (100, 240, 255)),
            ("Z", "Pauli-Z (Phase Flip)", session.inventory["Z"], (255, 220, 100)),
            ("S", "Phase-S (pi/2 Shift)", session.inventory["S"], (180, 140, 255)),
        ]
        for i, (g_key, g_desc, count, col) in enumerate(gates_list):
            gy = sb_y + 238 + i * 22
            badge = f"[{g_key}] {g_desc}: x{count}"
            g_surf = font_regular.render(badge, True, col if count > 0 else (120, 130, 150))
            screen.blit(g_surf, (sb_x + 16, gy))

        # Section: Live Quantum Event Feed
        pygame.draw.line(screen, (35, 45, 75), (sb_x + 16, sb_y + 334), (sb_x + sb_w - 16, sb_y + 334))
        lbl_log = font_bold.render("QUANTUM EVENT LOG", True, (160, 220, 160))
        screen.blit(lbl_log, (sb_x + 16, sb_y + 342))

        # Render recent events
        log_start_y = sb_y + 364
        for i, ev_text in enumerate(reversed(session.quantum_mgr.recent_events[-5:])):
            # Wrap or truncate long log lines for sidebar display
            display_text = ev_text if len(ev_text) < 42 else ev_text[:39] + "..."
            log_item = font_log.render(f"> {display_text}", True, (180, 205, 230))
            screen.blit(log_item, (sb_x + 16, log_start_y + i * 18))

        # Section: Controls & Guide
        pygame.draw.line(screen, (35, 45, 75), (sb_x + 16, sb_y + 466), (sb_x + sb_w - 16, sb_y + 466))
        lbl_ctrl = font_bold.render("MISSION CONTROLS", True, (255, 200, 100))
        screen.blit(lbl_ctrl, (sb_x + 16, sb_y + 474))

        controls = [
            "W/A/S/D or Arrows : Navigate Avatar",
            "Walk near Ψ wall  : Trigger Observer Collapse",
            "Collect Gates     : Gain Quantum Operators",
            "Key [X]           : Flip nearest wall state",
            "Key [H]           : Re-superpose nearest wall",
            "Key [R]           : Generate New Quantum Maze",
            "Key [ESC]         : Quit Simulation",
        ]
        for i, c_text in enumerate(controls):
            c_surf = font_regular.render(c_text, True, (180, 195, 215))
            screen.blit(c_surf, (sb_x + 16, sb_y + 496 + i * 18))

        # ------------------- VICTORY OVERLAY -------------------
        if session.game_won:
            # Semi-transparent backdrop overlay
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((5, 10, 20, 210))
            screen.blit(overlay, (0, 0))

            card_w = 640
            card_h = 320
            card_x = (WINDOW_W - card_w) // 2
            card_y = (WINDOW_H - card_h) // 2

            pygame.draw.rect(screen, (22, 32, 54), (card_x, card_y, card_w, card_h), border_radius=12)
            pygame.draw.rect(screen, (0, 230, 255), (card_x, card_y, card_w, card_h), width=2, border_radius=12)

            vic_title = font_large.render("QUANTUM MAZE ESCAPED!", True, (0, 255, 180))
            vic_rect = vic_title.get_rect(center=(WINDOW_W // 2, card_y + 50))
            screen.blit(vic_title, vic_rect)

            sub_title = font_bold.render("Observer collapse successfully negotiated to the exit boundary.", True, (210, 225, 245))
            sub_rect = sub_title.get_rect(center=(WINDOW_W // 2, card_y + 90))
            screen.blit(sub_title, sub_rect)

            stats_lines = [
                f"Total Steps Traversed: {session.player.steps}",
                f"Quantum Gates Harvested: {session.gates_collected}",
                f"Quantum Operators Applied: {session.gates_used}",
                f"Simulated Wave-Function Collapses: {sum(1 for p in session.quantum_mgr.pairs if p.is_measured)}",
            ]
            for i, st in enumerate(stats_lines):
                st_surf = font_regular.render(st, True, (255, 220, 140))
                st_rect = st_surf.get_rect(center=(WINDOW_W // 2, card_y + 130 + i * 24))
                screen.blit(st_surf, st_rect)

            prompt_surf = font_bold.render("Press [R] to Play Again  |  Press [ESC] to Quit", True, (0, 230, 255))
            p_rect = prompt_surf.get_rect(center=(WINDOW_W // 2, card_y + 260))
            screen.blit(prompt_surf, p_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
