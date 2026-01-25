#include "n-puzzle.hpp"
#include "Board.hpp"
#include "PuzzleData.hpp"

ui32	manhattanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, ui32 n)
{
	ui32	distance = 0;

	for (ui32 index = 0; index < tiles.size(); index++)
	{
		ui32	tile = tiles[index];

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

ui32	linearConflict(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, ui32 n)
{
	ui32	inversionCount = 0;
	const std::vector<ui32>&	si = solutionIndexes;

	for (ui32 i = 0; i < n; i++)
	{
		for (ui32 j = i + 1; j < n; j++)
		{
			if (tiles[si[i]] != 0 && tiles[si[j]] != 0 && tiles[si[i]] > tiles[si[j]])
			{
				inversionCount++;
			}
		}
	}
	return inversionCount * 2;
}

ui32	hammingDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, ui32 n)
{
	ui32	distance = 0;

	for (ui32 index = 0; index < n; index++)
	{
		ui32	tile = tiles[solutionIndexes[index]];

		if (tile != 0 && tile - 1 != index)
		{
			distance++;
		}		
	}
	return distance;
}

ui32	euclideanDistance(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, ui32 n)
{
	float	distance = 0;

	for (ui32 index = 0; index < tiles.size(); index++)
	{
		ui32	tile = tiles[index];

		if (tile != 0)
		{
			int	targetIndex = solutionIndexes[tile - 1];
			int	currentRow = index / n;
			int	currentCol = index % n;
			int	targetRow = targetIndex / n;
			int	targetCol = targetIndex % n;
			int	dx = currentRow - targetRow;
			int	dy = currentCol - targetCol;

			distance += std::sqrt(dx * dx + dy * dy);
		}
	}
	return static_cast<ui32>(distance);
}

ui32	PuzzleData::calculateHeuristicValue(const Board& board)
{
	int result = 0;
	int	n = PuzzleData::n;
	const std::vector<ui32>&	tiles = board.tiles;

	for (size_t i = 0; i < heuristics.size(); i++)
	{
		result += heuristics[i](tiles, solutionIndexes, n);
	}
	return result;
}