#pragma once

#include "Board.hpp"

#include <unordered_set>
#include <queue>

typedef uint32_t ui32;

class PuzzleData
{
	using HeuristicFunction = ui32 (*)(const std::vector<ui32>&, const std::vector<ui32>&, int);
	using TimePoint = std::chrono::high_resolution_clock::time_point;

	public:

	PuzzleData() = default;
	~PuzzleData() = default;
	PuzzleData(const PuzzleData &other) = delete;
	PuzzleData& operator=(const PuzzleData &other) = delete;

	void	configFromFile(const char* filename);
	void	configFromGUI();
	void	init(const std::vector<ui32>& initialState);

	void	addState(const Board& board);
	int		findSensibleMoves(Board& board) noexcept;
	void	setSolution();
	void	printSolution(std::ostream& os)	const noexcept;
	void	solve() noexcept;

	static int	n;
	static int	size;

	private:
	
	std::priority_queue<Board, std::vector<Board>, std::greater<Board>>	openBoards;
	std::vector<HeuristicFunction>		heuristics;
	std::unordered_set<Board>			closedBoards;
	std::unordered_map<Board, Board>	cameFrom;

	Board				solution;
	std::vector<ui32>	solutionIndexes;
	std::vector<ui32>	path;

	int		previousMove = 0;
	size_t	largestOpenBoardSize = 0;

	ui32	countInversions();
	ui32	calculateHeuristicValue(const Board& board);
	void	parseHeuristics();
	void	loopPathBackwards();

	TimePoint	startTime;
	TimePoint	endTime;
};