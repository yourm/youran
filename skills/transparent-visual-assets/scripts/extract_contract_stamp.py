#!/usr/bin/env python3
"""Extract visible red seal ink from a scanned contract into a transparent PNG.

This is deliberately deterministic. It removes grey/black document text by
color dominance and never redraws missing seal characters.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--crop", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"), required=True)
    parser.add_argument("--padding", type=int, default=8)
    args = parser.parse_args()

    source = Image.open(args.input).convert("RGB")
    crop = np.asarray(source.crop(tuple(args.crop)), dtype=np.float32)
    red, green, blue = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
    redness = red - (green + blue) / 2.0
    alpha = np.clip((redness - 3.0) / 86.0 * 255.0, 0, 255)

    try:
        import cv2

        binary = (redness > 10).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        alpha = np.maximum(alpha, closed.astype(np.float32) * 0.52)
    except ImportError:
        pass

    rgba = np.zeros((*crop.shape[:2], 4), dtype=np.uint8)
    rgba[:, :, :3] = (205, 18, 24)
    rgba[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    ys, xs = np.where(rgba[:, :, 3] > 0)
    if len(xs) == 0:
        raise SystemExit("No red seal ink detected; adjust the crop or inspect the source.")
    left = max(int(xs.min()) - args.padding, 0)
    top = max(int(ys.min()) - args.padding, 0)
    right = min(int(xs.max()) + args.padding + 1, rgba.shape[1])
    bottom = min(int(ys.max()) + args.padding + 1, rgba.shape[0])
    out = Image.fromarray(rgba[top:bottom, left:right], "RGBA")
    out.save(args.output, "PNG", optimize=True)
    if out.getpixel((0, 0))[3] != 0:
        raise SystemExit("Validation failed: output corner is not transparent.")


if __name__ == "__main__":
    main()
