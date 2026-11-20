#!/usr/bin/env python3
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DIGIT_COLORS = {
    0: "#94A3B8",
    1: "#F87171",
    2: "#FB923C",
    3: "#FACC15",
    4: "#4ADE80",
    5: "#2DD4BF",
    6: "#60A5FA",
    7: "#C084FC",
}
BACKGROUND = "#0F172A"
TEXT_COLOR = "#E2E8F0"
GRID_COLOR = "#1E293B"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Draw numbers as polygons whose side count matches each octal digit."
    )
    parser.add_argument("input", type=Path, help="text file with one integer per line")
    parser.add_argument("-o", "--output", type=Path, help="output PNG path (default: <input>.png)")
    parser.add_argument("--cell-size", type=int, default=84, help="size of one digit cell")
    parser.add_argument("--labels", action="store_true", help="print decimal -> octal beside each row")
    parser.add_argument("--no-legend", action="store_true", help="hide the digit/shape legend")
    return parser.parse_args()


def read_numbers(path):
    numbers = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.strip()
        if not text:
            continue
        try:
            numbers.append(int(text, 10))
        except ValueError:
            raise ValueError(f"{path}:{lineno}: not an integer: {text!r}") from None
    if not numbers:
        raise ValueError(f"{path}: no numbers found")
    return numbers


def get_font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def vertex_positions(cx, cy, radius, sides):
    return [
        (
            cx + radius * math.cos(-math.pi / 2 + 2 * math.pi * i / sides),
            cy + radius * math.sin(-math.pi / 2 + 2 * math.pi * i / sides),
        )
        for i in range(sides)
    ]


def draw_dot(draw, x, y, radius, color):
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def draw_digit(draw, cx, cy, radius, digit, width):
    color = DIGIT_COLORS[digit]
    dot = max(2, radius * 0.11)

    if digit == 0:
        draw_dot(draw, cx, cy, max(3, radius * 0.2), color)
        return

    points = vertex_positions(cx, cy, radius, max(digit, 2))

    if digit == 1:
        draw_dot(draw, points[0][0], points[0][1], max(4, radius * 0.16), color)
        return

    if digit == 2:
        draw.line(points, fill=color, width=width)
        for x, y in points:
            draw_dot(draw, x, y, max(4, radius * 0.16), color)
        return

    draw.line(points + [points[0]], fill=color, width=width, joint="curve")
    for x, y in points:
        draw_dot(draw, x, y, dot, color)


def main():
    args = parse_args()

    try:
        numbers = read_numbers(args.input)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    cell = max(24, args.cell_size)
    pad = cell // 3
    row_height = cell + cell // 4
    label_width = int(cell * 4.5) if args.labels else 0
    legend_height = int(cell * 1.6) if not args.no_legend else 0

    octal_strings = [format(abs(n), "o") for n in numbers]
    max_digits = max(len(s) for s in octal_strings)
    has_negative = any(n < 0 for n in numbers)
    content_width = max_digits * cell + (cell if has_negative else 0)
    legend_width = 8 * cell if not args.no_legend else 0

    width = pad * 2 + label_width + max(content_width, legend_width)
    height = pad * 2 + legend_height + len(numbers) * row_height

    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = get_font(max(12, cell // 5))

    y = pad
    if legend_height:
        for digit in range(8):
            cx = pad + label_width + digit * cell + cell // 2
            cy = y + cell // 2
            if digit % 2 == 0:
                draw.rectangle(
                    [cx - cell // 2, y, cx + cell // 2, y + cell],
                    fill=GRID_COLOR,
                )
            draw_digit(draw, cx, cy, cell * 0.28, digit, max(2, cell // 24))
            text = str(digit)
            box = draw.textbbox((0, 0), text, font=font)
            draw.text(
                (cx - (box[2] - box[0]) / 2, y + cell + cell // 12),
                text,
                fill=TEXT_COLOR,
                font=font,
            )
        y += legend_height

    for number, octal in zip(numbers, octal_strings):
        if args.labels:
            draw.text(
                (pad, y + cell // 3),
                f"{number} -> {octal if number >= 0 else '-' + octal}",
                fill=TEXT_COLOR,
                font=font,
            )

        offset = cell if number < 0 else 0
        if number < 0:
            minus_y = y + cell // 2
            draw.line(
                [
                    (pad + label_width + cell // 4, minus_y),
                    (pad + label_width + cell * 3 // 4, minus_y),
                ],
                fill=DIGIT_COLORS[1],
                width=max(2, cell // 16),
            )

        for index, char in enumerate(octal):
            cx = pad + label_width + offset + index * cell + cell // 2
            cy = y + cell // 2
            draw_digit(draw, cx, cy, cell * 0.32, int(char), max(2, cell // 20))
        y += row_height

    output = args.output or args.input.with_suffix(".png")
    try:
        image.save(output)
    except OSError as exc:
        print(f"error: cannot write {output}: {exc}", file=sys.stderr)
        return 1

    print(f"saved {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
