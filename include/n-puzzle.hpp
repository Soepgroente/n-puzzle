#pragma once

#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "Board.hpp"

#ifdef __linux__
	#define GUI "n_puzzle_gui_linux.py"
#elif __APPLE__
	#define GUI "n_puzzle_gui_mac.py"
#else
	#error "Unsupported platform"
#endif

ui32	manhattanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
ui32	linearConflict(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
ui32	hammingDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
ui32	euclideanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);