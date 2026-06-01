#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import signal
from pathlib import Path
from typing import Optional

from PIL import Image

from PyQt6.QtCore import Qt, QTimer, QProcess, QByteArray
from PyQt6.QtGui import (
	QColor, QBrush, QPen, QFont, QPainter, QPixmap, QImage
)
from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
	QPushButton, QComboBox, QLabel, QMessageBox, QGraphicsView,
	QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QSlider, QFrame,
	QGraphicsPixmapItem
)


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
	if img.mode not in ("RGB", "RGBA"):
		img = img.convert("RGBA")
	if img.mode == "RGB":
		qimg = QImage(img.tobytes("raw", "RGB"), img.width, img.height, QImage.Format.Format_RGB888)
	else:
		qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
	return QPixmap.fromImage(qimg.copy())


class PuzzleScene(QGraphicsScene):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setBackgroundBrush(QBrush(QColor(160, 82, 45)))


class WoodFrame(QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setStyleSheet("""QFrame {
			background: qlineargradient(x1: 0, y1:0, x2:1, y2:1,
			stop: 0 #8B4513, stop:0.5 #A0522D, stop:1 #8B4513);
			border: 3px solid #654321;
			border-radius: 8px;
			padding: 15px;
		}""")
		self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
		self.setLineWidth(3)


class NPuzzleGUI(QMainWindow):
	TILE_COLOR = QColor(76, 175, 80)
	EMPTY_COLOR = QColor(232, 213, 196)
	TILE_TEXT_COLOR = QColor(255, 255, 255)
	WOOD_COLOR = QColor(160, 82, 45)
	BG_COLOR = QColor(50, 50, 60)

	def __init__(self):
		super().__init__()

		# Paths / app dir
		self.app_dir = Path(__file__).resolve().parent
		self.solver_path = self.app_dir / "n-puzzle"
		self.puzzles_dir = self.app_dir / "puzzles"
		self.assets_dir = self.app_dir / "assets"

		# puzzle state
		self.n = 3
		self.grid: list[int] = []
		self.initial_grid: list[int] = []
		self.solution_moves: list[int] = []
		self.empty_pos: tuple[int, int] = (0, 0)

		# options
		self.selected_heuristic = "Manhattan distance"
		self.selected_puzzle_file: Optional[str] = None
		self.greedy_search_enabled = False

		# animation
		self.is_playing = False
		self.moves_per_second = 5.0
		self.animation_speed_ms = 200
		self.current_move_index = 0
		self.animation_timer = QTimer()
		self.animation_timer.timeout.connect(self._animation_tick)

		# QProcess solver (no threads)
		self.proc: Optional[QProcess] = None
		self._proc_stdout = ""
		self._proc_stderr = ""

		# picture mode
		self.picture_mode = False
		self.snake_image_path = str(self.assets_dir / "npuzzle.png")
		self._base_image: Optional[Image.Image] = None
		self._spiral_goal_map: Optional[list[list[int]]] = None
		self._tile_qpixmaps: dict[int, QPixmap] = {}

		# graphics
		self.tile_size = 80
		self._grid_items_built_for: Optional[tuple[int, int]] = None  # (n, tile_size)
		self._rect_items: dict[tuple[int, int], QGraphicsRectItem] = {}
		self._text_items: dict[tuple[int, int], QGraphicsTextItem] = {}
		self._pix_items: dict[tuple[int, int], Optional[QGraphicsPixmapItem]] = {}
		self._font = QFont("Helvetica", 18, QFont.Weight.Bold)

		# fade overlay
		self._fade_pixmap_item: Optional[QGraphicsPixmapItem] = None
		self._fade_timer: Optional[QTimer] = None
		self._fade_frames: list[QPixmap] = []
		self._fade_frame_index = 0

		# resize debounce
		self.resize_timer = QTimer()
		self.resize_timer.setSingleShot(True)
		self.resize_timer.timeout.connect(self._handle_resize)

		self._setup_ui()
		self._generate_puzzle()
		self.resize(1200, 1200)

	# ---------------- UI ----------------
	def _setup_ui(self):
		self.setWindowTitle("N-Puzzle Solver")
		self.setStyleSheet(f"QMainWindow {{ background-color: {self.BG_COLOR.name()}; }}")

		central = QWidget()
		central.setStyleSheet(f"background-color: {self.BG_COLOR.name()};")
		self.setCentralWidget(central)

		main = QVBoxLayout(central)
		main.setContentsMargins(15, 15, 15, 15)
		main.setSpacing(12)

		# row 1 buttons
		row1 = QHBoxLayout()
		row1.setSpacing(10)

		self.gen_button = QPushButton("Generate")
		self.gen_button.setStyleSheet(self._btn_css("#2196F3"))
		self.gen_button.clicked.connect(self._generate_puzzle)
		row1.addWidget(self.gen_button)

		self.reset_button = QPushButton("Reset")
		self.reset_button.setStyleSheet(self._btn_css("#F44336"))
		self.reset_button.clicked.connect(self._reset_puzzle)
		row1.addWidget(self.reset_button)

		self.solve_button = QPushButton("Solve")
		self.solve_button.setStyleSheet(self._btn_css("#FF9800"))
		self.solve_button.clicked.connect(self._solve_puzzle)
		row1.addWidget(self.solve_button)

		self.play_button = QPushButton("Play Solution")
		self.play_button.setStyleSheet(self._btn_css("#9C27B0"))
		self.play_button.clicked.connect(self._play_solution)
		self.play_button.setEnabled(False)
		row1.addWidget(self.play_button)

		self.cancel_button = QPushButton("Cancel")
		self.cancel_button.setStyleSheet(self._btn_css("#F44336"))
		self.cancel_button.clicked.connect(self._cancel)
		self.cancel_button.setEnabled(False)
		row1.addWidget(self.cancel_button)

		row1.addStretch()
		main.addLayout(row1)

		# row 2 config
		row2 = QHBoxLayout()
		row2.setSpacing(10)

		row2.addWidget(self._label("Grid Size (N):"))
		self.n_combo = QComboBox()
		self.n_combo.addItems([str(i) for i in range(2, 21)])
		self.n_combo.setCurrentText(str(self.n))
		self.n_combo.setStyleSheet(self._combo_css())
		self.n_combo.currentTextChanged.connect(self._on_n_changed)
		row2.addWidget(self.n_combo)

		row2.addSpacing(20)
		row2.addWidget(self._label("Heuristic:"))
		self.heuristic_combo = QComboBox()
		self.heuristic_combo.addItems([
			"Manhattan distance",
			"Linear conflict",
			"Hamming distance",
			"Manhattan + LC",
			"Dijkstra (no heuristic)",
		])
		self.heuristic_combo.setCurrentText("Manhattan distance")
		self.heuristic_combo.setStyleSheet(self._combo_css())
		self.heuristic_combo.currentTextChanged.connect(self._on_heuristic_changed)
		row2.addWidget(self.heuristic_combo)

		row2.addSpacing(20)
		row2.addWidget(self._label("Puzzle File:"))
		self.puzzle_combo = QComboBox()
		self.puzzle_combo.addItem("(Random)", None)
		for pf in self._load_puzzle_files():
			self.puzzle_combo.addItem(pf, pf)
		self.puzzle_combo.setStyleSheet(self._combo_css())
		self.puzzle_combo.currentIndexChanged.connect(self._on_puzzle_file_changed)
		row2.addWidget(self.puzzle_combo)

		row2.addStretch()
		main.addLayout(row2)

		# row 3 options
		row3 = QHBoxLayout()
		row3.setSpacing(10)

		self.greedy_button = QPushButton("Greedy Search")
		self.greedy_button.setCheckable(True)
		self.greedy_button.setChecked(False)
		self.greedy_button.setStyleSheet(self._toggle_css())
		self.greedy_button.clicked.connect(self._on_greedy_toggled)
		row3.addWidget(self.greedy_button)

		self.picture_button = QPushButton("Picture Mode")
		self.picture_button.setCheckable(True)
		self.picture_button.setChecked(False)
		self.picture_button.setStyleSheet(self._toggle_css())
		self.picture_button.clicked.connect(self._on_picture_toggled)
		row3.addWidget(self.picture_button)

		row3.addSpacing(20)
		row3.addWidget(self._label("Animation Speed:"))

		self.speed_slider = QSlider(Qt.Orientation.Horizontal)
		self.speed_slider.setMinimum(1)
		self.speed_slider.setMaximum(50)
		self.speed_slider.setValue(4)  # 2 moves/sec
		self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
		self.speed_slider.setTickInterval(5)
		self.speed_slider.setStyleSheet(self._slider_css())
		self.speed_slider.valueChanged.connect(self._on_speed_changed)
		row3.addWidget(self.speed_slider, 1)

		self.speed_value = QLabel("5.0 moves/sec")
		self.speed_value.setStyleSheet("font-size: 10pt; color: white; background: transparent; min-width: 110px;")
		row3.addWidget(self.speed_value)

		row3.addStretch()
		main.addLayout(row3)

		# status
		self.status_label = QLabel("Ready")
		self.status_label.setStyleSheet("font-size: 11pt; color: #aaa; background: transparent;")
		main.addWidget(self.status_label)

		# view
		self.wood_frame = WoodFrame()
		frame_layout = QVBoxLayout(self.wood_frame)
		frame_layout.setContentsMargins(0, 0, 0, 0)

		self.scene = PuzzleScene()
		self.view = QGraphicsView(self.scene)
		self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
		self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.view.setStyleSheet("QGraphicsView { border: none; background-color: #A0522D; }")
		self.view.setFrameStyle(QFrame.Shape.NoFrame)
		frame_layout.addWidget(self.view)

		main.addWidget(self.wood_frame, 1, Qt.AlignmentFlag.AlignCenter)

		self._update_view_size()

	def _label(self, text: str) -> QLabel:
		lbl = QLabel(text)
		lbl.setStyleSheet("font-size: 11pt; color: white; background: transparent;")
		return lbl

	def _btn_css(self, color: str) -> str:
		return f"""
			QPushButton {{
				background-color: {color};
				color: white;
				font-size: 11pt;
				font-weight: bold;
				padding: 8px 15px;
				border: none;
				border-radius: 4px;
			}}
			QPushButton:hover {{ background-color: #666; }}
			QPushButton:disabled {{ background-color: #555; color: #aaa; }}
		"""

	def _combo_css(self) -> str:
		return """
			QComboBox {
				font-size: 11pt;
				padding: 5px;
				background-color: white;
				color: black;
				border: 2px solid #555;
				border-radius: 4px;
			}
			QComboBox::drop-down { border: none; }
			QComboBox QAbstractItemView {
				background-color: white;
				color: black;
				selection-background-color: #5cb85c;
			}
		"""

	def _toggle_css(self) -> str:
		return """
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
			QPushButton:checked:hover { background-color: #7ad87a; }
			QPushButton:hover { background-color: #666; }
		"""

	def _slider_css(self) -> str:
		return """
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
			QSlider::handle:horizontal:hover { background: #4cae4c; }
		"""

	# ---------------- resize ----------------
	def resizeEvent(self, a0):
		super().resizeEvent(a0)
		self.resize_timer.start(100)

	def _handle_resize(self):
		self._hide_final_overlay()
		self._update_view_size()
		self._rebuild_scene_items()
		self._refresh_all_cells()

	def _update_view_size(self):
		max_canvas = 1080
		self.tile_size = min(80, max_canvas // self.n)
		canvas = self.n * self.tile_size
		self.scene.setSceneRect(0, 0, canvas, canvas)
		self.view.setMinimumSize(canvas + 20, canvas + 20)

		font_size = max(10, min(28, self.tile_size // 2))
		self._font = QFont("Helvetica", font_size, QFont.Weight.Bold)

	# ---------------- puzzles ----------------
	def _load_puzzle_files(self) -> list[str]:
		if not self.puzzles_dir.exists():
			return []
		return sorted([p.name for p in self.puzzles_dir.iterdir() if p.is_file()])

	def _on_puzzle_file_changed(self, index: int):
		self.selected_puzzle_file = self.puzzle_combo.itemData(index)
		if self.selected_puzzle_file:
			self._load_puzzle_from_file(self.puzzles_dir / self.selected_puzzle_file)
		else:
			self._generate_puzzle()

	def _load_puzzle_from_file(self, filepath: Path):
		self._hide_final_overlay()
		if self.picture_mode:
			self._try_load_random_picture()

		try:
			rows: list[list[int]] = []
			for raw in filepath.read_text().splitlines():
				line = raw.split("#", 1)[0].strip()
				if not line:
					continue
				rows.append([int(x) for x in line.split()])

			if not rows:
				raise ValueError("No grid data found in file")

			n = len(rows)
			for i, r in enumerate(rows):
				if len(r) != n:
					raise ValueError(f"Row {i} has {len(r)} values, expected {n}")

			self.n = n
			self.n_combo.setCurrentText(str(n))
			self._spiral_goal_map = None

			self.grid = [v for r in rows for v in r]
			self.initial_grid = self.grid.copy()
			self._update_empty_pos()

			self.solution_moves.clear()
			self.play_button.setEnabled(False)

			self._update_view_size()
			self._rebuild_scene_items()
			self._refresh_all_cells()
			self._update_status(f"Loaded puzzle from {filepath.name}")
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to load puzzle file:\n{e}")

	def _on_n_changed(self, value: str):
		self._hide_final_overlay()
		self.n = int(value)
		self.solution_moves.clear()
		self.play_button.setEnabled(False)
		self._spiral_goal_map = None
		self._update_view_size()
		self._generate_puzzle()

	def _generate_puzzle(self):
		self._hide_final_overlay()
		if self.picture_mode:
        # Try switching picture; if it fails, keep existing picture tiles
			old_path = self.snake_image_path
			old_base = self._base_image
			old_tiles = dict(self._tile_qpixmaps)
			old_goal = self._spiral_goal_map

			try:
				self.snake_image_path = self._pick_random_picture_asset()
				self._base_image = None
				self._spiral_goal_map = None
				self._ensure_picture_tiles()  # <-- force build now
				self._update_status(f"Picture: {Path(self.snake_image_path).name}")
			except Exception as e:
				# restore previous picture
				self.snake_image_path = old_path
				self._base_image = old_base
				self._tile_qpixmaps = old_tiles
				self._spiral_goal_map = old_goal
				QMessageBox.warning(self, "Image Error", f"Could not load new picture:\n{e}")


		size = self.n * self.n
		tiles = list(range(size))

		# Generate solvable only (mirrors C++ behavior)
		for _ in range(2000):
			random.shuffle(tiles)
			if self._is_solvable(tiles):
				break
		else:
			QMessageBox.critical(self, "Error", "Failed to generate a solvable puzzle.")
			return

		self.grid = tiles
		self.initial_grid = self.grid.copy()
		self._update_empty_pos()

		self.solution_moves.clear()
		self.play_button.setEnabled(False)

		self._update_view_size()
		self._rebuild_scene_items()
		self._refresh_all_cells()
		self._update_status(f"Generated random solvable {self.n}x{self.n} puzzle")

	def _restore_to_initial_grid(self):
		if not self.initial_grid:
			return
		self.grid = self.initial_grid.copy()
		self._update_empty_pos()

	def _reset_puzzle(self):
		if self.is_playing:
			return
		self._hide_final_overlay()
		if not self.initial_grid:
			QMessageBox.warning(self, "Warning", "No initial puzzle to reset to")
			return
		self._restore_to_initial_grid()
		self._refresh_all_cells()
		self._update_status("Puzzle reset to initial state")

	def _update_empty_pos(self):
		idx = self.grid.index(0)
		self.empty_pos = (idx // self.n, idx % self.n)

	# ---------------- solvability (matches C++) ----------------
	def _goal_tiles_flat(self) -> list[int]:
		goal = self._build_spiral_goal_map()
		return [goal[r][c] for r in range(self.n) for c in range(self.n)]

	def _build_goal_rank(self, goal_tiles: list[int]) -> list[int]:
		size = len(goal_tiles)
		goal_rank = [0] * size
		rank = 0
		for t in goal_tiles:
			if t == 0:
				continue
			goal_rank[t] = rank
			rank += 1
		return goal_rank

	def _count_inversions(self, tiles: list[int], goal_rank: list[int]) -> int:
		seq = [goal_rank[v] for v in tiles if v != 0]
		inv = 0
		for i in range(len(seq)):
			ai = seq[i]
			for j in range(i + 1, len(seq)):
				if ai > seq[j]:
					inv += 1
		return inv

	def _blank_row_from_bottom(self, blank_index: int) -> int:
		row_from_top = blank_index // self.n
		return self.n - row_from_top

	def _is_solvable(self, start_tiles: list[int]) -> bool:
		n = self.n
		goal_tiles = self._goal_tiles_flat()
		goal_rank = self._build_goal_rank(goal_tiles)

		start_inv = self._count_inversions(start_tiles, goal_rank)
		goal_inv = self._count_inversions(goal_tiles, goal_rank)

		if (n % 2) == 1:
			return (start_inv % 2) == (goal_inv % 2)

		start_blank = self._blank_row_from_bottom(start_tiles.index(0))
		goal_blank = self._blank_row_from_bottom(goal_tiles.index(0))
		return ((start_inv + start_blank) % 2) == ((goal_inv + goal_blank) % 2)

	# ---------------- scene items (fast updates) ----------------
	def _rebuild_scene_items(self):
		if self._grid_items_built_for == (self.n, self.tile_size):
			return

		self.scene.clear()
		self._rect_items.clear()
		self._text_items.clear()
		self._pix_items.clear()
		self._grid_items_built_for = (self.n, self.tile_size)

		if self.picture_mode:
			try:
				self._ensure_picture_tiles()
			except Exception:
				pass

		pen = QPen(QColor(30, 30, 30), 2)

		for r in range(self.n):
			for c in range(self.n):
				x = c * self.tile_size
				y = r * self.tile_size

				rect = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
				rect.setPen(pen)
				self.scene.addItem(rect)
				self._rect_items[(r, c)] = rect

				text = QGraphicsTextItem("")
				text.setFont(self._font)
				text.setDefaultTextColor(self.TILE_TEXT_COLOR)
				self.scene.addItem(text)
				self._text_items[(r, c)] = text

				self._pix_items[(r, c)] = None

	def _refresh_all_cells(self):
		for r in range(self.n):
			for c in range(self.n):
				self._refresh_cell(r, c)

	def _refresh_cell(self, r: int, c: int):
		v = self.grid[r * self.n + c]
		rect = self._rect_items[(r, c)]
		text = self._text_items[(r, c)]
		pix_item = self._pix_items[(r, c)]

		x = c * self.tile_size
		y = r * self.tile_size

		if v == 0:
			rect.setBrush(QBrush(self.EMPTY_COLOR))
			text.setPlainText("")
			text.hide()
			if pix_item is not None:
				pix_item.hide()
			return

		if self.picture_mode and v in self._tile_qpixmaps:
			rect.setBrush(QBrush(self.WOOD_COLOR))
			text.setPlainText("")
			text.hide()

			if pix_item is None:
				pix_item = self.scene.addPixmap(self._tile_qpixmaps[v])
				assert pix_item is not None
				pix_item.setZValue(10)
				self._pix_items[(r, c)] = pix_item
			else:
				pix_item.setPixmap(self._tile_qpixmaps[v])

			pix_item.setPos(x, y)
			pix_item.show()
			return

		# normal tile
		rect.setBrush(QBrush(self.TILE_COLOR))
		if pix_item is not None:
			pix_item.hide()

		text.setPlainText(str(v))
		br = text.boundingRect()
		text.setPos(x + (self.tile_size - br.width()) / 2,
					y + (self.tile_size - br.height()) / 2)
		text.show()

	# ---------------- picture mode ----------------
	def _pick_random_picture_asset(self) -> str:
		exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".avif"}
		files = [p for p in self.assets_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
		if not files:
			raise FileNotFoundError(f"No images found in {self.assets_dir}")

		random.shuffle(files)
		last_err: Exception | None = None

		for p in files:
			try:
				with Image.open(p) as im:
					im.verify()  # quick decode check
				return str(p)
			except Exception as e:
				last_err = e
				continue

		raise RuntimeError(f"Found images but none could be opened by Pillow. Last error: {last_err}")

	def _try_load_random_picture(self):
		try:
			self.snake_image_path = self._pick_random_picture_asset()
			self._base_image = None
			self._tile_qpixmaps.clear()
			self._spiral_goal_map = None
			self._update_status(f"Picture: {Path(self.snake_image_path).name}")
		except Exception as e:
			self._update_status(f"Random picture load failed: {e}")

	def _on_picture_toggled(self, checked: bool):
		self._hide_final_overlay()
		self.picture_mode = checked

		if self.picture_mode:
			try:
				self._ensure_picture_tiles()
			except Exception as e:
				QMessageBox.critical(self, "Image Error", str(e))
				self.picture_mode = False
				self.picture_button.setChecked(False)

		self._rebuild_scene_items()
		self._refresh_all_cells()

	def _build_spiral_goal_map(self) -> list[list[int]]:
		n = self.n
		goal: list[list[int]] = [[0] * n for _ in range(n)]
		top, left = 0, 0
		bottom, right = n - 1, n - 1
		val = 1
		last = n * n
		while top <= bottom and left <= right:
			for c in range(left, right + 1):
				goal[top][c] = val
				val += 1
			top += 1
			for r in range(top, bottom + 1):
				goal[r][right] = val
				val += 1
			right -= 1
			if top <= bottom:
				for c in range(right, left - 1, -1):
					goal[bottom][c] = val
					val += 1
				bottom -= 1
			if left <= right:
				for r in range(bottom, top - 1, -1):
					goal[r][left] = val
					val += 1
				left += 1
		for r in range(n):
			for c in range(n):
				if goal[r][c] == last:
					goal[r][c] = 0
					return goal
		return goal

	def _correct_tile_number_for_position(self, r: int, c: int) -> int:
		if self._spiral_goal_map is None or len(self._spiral_goal_map) != self.n:
			self._spiral_goal_map = self._build_spiral_goal_map()
		return self._spiral_goal_map[r][c]

	def _ensure_picture_tiles(self):
		if self.tile_size <= 0:
			return

		if self._base_image is None:
			self._base_image = Image.open(self.snake_image_path).convert("RGB")

		tile = self.tile_size
		board_px = tile * self.n
		board_img = self._base_image.resize((board_px, board_px), Image.Resampling.LANCZOS)

		self._tile_qpixmaps.clear()
		for r in range(self.n):
			for c in range(self.n):
				num = self._correct_tile_number_for_position(r, c)
				if num == 0:
					continue
				crop = board_img.crop((c * tile, r * tile, (c + 1) * tile, (r + 1) * tile))
				self._tile_qpixmaps[num] = pil_to_qpixmap(crop)

	def _capture_board_image(self) -> Image.Image:
		tile = self.tile_size
		n = self.n

		if self._base_image is None:
			self._base_image = Image.open(self.snake_image_path).convert("RGB")

		board_img = self._base_image.resize((tile * n, tile * n), Image.Resampling.LANCZOS)
		out = Image.new("RGB", (tile * n, tile * n), (0, 0, 0))

		goal_map = self._build_spiral_goal_map()
		pos: dict[int, tuple[int, int]] = {}
		for rr in range(n):
			for cc in range(n):
				pos[goal_map[rr][cc]] = (rr, cc)

		for r in range(n):
			for c in range(n):
				v = self.grid[r * n + c]
				if v == 0:
					continue
				gr, gc = pos[v]
				crop = board_img.crop((gc * tile, gr * tile, (gc + 1) * tile, (gr + 1) * tile))
				out.paste(crop, (c * tile, r * tile))
		return out

	# ---------------- options ----------------
	def _on_speed_changed(self, value: int):
		self.moves_per_second = value / 2.0
		self.animation_speed_ms = int(1000 / self.moves_per_second)
		self.speed_value.setText(f"{self.moves_per_second:.1f} moves/sec")
		if self.animation_timer.isActive():
			self.animation_timer.setInterval(self.animation_speed_ms)

	def _on_heuristic_changed(self, value: str):
		self.selected_heuristic = value

	def _on_greedy_toggled(self, checked: bool):
		self._hide_final_overlay()
		self.greedy_search_enabled = checked

	# ---------------- solver (QProcess) ----------------
	def _solve_puzzle(self):
		self._hide_final_overlay()

		if not self.solver_path.exists():
			QMessageBox.critical(self, "Error", f"Solver not found: {self.solver_path}")
			return

		if self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning:
			return

		self._proc_stdout = ""
		self._proc_stderr = ""

		self.solve_button.setEnabled(False)
		self.cancel_button.setEnabled(True)
		self._update_status("Solving puzzle...")

		self.proc = QProcess(self)
		self.proc.setWorkingDirectory(str(self.app_dir))

		args: list[str] = []
		if self.selected_puzzle_file:
			args.append(self.selected_puzzle_file)

		self.proc.readyReadStandardOutput.connect(self._on_proc_stdout)
		self.proc.readyReadStandardError.connect(self._on_proc_stderr)
		self.proc.finished.connect(self._on_proc_finished)

		self.proc.start(str(self.solver_path), args)

		# Build stdin exactly as C++ expects:
		# - parseHeuristics(): 1 line (or 2 if greedy)
		# - configFromGUI(): reads numbers until EOF
		lines: list[str] = []
		if self.greedy_search_enabled:
			lines.append("Greedy search enabled")
		lines.append(self.selected_heuristic)

		# Only send grid when NOT using file input
		if not self.selected_puzzle_file:
			lines.append(" ".join(map(str, self.grid)))

		input_data = "\n".join(lines) + "\n"
		self.proc.write(input_data.encode("utf-8"))
		self.proc.closeWriteChannel()  # forces EOF to stop configFromGUI()

	def _on_proc_stdout(self):
		assert self.proc is not None
		ba = self.proc.readAllStandardOutput()
		self._proc_stdout += ba.data().decode("utf-8", errors="replace")

	def _on_proc_stderr(self):
		assert self.proc is not None
		ba = self.proc.readAllStandardError()
		self._proc_stderr += ba.data().decode("utf-8", errors="replace")

	def _on_proc_finished(self, exit_code: int, _exit_status):
		stdout = self._proc_stdout.strip()
		stderr = self._proc_stderr.strip()

		self.solve_button.setEnabled(True)
		self.cancel_button.setEnabled(False)

		# Process object can be re-used but easiest is discard
		self.proc = None

		if exit_code != 0:
			# show alert like linux gui
			details = stderr or stdout or f"(no output; exit code {exit_code})"
			self._update_status("Solve failed")
			QMessageBox.critical(self, "Solver Error", details)
			return

		try:
			result = json.loads(stdout)
		except Exception as e:
			self._update_status("Solve failed")
			QMessageBox.critical(self, "Solver Error", f"Invalid JSON from solver:\n{e}\n\nOutput:\n{stdout}\n\nStderr:\n{stderr}")
			return

		self.solution_moves = result.get("moves", [])
		self.play_button.setEnabled(bool(self.solution_moves))

		stats_msg = self._format_stats(result, len(self.solution_moves))
		self._update_status(stats_msg)

	def _cancel(self):
		# cancel animation
		if self.is_playing:
			self._stop_animation(cancelled=True)
			return

		# cancel solver
		if self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning:
			self.proc.terminate()
			if not self.proc.waitForFinished(300):
				self.proc.kill()

		self.solve_button.setEnabled(True)
		self.cancel_button.setEnabled(False)
		self._update_status("Cancelled")

	def _format_stats(self, result: dict, num_moves: int) -> str:
		time_ms = result.get("time_ms", "N/A")
		total = result.get("total_searched", "N/A")
		peak_states = result.get("peak_memory_states", "N/A")
		peak_bytes = result.get("peak_memory_bytes", "N/A")

		if isinstance(peak_bytes, int):
			if peak_bytes < 1024:
				mem_str = f"{peak_bytes} bytes"
			elif peak_bytes < 1024 * 1024:
				mem_str = f"{peak_bytes / 1024:.2f} KB"
			else:
				mem_str = f"{peak_bytes / (1024 * 1024):.2f} MB"
		else:
			mem_str = str(peak_bytes)

		return (f"Solution: {num_moves} moves | "
				f"Time: {time_ms} ms | "
				f"Searched: {total} boards | "
				f"Peak memory: {peak_states} states ({mem_str})")

	# ---------------- play / animation ----------------
	def _play_solution(self):
		self._hide_final_overlay()
		if not self.solution_moves:
			QMessageBox.information(self, "No Solution", "No solution available to play")
			return
		if self.is_playing:
			return

		self._restore_to_initial_grid()
		self._refresh_all_cells()

		self.is_playing = True
		self.current_move_index = 0

		self.gen_button.setEnabled(False)
		self.reset_button.setEnabled(False)
		self.solve_button.setEnabled(False)
		self.play_button.setEnabled(False)
		self.cancel_button.setEnabled(True)
		self.n_combo.setEnabled(False)

		self.animation_timer.start(self.animation_speed_ms)
		self._update_status("Playing solution...")

	def _animation_tick(self):
		if self.current_move_index >= len(self.solution_moves):
			self._stop_animation(cancelled=False)
			return

		move = self.solution_moves[self.current_move_index]
		old_blank = self.empty_pos

		if not self._apply_move(move):
			self.animation_timer.stop()
			QMessageBox.critical(self, "Error", f"Invalid move at step {self.current_move_index + 1}")
			self._stop_animation(cancelled=True)
			return

		new_blank = self.empty_pos
		self._refresh_cell(old_blank[0], old_blank[1])
		self._refresh_cell(new_blank[0], new_blank[1])

		self.current_move_index += 1
		self._update_status(f"Playing solution...Step {self.current_move_index}/{len(self.solution_moves)}")

	def _stop_animation(self, cancelled: bool):
		self.animation_timer.stop()
		self.is_playing = False

		self.gen_button.setEnabled(True)
		self.reset_button.setEnabled(True)
		self.solve_button.setEnabled(True)
		self.n_combo.setEnabled(True)
		self.play_button.setEnabled(bool(self.solution_moves))
		self.cancel_button.setEnabled(False)

		if cancelled:
			self._update_status("Animation cancelled")
			return

		self._fade_in_solved_picture(duration_ms=800, steps=20)
		self._update_status("Solution complete!")

	def _apply_move(self, move: int) -> bool:
		row, col = self.empty_pos
		nr, nc = row, col

		if move == 1:
			nr -= 1
		elif move == 2:
			nr += 1
		elif move == 3:
			nc -= 1
		elif move == 4:
			nc += 1
		else:
			return False

		if not (0 <= nr < self.n and 0 <= nc < self.n):
			return False

		old_idx = row * self.n + col
		new_idx = nr * self.n + nc
		self.grid[old_idx], self.grid[new_idx] = self.grid[new_idx], self.grid[old_idx]
		self.empty_pos = (nr, nc)
		return True

	# ---------------- fade overlay ----------------
	def _fade_in_solved_picture(self, duration_ms: int = 600, steps: int = 12):
		if not self.picture_mode:
			return

		try:
			tile = self.tile_size
			n = self.n
			w = tile * n
			h = tile * n

			if self._base_image is None:
				self._base_image = Image.open(self.snake_image_path).convert("RGB")
			solved = self._base_image.resize((w, h), Image.Resampling.LANCZOS)
			start = self._capture_board_image()

			self._fade_frames = []
			for i in range(steps + 1):
				t = i / steps
				frame = Image.blend(start, solved, t)
				self._fade_frames.append(pil_to_qpixmap(frame))

			self._fade_frame_index = 0

			if self._fade_pixmap_item is None:
				self._fade_pixmap_item = self.scene.addPixmap(self._fade_frames[0])
				assert self._fade_pixmap_item is not None
				self._fade_pixmap_item.setPos(0, 0)
				self._fade_pixmap_item.setZValue(9999)
			else:
				self._fade_pixmap_item.setPixmap(self._fade_frames[0])
				self._fade_pixmap_item.setPos(0, 0)
				self._fade_pixmap_item.setZValue(9999)

			delay = max(1, duration_ms // steps)
			if self._fade_timer is None:
				self._fade_timer = QTimer()
				self._fade_timer.timeout.connect(self._fade_tick)
			self._fade_timer.stop()
			self._fade_timer.start(delay)

		except Exception:
			return

	def _fade_tick(self):
		if not self._fade_frames or self._fade_pixmap_item is None:
			if self._fade_timer:
				self._fade_timer.stop()
			return

		self._fade_frame_index += 1
		if self._fade_frame_index >= len(self._fade_frames):
			if self._fade_timer:
				self._fade_timer.stop()
			return

		self._fade_pixmap_item.setPixmap(self._fade_frames[self._fade_frame_index])

	def _hide_final_overlay(self):
		if self._fade_timer is not None and self._fade_timer.isActive():
			self._fade_timer.stop()
		self._fade_frames = []
		self._fade_frame_index = 0

		if self._fade_pixmap_item is not None and self._fade_pixmap_item.scene() is self.scene:
			self.scene.removeItem(self._fade_pixmap_item)
		self._fade_pixmap_item = None

	# ---------------- misc ----------------
	def _update_status(self, msg: str):
		self.status_label.setText(msg)

	def closeEvent(self, a0):
		# stop solver if running
		if self.proc is not None and self.proc.state() != QProcess.ProcessState.NotRunning:
			self.proc.kill()
		super().closeEvent(a0)


def main():
	app = QApplication([])
	w = NPuzzleGUI()
	w.show()
	app.exec()


if __name__ == "__main__":
	main()