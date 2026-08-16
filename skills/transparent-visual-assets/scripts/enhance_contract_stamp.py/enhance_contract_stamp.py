#!/usr/bin/env python3
"""Sharpen visible red ink in a scanned contract seal.

This is a deterministic enhancement pass for low-resolution scans. It separates
red ink from black/grey document text, bridges tiny scan breaks, and exports a
larger antialiased RGBA PNG. It never invents missing characters.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def _extract_alpha(rgb: np.ndarray, boost: float) -> np.ndarray:
    red, green, blue = (rgb[:, :, i].astype(np.float32) for i in range(3))
    redness = red - (green + blue) / 2.0

    try:
        import cv2

        # A small median pass removes isolated red scanner specks without
        # erasing the narrow strokes in the circular text.
        redness = cv2.medianBlur(np.clip(redness, 0, 255).astype(np.float32), 3)
        soft = np.clip((redness - 2.5) / 68.0 * 255.0 * boost, 0, 255)
        ink = (redness >= 12.0).astype(np.uint8) * 255
        ink = cv2.morphologyEx(
            ink,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
        # Preserve anti-aliased edges while giving broken glyph strokes a
        # stable opaque core. This is deliberately modest to avoid swelling
        # the outer ring.
        core = ink.astype(np.float32) * 0.90
        # Keep a crisp core and a soft photographic edge. A final blur here
        # would make small Chinese strokes look foggy after supersampling.
        alpha = np.maximum(soft, core)
        return np.clip(alpha, 0, 255).astype(np.uint8)
    except ImportError:
        return np.clip((redness - 3.0) / 76.0 * 255.0 * boost, 0, 255).astype(np.uint8)


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
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--padding", type=int, default=16)
    parser.add_argument("--boost", type=float, default=1.10)
    args = parser.parse_args()
    if args.scale < 1:
        raise SystemExit("--scale must be at least 1")

    source = Image.open(args.input).convert("RGB")
    crop = source.crop(tuple(args.crop))
    rgb = np.asarray(crop, dtype=np.uint8)
    alpha = _extract_alpha(rgb, args.boost)

    ys, xs = np.where(alpha > 4)
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
