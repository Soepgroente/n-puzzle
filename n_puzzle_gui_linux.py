import tkinter as tk
from tkinter import ttk, messagebox
import random
import subprocess
import json
import threading
import time
from typing import List, Tuple
from PIL import Image, ImageTk
import os
import signal

class NPuzzleGUI:   
	def __init__(self, root):
		self.root = root
		self.root.title("N-Puzzle Solver")
		
		self.n = 3
		self.grid = []
		self.initial_grid = []
		self.solution_steps = []
		self.empty_pos = (0, 0)
		self.is_playing = False
		self.tile_labels = []
		self.tile_frames = []
		self.moves_per_second = 2.0
		self.solver_process = None
		self.current_tile_size = 0
		self.current_font_size = 0
		self.selected_heuristic = "Manhattan distance"
		self.selected_puzzle_file = None
		self.greedy_search_enabled = False
		
		self.tile_color = "#4CAF50"
		self.empty_color = "#E8D5C4"
		self.text_color = "white"
		self.wood_color = "#8B4513"
		self.wood_dark = "#654321"

		self.picture_mode = False
		self.snake_image_path = "assets/npuzzle.png"
		self._base_image = None
		self._tile_photoimages = {}
		self._spiral_goal_map = None
		self._fade_overlay = None
		self._fade_photo = None
		self._fade_overlay_visible = False
		self._fade_after_ids = []

		self.setup_ui()
		self.initialize_grid()
		self.cancel_animation_event = threading.Event()
		
		self.resize_after_id = None
		self.root.bind('<Configure>', self.on_window_resize)
		self.last_width = self.root.winfo_width()
		self.last_height = self.root.winfo_height()
		
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		# try:
		# 	self.load_random_picture()
		# except Exception as e:
		# 	self.update_status(f"Picture load skipped: {e}")
		
	def setup_ui(self):
		main_container = tk.Frame(self.root)
		main_container.pack(expand=True, fill=tk.BOTH)
		
		self.root.minsize(480, 480)
		self.root.maxsize(3860, 3860)
		
		control_frame = tk.Frame(main_container, padx=10, pady=15)
		control_frame.pack(side=tk.TOP, fill=tk.X)
		
			# Row 1: Action buttons
		first_row = tk.Frame(control_frame)
		first_row.pack(side=tk.TOP, pady=5, fill=tk.X)
		
		self.generate_btn = tk.Button(
			first_row,
			text="Generate",
			command=self.generate_puzzle,
			bg="#2196F3",
			fg="white",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2"
		)
		self.generate_btn.pack(side=tk.LEFT, padx=5)

		self.reset_btn = tk.Button(
			first_row,
			text="Reset",
			command=self.reset_puzzle,
			bg="#F44336",
			fg="white",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2"
		)
		self.reset_btn.pack(side=tk.LEFT, padx=5)

		self.solve_btn = tk.Button(
			first_row,
			text="Solve",
			command=self.solve_puzzle,
			bg="#FF9800",
			fg="white",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2"
		)
		self.solve_btn.pack(side=tk.LEFT, padx=5)
		
		self.play_btn = tk.Button(
			first_row,
			text="Play Solution",
			command=self.play_solution,
			bg="#9C27B0",
			fg="white",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2",
			state=tk.DISABLED
		)
		self.play_btn.pack(side=tk.LEFT, padx=5)
		
		self.cancel_btn = tk.Button(
			first_row,
			text="Cancel",
			command=self.cancel_solve,
			bg="#F44336",
			fg="white",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2",
			state=tk.DISABLED
		)
		self.cancel_btn.pack(side=tk.LEFT, padx=5)
		
		# Row 2: Grid Size, Heuristic, Puzzle File
		config_row = tk.Frame(control_frame)
		config_row.pack(side=tk.TOP, pady=5, fill=tk.X)
		
		tk.Label(config_row, text="Grid Size (N):").pack(side=tk.LEFT, padx=5)
		self.n_var = tk.IntVar(value=3)
		n_dropdown = ttk.Combobox(
			config_row, 
			textvariable=self.n_var,
			values=list(range(2, 21)),
			state="readonly",
			width=5
		)
		n_dropdown.pack(side=tk.LEFT, padx=5)
		n_dropdown.bind("<<ComboboxSelected>>", self.on_n_changed)

		tk.Label(config_row, text="Heuristic:").pack(side=tk.LEFT, padx=(15, 5))
		self.heuristic_var = tk.StringVar(value="Manhattan distance")
		heuristic_dropdown = ttk.Combobox(
			config_row,
			textvariable=self.heuristic_var,
			values=["Manhattan distance", "Linear conflict", "Hamming distance", 
					"Manhattan + LC", "Dijkstra (no heuristic)"],
			state="readonly",
			width=20
		)
		heuristic_dropdown.pack(side=tk.LEFT, padx=5)
		heuristic_dropdown.bind("<<ComboboxSelected>>", self.on_heuristic_changed)

		tk.Label(config_row, text="Puzzle File:").pack(side=tk.LEFT, padx=(15, 5))
		self.puzzle_file_var = tk.StringVar(value="(Random)")
		puzzle_files = self.load_puzzle_files()
		puzzle_values = ["(Random)"] + puzzle_files
		puzzle_dropdown = ttk.Combobox(
			config_row,
			textvariable=self.puzzle_file_var,
			values=puzzle_values,
			state="readonly",
			width=20
		)
		puzzle_dropdown.pack(side=tk.LEFT, padx=5)
		puzzle_dropdown.bind("<<ComboboxSelected>>", self.on_puzzle_file_changed)
		
		# Row 3: Greedy search & Animation speed
		options_row = tk.Frame(control_frame)
		options_row.pack(side=tk.TOP, pady=10, fill=tk.X)

		self.greedy_var = tk.BooleanVar(value=False)
		self.greedy_btn = tk.Button(
			options_row,
			text="Greedy Search",
			command=self.on_greedy_toggled,
			bg="#555",
			fg="#aaa",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2",
			relief=tk.RAISED
		)
		self.greedy_btn.pack(side=tk.LEFT, padx=5)

		# Bind hover effects
		self.greedy_btn.bind("<Enter>", self.on_greedy_hover_enter)
		self.greedy_btn.bind("<Leave>", self.on_greedy_hover_leave)

		self.picture_btn = tk.Button(
			options_row,
			text="Picture Mode",
			command=self.on_picture_toggled,
			bg="#555",
			fg="#aaa",
			padx=15,
			pady=5,
			font=("Arial", 10, "bold"),
			cursor="hand2",
			relief=tk.RAISED
		)
		self.picture_btn.pack(side=tk.LEFT, padx=5)

		tk.Label(options_row, text="Animation Speed:").pack(side=tk.LEFT, padx=(15, 5))
		
		self.speed_var = tk.DoubleVar(value=2.0)
		speed_slider = tk.Scale(
			options_row,
			from_=0.5,
			to=25.0,
			resolution=0.5,
			orient=tk.HORIZONTAL,
			variable=self.speed_var,
			length=200,
			command=self.on_speed_changed
		)
		speed_slider.pack(side=tk.LEFT, padx=5)
		
		self.speed_label = tk.Label(options_row, text="2.0 moves/sec", width=15)
		self.speed_label.pack(side=tk.LEFT, padx=5)
		
		# Status row
		status_row = tk.Frame(control_frame)
		status_row.pack(side=tk.TOP, pady=5)
		
		self.status_label = tk.Label(
			status_row,
			text="Ready",
			fg="#666",
			font=("Arial", 10)
		)
		self.status_label.pack()
		
		# Puzzle display area
		puzzle_container = tk.Frame(main_container)
		puzzle_container.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)
		
		self.outer_frame = tk.Frame(
			puzzle_container,
			bg=self.wood_dark,
			padx=20,
			pady=20
		)
		self.outer_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
		
		inner_frame = tk.Frame(
			self.outer_frame,
			bg=self.wood_color,
			padx=15,
			pady=15,
			relief=tk.RIDGE,
			borderwidth=5
		)
		inner_frame.pack()
		
		self.grid_frame = tk.Frame(
			inner_frame,
			bg=self.wood_color,
			padx=5,
			pady=5
		)
		self.grid_frame.pack()
		
	def on_window_resize(self, event):
		if event.widget != self.root:
			return
			
		current_width = self.root.winfo_width()
		current_height = self.root.winfo_height()
		
		if (abs(current_width - self.last_width) > 10 or 
			abs(current_height - self.last_height) > 10):
			
			if self.resize_after_id:
				self.root.after_cancel(self.resize_after_id)
			
			self.resize_after_id = self.root.after(100, self.do_resize)
	
	def on_heuristic_changed(self, event):
		self.selected_heuristic = self.heuristic_var.get()

	def on_greedy_toggled(self):
		self.hide_final_overlay()
		self.greedy_search_enabled = not self.greedy_search_enabled
		if self.greedy_search_enabled:
			self.greedy_btn.config(bg="#90ee90", fg="#333", activebackground="#7ad87a")
		else:
			self.greedy_btn.config(bg="#555", fg="#aaa", activebackground="#666")

	def on_greedy_hover_enter(self, event):
		if self.greedy_search_enabled:
			self.greedy_btn.config(bg="#7ad87a")
		else:
			self.greedy_btn.config(bg="#666")

	def on_greedy_hover_leave(self, event):
		if self.greedy_search_enabled:
			self.greedy_btn.config(bg="#90ee90")
		else:
			self.greedy_btn.config(bg="#555")

	def on_puzzle_file_changed(self, event):
		selected = self.puzzle_file_var.get()
		if selected == "(Random)":
			self.selected_puzzle_file = None
			self.generate_puzzle()
		else:
			self.selected_puzzle_file = selected
			self.load_puzzle_from_file(f"puzzles/{selected}")

	def load_puzzle_files(self):
		"""Load available puzzle files from puzzles/ directory."""
		puzzle_dir = "puzzles"
		if not os.path.exists(puzzle_dir):
			return []
		
		files = [f for f in os.listdir(puzzle_dir) 
				if os.path.isfile(os.path.join(puzzle_dir, f))]
		return sorted(files)

	def load_puzzle_from_file(self, filepath):
		"""Load a puzzle from a file and display it."""
		self.hide_final_overlay()
		if self.picture_mode:
			try:
				self.load_random_picture()
			except Exception as e:
				self.update_status(f"Random picture load failed: {e}")
		try:
			with open(filepath, 'r') as f:
				lines = f.readlines()
			
			grid_rows = []
			
			for line in lines:
				if '#' in line:
					line = line[:line.index('#')]
				
				line = line.strip()
				if not line:
					continue
				
				tokens = line.split()
				row = [int(token) for token in tokens]
				grid_rows.append(row)
			
			if not grid_rows:
				raise ValueError("No grid data found in file")
			
			n = len(grid_rows)
			
			for i, row in enumerate(grid_rows):
				if len(row) != n:
					raise ValueError(f"Row {i} has {len(row)} values, expected {n}")
			
			self.n = n
			self.n_var.set(n)
			self._spiral_goal_map = None
			self.grid = grid_rows
			self.initial_grid = [row[:] for row in grid_rows]
			
			for i in range(n):
				for j in range(n):
					if self.grid[i][j] == 0:
						self.empty_pos = (i, j)
						break
			
			self.solution_steps = []
			self.play_btn.config(state=tk.DISABLED)
			self.draw_grid()
			self.update_status(f"Loaded puzzle from {os.path.basename(filepath)}")
			
		except Exception as e:
			messagebox.showerror("Error", f"Failed to load puzzle file:\n{str(e)}")

	def restore_to_initial_grid(self):
		"""Restore the board to the exact state that was solved (initial_grid)."""
		if not self.initial_grid:
			return

		self.grid = [row[:] for row in self.initial_grid]

		# recompute empty_pos
		for i in range(self.n):
			for j in range(self.n):
				if self.grid[i][j] == 0:
					self.empty_pos = (i, j)
					return

	def reset_puzzle(self):
		"""Reset the puzzle to initial configuration."""
		if self.is_playing == True:
			return
		self.hide_final_overlay()
		if not self.initial_grid:
			messagebox.showwarning("Warning", "No initial puzzle to reset to")
			return
		
		self.restore_to_initial_grid()
		
		for i in range(self.n):
			for j in range(self.n):
				self.update_tile(i, j)
		
		self.update_status("Puzzle reset to initial state")

	def do_resize(self):
		self.hide_final_overlay()
		self.last_width = self.root.winfo_width()
		self.last_height = self.root.winfo_height()
		self.draw_grid()
		self.resize_after_id = None
	
	def on_speed_changed(self, value):
		self.moves_per_second = float(value)
		self.speed_label.config(text=f"{self.moves_per_second:.1f} moves/sec")
		
	def calculate_tile_size(self):
		window_width = self.root.winfo_width()
		window_height = self.root.winfo_height()
		
		available_width = max(200, window_width - 120)
		available_height = max(200, window_height - 260)
		
		max_tile_width = (available_width - 80) // self.n
		max_tile_height = (available_height - 80) // self.n
		
		tile_size = min(max_tile_width, max_tile_height)
		tile_size = max(20, min(tile_size, 150))

		max_number = self.n * self.n - 1
		num_digits = len(str(max_number))
		
		base_font_size = tile_size // 3
		
		if num_digits == 1:
			font_size = base_font_size
		elif num_digits == 2:
			font_size = int(base_font_size * 0.85)
		else:
			font_size = int(base_font_size * 0.65)

		font_size = max(6, min(32, font_size))
		return tile_size, font_size
		
	def initialize_grid(self):
		self.n = self.n_var.get()
		size = self.n * self.n
		
		self.grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
		num = 1
		for i in range(self.n):
			for j in range(self.n):
				if num < size:
					self.grid[i][j] = num
					num += 1
				else:
					self.grid[i][j] = 0
					self.empty_pos = (i, j)
		
		self.draw_grid()
		
	def draw_grid(self):
		for widget in self.grid_frame.winfo_children():
			if widget is self._fade_overlay:
				continue
			widget.destroy()
		
		self.tile_labels = []
		self.tile_frames = []
		
		tile_size, font_size = self.calculate_tile_size()
		self.current_tile_size = tile_size
		self.current_font_size = font_size
		
		for i in range(self.n):
			row_labels = []
			row_frames = []
			for j in range(self.n):
				value = self.grid[i][j]
				
				tile_frame = tk.Frame(
					self.grid_frame,
					width=tile_size,
					height=tile_size,
					bg=self.wood_color
				)
				tile_frame.grid(row=i, column=j, padx=0, pady=0, sticky="nsew")
				tile_frame.grid_propagate(False)
				row_frames.append(tile_frame)
				
				if value == 0:
					lbl = tk.Label(
						tile_frame,
						text="",
						bg=self.empty_color,
						relief=tk.SUNKEN,
						borderwidth=2,
						font=("Arial", font_size, "bold")
					)
				else:
					lbl = tk.Label(
						tile_frame,
						text=str(value),
						bg=self.tile_color,
						fg=self.text_color,
						relief=tk.RAISED,
						borderwidth=2,
						font=("Arial", font_size, "bold")
					)
				
				lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
				row_labels.append(lbl)
			
			self.tile_labels.append(row_labels)
			self.tile_frames.append(row_frames)
		self.refresh_picture_assets_and_tiles()
	
	def update_tile(self, row, col):
		value = self.grid[row][col]
		lbl = self.tile_labels[row][col]

		if value == 0:
			lbl.config(text="", image="", bg=self.empty_color, relief=tk.SUNKEN)
			return

		if self.picture_mode:
			if value not in self._tile_photoimages:
				self.ensure_snake_tiles()

			img = self._tile_photoimages.get(value)
			if img is None:
				# fallback
				lbl.config(text=str(value), image="", bg=self.tile_color, fg=self.text_color, relief=tk.RAISED)
			else:
				lbl.config(text="", image=img, bg=self.wood_color, relief=tk.RAISED)
		else:
			lbl.config(text=str(value), image="", bg=self.tile_color, fg=self.text_color, relief=tk.RAISED)
	
	def on_n_changed(self, event):
		self.hide_final_overlay()
		self.solution_steps = []
		self.play_btn.config(state=tk.DISABLED)
		self._spiral_goal_map = None
		self.initialize_grid()
		self.update_status("Grid size changed.  Click Generate to create a puzzle.")
	
	def generate_puzzle(self):
		self.hide_final_overlay()
		if self.picture_mode:
			try:
				self.load_random_picture()
			except Exception as e:
				self.update_status(f"Random picture load failed: {e}")
		self.n = self.n_var.get()
		size = self.n * self.n
		numbers = list(range(size))
		random.shuffle(numbers)

		self.grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
		idx = 0
		for i in range(self.n):
			for j in range(self.n):
				self.grid[i][j] = numbers[idx]
				if numbers[idx] == 0:
					self.empty_pos = (i, j)
				idx += 1

		self.initial_grid = [row[:] for row in self.grid]
		self.solution_steps = []
		self.play_btn.config(state=tk.DISABLED)
		
		self.refresh_picture_assets_and_tiles()		
		self.update_status(f"Generated random {self.n}x{self.n} puzzle")
	
	def get_grid_as_list(self) -> List[int]:
		result = []
		for row in self.grid:
			result.extend(row)
		return result
	
	def solve_puzzle(self):
		self.hide_final_overlay()
		self.update_status("Solving puzzle...")
		self.solve_btn.config(state=tk.DISABLED)
		self.cancel_btn.config(state=tk.NORMAL)
		
		# Run in a separate thread to avoid blocking UI
		thread = threading.Thread(target=self.run_solver)
		thread.daemon = True
		thread.start()
	
	def cancel_solve(self):
		# If playing, cancel animation
		if self.is_playing:
			self.cancel_animation_event.set()
			self.update_status("Cancelling animation...")
			return

		# Otherwise cancel solver subprocess (your existing logic)
		if self.solver_process and self.solver_process.poll() is None:
			try:
				if os.name == 'nt':
					self.solver_process.terminate()
				else:
					self.solver_process.send_signal(signal.SIGTERM)
				self.update_status("Solver cancelled")
			except Exception as e:
				self.update_status(f"Error cancelling:  {e}")

		self.solve_btn.config(state=tk.NORMAL)
		self.cancel_btn.config(state=tk.DISABLED)
	
	def run_solver(self):
		"""Run the solver executable in a separate thread"""
		try:
			# Build input string
			input_lines = []
			
			if self.greedy_search_enabled:
				input_lines.append("Greedy search enabled")
			
			input_lines.append(self.selected_heuristic)
			
			# Add grid data
			grid_data = self.get_grid_as_list()
			input_lines.append(' '.join(map(str, grid_data)))
			
			input_data = '\n'.join(input_lines)
			
			# Build command
			cmd = ["./n-puzzle"]
			if self.selected_puzzle_file:
				cmd.append(self.selected_puzzle_file)

			self.solver_process = subprocess.Popen(
				cmd,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				bufsize=1
			)
			
			stdout, stderr = self.solver_process.communicate(input=input_data, timeout=300)
			
			if self.solver_process.returncode == 0:
				try:
					result = json.loads(stdout)
					self.solution_steps = result.get("moves", [])
					
					# Extract stats
					num_moves = len(self.solution_steps)
					time_ms = result.get("time_ms", "N/A")
					total_searched = result.get("total_searched", "N/A")
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

					if isinstance(time_ms, int):
						if time_ms < 1000:
							time_ms = str(time_ms)
						elif time_ms < 1000 * 60:
							time_ms = f"{time_ms / 1000:.2f} sec"
						else:
							time_ms = f"{time_ms / (1000 * 60)}:{time_ms % (1000 * 60) / 1000:.2f}"
					
					stats_msg = (f"Solution: {num_moves} moves | "
								f"Time: {time_ms} ms | "
								f"Searched: {total_searched} boards | "
								f"Peak memory: {peak_states} states"
								f" ({mem_str})")
					
					self.root.after(0, lambda msg=stats_msg: self.on_solve_success(msg))
				except json.JSONDecodeError as e:
					error_msg = f"Invalid JSON response: {e}\nOutput: {stdout[:200]}"
					self.root.after(0, lambda msg=error_msg: self.on_solve_error(msg))
			else:
				error_msg = stderr if stderr else f"Process exited with code {self.solver_process.returncode}"
				self.root.after(0, lambda msg=error_msg: self.on_solve_error(msg))
				
		except subprocess.TimeoutExpired:
			if self.solver_process:
				self.solver_process.kill()
			error_msg = "Solver timed out (exceeded 5 minutes)"
			self.root.after(0, lambda msg=error_msg: self.on_solve_error(msg))
			
		except FileNotFoundError:
			self.root.after(0, lambda: self.on_solve_error(
				"Executable 'n-puzzle' not found. Please ensure it's in the current directory."
			))
		except Exception as e:
			error_msg = f"Unexpected error: {str(e)}"
			self.root.after(0, lambda msg=error_msg: self.on_solve_error(msg))
		finally:
			self.solver_process = None

	def on_solve_success(self, stats_msg):
		self.solve_btn.config(state=tk.NORMAL)
		self.cancel_btn.config(state=tk.DISABLED)
		self.play_btn.config(state=tk.NORMAL)
		self.update_status(stats_msg)
	
	def on_solve_error(self, error_msg):
		self.solve_btn.config(state=tk.NORMAL)
		self.cancel_btn.config(state=tk.DISABLED)
		self.update_status("Solve failed")
		messagebox.showerror("Solver Error", error_msg)
	
	def play_solution(self):
		self.hide_final_overlay()
		if not self.solution_steps:
			messagebox.showinfo("No Solution", "No solution available to play")
			return
		if self.is_playing:
			return
		
		self.restore_to_initial_grid()
		self.refresh_picture_assets_and_tiles()
		self.cancel_animation_event.clear()

		self.generate_btn.config(state=tk.DISABLED)
		self.solve_btn.config(state=tk.DISABLED)
		self.play_btn.config(state=tk.DISABLED)
		self.cancel_btn.config(state=tk.NORMAL)
		
		self.is_playing = True
		self.update_status("Playing solution...")
		
		thread = threading.Thread(target=self.animate_solution)
		thread.daemon = True
		thread.start()
	
	def animate_solution(self):
		for step_num, move in enumerate(self.solution_steps, 1):
			if self.cancel_animation_event.is_set():
				self.root.after(0, self.on_animation_cancelled)
				return

			delay = 1.0 / self.moves_per_second
			time.sleep(delay)

			if self.cancel_animation_event.is_set():
				self.root.after(0, self.on_animation_cancelled)
				return

			self.root.after(0, lambda m=move, s=step_num: self.apply_move(m, s))

		# finished normally
		delay = 1.0 / self.moves_per_second
		time.sleep(delay)

		if self.cancel_animation_event.is_set():
			self.root.after(0, self.on_animation_cancelled)
			return

		self.root.after(0, self.on_animation_complete)

	def on_animation_cancelled(self):
		self.is_playing = False
		self.generate_btn.config(state=tk.NORMAL)
		self.solve_btn.config(state=tk.NORMAL)
		self.play_btn.config(state=tk.NORMAL)
		self.cancel_btn.config(state=tk.DISABLED)
		self.update_status("Animation cancelled")

	def apply_move(self, move:  int, step_num: int):
		"""Moves:  1=up, 2=down, 3=left, 4=right"""
		row, col = self.empty_pos
		new_row, new_col = row, col

		match move:
			case 1:
				new_row = row - 1
			case 2:
				new_row = row + 1
			case 3:
				new_col = col - 1
			case 4:
				new_col = col + 1
			case _:
				return

		if 0 <= new_row < self.n and 0 <= new_col < self.n:
			self.grid[row][col], self.grid[new_row][new_col] = \
				self.grid[new_row][new_col], self.grid[row][col]
			self.empty_pos = (new_row, new_col)
			
			self.update_tile(row, col)
			self.update_tile(new_row, new_col)
			
			self.update_status(f"Playing solution...Step {step_num}/{len(self.solution_steps)}")
	
	def build_spiral_goal_map(self):
		n = self.n
		goal = [[None] * n for _ in range(n)]

		# Spiral fill coordinates
		top, left = 0, 0
		bottom, right = n - 1, n - 1
		val = 1
		last = n * n

		while top <= bottom and left <= right:
			# left->right along top
			for c in range(left, right + 1):
				goal[top][c] = val
				val += 1
			top += 1

			# top->bottom along right
			for r in range(top, bottom + 1):
				goal[r][right] = val
				val += 1
			right -= 1

			if top <= bottom:
				# right->left along bottom
				for c in range(right, left - 1, -1):
					goal[bottom][c] = val
					val += 1
				bottom -= 1

			if left <= right:
				# bottom->top along left
				for r in range(bottom, top - 1, -1):
					goal[r][left] = val
					val += 1
				left += 1

		# Replace the last value (N^2) with 0 (blank)
		for r in range(n):
			for c in range(n):
				if goal[r][c] == last:
					goal[r][c] = 0
					break

		return goal

	def correct_tile_number_for_position(self, r, c):
		if self._spiral_goal_map is None or len(self._spiral_goal_map) != self.n:
			self._spiral_goal_map = self.build_spiral_goal_map()
		return self._spiral_goal_map[r][c]

	def on_picture_toggled(self):
		self.hide_final_overlay()
		self.picture_mode = not self.picture_mode

		if self.picture_mode:
			self.picture_btn.config(bg="#90ee90", fg="#333", activebackground="#7ad87a")
			self.ensure_snake_tiles()
		else:
			self.picture_btn.config(bg="#555", fg="#aaa", activebackground="#666")

		# Refresh display
		for i in range(self.n):
			for j in range(self.n):
				self.update_tile(i, j)

	def ensure_snake_tiles(self):
		"""Load + resize + slice the snake image into N*N PhotoImages keyed by tile number."""
		if self.current_tile_size <= 0:
			return

		try:
			if self._base_image is None:
				self._base_image = Image.open(self.snake_image_path).convert("RGB")
		except Exception as e:
			messagebox.showerror("Image Error", f"Failed to load snake image:\n{e}")
			self.picture_mode = False
			self.picture_btn.config(bg="#555", fg="#aaa", activebackground="#666")
			return

		tile = self.current_tile_size
		board_px = tile * self.n

		# Resize to exact board size (simple; no aspect preservation)
		board_img = self._base_image.resize((board_px, board_px), Image.Resampling.LANCZOS)

		self._tile_photoimages.clear()

		# For each board cell, crop slice, then assign it to the tile number that belongs there in the spiral goal.
		for r in range(self.n):
			for c in range(self.n):
				correct_num = self.correct_tile_number_for_position(r, c)
				if correct_num == 0:
					continue  # blank has no image

				left = c * tile
				upper = r * tile
				right = left + tile
				lower = upper + tile

				crop = board_img.crop((left, upper, right, lower))
				self._tile_photoimages[correct_num] = ImageTk.PhotoImage(crop)

	def capture_board_image(self):
		"""
		Reconstruct current board as a PIL image using the existing tile slices.
		Requires picture_mode and _tile_photoimages to be available.
		"""
		tile = self.current_tile_size
		n = self.n
		board = Image.new("RGB", (tile * n, tile * n), (0, 0, 0))

		# Need PIL crops; easiest: rebuild from base image in current size.
		if self._base_image is None:
			self._base_image = Image.open(self.snake_image_path).convert("RGB")

		board_img = self._base_image.resize((tile * n, tile * n), Image.Resampling.LANCZOS)

		# Paste slices according to CURRENT positions (value tells which slice to use)
		# We can crop slice for where that tile belongs in the SOLVED layout.
		for r in range(n):
			for c in range(n):
				v = self.grid[r][c]
				if v == 0:
					continue

				# Find where tile v belongs in the goal layout, then crop that slice:
				gr, gc = self.find_goal_position_for_tile(v)
				crop = board_img.crop((gc * tile, gr * tile, (gc + 1) * tile, (gr + 1) * tile))
				board.paste(crop, (c * tile, r * tile))

		return board

	def find_goal_position_for_tile(self, tile_value: int) -> tuple[int, int]:
		"""Return (r,c) in the spiral goal where tile_value belongs."""
		if self._spiral_goal_map is None or len(self._spiral_goal_map) != self.n:
			self._spiral_goal_map = self.build_spiral_goal_map()
		for r in range(self.n):
			for c in range(self.n):
				if self._spiral_goal_map[r][c] == tile_value:
					return (r, c)
		raise ValueError(f"Tile {tile_value} not found in goal map")

	def fade_in_solved_picture(self, duration_ms=600, steps=12):
		"""Fade from current board rendering to the complete solved picture."""
		if not self.picture_mode:
			return

		tile = self.current_tile_size
		n = self.n
		w = tile * n
		h = tile * n

		# Base solved image (complete picture)
		if self._base_image is None:
			self._base_image = Image.open(self.snake_image_path).convert("RGB")
		solved = self._base_image.resize((w, h), Image.Resampling.LANCZOS)

		# Current board snapshot (reconstructed)
		try:
			start = self.capture_board_image()
		except Exception:
			# If anything fails, just skip fade
			return

		# Create overlay label once
		if self._fade_overlay is None:
			self._fade_overlay = tk.Label(self.grid_frame, bd=0)
		self._fade_overlay.place(x=0, y=0, width=w, height=h)
		self._fade_overlay.lift()
		self._fade_overlay_visible = False

		delay = max(1, duration_ms // steps)

		def step(i):
			t = i / steps
			frame = Image.blend(start, solved, t)
			self._fade_photo = ImageTk.PhotoImage(frame)
			self._fade_overlay.config(image=self._fade_photo)

			if i < steps:
				aid = self.root.after(delay, lambda: step(i + 1))
				self._fade_after_ids.append(aid)
			else:
				self._fade_overlay_visible = True

		# cancel any previous scheduled fade steps
		for aid in getattr(self, "_fade_after_ids", []):
			try:
				self.root.after_cancel(aid)
			except Exception:
				pass
		self._fade_after_ids = []
		step(0)
	
	def hide_final_overlay(self):
		ov = self._fade_overlay
		if ov is None:
			self._fade_overlay_visible = False
			self._fade_photo = None
			return

		try:
			# If Tk already destroyed it, this will throw.
			ov.place_forget()
			ov.config(image="")
		except tk.TclError:
			# Overlay was destroyed (e.g. by draw_grid); drop the reference.
			self._fade_overlay = None

		self._fade_photo = None
		self._fade_overlay_visible = False

		for aid in getattr(self, "_fade_after_ids", []):
			try:
				self.root.after_cancel(aid)
			except Exception:
				pass
		self._fade_after_ids = []

	def refresh_picture_assets_and_tiles(self):
		"""Rebuild cached spiral mapping + image slices (if enabled) and refresh all tiles."""
		self._spiral_goal_map = None
		self._tile_photoimages.clear()

		self.pick_random_picture_asset()
		if self.picture_mode:
			self.ensure_snake_tiles()

		for i in range(self.n):
			for j in range(self.n):
				self.update_tile(i, j)

	def pick_random_picture_asset(self):
		assets_dir = "assets"
		exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".avif"}

		if not os.path.isdir(assets_dir):
			raise FileNotFoundError(f"Assets directory not found: {assets_dir}")

		files = [
			os.path.join(assets_dir, f)
			for f in os.listdir(assets_dir)
			if os.path.splitext(f.lower())[1] in exts
			and os.path.isfile(os.path.join(assets_dir, f))
		]

		if not files:
			raise FileNotFoundError(f"No images found in {assets_dir} (extensions: {sorted(exts)})")

		return random.choice(files)

	def load_random_picture(self):
		self.snake_image_path = self.pick_random_picture_asset()

		# Clear image caches so ensure_snake_tiles() reloads and reslices
		self._base_image = None
		self._tile_photoimages.clear()

		# If picture mode is on, regenerate slices immediately
		if self.picture_mode:
			self.ensure_snake_tiles()
			self.refresh_picture_assets_and_tiles()

		self.update_status(f"Picture: {os.path.basename(self.snake_image_path)}")

	def on_animation_complete(self):
		self.is_playing = False
		self.generate_btn.config(state=tk.NORMAL)
		self.solve_btn.config(state=tk.NORMAL)
		self.play_btn.config(state=tk.NORMAL)
		self.cancel_btn.config(state=tk.DISABLED)
		self.fade_in_solved_picture(duration_ms=800, steps=20)
		self.update_status("Solution complete!")
	
	def update_status(self, message: str):
		self.status_label.config(text=message)
	
	def on_closing(self):
		if self.solver_process and self.solver_process.poll() is None:
			self.solver_process.kill()
		
		self.root.destroy()

def main():
	root = tk.Tk()
	root.geometry("1200x1200")
	root.resizable(True, True)
	app = NPuzzleGUI(root)
	root.mainloop()

if __name__ == "__main__":
	main()