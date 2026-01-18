#!/usr/bin/env python3
"""
N-Puzzle GUI for macOS using Qt
Displays an interactive N×N sliding puzzle grid with controls to generate,
solve, and animate solutions.   
"""

import sys
import random
import subprocess
import json
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
	QPushButton, QComboBox, QLabel, QMessageBox, QGraphicsView,
	QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter, QResizeEvent


class PuzzleScene(QGraphicsScene):
	"""Custom graphics scene for the puzzle grid."""
	
	def __init__(self, parent=None):
		super().__init__(parent)
		# Wood color for background
		self.setBackgroundBrush(QBrush(QColor(160, 82, 45)))  # Sienna brown


class WoodFrame(QFrame):
	"""Custom frame widget with wood-like appearance."""
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setStyleSheet("""
			QFrame {
				background:  qlineargradient(x1: 0, y1:0, x2:1, y2:1,
					stop: 0 #8B4513, stop:0.5 #A0522D, stop:1 #8B4513);
				border:  3px solid #654321;
				border-radius:  8px;
				padding: 15px;
			}
		""")
		self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
		self.setLineWidth(3)


class NPuzzleGUI(QMainWindow):
	"""Main application window for the N-Puzzle solver."""
	
	# Colors
	TILE_COLOR = QColor(34, 139, 34)  # Forest green
	WOOD_COLOR = QColor(160, 82, 45)  # Sienna brown (same as board)
	TILE_TEXT_COLOR = QColor(255, 255, 255)
	BG_COLOR = QColor(50, 50, 60)  # Dark blue-gray
	
	def __init__(self):
		super().__init__()
		
		# State variables
		self.n = 3  # Grid size
		self.grid: List[int] = []  # Current puzzle state
		self.solution_moves: List[int] = []  # Stored solution
		self.animation_running = False
		self.empty_pos:  Tuple[int, int] = (0, 0)
		
		# Graphics items cache
		self.tile_rects = {}
		self.tile_texts = {}
		self.tile_size = 80
		
		# Animation timer and speed (default:  2 moves per second = 500ms)
		self.animation_timer = QTimer()
		self.animation_timer.timeout.connect(self._animation_tick)
		self.current_move_index = 0
		self.animation_speed_ms = 500  # milliseconds between moves

		self.resize_timer = QTimer()
		self.resize_timer. setSingleShot(True)
		self.resize_timer.timeout. connect(self._handle_resize)
		
		self._setup_ui()
		self._generate_puzzle()
		
	def _setup_ui(self):
		"""Set up the user interface."""
		self.setWindowTitle("N-Puzzle Solver")
		self.setStyleSheet(f"QMainWindow {{ background-color: {self.BG_COLOR.name()}; }}")
		
		# Central widget
		central_widget = QWidget()
		central_widget.setStyleSheet(f"background-color: {self.BG_COLOR.name()};")
		self.setCentralWidget(central_widget)
		
		# Main layout
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(15, 15, 15, 15)
		main_layout.setSpacing(15)
		
		# Control panel
		control_layout = QHBoxLayout()
		control_layout.setSpacing(10)
		
		# N selector
		n_label = QLabel("Grid Size (N):")
		n_label.setStyleSheet("font-size: 12pt; color: white; background:  transparent;")
		control_layout.addWidget(n_label)
		
		self.n_combo = QComboBox()
		self.n_combo.addItems([str(i) for i in range(2, 21)])
		self.n_combo.setCurrentText(str(self.n))
		self.n_combo.setStyleSheet("""
			QComboBox {
				font-size: 12pt;
				padding: 5px;
				min-width: 60px;
				background-color: white;
				color: black;
				border: 2px solid #555;
				border-radius: 4px;
			}
			QComboBox::drop-down {
				border: none;
			}
			QComboBox QAbstractItemView {
				background-color: white;
				color: black;
				selection-background-color: #5cb85c;
			}
		""")
		self.n_combo.currentTextChanged.connect(self._on_n_changed)
		control_layout.addWidget(self.n_combo)
		
		control_layout.addSpacing(10)
		
		# Generate button
		self.gen_button = QPushButton("Generate")
		self.gen_button.setStyleSheet("""
			QPushButton {
				background-color: #5cb85c;
				color:  white;
				font-size:  12pt;
				font-weight: bold;
				padding: 8px 15px;
				border:  none;
				border-radius: 4px;
			}
			QPushButton:hover {
				background-color: #4cae4c;
			}
			QPushButton:pressed {
				background-color: #449d44;
			}
			QPushButton:disabled {
				background-color: #555;
				color: #aaa;
			}
		""")
		self.gen_button.clicked.connect(self._generate_puzzle)
		control_layout.addWidget(self.gen_button)
		
		# Solve button
		self.solve_button = QPushButton("Solve")
		self.solve_button.setStyleSheet("""
			QPushButton {
				background-color: #5bc0de;
				color: white;
				font-size: 12pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:hover {
				background-color: #46b8da;
			}
			QPushButton:pressed {
				background-color: #31b0d5;
			}
			QPushButton:disabled {
				background-color: #555;
				color: #aaa;
			}
		""")
		self.solve_button.clicked.connect(self._solve_puzzle)
		control_layout.addWidget(self.solve_button)
		
		# Play solution button
		self.play_button = QPushButton("Play Solution")
		self.play_button.setStyleSheet("""
			QPushButton {
				background-color: #f0ad4e;
				color: white;
				font-size: 12pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:hover {
				background-color: #ec971f;
			}
			QPushButton:pressed {
				background-color: #d58512;
			}
			QPushButton:disabled {
				background-color: #555;
				color: #aaa;
			}
		""")
		self.play_button.clicked.connect(self._play_solution)
		self.play_button.setEnabled(False)
		control_layout.addWidget(self.play_button)
		
		control_layout.addStretch()
		
		main_layout.addLayout(control_layout)
		
		# Speed control
		speed_layout = QHBoxLayout()
		speed_layout.setSpacing(10)
		
		speed_label = QLabel("Animation Speed:")
		speed_label.setStyleSheet("font-size: 11pt; color: white; background: transparent;")
		speed_layout.addWidget(speed_label)
		
		slow_label = QLabel("Slow")
		slow_label.setStyleSheet("font-size: 10pt; color: #aaa; background: transparent;")
		speed_layout.addWidget(slow_label)
		
		self.speed_slider = QSlider(Qt.Orientation.Horizontal)
		self.speed_slider.setMinimum(1)  # 0.5 moves/sec (2000ms)
		self.speed_slider.setMaximum(20)  # 10 moves/sec (100ms)
		self.speed_slider.setValue(4)  # 2 moves/sec (500ms) - default
		self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
		self.speed_slider.setTickInterval(2)
		self.speed_slider.setStyleSheet("""
			QSlider::groove:horizontal {
				border: 1px solid #999;
				height: 8px;
				background: #666;
				margin: 2px 0;
				border-radius: 4px;
			}
			QSlider::handle:horizontal {
				background: #5cb85c;
				border: 2px solid #4cae4c;
				width: 18px;
				margin: -5px 0;
				border-radius: 9px;
			}
			QSlider::handle:horizontal:hover {
				background: #4cae4c;
			}
		""")
		self.speed_slider.valueChanged.connect(self._on_speed_changed)
		speed_layout.addWidget(self.speed_slider, 1)
		
		fast_label = QLabel("Fast")
		fast_label.setStyleSheet("font-size: 10pt; color: #aaa; background: transparent;")
		speed_layout.addWidget(fast_label)
		
		self.speed_value_label = QLabel("2.0 moves/sec")
		self.speed_value_label.setStyleSheet("font-size: 10pt; color: white; background: transparent; min-width: 110px;")
		speed_layout.addWidget(self.speed_value_label)
		
		speed_layout.addStretch()
		
		main_layout.addLayout(speed_layout)
		
		# Wood frame container for puzzle
		self.wood_frame = WoodFrame()
		frame_layout = QVBoxLayout(self.wood_frame)
		frame_layout.setContentsMargins(0, 0, 0, 0)
		
		# Graphics view for puzzle
		self.scene = PuzzleScene()
		self.view = QGraphicsView(self.scene)
		self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
		self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setStyleSheet("""
			QGraphicsView {
				border: none;
				background-color: #A0522D;
			}
		""")
		# Disable frame around view
		self.view.setFrameStyle(QFrame.Shape.NoFrame)
		
		frame_layout.addWidget(self.view)
		
		main_layout.addWidget(self.wood_frame, 1, Qt.AlignmentFlag.AlignCenter)
		
		self._update_view_size()
		
	def resizeEvent(self, a0):
		"""Handle window resize events."""
		super().resizeEvent(a0)
		# Debounce resize events - only update after 100ms of no resizing
		self.resize_timer.start(100)
		
	def _handle_resize(self):
		"""Actually handle the resize after debouncing."""
		self._update_view_size()

	def _on_speed_changed(self, value:  int):
		"""Handle speed slider change."""
		# Map slider value (1-20) to moves per second (0.5-10)
		moves_per_second = value / 2.0
		self.animation_speed_ms = int(1000 / moves_per_second)
		self.speed_value_label.setText(f"{moves_per_second:.1f} moves/sec")
		
	def _update_view_size(self):
		"""Update the view size based on grid size."""
		# Dynamically adjust tile size
		max_canvas_size = 1080
		self.tile_size = min(80, max_canvas_size // self.n)
		
		canvas_size = self.n * self.tile_size
		
		self.scene.setSceneRect(0, 0, canvas_size, canvas_size)
		self.view.setMinimumSize(canvas_size + 20, canvas_size + 20)
		self.view.setMaximumSize(max_canvas_size + 20, max_canvas_size + 20)
		
		# Adjust window size
		self.adjustSize()
		
	def _on_n_changed(self, value: str):
		"""Handle N value change."""
		self.n = int(value)
		self.solution_moves.clear()
		self.play_button.setEnabled(False)
		
		# Clear the scene
		self.scene.clear()
		self.tile_rects.clear()
		self.tile_texts.clear()
		
		self._update_view_size()
		self._generate_puzzle()
		
	def _generate_puzzle(self):
		"""Generate a random puzzle configuration."""
		# Create list [0, 1, 2, ..., n*n-1] and shuffle
		self.grid = list(range(self.n * self.n))
		random.shuffle(self.grid)
		
		# Find empty tile position
		self._update_empty_pos()
		
		# Clear any previous solution
		self.solution_moves.clear()
		self.play_button.setEnabled(False)
		
		self._draw_grid()
		
	def _update_empty_pos(self):
		"""Update the position of the empty tile (0)."""
		idx = self.grid.index(0)
		self.empty_pos = (idx // self.n, idx % self.n)

	def _draw_grid(self):
		"""Draw the puzzle grid."""
		# Clear existing items
		for item in list(self.tile_rects.values()) + list(self.tile_texts.values()):
			self.scene.removeItem(item)
		self.tile_rects.clear()
		self.tile_texts. clear()
		
		# Adjust font size for larger grids
		font_size = max(10, min(28, self.tile_size // 2))
		font = QFont("Helvetica", font_size, QFont.Weight.Bold)
		
		for i in range(self.n):
			for j in range(self.n):
				idx = i * self.n + j
				value = self.grid[idx]
				
				x = j * self.tile_size
				y = i * self.tile_size
				
				tile_id = (i, j)
				
				# Determine tile color (wood color for empty, green for tiles)
				color = self.WOOD_COLOR if value == 0 else self. TILE_COLOR
				
				# Create rectangle
				rect_item = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
				rect_item.setBrush(QBrush(color))
				rect_item. setPen(QPen(QColor(30, 30, 30), 2))
				self.scene.addItem(rect_item)
				self.tile_rects[tile_id] = rect_item
				
				# Create text
				text = "" if value == 0 else str(value)
				text_item = QGraphicsTextItem(text)
				text_item.setFont(font)
				text_item.setDefaultTextColor(self.TILE_TEXT_COLOR)
				self.scene.addItem(text_item)
				self.tile_texts[tile_id] = text_item
				
				# Hide text for empty tiles
				if value == 0:
					text_item.setVisible(False)
				else:
					# Center the text
					text_rect = text_item.boundingRect()
					text_x = x + (self.tile_size - text_rect.width()) / 2
					text_y = y + (self.tile_size - text_rect.height()) / 2
					text_item.setPos(text_x, text_y)

	def _solve_puzzle(self):
		"""Call the n-puzzle executable and receive solution."""
		# Prepare input for the executable
		grid_str = ' '.join(map(str, self.grid))
		
		try:
			# Launch the executable
			result = subprocess.run(
				['./n-puzzle'],
				input=grid_str,
				capture_output=True,
				text=True,
				timeout=30
			)
			
			if result.returncode != 0:
				QMessageBox.critical(
					self,
					"Error",
					f"Solver failed:\n{result.stderr}"
				)
				return
			
			# Parse JSON output
			output = result.stdout.strip()
			data = json.loads(output)
			
			if "moves" in data:
				self.solution_moves = data["moves"]
				self.play_button.setEnabled(True)
				QMessageBox.information(
					self,
					"Success",
					f"Solution found:  {len(self.solution_moves)} moves"
				)
			else:
				QMessageBox.critical(self, "Error", "Invalid response format")
				
		except subprocess.TimeoutExpired:
			QMessageBox.critical(self, "Error", "Solver timed out")
		except FileNotFoundError:
			QMessageBox.critical(
				self,
				"Error",
				"Executable 'n-puzzle' not found in current directory"
			)
		except json.JSONDecodeError:
			QMessageBox.critical(
				self,
				"Error",
				f"Invalid JSON response:\n{result.stdout}"
			)
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Unexpected error:\n{str(e)}")
			
	def _play_solution(self):
		"""Animate the solution step by step."""
		if not self.solution_moves:
			QMessageBox.warning(self, "Warning", "No solution to play")
			return
			
		if self.animation_running:
			return
			
		self.animation_running = True
		self.current_move_index = 0
		self._disable_buttons()
		
		# Start animation timer with current speed
		self.animation_timer.start(self.animation_speed_ms)
		
	def _animation_tick(self):
		"""Handle one animation frame."""
		if self.current_move_index >= len(self.solution_moves):
			# Animation complete
			self.animation_timer.stop()
			self.animation_running = False
			self._enable_buttons()
			return
			
		move = self.solution_moves[self.current_move_index]
		
		# Apply move:  1=up, 2=down, 3=left, 4=right
		success = self._apply_move(move)
		
		if not success:
			self.animation_timer.stop()
			QMessageBox.critical(
				self,
				"Error",
				f"Invalid move at step {self.current_move_index + 1}"
			)
			self.animation_running = False
			self._enable_buttons()
			return
			
		self._draw_grid()
		self.current_move_index += 1
		
	def _apply_move(self, move: int) -> bool:
		"""
		Apply a move to the puzzle.
		Moves: 1=up, 2=down, 3=left, 4=right (moving the empty tile)
		Returns True if move was valid, False otherwise.
		"""
		row, col = self.empty_pos
		new_row, new_col = row, col
		
		if move == 1:  # Move empty tile up
			new_row -= 1
		elif move == 2:  # Move empty tile down
			new_row += 1
		elif move == 3:  # Move empty tile left
			new_col -= 1
		elif move == 4:  # Move empty tile right
			new_col += 1
		else:
			return False
			
		# Check bounds
		if not (0 <= new_row < self.n and 0 <= new_col < self.n):
			return False
			
		# Swap empty tile with target tile
		old_idx = row * self.n + col
		new_idx = new_row * self.n + new_col
		
		self.grid[old_idx], self.grid[new_idx] = self.grid[new_idx], self.grid[old_idx]
		self.empty_pos = (new_row, new_col)
		
		return True
		
	def _disable_buttons(self):
		"""Disable control buttons during animation."""
		self.gen_button.setEnabled(False)
		self.solve_button.setEnabled(False)
		self.play_button.setEnabled(False)
		self.n_combo.setEnabled(False)
		self.speed_slider.setEnabled(False)
		
	def _enable_buttons(self):
		"""Enable control buttons after animation."""
		self.gen_button.setEnabled(True)
		self.solve_button.setEnabled(True)
		self.n_combo.setEnabled(True)
		self.speed_slider.setEnabled(True)
		if self.solution_moves:
			self.play_button.setEnabled(True)


def main():
	"""Main entry point."""
	app = QApplication(sys.argv)
	window = NPuzzleGUI()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
