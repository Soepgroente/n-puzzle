#include "PuzzleData.hpp"
#include "n-puzzle.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

ui32 PuzzleData::n = 0;
ui32 PuzzleData::size = 0;

static bool	isEven(ui32 number)
{
	return (number % 2) == 0;
}

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
	ui32 inversions = countInversions();

	if (isEven(n) == false && isEven(inversions) == false)
	{
		throw std::invalid_argument("Initial configuration is not solvable: odd number of inversions in odd-sized puzzle");
	}
	if (isEven(n) == true && isEven(initialBoard.emptyTile / n + 1) == isEven(inversions))
	{
		throw std::invalid_argument("Initial configuration is not solvable: parity condition failed for even-sized puzzle");
	}
}

void	PuzzleData::parseHeuristics()
{
	std::string	input;
	std::ofstream file("heuristics_log.txt");
	std::getline(std::cin, input);

	file << "Selected heuristic: " << input << std::endl;
	if (input.empty() == true)
	{
		throw std::invalid_argument("No heuristics specified");
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
	file.close();
}

void	PuzzleData::configFromFile(const char* filename)
{
	parseHeuristics();
	std::ifstream file(filename);

	if (file.is_open() == false)
	{
		throw std::invalid_argument("Could not open file: " + std::string(filename));
	}
	std::string line;
	std::string	lineWithoutComments;
	std::vector<ui32>	tiles;

	while (file.eof() == false)
	{
		std::getline(file, line, '\n');
		if (line.empty())
		{
			continue;
		}
		ui32 rowCount = 0;
		std::string tile;
		std::istringstream stream(line);

		std::getline(stream, lineWithoutComments, '#');
		stream.str(lineWithoutComments);

		while (stream.eof() == false)
		{
			stream >> tile;
			if (tile.empty())
			{
				continue;
			}
			while (tile[0] == ' ' || tile[0] == '\t')
			{
				tile.erase(0, 1);
			}
			try
			{
				tiles.push_back(std::stoi(tile));
			}
			catch (const std::exception&)
			{
				throw std::invalid_argument("Non-integer value in file: " + std::string(filename));
			}
			rowCount++;
		}
		if (PuzzleData::n == 0)
		{
			PuzzleData::n = rowCount;
		}
		else if (PuzzleData::n != rowCount)
		{
			throw std::invalid_argument("Inconsistent row lengths in file: " + std::string(filename));
		}
	}
	init(tiles);
}

void	PuzzleData::configFromGUI()
{
	parseHeuristics();
	std::string	line;
	std::vector<ui32>	startingConfiguration;
	
	while (std::getline(std::cin,line).fail() == false)
	{
		std::stringstream	ss(line);

		int	value;
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