from typing import Dict, List, Tuple

import AbaloneGraphics
import variables


class Abalone:
    ARRANGEMENT = [5, 6, 7, 8, 9, 8, 7, 6, 5]  # const
    DIRECTIONS = ['right', 'left', 'top right', 'top left', 'bottom right', 'bottom left']

    def __init__(self) -> None:
        # Create the board:
        rows = 9
        curr = 5
        # Initialize every cell to its correct value
        self.board: List[Cell] = []
        self.pushed_out: Dict[str, int] = {'black': 0, 'white': 0}
        adder = 0
        index = 0
        row_start = 0
        row_end = row_start + curr - 1
        for i in range(rows):
            for j in range(curr):
                dist = abs(rows // 2 - i)
                if min(j, curr - j - 1) < adder:
                    dist = rows // 2 - min(j, curr - j - 1)
                cell = Cell('blank', index, i, row_start, row_end, dist)
                index += 1
                self.board.append(cell)
            curr += 1 if rows // 2 - i > 0 else -1
            adder += 1 if rows // 2 - i > 0 else -1
            row_start = row_end + 1
            row_end = row_start + curr - 1
        # Initialize board configuration
        if variables.regular_layout:
            for i in self.board[:11] + self.board[13:16]:
                i.value = 'white'
            for i in self.board[50:] + self.board[45:48]:
                i.value = 'black'
        else:  # Daisy format
            for i in (self.board[5:7] + self.board[11:14] + self.board[19:21] + self.board[40:42]
                      + self.board[47:50] + self.board[54:56]):
                i.value = 'black'
            for i in (self.board[9:11] + self.board[15:18] + self.board[23:25] + self.board[36:38]
                      + self.board[43:46] + self.board[50:52]):
                i.value = 'white'

        self._all_lines: List[List[int]] = []
        for i in [0, 5, 11, 18, 26, 35, 43, 50, 56]:
            self._all_lines.append(self.get_line(i, 'right'))
        for i in [26, 35, 43, 50, 56, 57, 58, 59, 60]:
            self._all_lines.append(self.get_line(i, 'top right'))
        for i in [56, 57, 58, 59, 60, 55, 49, 42, 34]:
            self._all_lines.append(self.get_line(i, 'top left'))

    def get_line(self, index: int, direction: str) -> List[int]:
        """ Return a list of indexes on one line, that a move can be played on """

        # Possible directions: [top / bottom] + left / right

        def diag(op: int, offset: int, condition: int, stop: int = -1) -> List[int]:
            """ Helper function to avoid code duplication, nested for incapsulation's sake """
            # stop - stop when reached a row whose index is "stop" (get rows [index, stop))
            # condition - after the addition how far above should the next row be
            # offset - amount to add to the index each time
            # op - add or subtract - either 1 or -1
            res = [index]
            next_idx = index + op * (self.board[index].row_size) + offset
            while (0 <= next_idx <= 60 and
                   self.board[next_idx].row_index + condition == self.board[res[-1]].row_index and
                   self.board[next_idx].row_index != stop):
                res.append(next_idx)
                next_idx = next_idx + op * (self.board[next_idx].row_size) + offset
            return res

        cell = self.board[index]
        if direction == "right":
            return [i for i in range(index, cell.row_end + 1)]

        if direction == "left":
            return [i for i in range(index, cell.row_start - 1, -1)]

        if direction == "top right":
            if cell.row_index <= 4:
                return diag(-1, 1, 1)
            res = diag(-1, 0, 1, 3)
            index = res[-1]
            res.pop(-1)
            res += diag(-1, 1, 1)
            return res

        if direction == "top left":
            if cell.row_index <= 4:
                return diag(-1, 0, 1)
            res = diag(-1, -1, 1, 3)
            index = res[-1]
            res.pop(-1)
            res += diag(-1, 0, 1)
            return res

        if direction == "bottom right":
            if cell.row_index > 4:
                return diag(1, 0, -1)
            res = diag(1, 1, -1, 5)
            index = res[-1]
            res.pop(-1)
            res += diag(1, 0, -1)
            return res

        if direction == "bottom left":
            if cell.row_index > 4:
                return diag(1, -1, -1)
            res = diag(1, 0, -1, 5)
            index = res[-1]
            res.pop(-1)
            res += diag(1, -1, -1)
            return res

        return []  # Fallback for unexpected direction

    def make_move(self, index: int, direction: str) -> None:
        """ Tries to make a move (single ball), if not possible raises an InvalidMove exception """
        line = self.get_line(index, direction)
        pusher_ball = self.board[line[0]]  # The ball chosen to try and move
        if pusher_ball.value == 'blank':
            raise InvalidMove("An empty cell was chosen")
        if len(line) == 1:
            raise InvalidMove("You cannot eliminate yourself!")

        pusher_balls = 1  # The amount we try to push at once
        i = 0
        for i in range(1, len(line)):  # Count that amount
            if self.board[line[i]].value == pusher_ball.value:
                pusher_balls += 1
                if pusher_balls > 3:
                    raise InvalidMove("Cannot push more than 3 balls")
            else:
                break
        else:
            raise InvalidMove("You cannot eliminate yourself!")

        # Got here if try to push < 4 balls, and we found potential space to push them to
        if self.board[line[i]].value == 'blank':  # i is the next item in the list
            self.board[line[i]].value = self.board[line[0]].value  # Blank spot fills in with the pusher ball
            self.board[line[0]].value = 'blank'  # The pushing ball turns to blank
            return  # Push successful, simple move done

        # Trying to push an enemy ball if got here
        pushed_ball = self.board[line[i]]
        pushed_balls = 0
        j = 0
        for j in range(i, len(line)):  # Count amount of enemy balls trying to push
            if self.board[line[j]].value == pushed_ball.value:
                pushed_balls += 1
                if pushed_balls >= pusher_balls:
                    raise InvalidMove("Cannot push over or equal amount of enemy balls")
            else:
                break
        else:
            self.pushed_out[self.board[line[pusher_balls]].value] += 1
            self.board[line[pusher_balls]].value = self.board[line[0]].value  # pushed_ball = pusher_ball
            self.board[line[0]].value = 'blank'  # The pushing ball turns to blank
            return  # Push successful, pushed enemy ball out of the board!

        # Got here if hit a blank spot and therefore can move, or there is a pusher ball type ball in the way
        if self.board[line[j]].value == pusher_ball.value:
            raise InvalidMove("Cannot push your own balls through enemy ones!")

        self.board[line[j]].value = pushed_ball.value  # Blank spot became occupied by the enemy ball
        self.board[line[pusher_balls]].value = self.board[line[0]].value  # pushed_ball = pusher_ball
        self.board[line[0]].value = 'blank'  # The pushing ball turns to blank
        return  # Push successful, pushed enemy balls

    def move(self, indices: List[int], direction: str) -> None:
        """ Make a diagonal move with 2/3 balls selected, if impossible raise InvalidMove """
        if len(indices) < 0:
            raise InvalidMove("No target was selected!")
        if len(indices) > 3:
            raise InvalidMove("Cannot push more than 3 balls")
        if len(indices) == 1:
            self.make_move(indices[0], direction)
            return

        # Check if indices are in a straight line
        found_direction = None
        for dirct in self.DIRECTIONS:
            line = self.get_line(indices[0], dirct)
            if line[:len(indices)] == indices:
                found_direction = dirct
                break

        if not found_direction:
            raise InvalidMove("Chosen balls are not in a straight line!")

        # Verify all balls are of same type
        ball_type = self.board[indices[0]].value
        for i in indices:
            if self.board[i].value == 'blank' or self.board[i].value != ball_type:
                raise InvalidMove("You have not chosen the same kind of balls (or none at all)")

        # Try to move balls
        target_indices = []
        for i in indices:
            line = self.get_line(i, direction)
            if not (len(line) > 1 and self.board[line[1]].value == 'blank'):
                break
            target_indices.append(line[1])  # If everything is legal, we will move the selected balls to these locations
        else:  # Never broke the loop - all indices legal
            for i in range(len(indices)):
                self.board[target_indices[i]].value = self.board[indices[i]].value
                self.board[indices[i]].value = 'blank'
            return

        raise InvalidMove("Path blocked")

    def calc_distance(self, value: str) -> int:
        """Used in the calculation of the value of a given board in self.evaluate_max/min"""
        total = 0
        for i in self.board:
            if i.value == value:
                total += 4 - i.distance
        return total

    def get_adjacent(self, index: int) -> List['Cell']:
        """Returns a list of all adjacent friendly balls"""
        value = self.board[index].value
        total = []
        for direction in self.DIRECTIONS:
            temp = self.get_line(index, direction)
            if len(temp) > 1 and self.board[temp[1]].value == value:
                total.append(self.board[temp[1]])
        return total

    def calc_chunks(self, value: str) -> int:
        """Returns the total value of all chunks, used in the calculation of the value of a given board in self.evaluate_max/min"""
        res = 0
        for i in range(len(self.board)):
            if self.board[i].value == value:
                temp = self.get_adjacent(i)
                res += len(temp)
        if res == 6:
            return 2
        return res

    def calc_sequences(self, value: str) -> int:
        """Returns the value of sequences of balls, used in the calculation of the value of a given board in self.evaluate_max/min"""
        result = 0
        for line in self._all_lines:
            seq = 0
            for i in line:
                if self.board[i].value == value:
                    seq += 1
                else:
                    result += 0 if seq != 2 and seq != 3 else 1 if seq == 2 else 3
                    seq = 0
            result += 0 if seq != 2 and seq != 3 else 1 if seq == 2 else 3
        return result

    def get_available_moves(self, value: str) -> List[Tuple[List[int], str]]:
        """Returns all possible moves"""
        moves = []  # move format: ([index 1, index 2, index 3], direction)
        for i, line in enumerate(self._all_lines):
            directions = [
                ['top right', 'top left', 'bottom right', 'bottom left'],
                ['right', 'left', 'top left', 'bottom right'],
                ['right', 'left', 'top right', 'bottom left']
            ][i // 9]

            last = []
            for index in line:
                if self.board[index].value == value:
                    for direction in directions:
                        moves.append(([index], direction))

                    for j in range(1, min(len(last), 2) + 1):
                        for direction in directions:
                            moves.append((sorted([index] + last[-1 * j:]), direction))

                    last.append(index)
                else:
                    last = []
        return moves

    def minimax(self, value: str, depth: int) -> Tuple[List[int], str]:
        """Returns the optimal move"""
        diff = AbaloneGraphics.difficulty
        push_out_value = 45 if diff == 1 else 50 if diff == 2 else 75
        return self.evaluate_max(
            value,
            min(2, depth),
            self.pushed_out,
            float('inf'),
            push_out_value,
            variables.percentage_display
        )[1]

    def evaluate_max(
            self,
            value: str,
            depth: int,
            curr: Dict[str, int],
            smaller: float,
            push_out_value: int,
            percentage_display: bool = False
    ) -> Tuple[float, Tuple[List[int], str]]:
        """Evaluate board from maximizing player's perspective"""
        # curr - state of how many balls are out at the time of the evaluation
        # smaller - cut the tree when your best is greater than "smaller" (all valid results must be smaller than it)
        value2 = 'black' if value == 'white' else 'white'
        backup = [i.value for i in self.board]
        pushed_out = dict(self.pushed_out)
        moves = self.get_available_moves(value)
        best = float('-inf')
        best_move = []

        for i, move in enumerate(moves):
            if percentage_display:
                print(f"{round(i / len(moves) * 100, 2)}% done")

            val = 0
            try:
                if depth == 1:
                    self.move(move[0], move[1])
                    val += push_out_value * (
                            self.pushed_out[value2] - curr[value2] -
                            (self.pushed_out[value] - curr[value])
                    )

                    if val == 0 and variables.boring_moves >= variables.boring_move_cap:  # none pushed = boring move!
                        val -= 250  # penalty
                    elif val != 0:
                        val += 250

                    val += self.calc_chunks(value) - self.calc_chunks(value2)
                    val += self.calc_distance(value) - self.calc_distance(value2)
                    val += self.calc_sequences(value) - self.calc_sequences(value2)
                else:
                    self.move(move[0], move[1])
                    val = self.evaluate_min(value, depth - 1, curr, best, push_out_value)[0]

                if best < val:
                    best = val
                    best_move = move

                # restore board
                for i in move[0]:
                    for j in self.get_line(i, move[1]):
                        self.board[j].value = backup[j]
                self.pushed_out = dict(pushed_out)  # restore pushed out

                if best >= smaller:
                    return best, best_move

            except InvalidMove:
                pass

        return best, best_move

    def evaluate_min(
            self,
            value: str,
            depth: int,
            curr: Dict[str, int],
            greater: float,
            push_out_value: int
    ) -> Tuple[float, Tuple[List[int], str]]:
        """Evaluate board from minimizing player's perspective"""
        # curr - state of how many balls are out at the time of the evaluation
        # greater - cut the tree when your best is smaller than "greater" (all valid results must be greater than it)
        value2 = 'black' if value == 'white' else 'white'
        backup = [i.value for i in self.board]
        pushed_out = dict(self.pushed_out)
        moves = self.get_available_moves(value2)
        best = float('inf')
        best_move = []

        for move in moves:
            val = 0
            try:
                if depth == 1:
                    self.move(move[0], move[1])
                    val += push_out_value * (
                            self.pushed_out[value2] - curr[value2] -
                            (self.pushed_out[value] - curr[value])
                    )

                    if val == 0 and variables.boring_moves >= variables.boring_move_cap:  # none pushed = boring move!
                        val -= 250  # penalty
                    elif val != 0:
                        val += 250

                    val += self.calc_chunks(value) - self.calc_chunks(value2)
                    val += self.calc_distance(value) - self.calc_distance(value2)
                    val += self.calc_sequences(value) - self.calc_sequences(value2)
                else:
                    self.move(move[0], move[1])
                    val = self.evaluate_max(value, depth - 1, curr, best, push_out_value)[0]

                if best > val:
                    best = val
                    best_move = move

                # restore board
                for i in move[0]:
                    for j in self.get_line(i, move[1]):
                        self.board[j].value = backup[j]
                self.pushed_out = dict(pushed_out)  # restore pushed out

                if best <= greater:
                    return best, best_move

            except InvalidMove:
                pass

        return best, best_move


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InvalidMove(Error):
    """Exception raised for invalid moves in the game."""

    def __init__(self, message: str) -> None:
        self.message = message


class Cell:
    """Represents a cell on the Abalone board."""

    def __init__(self, value: str, index: int, row_index: int, row_start: int, row_end: int, distance: int) -> None:
        self.index = index
        self.row_index = row_index
        self.distance = distance
        self.value = value
        self.row_start = row_start
        self.row_end = row_end
        self.row_size = row_end - row_start + 1
