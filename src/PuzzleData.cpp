#include "PuzzleData.hpp"
#include "n-puzzle.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>
#include <cmath>
#ifdef __linux__
	#include <sys/sysinfo.h>
#elif __APPLE__
	#include <sys/types.h>
	#include <sys/sysctl.h>
#endif

int PuzzleData::n = 0;
int PuzzleData::size = 0;

PuzzleData::PuzzleData()
{
	#ifdef __linux__
		struct sysinfo info;

		sysinfo(&info);
		availableRamSize = info.totalram / sizeof(Board);
	#elif __APPLE__
		int mib[2] = {CTL_HW, HW_MEMSIZE};
		size_t memsize;
		size_t len = sizeof(memsize);
		sysctl(mib, 2, &memsize, &len, NULL, 0);
		availableRamSize = memsize / (sizeof(Board) + sizeof(void*) * 2);
	#else
		availableRamSize = 8 * 1024 * 1024 * 1024 / (sizeof(Board) + sizeof(void*) * 2); // Default to 8GB RAM
	#endif
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

static ui32	countInversions(const std::vector<ui32>& tiles, const std::vector<ui32>& order)
{
	std::vector<ui32> seq;
	seq.reserve(tiles.size());

	for (ui32 index : order)
	{
		ui32 v = tiles[index];
		if (v != 0)
		{
			seq.push_back(v);
		}
	}

	ui32 inversions = 0;
	for (size_t i = 0; i < seq.size(); i++)
	{
		for (size_t j = i + 1; j < seq.size(); j++)
		{
			if (seq[i] > seq[j])
			{
				inversions++;
			}
		}
	}
	return inversions;
}

static ui32	blankRowFromBottom(ui32 blankIndex, ui32 n)
{
	ui32 rowFromTop = blankIndex / n;

	return n - rowFromTop;
}

static bool	isSolvable(const Board& start, const Board& goal, const std::vector<ui32>& readingOrder)
{
	const ui32 n = static_cast<ui32>(PuzzleData::n);

	ui32 startInv = countInversions(start.tiles, readingOrder);
	ui32 goalInv  = countInversions(goal.tiles, readingOrder);

	/*	even gridsize	*/
	if ((n % 2) == 1)
	{
		return (startInv % 2) == (goalInv % 2);
	}

	/*	odd gridsize	*/
	ui32 startBlank = blankRowFromBottom(start.emptyTile, n);
	ui32 goalBlank  = blankRowFromBottom(goal.emptyTile, n);

	return ((startInv + startBlank) % 2) == ((goalInv + goalBlank) % 2);
}

void	PuzzleData::init(const std::vector<ui32>& initialState)
{
	Board	initialBoard(initialState);

	checkInitialConfiguration(initialBoard);
	setSolution();
	if (isSolvable(initialBoard, solution, solutionIndexes) == false)
	{
		throw std::invalid_argument("Puzzle is not solvable");
	}
	addState(initialBoard);

	const ui32 N = static_cast<ui32>(PuzzleData::n);
	const ui32 size = static_cast<ui32>(solutionIndexes.size());

	goalInfo.goalRow.resize(size);
	goalInfo.goalCol.resize(size);
	for (ui32 tile = 1; tile < size; tile++)
	{
		ui32 goalIdx = solutionIndexes[tile - 1];

		goalInfo.goalRow[tile] = goalIdx / N;
		goalInfo.goalCol[tile] = goalIdx % N;
	}
	const ui32 blankGoalIdx = solutionIndexes.back();

	goalInfo.goalRow[0] = blankGoalIdx / N;
	goalInfo.goalCol[0] = blankGoalIdx % N;
}

void	PuzzleData::parseHeuristics()
{
	std::string	input;
	std::getline(std::cin, input);

	if (input == "Greedy search enabled")
	{
		greedySearch = true;
		std::getline(std::cin, input);
	}
	if (input.empty() == true || input == "none" || input == "Dijkstra (no heuristic)")
	{
		return ;
	}
	else if (input == "Manhattan distance")
	{
		heuristics.push_back(&manhattanDistance);
	}
	else if (input == "Linear conflict")
	{
		heuristics.push_back(&linearConflict);
	}
	else if (input == "Hamming distance")
	{
		heuristics.push_back(&hammingDistance);
	}
	else if (input == "Manhattan + LC")
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