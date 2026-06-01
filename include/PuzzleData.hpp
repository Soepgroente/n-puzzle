#pragma once

#include "Board.hpp"

#include <unordered_set>
#include <unordered_map>
#include <queue>
#include <chrono>

typedef uint32_t ui32;

struct GoalInfo
{
	std::vector<ui32> goalRow;
	std::vector<ui32> goalCol;
};

class PuzzleData
{
	using HeuristicFunction = int (*)(const std::vector<ui32>&, const std::vector<ui32>&, int);
	using TimePoint = std::chrono::high_resolution_clock::time_point;

	public:

	PuzzleData();
	~PuzzleData() = default;
	PuzzleData(const PuzzleData &other) = delete;
	PuzzleData& operator=(const PuzzleData &other) = delete;

	void	configFromFile(const char* filename);
	void	configFromGUI();
	void	init(const std::vector<ui32>& initialState);

	int		findSensibleMoves(Board& board) noexcept;
	void	setSolution();
	void	printSolution(std::ostream& os)	noexcept;
	void	solve() noexcept;

	static int	n;
	static int	size;

	private:
	
	std::priority_queue<Board, std::vector<Board>, std::greater<Board>>	openBoards;
	std::vector<HeuristicFunction>		heuristics;
	std::unordered_set<Board>			closedBoards;
	std::unordered_map<Board, Board>	cameFrom;

	Board				solution;
	GoalInfo			goalInfo;
	std::vector<ui32>	solutionIndexes;
	std::vector<ui32>	path;

	size_t	time = 0;

	size_t	largestOpenBoardSize = 0;
	size_t	peakMemoryUsage = 0;
	size_t	availableRamSize;

	ui32	calculateHeuristicValue(const Board& board);
	void	parseHeuristics(std::string input);
	void	loopPathBackwards();

	bool	greedySearch = false;

	TimePoint	startTime;
	TimePoint	endTime;
};