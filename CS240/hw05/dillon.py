def main():
    """ (Nonetype) -> Nonetype
    Displays the title, asks the user for the number of discs, sets up the\
    initial state for the game (all discs on a single peg) and calls the\
    solver.
    """
    print('\nTower of Hanoi\n')
    tower_size = int(input('How many discs shall I solve for? '))
    print()
    tower_height = range(tower_size)
    user_input = reversed(tower_height)
    source = ['A']
    destination = ['B']
    for item in user_input:
        source.append(item)
    spare = ['C']
    move_tower(tower_size, source, destination, spare)
    print()
    print()


def move_tower(tower_size, source, destination, spare):
    """ (int, list, list, list) -> Nonetype
    Expects an integer specifying the tower size and three lists that\
    represent the pegs. Prints each move it makes and returns nothing.

    >>> move_tower(1, ['A', 1], ['B'], ['C'])
    Move disc 1 from A to B

    >>> move_tower(2, ['A', 2, 1], ['B'], ['C'])
    Move disc 1 from A to C
    Move disc 2 from A to B
    Move disc 1 from C to B

    >>> move_tower(3, ['A', 3, 2, 1], ['B'], ['C'])
    Move disc 1 from A to B
    Move disc 2 from A to C
    Move disc 1 from B to C
    Move disc 3 from A to B
    Move disc 1 from C to A
    Move disc 2 from C to B
    Move disc 1 from A to B
    """
    if tower_size == 1:
        # move source to destination
        destination.append(source.pop())
        print('Move disc {} from {} to {}'.format(
            tower_size, source[0], destination[0]))
    else:
        move_tower(tower_size - 1, source, spare, destination)
        # move nth source destination
        destination.append(source.pop())
        print('Move disc {} from {} to {}'.format(
            tower_size, source[0], destination[0]))
        move_tower(tower_size - 1, spare, destination, source)


if __name__ == '__main__':
    import doctest
    doctest.testmod()