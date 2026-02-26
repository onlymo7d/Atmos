#!/usr/bin/env python3
import math
import time
import sys

def main():
    A = 0.0
    B = 0.0
    width = 80
    height = 22
    chars = ".,-~:;=!*#$@"

    print("\x1b[2J", end="")

    try:
        while True:
            z = [0.0] * (width * height)
            b = [" "] * (width * height)

            for j in range(0, 628, 7):
                for i in range(0, 628, 2):
                    c = math.sin(i / 100.0)
                    d = math.cos(j / 100.0)
                    e = math.sin(A)
                    f = math.sin(j / 100.0)
                    g = math.cos(A)
                    h = d + 2
                    D = 1.0 / (c * h * e + f * g + 5)
                    l = math.cos(i / 100.0)
                    m = math.cos(B)
                    n = math.sin(B)
                    t = c * h * g - f * e

                    x = int(40 + 30 * D * (l * h * m - t * n))
                    y = int(12 + 15 * D * (l * h * n + t * m))
                    o = x + width * y
                    N = int(
                        8
                        * (
                            (f * e - c * d * g) * m
                            - c * d * e
                            - f * g
                            - l * d * n
                        )
                    )

                    if 0 <= o < width * height and D > z[o]:
                        z[o] = D
                        idx = N if 0 <= N < len(chars) else 0
                        b[o] = chars[idx]

            print("\x1b[H", end="")
            for k in range(height):
                print(''.join(b[k * width : (k + 1) * width]))

            A += 0.07
            B += 0.03
            time.sleep(0.03)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()