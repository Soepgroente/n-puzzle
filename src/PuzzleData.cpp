#include "PuzzleData.hpp"
#include "n-puzzle.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

int PuzzleData::n = 0;
int PuzzleData::size = 0;

// static bool	isEven(ui32 number)
// {
// 	return (number % 2) == 0;
// }

static void	checkInitialConfiguration(Board& board)
{
	size_t	size = board.tiles.size();
	std::vector<bool>	seen(size, false);

	PuzzleData::size = static_cast<ui32>(size);
	if (PuzzleData::n == 0)
	{
		PuzzleData::n = static_cast<ui32>(std::sqrt(size));
	}
	if (PuzzleData::n * PuzzleData::n != PuzzleData::size)
	{
		std::cerr << "Size: " << PuzzleData::size << ", n: " << PuzzleData::n << std::endl;
		throw std::invalid_argument("Initial configuration size is not a perfect square");
	}
	for (size_t i = 0; i < size; i++)
	{
		int tile = board.tiles[i];
		if (tile < 0 || tile >= static_cast<int>(size))
		{
			throw std::invalid_argument("Tile value out of range in initial configuration");
		}
		if (seen[tile] == true)
		{
			throw std::invalid_argument("Duplicate tile value in initial configuration");
		}
		seen[tile] = true;
		if (tile == 0)
		{
			board.emptyTile = i;
		}
	}
}

static std::vector<ui32>	getReadingOrder()
{
	std::vector<ui32>	readingOrder;
	int n = PuzzleData::n;
	int	top = 0, bottom = n - 1;
	int	left = 0, right = n - 1;

	readingOrder.reserve(PuzzleData::size);

	while (top <= bottom && left <= right)
	{
		for (int col = left; col <= right; col++)
		{
			readingOrder.push_back(top * n + col);
		}
		top++;
		for (int row = top; row <= bottom; row++)
		{
			readingOrder.push_back(row * n + right);
		}
		right--;
		if (top <= bottom)
		{
			for (int col = right; col >= left; col--)
			{
				readingOrder.push_back(bottom * n + col);
			}
			bottom--;
		}
		if (left <= right)
		{
			for (int row = bottom; row >= top; row--)
			{
				readingOrder.push_back(row * n + left);
			}
			left++;
		}
	}
	return readingOrder;
}

ui32	PuzzleData::countInversions()
{
	const Board& initialBoard = openBoards.top();
	ui32	inversionCount = 0;
	const std::vector<ui32>&	si = solutionIndexes;

	for (size_t i = 0; i < initialBoard.tiles.size(); i++)
	{
		for (size_t j = i + 1; j < initialBoard.tiles.size(); j++)
		{
			if (initialBoard.tiles[si[i]] != 0 && initialBoard.tiles[si[j]] != 0 &&
				initialBoard.tiles[si[i]] > initialBoard.tiles[si[j]])
			{
				inversionCount++;
			}
		}
	}
	return inversionCount;
}

void	PuzzleData::setSolution()
{
	solutionIndexes = getReadingOrder();
	std::vector<ui32> sol(size, 0);
	ui32	num = 1;
	
	for (size_t i = 0; i < solutionIndexes.size(); i++, num++)
	{
		sol[solutionIndexes[i]] = num;
	}
	sol[solutionIndexes.back()] = 0;
	solution = Board(sol);
}

void	PuzzleData::init(const std::vector<ui32>& initialState)
{
	Board	initialBoard(initialState);

	checkInitialConfiguration(initialBoard);
	addState(initialBoard);
	setSolution();
	// ui32 inversions = countInversions();

	// if (isEven(n) == false && isEven(inversions) == false)
	// {
	// 	throw std::invalid_argument("Initial configuration is not solvable: odd number of inversions in odd-sized puzzle");
	// }
	// if (isEven(n) == true && isEven(initialBoard.emptyTile / n + 1) == isEven(inversions))
	// {
	// 	throw std::invalid_argument("Initial configuration is not solvable: parity condition failed for even-sized puzzle");
	// }
}

void	PuzzleData::parseHeuristics()
{
	std::string	input;
	std::getline(std::cin, input);

	if (input.empty() == true || input == "none")
	{
		return ;
	}
	else if (input == "manhattan distance")
	{
		heuristics.push_back(&manhattanDistance);
	}
	else if (input == "linear conflict")
	{
		heuristics.push_back(&linearConflict);
	}
	else if (input == "hamming distance")
	{
		heuristics.push_back(&hammingDistance);
	}
	else if (input == "euclidean distance")
	{
		heuristics.push_back(&euclideanDistance);
	}
	else if (input == "manhattan + LC")
	{
		heuristics.push_back(&manhattanDistance);
		heuristics.push_back(&linearConflict);
	}
	else
	{
		throw std::invalid_argument("Unknown heuristic: " + input);
	}
}

void	PuzzleData::configFromFile(const char* filename)
{
	parseHeuristics();
	std::ifstream file(std::string("puzzles/") + filename);

	if (file.is_open() == false)
	{
		throw std::invalid_argument("Could not open file: " + std::string(filename));
	}
	std::vector<ui32>	startingConfiguration;
	std::string	line;
	int		rowCount;
	ui32	tile;

	while (file.eof() == false)
	{
		std::getline(file, line, '\n');
		size_t	poundSign = line.find('#');

		if (poundSign != std::string::npos)
		{
			line = line.substr(0, poundSign);
		}
		std::istringstream stream(line);

		rowCount = 0;
		while ((stream >> tile).fail() == false)
		{
			startingConfiguration.push_back(tile);
			rowCount++;
		}
		if (rowCount > 0)
		{
			if (PuzzleData::n == 0)
			{
				PuzzleData::n = rowCount;
			}
			else if (PuzzleData::n != rowCount)
			{
				throw std::invalid_argument("Inconsistent row lengths in file: " + std::string(filename));
			}
		}
	}
	init(startingConfiguration);
}

void	PuzzleData::configFromGUI()
{
	parseHeuristics();
	std::string	line;
	std::vector<ui32>	startingConfiguration;
	ui32	value;
	
	while (std::getline(std::cin, line).fail() == false)
	{
		std::stringstream	ss(line);

		while ((ss >> value).fail() == false)
		{
			startingConfiguration.push_back(value);
		}
	}
	init(startingConfiguration);
}

void	PuzzleData::addState(const Board& board)
{
	openBoards.push(board);
}