#pragma once

#include <array>
#include <vector>
#include <iostream>

class Board
{
	public:

	Board() = delete;
	~Board() = default;
	Board(const char* filename);
	Board(const Board &other);
	Board& operator=(const Board &other);

	int	operator[](int index) const { return tiles[index]; }

	const std::vector<int>& getTiles() const { return tiles; }
	int getN() const { return n; }
	int getSize() const { return size; }

	static bool	isSolved(const std::vector<int>& tiles) noexcept;
	void		setSolution() noexcept;

	private:
	
	static std::vector<int>	solution;
	std::vector<int>	tiles;
	
	static int	n;
	static int	size;
	int			hole;

	void	calculateMoveOrder(std::array<int, 4>& order) const noexcept;
};

std::ostream& operator<<(std::ostream& os, const Board& board);