#!/usr/bin/env python3
"""Extract red contract-seal ink while preserving fine character counters.

This deterministic pass separates red chroma from neutral document text. It
does not dilate, close, blur, sharpen, or redraw the seal, because those steps
can merge adjacent Chinese strokes and make readable characters look muddy.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def _extract_alpha(
    rgb: np.ndarray,
    method: str,
    low: float,
    high: float,
    gamma: float,
) -> np.ndarray:
    red, green, blue = (rgb[:, :, i].astype(np.float32) for i in range(3))
    if method == "lab":
        import cv2
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        signal = lab[:, :, 1].astype(np.float32) - 128.0
    else:
        signal = red - (green + blue) / 2.0

    matte = np.clip((signal - low) / max(high - low, 1e-6), 0.0, 1.0)
    matte = np.power(matte, gamma)
    return np.rint(matte * 255.0).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--crop",
        nargs=4,
        type=int,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        required=True,
    )
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--padding", type=int, default=10)
    parser.add_argument("--method", choices=("lab", "difference"), default="lab")
    parser.add_argument("--low", type=float)
    parser.add_argument("--high", type=float)
    parser.add_argument("--gamma", type=float, default=1.25)
    args = parser.parse_args()
    if args.scale < 1:
        raise SystemExit("--scale must be at least 1")

    source = Image.open(args.input).convert("RGB")
    crop = source.crop(tuple(args.crop))
    rgb = np.asarray(crop, dtype=np.uint8)
    default_low, default_high = ((2.0, 52.0) if args.method == "lab" else (3.0, 135.0))
    low = default_low if args.low is None else args.low
    high = default_high if args.high is None else args.high
    alpha = _extract_alpha(rgb, args.method, low, high, args.gamma)

    ys, xs = np.where(alpha > 2)
    if len(xs) == 0:
        raise SystemExit("No red seal ink detected; adjust the crop or inspect the source.")
    left = max(int(xs.min()) - args.padding, 0)
    top = max(int(ys.min()) - args.padding, 0)
    right = min(int(xs.max()) + args.padding + 1, alpha.shape[1])
    bottom = min(int(ys.max()) + args.padding + 1, alpha.shape[0])
    alpha = alpha[top:bottom, left:right]

    if args.scale != 1:
        alpha = np.asarray(
            Image.fromarray(alpha, "L").resize(
                (alpha.shape[1] * args.scale, alpha.shape[0] * args.scale),
                Image.Resampling.LANCZOS,
            ),
            dtype=np.uint8,
        )

    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[:, :, :3] = (205, 18, 24)
    rgba[:, :, 3] = alpha
    out = Image.fromarray(rgba, "RGBA")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, "PNG", optimize=True)
    if out.getpixel((0, 0))[3] != 0 or out.getpixel((out.width - 1, out.height - 1))[3] != 0:
        raise SystemExit("Validation failed: output corners must be transparent.")


if __name__ == "__main__":
    main()
