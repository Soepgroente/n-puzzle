#include "n-puzzle.hpp"
#include "Board.hpp"
#include "PuzzleData.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char** argv)
{
	std::vector<ui32>	startingConfiguration;
	PuzzleData			puzzleData;

	if (argc > 2)
	{
		for (int i = 0; argv[i] != nullptr; i++)
		{
			std::cerr << argv[i] << " ";
		}
		std::cerr << "\nUse the GUI or use: " << argv[0] << " [puzzle_file, (optional)heuristic, (optional)greedy search]" << std::endl;
		std::cerr << "Available heuristics:\nManhattan distance\nLinear conflict\nHamming distance\nManhattan + LC\nDijkstra (default)" << std::endl;
		return 1;
	}
	try
	{
		if (argc == 2)
		{
			puzzleData.configFromFile(argv[1]);
		}
		else
		{
			puzzleData.configFromGUI();
		}
	}
	catch (std::exception& e)
	{
		std::cerr << e.what() << std::endl;
		return 2;
	}
	puzzleData.solve();
	puzzleData.printSolution(std::cout);
	return 0;
}
