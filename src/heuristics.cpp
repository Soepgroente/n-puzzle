#include "n-puzzle.hpp"
#include "Board.hpp"
#include "PuzzleData.hpp"

const GoalInfo* info;

int countConflictsInRow(const std::vector<ui32>& tiles, const GoalInfo& goalInfo, ui32 row, ui32 size)
{
    ui32 conflicts = 0;
    
    for (ui32 col1 = 0; col1 < size; col1++)
    {
        ui32 idx1 = row * size + col1;
        ui32 tile1 = tiles[idx1];
        
        if (tile1 == 0) continue;
        if (goalInfo.goalRow[tile1] != row) continue;
        
        ui32 goalCol1 = goalInfo.goalCol[tile1];
        
        for (ui32 col2 = col1 + 1; col2 < size; col2++)
        {
            ui32 idx2 = row * size + col2;
            ui32 tile2 = tiles[idx2];
            
            if (tile2 == 0) continue;
            if (goalInfo.goalRow[tile2] != row) continue;
            
            if (goalCol1 > goalInfo.goalCol[tile2])
            {
                conflicts++;
            }
        }
    }    
    return conflicts;
}

int countConflictsInColumn(const std::vector<ui32>& tiles, const GoalInfo& goalInfo, ui32 col, ui32 size)
{
    ui32 conflicts = 0;
    
    for (ui32 row1 = 0; row1 < size; row1++)
    {
        ui32 idx1 = row1 * size + col;
        ui32 tile1 = tiles[idx1];
        
        if (tile1 == 0) continue;
        if (goalInfo.goalCol[tile1] != col) continue;
        
        ui32 goalRow1 = goalInfo.goalRow[tile1];
        
        for (ui32 row2 = row1 + 1; row2 < size; row2++)
        {
            ui32 idx2 = row2 * size + col;
            ui32 tile2 = tiles[idx2];
            
            if (tile2 == 0) continue;
            if (goalInfo.goalCol[tile2] != col) continue;
            
            if (goalRow1 > goalInfo.goalRow[tile2])
            {
                conflicts++;
            }
        }
    }    
    return conflicts;
}

int	linearConflict(const std::vector<ui32>& tiles, const std::vector<ui32>& solutionIndexes, int n)
{
	(void)solutionIndexes;
	int conflicts = 0;

	for (int row = 0; row < n; row++)
	{
		conflicts += countConflictsInRow(tiles, *info, row, n);
	}
	for (int col = 0; col < n; col++)
	{
		conflicts += countConflictsInColumn(tiles, *info, col, n);
	}
	return conflicts * 2;
}

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

	info = &goalInfo;

	for (int i = 0; i < size; i++)
	{
		result += heuristics[i](tiles, solutionIndexes, n);
	}
	return static_cast<ui32>(result);
}