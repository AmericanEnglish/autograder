# David Lewis
# dlewis@olivetcollege.edu


def main():
    print('\nTower of Hanoi\n')
    tower_size = int(input('How many discs shall I solve for? '))
    print('\n')
    source = ([], 'A')
    for x in reversed(range(tower_size)):
        source[0].append(x + 1)
    destination = ([], 'C')
    spare = ([], 'B')
    move_tower(tower_size, source, destination, spare)
    print()


def move_tower(tower_size, source, destination, spare):
    """
    Moves discs from source to destination in a recursive manner.

    >>> move_tower(2, ([2, 1], 'A'), ([], 'C'), ([], 'B'))
    Move disc 1 from A to B
    Move disc 2 from A to C
    Move disc 1 from B to C

    """
    if tower_size == 1:
        # move disc from source to destination
        destination[0].append(source[0].pop())
        print('Move disc {} from {} to {}'.format(
            tower_size, source[1], destination[1]))
    else:
        # move tower_size - 1 from source to spare
        move_tower(tower_size - 1, source, spare, destination)
        # move nth disc from source to destination
        destination[0].append(source[0].pop())
        print('Move disc {} from {} to {}'.format(
            tower_size, source[1], destination[1]))
        # move tower_size - 1 from spare to destination
        move_tower(tower_size - 1, spare, destination, source)

if __name__ == '__main__':
    main()
