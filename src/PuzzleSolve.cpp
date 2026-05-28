#include "PuzzleData.hpp"

#include <algorithm>
#include <iostream>
#include <iomanip>

enum Direction
{
	NONE = 0,
	UP = 1,
	DOWN = 2,
	LEFT = 3,
	RIGHT = 4
};

int	PuzzleData::findSensibleMoves(Board& board) noexcept
{
	int	legalmoves = 0;

	if (board.emptyTile - n >= 0)
	{
		board.up();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << UP);
		}
		board.down();
	}
	if (board.emptyTile + n < size)
	{
		board.down();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << DOWN);
		}
		board.up();
	}
	if (board.emptyTile % n != 0)
	{
		board.left();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << LEFT);
		}
		board.right();
	}
	if (board.emptyTile % n != n - 1)
	{
		board.right();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << RIGHT);
		}
		board.left();
	}
	return legalmoves;
}

void	PuzzleData::loopPathBackwards()
{
	Board	currentBoard = solution;

	while (cameFrom.find(currentBoard) != cameFrom.end())
	{
		Board	parentBoard = cameFrom[currentBoard];
		Direction	move = NONE;

		if (currentBoard.emptyTile == parentBoard.emptyTile - static_cast<int>(n))
		{
			move = UP;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile + static_cast<int>(n))
		{
			move = DOWN;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile - 1)
		{
			move = LEFT;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile + 1)
		{
			move = RIGHT;
		}
		path.push_back(move);
		currentBoard = parentBoard;
	}
	std::reverse(path.begin(), path.end());
	endTime = std::chrono::high_resolution_clock::now();
}

void	PuzzleData::solve() noexcept
{
	int	moves;
	size_t	memoryFootPrint = sizeof(Board) + sizeof(void*) * 2;

	startTime = std::chrono::high_resolution_clock::now();
	while (openBoards.empty() == false)
	{
		time++;
		peakMemoryUsage = std::max(peakMemoryUsage, closedBoards.size() * memoryFootPrint + openBoards.size() * memoryFootPrint);
		if (peakMemoryUsage >= availableRamSize)
		{
			endTime = std::chrono::high_resolution_clock::now();
			std::cout << "Memory limit reached, aborting search at " << openBoards.size() + closedBoards.size() << " boards." << std::endl;
			break;
		}
		Board currentBoard = openBoards.top();

		openBoards.pop();
		if (currentBoard == solution)
		{
			openBoards.push(currentBoard);
			loopPathBackwards();
			break;
		}
		moves = findSensibleMoves(currentBoard);
		if (moves == 0)
		{
			closedBoards.insert(currentBoard);
			continue;
		}
		for (int direction = UP; direction <= RIGHT; direction++)
		{
			if ((moves & (1 << direction)) == 0)
			{
				continue;
			}
			Board newBoard = currentBoard;

			switch (direction)
			{
				case UP: newBoard.up();  break;
				case DOWN: newBoard.down(); break;
				case LEFT: newBoard.left(); break;
				case RIGHT: newBoard.right(); break;
				default: break;
			}
			newBoard.distanceTraveled++;
			newBoard.heuristicValue = calculateHeuristicValue(newBoard);
			if (greedySearch == true)
			{
				newBoard.totalScore = newBoard.heuristicValue;
			}
			else
			{
				newBoard.totalScore = newBoard.distanceTraveled + newBoard.heuristicValue;
			}
			cameFrom[newBoard] = currentBoard;
			openBoards.push(newBoard);
			largestOpenBoardSize = std::max(largestOpenBoardSize, openBoards.size() + closedBoards.size());
		}
		closedBoards.insert(currentBoard);
	}
}

void	PuzzleData::printSolution(std::ostream& os)	noexcept
{
	size_t	size = path.size();
	size_t	boardStates = closedBoards.size();
	
	endTime = std::chrono::high_resolution_clock::now();
	if (openBoards.empty() == true)
	{
		std::cout << "No solution found!" << std::endl;
		return ;
	}
	if (size == 0)
	{
		if (peakMemoryUsage < 1000)
		{
			os << "Puzzle was already solved!" << std::endl;
		}
		return ;
	}
	os << "{\"moves\": [";
	for (size_t i = 0; i < size - 1; i++)
	{
		os << path[i] << ", ";
	}
	if (size > 0)
	{
		os << path[size - 1];
	}
	os << "],\n";
	os << "\"time_ms\": " << std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count() << ",\n";
	os << "\"total_searched\": " << time << ",\n";
	os << "\"peak_memory_states\": " << boardStates << ",\n";
	os << "\"peak_memory_bytes\": " << boardStates * sizeof(Board) << "\n}" << std::endl;
}