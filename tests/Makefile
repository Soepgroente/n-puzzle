NAME		:= tests
CC			:= c++

BASE_CPPFLAGS	:=	-Wall -Wextra -Werror -std=c++20 -fPIC
RELEASE_FLAGS	:=	-DNDEBUG -flto -O3 -march=native -fno-math-errno
DEBUG_FLAGS		:=	-g -fsanitize=address

INCLUDES	:=	-I/opt/homebrew/include \
				-I./ \
				-I../include \

SRCS		:=	Board.cpp \
				heuristics.cpp \
				PuzzleData.cpp \
				PuzzleSolve.cpp \
				parsingTests.cpp \
				solutionTests.cpp \
				testMain.cpp \

OBJDIR		:=	obj
OBJS		:=	$(addprefix $(OBJDIR)/,$(notdir $(SRCS:%.cpp=%.o)))

CPPFLAGS	=	$(BASE_CPPFLAGS) $(RELEASE_FLAGS)

all: $(NAME)

test: $(TEST_EXEC)

runtest: $(TEST_EXEC)
	./$(TEST_EXEC)

debug: CPPFLAGS = $(BASE_CPPFLAGS) $(DEBUG_FLAGS)
debug: all

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(NAME): $(OBJDIR) $(OBJS)
	ar -rcs $(NAME) $(OBJS)

$(OBJDIR)/%.o: %.cpp
	$(CC) $(CPPFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -rf $(OBJDIR)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re