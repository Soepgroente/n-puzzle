#include "n-puzzle.hpp"
#include "Board.hpp"
#include "PuzzleData.hpp"

int	manhattanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n)
{
	ui32	distance = 0;
	int size = static_cast<int>(tiles.size());

	for (int index = 0; index < size; index++)
	{
		int	tile = tiles[index];

		if (tile != 0)
		{
			int	targetIndex = solutionIndexes[tile - 1];
			int	currentRow = index / n;
			int	currentCol = index % n;
			int	targetRow = targetIndex / n;
			int	targetCol = targetIndex % n;

			distance += std::abs(currentRow - targetRow) + std::abs(currentCol - targetCol);
		}
	}
	return distance;
}

int	linearConflict(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n)
{
	ui32	inversionCount = 0;
	const std::vector<ui32>&	si = solutionIndexes;

	for (int i = 0; i < n; i++)
	{
		for (int j = i + 1; j < n; j++)
		{
			if (tiles[si[i]] != 0 && tiles[si[j]] != 0 && tiles[si[i]] > tiles[si[j]])
			{
				inversionCount++;
			}
		}
	}
	return inversionCount * 2;
}

int	hammingDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n)
{
	ui32	distance = 0;

	for (int index = 0; index < n; index++)
	{
		int	tile = tiles[solutionIndexes[index]];

		if (tile != 0 && tile - 1 != index)
		{
			distance++;
		}
	}
	return distance;
}

ui32	PuzzleData::calculateHeuristicValue(const Board& board)
{
	int result = 0;
	int	n = PuzzleData::n;
	int size = static_cast<int>(heuristics.size());
	const std::vector<ui32>&	tiles = board.tiles;

	for (int i = 0; i < size; i++)
	{
		result += heuristics[i](tiles, solutionIndexes, n);
	}
	return static_cast<ui32>(result);
}