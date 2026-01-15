EXEC		:= n-puzzle
CC			:= c++
INCLUDES	:= -I./includes
BASEFLAGS	:= -Wall -Wextra -Werror -std=c++20
DEBUGFLAGS	:= -g -fsanitize=address
OPTIMFLAGS	:= -O3 -flto -march=native -funroll-loops -DNDEBUG -fnomath

SRC_DIR		:= src
OBJ_DIR		:= obj

SRCS	:=	main.cpp \
			Board.cpp \
			BoardSolve.cpp \

OBJS		:=	$(addprefix $(OBJDIR)/,$(notdir $(SRCS:%.cpp=%.o)))

CPPFLAGS	= $(BASEFLAGS) $(OPTIMFLAGS)

all: $(EXEC)

debug: CPPFLAGS = $(BASEFLAGS) $(DEBUGFLAGS)
debug: re

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(EXEC): $(OBJ_DIR) $(OBJS)
	$(CC) $(CPPFLAGS) $(INCLUDES) $^ -o $@

$(OBJ_DIR)/%.o: %.cpp
	$(CC) $(CPPFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(EXEC)

re: fclean all

.PHONY: all clean fclean re debug

