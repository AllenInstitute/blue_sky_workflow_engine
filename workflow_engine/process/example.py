from time import sleep
import sys

if __name__ == '__main__':
    life_seconds = sys.argv[-1]

    for i in range(int(life_seconds)):
        sleep(1)
        print(i)
        with open('test.out', 'w') as f:
            f.write(life_seconds)
