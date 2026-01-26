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

int	manhattanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
int	linearConflict(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
int	hammingDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);
int	euclideanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n);