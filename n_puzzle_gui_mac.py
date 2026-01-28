#!/usr/bin/env python3
import os
import sys
import random
import subprocess
import json
from typing import List, Tuple
from pathlib import Path

from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
	QPushButton, QComboBox, QLabel, QMessageBox, QGraphicsView,
	QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter

class PuzzleScene(QGraphicsScene):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setBackgroundBrush(QBrush(QColor(160, 82, 45)))

class WoodFrame(QFrame):
	"""Custom frame widget with wood-like appearance."""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setStyleSheet("""QFrame {
			background:  qlineargradient(x1: 0, y1:0, x2:1, y2:1,
			stop: 0 #8B4513, stop:0.5 #A0522D, stop:1 #8B4513);
			border:  3px solid #654321;
			border-radius:  8px;
			padding: 15px; }""")
		self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
		self.setLineWidth(3)

class NPuzzleGUI(QMainWindow):
	TILE_COLOR = QColor(34, 139, 34)
	WOOD_COLOR = QColor(160, 82, 45)
	TILE_TEXT_COLOR = QColor(255, 255, 255)
	BG_COLOR = QColor(50, 50, 60)
	
	def __init__(self):
		super().__init__()

		self.n = 3
		self.grid: List[int] = []
		self.initial_grid: List[int] = []
		self.solution_moves: List[int] = []
		self.animation_running = False
		self.empty_pos:  Tuple[int, int] = (0, 0)
		
		self.tile_rects = {}
		self.tile_texts = {}
		self.tile_size = 80
		
		self.animation_timer = QTimer()
		self.animation_timer.timeout.connect(self._animation_tick)
		self.current_move_index = 0
		self.animation_speed_ms = 500
		self.selected_heuristic = "Manhattan distance"
		self.selected_puzzle_file = None

		self.resize_timer = QTimer()
		self.resize_timer.setSingleShot(True)
		self.resize_timer.timeout.connect(self._handle_resize)
		
		self._setup_ui()
		self._generate_puzzle()
		
	def _setup_ui(self):
		self.setWindowTitle("N-Puzzle Solver")
		self.setStyleSheet(f"QMainWindow {{ background-color: {self.BG_COLOR.name()}; }}")

		central_widget = QWidget()
		central_widget.setStyleSheet(f"background-color: {self.BG_COLOR.name()};")
		self.setCentralWidget(central_widget)
		
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(15, 15, 15, 15)
		main_layout.setSpacing(15)
		
		control_layout = QHBoxLayout()
		control_layout.setSpacing(10)
		
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
		
		self.gen_button = QPushButton("Generate")
		self.gen_button.setStyleSheet(
			"""QPushButton
			{
				background-color: #5cb85c;
				color:  white;
				font-size:  12pt;
				font-weight: bold;
				padding: 8px 15px;
				border:  none;
				border-radius: 4px;
			}
			QPushButton:hover { background-color: #4cae4c; }
			QPushButton:pressed { background-color: #449d44; }
			QPushButton:disabled { background-color: #555; color: #aaa; }""")
		self.gen_button.clicked.connect(self._generate_puzzle)
		control_layout.addWidget(self.gen_button)

		self.reset_button = QPushButton("Reset")
		self.reset_button.setStyleSheet(
			"""QPushButton
			{
				background-color: #d9534f;
				color: white;
				font-size: 12pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:hover { background-color: #c9302c; }
			QPushButton:pressed { background-color: #ac2925; }
			QPushButton:disabled { background-color: #555; color: #aaa; }""")
		self.reset_button.clicked.connect(self._reset_puzzle)
		control_layout.addWidget(self.reset_button)

		self.solve_button = QPushButton("Solve")
		self.solve_button.setStyleSheet(
			"""QPushButton
			{
				background-color: #5bc0de;
				color: white;
				font-size: 12pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:hover {	background-color: #46b8da; }
			QPushButton:pressed { background-color: #31b0d5; }
			QPushButton:disabled { background-color: #555; color: #aaa; }""")

		self.solve_button.clicked.connect(self._solve_puzzle)
		control_layout.addWidget(self.solve_button)
		
		self.play_button = QPushButton("Play Solution")
		self.play_button.setStyleSheet(
			"""QPushButton
			{
				background-color: #f0ad4e;
				color: white;
				font-size: 12pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:hover { background-color: #ec971f; }
			QPushButton:pressed { background-color: #d58512; }
			QPushButton:disabled { background-color: #555; color: #aaa; }""")
		self.play_button.clicked.connect(self._play_solution)
		self.play_button.setEnabled(False)
		control_layout.addWidget(self.play_button)
		control_layout.addStretch()
		main_layout.addLayout(control_layout)

		speed_layout = QHBoxLayout()
		speed_layout.setSpacing(10)
		speed_label = QLabel("Animation Speed:")
		speed_label.setStyleSheet("font-size: 11pt; color: white; background: transparent;")
		speed_layout.addWidget(speed_label)
		
		slow_label = QLabel("Slow")
		slow_label.setStyleSheet("font-size: 10pt; color: #aaa; background: transparent;")
		speed_layout.addWidget(slow_label)
		
		self.speed_slider = QSlider(Qt.Orientation.Horizontal)
		self.speed_slider.setMinimum(1)
		self.speed_slider.setMaximum(20)
		self.speed_slider.setValue(4)  # 2 moves/sec (500ms) - default
		self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
		self.speed_slider.setTickInterval(2)
		self.speed_slider.setStyleSheet(
			"""QSlider::groove:horizontal
			{
				border: 1px solid #999;
				height: 8px;
				background: #666;
				margin: 2px 0;
				border-radius: 4px;
			}
			QSlider::handle:horizontal
			{
				background: #5cb85c;
				border: 2px solid #4cae4c;
				width: 18px;
				margin: -5px 0;
				border-radius: 9px;
			}
			QSlider::handle:horizontal:hover { background: #4cae4c; }""")
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

		heuristic_layout = QHBoxLayout()
		heuristic_layout.setSpacing(10)

		heuristic_label = QLabel("Heuristic:")
		heuristic_label.setStyleSheet("font-size: 11pt; color: white; background:  transparent;")
		heuristic_layout.addWidget(heuristic_label)

		self.heuristic_combo = QComboBox()
		self.heuristic_combo.addItems(["Manhattan distance", "Linear conflict", "Hamming distance", "Manhattan + LC", "Dijkstra (no heuristic)"])
		self.heuristic_combo.setCurrentText("manhattan")
		self.heuristic_combo.setStyleSheet("""
			QComboBox {
				font-size: 11pt;
				padding: 5px;
				min-width: 120px;
				background-color: white;
				color: black;
				border: 2px solid #555;
				border-radius: 4px;
			}
			QComboBox::drop-down { border:  none; }
			QComboBox QAbstractItemView {
				background-color: white;
				color: black;
				selection-background-color: #5cb85c;
			}
		""")
		self.heuristic_combo.currentTextChanged.connect(self._on_heuristic_changed)
		heuristic_layout.addWidget(self.heuristic_combo)

		heuristic_layout.addSpacing(20)

		heuristic_layout.addSpacing(20)

		# Greedy search toggle button
		self.greedy_button = QPushButton("Greedy Search")
		self.greedy_button.setCheckable(True)
		self.greedy_button.setChecked(False)
		self.greedy_button.setStyleSheet("""
			QPushButton {
				background-color: #555;
				color: #aaa;
				font-size: 11pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}
			QPushButton:checked {
				background-color: #90ee90;
				color: #333;
			}
			QPushButton:checked:hover {
				background-color: #7ad87a;
			}
			QPushButton:hover {
				background-color: #666;
			}
		""")
		heuristic_layout.addWidget(self.greedy_button)

		# Puzzle file selector
		puzzle_label = QLabel("Puzzle File:")
		puzzle_label.setStyleSheet("font-size: 11pt; color: white; background:  transparent;")
		heuristic_layout.addWidget(puzzle_label)

		self.puzzle_combo = QComboBox()
		puzzle_files = self._load_puzzle_files()
		if puzzle_files:
			self.puzzle_combo.addItem("(Random)", None)
			for pf in puzzle_files:
				self.puzzle_combo.addItem(pf, pf)
		else:
			self.puzzle_combo.addItem("(Random)", None)
		self.puzzle_combo.setStyleSheet("""
			QComboBox {
				font-size:  11pt;
				padding:  5px;
				min-width: 150px;
				background-color:  white;
				color: black;
				border: 2px solid #555;
				border-radius: 4px;
			}
			QComboBox::drop-down { border: none; }
			QComboBox QAbstractItemView {
				background-color: white;
				color:  black;
				selection-background-color: #5cb85c;
			}
		""")
		self.puzzle_combo.currentIndexChanged.connect(self._on_puzzle_file_changed)
		heuristic_layout.addWidget(self.puzzle_combo)

		heuristic_layout.addStretch()
		main_layout.addLayout(heuristic_layout)

		stats_layout = QHBoxLayout()
		stats_layout.setSpacing(15)

		self.stats_label = QLabel("Stats:  No solution yet")
		self.stats_label.setStyleSheet("font-size:  10pt; color: #aaa; background: transparent;")
		stats_layout.addWidget(self.stats_label)
		stats_layout.addStretch()
		main_layout.addLayout(stats_layout)

		self.wood_frame = WoodFrame()
		frame_layout = QVBoxLayout(self.wood_frame)
		frame_layout.setContentsMargins(0, 0, 0, 0)

		self.scene = PuzzleScene()
		self.view = QGraphicsView(self.scene)
		self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
		self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setStyleSheet("""QGraphicsView { border: none; background-color: #A0522D;	}""")
		self.view.setFrameStyle(QFrame.Shape.NoFrame)
		frame_layout.addWidget(self.view)
		main_layout.addWidget(self.wood_frame, 1, Qt.AlignmentFlag.AlignCenter)
		self._update_view_size()

	def _load_puzzle_files(self):
		puzzle_dir = Path("puzzles")
		if not puzzle_dir.exists():
			return []
		puzzle_files = sorted([f.name for f in puzzle_dir.iterdir() if f.is_file()])
		return puzzle_files

	def _load_puzzle_from_file(self, filepath: str):
		"""Load a puzzle from a file and display it in the GUI."""
		try:
			with open(filepath, 'r') as f:
				lines = f.readlines()
			
			grid_rows = []
			
			for line in lines:
				# Remove comments (everything after #)
				if '#' in line:
					line = line[:line.index('#')]
				
				# Strip whitespace
				line = line.strip()
				
				# Skip empty lines
				if not line:
					continue
				
				# Split into tokens and parse as integers
				tokens = line.split()
				row = [int(token) for token in tokens]
				grid_rows.append(row)
			
			# Validate - all rows should have same length
			if not grid_rows:
				raise ValueError("No grid data found in file")
			
			n = len(grid_rows)
			
			# Check all rows have correct length
			for i, row in enumerate(grid_rows):
				if len(row) != n:
					raise ValueError(f"Row {i} has {len(row)} values, expected {n}")
			
			# Flatten to 1D list
			grid_values = [val for row in grid_rows for val in row]
			
			# Validate total count
			if len(grid_values) != n * n:
				raise ValueError(f"Expected {n * n} values, found {len(grid_values)}")
			
			# Update GUI
			self.n = n
			self.n_combo.setCurrentText(str(n))
			self.grid = grid_values
			self.initial_grid = grid_values.copy()
			self._update_empty_pos()
			self.solution_moves.clear()
			self.play_button.setEnabled(False)
			self.stats_label.setText("Stats: No solution yet")
			self.stats_label.setStyleSheet("font-size: 10pt; color: #aaa; background: transparent;")
			
			# Clear and redraw
			self.scene.clear()
			self.tile_rects.clear()
			self.tile_texts.clear()
			self._update_view_size()
			self._draw_grid()
			
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to load puzzle file:\n{str(e)}")

	def resizeEvent(self, a0):
		super().resizeEvent(a0)
		self.resize_timer.start(100)
		
	def _handle_resize(self):
		self._update_view_size()

	def _on_speed_changed(self, value:  int):
		moves_per_second = value / 2.0
		self.animation_speed_ms = int(1000 / moves_per_second)
		self.speed_value_label.setText(f"{moves_per_second:.1f} moves/sec")
		if self.animation_running:
			self.animation_timer.setInterval(self.animation_speed_ms)

	def _on_heuristic_changed(self, value:  str):
		self.selected_heuristic = value

	def _on_puzzle_file_changed(self, index: int):
		self.selected_puzzle_file = self.puzzle_combo.itemData(index)
		
		if self.selected_puzzle_file:
			filepath = f"puzzles/{self.selected_puzzle_file}"
			self._load_puzzle_from_file(filepath)
		else:
			self._generate_puzzle()
		
	def _update_view_size(self):
		max_canvas_size = 1080
		self.tile_size = min(80, max_canvas_size // self.n)
		canvas_size = self.n * self.tile_size

		self.scene.setSceneRect(0, 0, canvas_size, canvas_size)
		self.view.setMinimumSize(canvas_size + 20, canvas_size + 20)
		self.view.setMaximumSize(max_canvas_size + 20, max_canvas_size + 20)
		self.adjustSize()
		
	def _on_n_changed(self, value: str):
		self.n = int(value)
		self.solution_moves.clear()
		self.play_button.setEnabled(False)
		
		self.scene.clear()
		self.tile_rects.clear()
		self.tile_texts.clear()
		self._update_view_size()
		self._generate_puzzle()
		
	def _generate_puzzle(self):
		self.grid = list(range(self.n * self.n))
		random.shuffle(self.grid)

		self.initial_grid = self.grid.copy()
		self._update_empty_pos()
		self.solution_moves.clear()
		self.play_button.setEnabled(False)
		self._draw_grid()
		
	def _update_empty_pos(self):
		idx = self.grid.index(0)
		self.empty_pos = (idx // self.n, idx % self.n)

	def _draw_grid(self):
		for item in list(self.tile_rects.values()) + list(self.tile_texts.values()):
			self.scene.removeItem(item)
		self.tile_rects.clear()
		self.tile_texts.clear()
		
		font_size = max(10, min(28, self.tile_size // 2))
		font = QFont("Helvetica", font_size, QFont.Weight.Bold)
		
		for i in range(self.n):
			for j in range(self.n):
				idx = i * self.n + j
				value = self.grid[idx]
				
				x = j * self.tile_size
				y = i * self.tile_size
				
				tile_id = (i, j)
				
				color = self.WOOD_COLOR if value == 0 else self.TILE_COLOR
				
				rect_item = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
				rect_item.setBrush(QBrush(color))
				rect_item.setPen(QPen(QColor(30, 30, 30), 2))
				self.scene.addItem(rect_item)
				self.tile_rects[tile_id] = rect_item
				
				text = "" if value == 0 else str(value)
				text_item = QGraphicsTextItem(text)
				text_item.setFont(font)
				text_item.setDefaultTextColor(self.TILE_TEXT_COLOR)
				self.scene.addItem(text_item)
				self.tile_texts[tile_id] = text_item
				
				if value == 0:
					text_item.setVisible(False)
				else:
					text_rect = text_item.boundingRect()
					text_x = x + (self.tile_size - text_rect.width()) / 2
					text_y = y + (self.tile_size - text_rect.height()) / 2
					text_item.setPos(text_x, text_y)

	def _solve_puzzle(self):
		cmd = ['./n-puzzle']
		
		if self.selected_puzzle_file:
			cmd.append(f"{self.selected_puzzle_file}")
			if self.greedy_button.isChecked():
				input_data = f"Greedy search enabled\n{self.selected_heuristic}"
			else:
				input_data = self.selected_heuristic
		else:
			if self.greedy_button.isChecked():
				input_data = f"Greedy search enabled\n{self.selected_heuristic}\n{' '.join(map(str, self.grid))}"
			else:
				input_data = f"{self.selected_heuristic}\n{' '.join(map(str, self.grid))}"
		
		try:
			result = subprocess.run(
				cmd,
				input=input_data,
				capture_output=True,
				text=True,
				timeout=None
			)
			
			if result.returncode != 0:
				QMessageBox.critical(self, "Error", f"Solver failed:\n{result.stderr}")
				return
			
			output = result.stdout.strip()
			data = json.loads(output)
			
			if "moves" in data:
				self.solution_moves = data["moves"]
				self.play_button.setEnabled(True)
				
				num_moves = len(self.solution_moves)
				time_ms = data.get("time_ms", "N/A")
				total_searched = data.get("total_searched", "N/A")
				peak_states = data.get("peak_memory_states", "N/A")
				peak_bytes = data.get("peak_memory_bytes", "N/A")

				if isinstance(peak_bytes, int):
					if peak_bytes < 1024:
						mem_str = f"{peak_bytes} bytes"
					elif peak_bytes < 1024 * 1024:
						mem_str = f"{peak_bytes / 1024:.2f} KB"
					else:
						mem_str = f"{peak_bytes / (1024 * 1024):.2f} MB"
				else:
					mem_str = str(peak_bytes)
				if isinstance(time_ms, int):
					if time_ms < 1000:
						time_ms = str(time_ms)
					elif time_ms < 1000 * 60:
						time_ms = f"{time_ms / 1000:.2f} sec"
					else:
						time_ms = f"{time_ms / (1000 * 60)}:{time_ms % (1000 * 60) / 1000:.2f}"

				stats_text = (f"Solution: {num_moves} moves | "
							f"Time: {time_ms} ms | "
				  			f"Searched: {total_searched} boards | "
							f"Peak Memory: {peak_states} states ({mem_str})")
				self.stats_label.setText(stats_text)
				self.stats_label.setStyleSheet("font-size: 10pt; color: #5cb85c; background: transparent;")
				
				QMessageBox.information(self, "Success", 
					f"Solution found!\n\n"
					f"Moves: {num_moves}\n"
					f"Boards searched: {total_searched}\n"
					f"Peak memory: {peak_states} states ({mem_str})")
			else:
				QMessageBox.critical(self, "Error", "Invalid response format")
				
		except subprocess.TimeoutExpired:
			QMessageBox.critical(self, "Error", "Solver timed out")
		except FileNotFoundError:
			QMessageBox.critical(self, "Error", "Executable 'n-puzzle' not found in current directory")
		except json.JSONDecodeError:
			QMessageBox.critical(self, "Error", f"Invalid JSON response:\n{result.stdout}")
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Unexpected error:\n{str(e)}")
		
	def _play_solution(self):
		if not self.solution_moves:
			QMessageBox.warning(self, "Warning", "No solution to play")
			return
		if self.animation_running:
			return
		self.animation_running = True
		self.current_move_index = 0
		self._disable_buttons()
		self.animation_timer.start(self.animation_speed_ms)

	def _reset_puzzle(self):
		if not hasattr(self, 'initial_grid') or not self.initial_grid:
			QMessageBox.warning(self, "Warning", "No initial puzzle to reset to")
			return
		
		self.grid = self.initial_grid.copy()
		self._update_empty_pos()
		self._draw_grid()
		
	def _animation_tick(self):
		if self.current_move_index >= len(self.solution_moves):
			self.animation_timer.stop()
			self.animation_running = False
			self._enable_buttons()
			return
			
		move = self.solution_moves[self.current_move_index]
		success = self._apply_move(move)
		
		if not success:
			self.animation_timer.stop()
			QMessageBox.critical(self, "Error", f"Invalid move at step {self.current_move_index + 1}")
			self.animation_running = False
			self._enable_buttons()
			return
			
		self._draw_grid()
		self.current_move_index += 1
		
	def _apply_move(self, move: int) -> bool:
		row, col = self.empty_pos
		new_row, new_col = row, col

		match move:
			case 1:
				new_row -= 1
			case 2:
				new_row += 1
			case 3:
				new_col -= 1
			case 4:
				new_col += 1
			case _:
				return False

		if not (0 <= new_row < self.n and 0 <= new_col < self.n):
			return False
			
		old_idx = row * self.n + col
		new_idx = new_row * self.n + new_col
		
		self.grid[old_idx], self.grid[new_idx] = self.grid[new_idx], self.grid[old_idx]
		self.empty_pos = (new_row, new_col)
		
		return True
	
	def _disable_buttons(self):
		self.gen_button.setEnabled(False)
		self.reset_button.setEnabled(False)
		self.solve_button.setEnabled(False)
		self.play_button.setEnabled(False)
		self.n_combo.setEnabled(False)
		
	def _enable_buttons(self):
		self.gen_button.setEnabled(True)
		self.reset_button.setEnabled(True)
		self.solve_button.setEnabled(True)
		self.n_combo.setEnabled(True)
		if self.solution_moves:
			self.play_button.setEnabled(True)


def main():
	app = QApplication(sys.argv)
	window = NPuzzleGUI()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
