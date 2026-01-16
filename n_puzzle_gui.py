import tkinter as tk
from tkinter import ttk, messagebox
import random
import subprocess
import json
import threading
import time
from typing import List, Tuple

class NPuzzleGUI:  
	def __init__(self, root):
		self.root = root
		self.root.title("N-Puzzle Solver")
		
		# Configuration
		self.n = 3  # Default grid size
		self.grid = []  # Current puzzle state
		self.solution_steps = []  # Store solution from executable
		self.empty_pos = (0, 0)  # Position of empty tile (row, col)
		self.is_playing = False  # Flag for animation
		self.tile_buttons = []  # GUI tile buttons
		self.moves_per_second = 2.0  # Animation speed
		
		# Colors
		self.tile_color = "#4CAF50"
		self.empty_color = "#E8D5C4"  # Light wood color for empty space
		self.text_color = "white"
		self.wood_color = "#8B4513"  # Saddle brown for frame
		self.wood_dark = "#654321"  # Dark wood
		
		self.setup_ui()
		self.initialize_grid()
		
		# Bind resize event
		self.root.bind('<Configure>', self.on_window_resize)
		self.last_width = self.root.winfo_width()
		self.last_height = self.root.winfo_height()
		
	def setup_ui(self):
		"""Create the user interface"""
		# Main container
		main_container = tk.Frame(self.root)
		main_container.pack(expand=True, fill=tk.BOTH)
		
		# Control panel - centered at top
		control_frame = tk.Frame(main_container, padx=10, pady=15)
		control_frame.pack(side=tk.TOP)
		
		# First row of controls
		first_row = tk.Frame(control_frame)
		first_row.pack(side=tk.TOP, pady=5)
		
		# N selector
		tk.Label(first_row, text="Grid Size (N):").pack(side=tk.LEFT, padx=5)
		self.n_var = tk.IntVar(value=3)
		n_dropdown = ttk.Combobox(
			first_row, 
			textvariable=self.n_var,
			values=list(range(2, 21)),
			state="readonly",
			width=5
		)
		n_dropdown.pack(side=tk.LEFT, padx=5)
		n_dropdown.bind("<<ComboboxSelected>>", self.on_n_changed)
		
		# Generate button
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
		
		# Solve button
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
		
		# Play solution button
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
		
		# Second row - Speed slider
		second_row = tk.Frame(control_frame)
		second_row.pack(side=tk.TOP, pady=10)
		
		tk.Label(second_row, text="Animation Speed: ").pack(side=tk.LEFT, padx=5)
		
		# Speed slider (0.5 to 10 moves per second)
		self.speed_var = tk.DoubleVar(value=2.0)
		speed_slider = tk.Scale(
			second_row,
			from_=0.5,
			to=10.0,
			resolution=0.5,
			orient=tk.HORIZONTAL,
			variable=self.speed_var,
			length=200,
			command=self.on_speed_changed
		)
		speed_slider.pack(side=tk.LEFT, padx=5)
		
		self.speed_label = tk.Label(second_row, text="2.0 moves/sec", width=15)
		self.speed_label.pack(side=tk.LEFT, padx=5)
		
		# Status label
		status_row = tk.Frame(control_frame)
		status_row.pack(side=tk.TOP, pady=5)
		
		self.status_label = tk.Label(
			status_row,
			text="Ready",
			fg="#666",
			font=("Arial", 10)
		)
		self.status_label.pack()
		
		# Puzzle container - centered and expandable
		puzzle_container = tk.Frame(main_container)
		puzzle_container.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=20, pady=20)
		
		# Outer wood frame (darker, thicker border)
		self.outer_frame = tk.Frame(
			puzzle_container,
			bg=self.wood_dark,
			padx=20,
			pady=20
		)
		self.outer_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
		
		# Inner wood frame (lighter wood color)
		inner_frame = tk.Frame(
			self.outer_frame,
			bg=self.wood_color,
			padx=15,
			pady=15,
			relief=tk.RIDGE,
			borderwidth=5
		)
		inner_frame.pack()
		
		# Grid frame - this will hold the tiles
		self.grid_frame = tk.Frame(
			inner_frame,
			bg=self.wood_color,
			padx=5,
			pady=5
		)
		self.grid_frame.pack()
		
	def on_window_resize(self, event):
		"""Handle window resize events"""
		# Only redraw if the window size actually changed significantly
		# and if the event is for the root window
		if event.widget == self.root:
			current_width = self.root.winfo_width()
			current_height = self.root.winfo_height()
			
			# Check if size changed by more than 10 pixels
			if (abs(current_width - self.last_width) > 10 or 
				abs(current_height - self.last_height) > 10):
				self.last_width = current_width
				self.last_height = current_height
				self.draw_grid()
	
	def on_speed_changed(self, value):
		"""Handle speed slider change"""
		self.moves_per_second = float(value)
		self.speed_label.config(text=f"{self.moves_per_second:.1f} moves/sec")
		
	def calculate_tile_size(self):
		"""Calculate optimal tile size based on window size and N"""
		# Get available space (window size minus controls and padding)
		window_width = self.root.winfo_width()
		window_height = self.root.winfo_height()
		
		# Reserve space for controls (approximately 180 pixels at top)
		# and padding (40 pixels on sides, 40 pixels top/bottom for puzzle area)
		available_width = max(200, window_width - 120)  # 60px padding on each side
		available_height = max(200, window_height - 260)  # 180px controls + 80px padding
		
		# Calculate tile size based on grid size
		# Add extra space for wood frame borders (about 80 pixels total)
		max_tile_width = (available_width - 80) // self.n
		max_tile_height = (available_height - 80) // self.n
		
		# Use the smaller dimension to ensure square tiles that fit
		tile_size = min(max_tile_width, max_tile_height)
		
		# Set minimum and maximum tile sizes
		tile_size = max(20, min(tile_size, 150))
		
		# Calculate font size based on tile size
		font_size = max(8, min(32, tile_size // 3))
		
		return tile_size, font_size
		
	def initialize_grid(self):
		"""Initialize the puzzle grid to solved state"""
		self.n = self.n_var.get()
		size = self.n * self.n
		
		# Create grid in solved state:  1, 2, 3, ..., n*n-1, 0
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
		"""Draw the puzzle grid"""
		# Clear existing buttons
		for widget in self.grid_frame.winfo_children():
			widget.destroy()
		
		self.tile_buttons = []
		
		# Calculate tile size dynamically
		tile_size, font_size = self.calculate_tile_size()
		
		for i in range(self.n):
			row_buttons = []
			for j in range(self.n):
				value = self.grid[i][j]
				
				# Create frame for each tile to control exact sizing
				tile_frame = tk.Frame(
					self.grid_frame,
					width=tile_size,
					height=tile_size,
					bg=self.wood_color
				)
				tile_frame.grid(row=i, column=j, padx=0, pady=0, sticky="nsew")
				tile_frame.grid_propagate(False)
				
				if value == 0:
					# Empty tile
					btn = tk.Label(
						tile_frame,
						text="",
						bg=self.empty_color,
						relief=tk.SUNKEN,
						borderwidth=2,
						font=("Arial", font_size, "bold")
					)
				else:
					# Numbered tile
					btn = tk.Label(
						tile_frame,
						text=str(value),
						bg=self.tile_color,
						fg=self.text_color,
						relief=tk.RAISED,
						borderwidth=2,
						font=("Arial", font_size, "bold")
					)
				
				btn.place(relx=0, rely=0, relwidth=1, relheight=1)
				row_buttons.append(btn)
			
			self.tile_buttons.append(row_buttons)
	
	def on_n_changed(self, event):
		"""Handle N dropdown change"""
		self.solution_steps = []
		self.play_btn.config(state=tk.DISABLED)
		self.initialize_grid()
		self.update_status("Grid size changed. Click Generate to create a puzzle.")
	
	def generate_puzzle(self):
		"""Generate a random puzzle configuration"""
		self.n = self.n_var.get()
		size = self.n * self.n
		
		# Create a list of numbers from 0 to n*n-1
		numbers = list(range(size))
		
		# Shuffle until we get a solvable configuration
		# For simplicity, we'll just shuffle and check basic solvability
		random.shuffle(numbers)
		
		# Convert to 2D grid
		self.grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
		idx = 0
		for i in range(self.n):
			for j in range(self.n):
				self.grid[i][j] = numbers[idx]
				if numbers[idx] == 0:
					self.empty_pos = (i, j)
				idx += 1
		
		self.solution_steps = []
		self.play_btn.config(state=tk.DISABLED)
		self.draw_grid()
		self.update_status(f"Generated random {self.n}x{self.n} puzzle")
	
	def get_grid_as_list(self) -> List[int]:
		"""Convert 2D grid to 1D list"""
		result = []
		for row in self.grid:
			result.extend(row)
		return result
	
	def solve_puzzle(self):
		"""Launch the n-puzzle executable and get solution"""
		self.update_status("Solving puzzle...")
		self.solve_btn.config(state=tk.DISABLED)
		
		# Run in a separate thread to avoid blocking UI
		thread = threading.Thread(target=self.run_solver)
		thread.daemon = True
		thread.start()
	
	def run_solver(self):
		"""Run the solver executable in a separate thread"""
		try: 
			# Prepare input data
			grid_data = self.get_grid_as_list()
			input_data = {
				"n": self.n,
				"grid": grid_data
			}
			
			# Call the executable (adjust path as needed)
			# The executable should accept JSON input and output JSON with solution
			process = subprocess.Popen(
				["./n-puzzle"],  # Change to your executable name/path
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True
			)
			
			# Send input and get output
			stdout, stderr = process.communicate(input=json.dumps(input_data))
			
			if process.returncode == 0:
				# Parse solution (expecting JSON array of moves)
				# Moves:  1=up, 2=down, 3=left, 4=right
				result = json.loads(stdout)
				self.solution_steps = result.get("moves", [])
				
				self.root.after(0, self.on_solve_success)
			else:
				error_msg = stderr if stderr else "Unknown error"
				self.root.after(0, lambda:  self.on_solve_error(error_msg))
				
		except FileNotFoundError:
			self.root.after(0, lambda: self.on_solve_error(
				"Executable 'n-puzzle' not found. Please ensure it's in the current directory."
			))
		except json.JSONDecodeError as e:
			self.root.after(0, lambda: self.on_solve_error(f"Invalid JSON response: {e}"))
		except Exception as e:
			self.root.after(0, lambda: self.on_solve_error(str(e)))
	
	def on_solve_success(self):
		"""Called when solver completes successfully"""
		self.solve_btn.config(state=tk.NORMAL)
		self.play_btn.config(state=tk.NORMAL)
		self.update_status(f"Solution found! {len(self.solution_steps)} moves")
	
	def on_solve_error(self, error_msg):
		"""Called when solver encounters an error"""
		self.solve_btn.config(state=tk.NORMAL)
		self.update_status("Solve failed")
		messagebox.showerror("Solver Error", error_msg)
	
	def play_solution(self):
		"""Animate the solution steps"""
		if not self.solution_steps:
			messagebox.showinfo("No Solution", "No solution available to play")
			return
		
		if self.is_playing:
			return
		
		# Reset to generated state - would need to store original state
		# For now, just disable buttons during playback
		self.generate_btn.config(state=tk.DISABLED)
		self.solve_btn.config(state=tk.DISABLED)
		self.play_btn.config(state=tk.DISABLED)
		
		self.is_playing = True
		self.update_status("Playing solution...")
		
		# Run animation in separate thread
		thread = threading.Thread(target=self.animate_solution)
		thread.daemon = True
		thread.start()
	
	def animate_solution(self):
		"""Animate each move in the solution"""
		delay = 1.0 / self.moves_per_second
		
		for step_num, move in enumerate(self.solution_steps, 1):
			time.sleep(delay)
			self.root.after(0, lambda m=move, s=step_num: self.apply_move(m, s))
		
		time.sleep(delay)
		self.root.after(0, self.on_animation_complete)
	
	def apply_move(self, move:  int, step_num: int):
		"""Apply a single move to the grid
		Moves:  1=up, 2=down, 3=left, 4=right
		(These moves represent moving the empty tile in that direction)
		"""
		row, col = self.empty_pos
		new_row, new_col = row, col
		
		if move == 1:  # Move empty tile up
			new_row = row - 1
		elif move == 2:  # Move empty tile down
			new_row = row + 1
		elif move == 3:  # Move empty tile left
			new_col = col - 1
		elif move == 4:  # Move empty tile right
			new_col = col + 1
		else:
			return
		
		# Check bounds
		if 0 <= new_row < self.n and 0 <= new_col < self.n:
			# Swap tiles
			self.grid[row][col], self.grid[new_row][new_col] = \
				self.grid[new_row][new_col], self.grid[row][col]
			self.empty_pos = (new_row, new_col)
			
			self.draw_grid()
			self.update_status(f"Playing solution...Step {step_num}/{len(self.solution_steps)}")
	
	def on_animation_complete(self):
		"""Called when animation finishes"""
		self.is_playing = False
		self.generate_btn.config(state=tk.NORMAL)
		self.solve_btn.config(state=tk.NORMAL)
		self.play_btn.config(state=tk.NORMAL)
		self.update_status("Solution complete!")
	
	def update_status(self, message: str):
		"""Update the status label"""
		self.status_label.config(text=message)

def main():
	root = tk.Tk()
	root.geometry("700x750")
	root.resizable(True, True)
	app = NPuzzleGUI(root)
	root.mainloop()

if __name__ == "__main__":
	main()