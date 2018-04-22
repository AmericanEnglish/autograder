# David Lewis
# dlewis@olivetcollege.edu


def move_tower(tower_size, source, destination, spare):
    # print(tower_size, source, destination, spare)
    """
    Moves discs from source to destination in a recursive manner.

    >>> move_tower(2, ([2, 1], 'A'), ([], 'C'), ([], 'B'))
    Move disc 1 from A to B
    Move disc 2 from A to C
    Move disc 1 from B to C

    """
    if tower_size >= 1:
        move_tower(tower_size - 1, source, spare, destination)
        print('Move disc {} from {} to {}'.format(
            tower_size, source[0], destination[0]))
        destination.append(source.pop())
        move_tower(tower_size - 1, spare, destination, source)
        print('{} {} {}'.format(source, destination, spare))


def main():
    print('\nTower of Hanoi\n')
    tower_size = int(input('How many discs shall I solve for? '))
    print('\n')
    source = ['A']
    for x in reversed(range(tower_size)):
        source.append(x + 1)
    destination = ['C']
    spare = ['B']
    move_tower(tower_size, source, destination, spare)
    print()

if __name__ == '__main__':
    main()
