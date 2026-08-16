# Scanned contract seal extraction

Use this branch when the source is a scanned contract or photographed document with a colored seal over printed text. Generic background-removal models are not reliable here: they can erase fine seal characters or retain black document text.

## Method

1. Keep the original image read-only and make a tight crop around the confirmed seal.
2. For a red seal, separate ink by color dominance (`R - (G+B)/2`) instead of luminance. Grey/black document text is near zero and should become transparent.
3. Convert the color signal to a continuous alpha matte and use a canonical red for the output variant. Do not run dilation, closing, median blur, sharpening, or hard thresholding on seal text: these operations fill counters and merge adjacent Chinese strokes.
4. Trim transparent margins while keeping 6–10 px safety padding. Preserve the seal aspect ratio.
5. If the user requests clearer characters, run `enhance_contract_stamp_v2.py` from the skill root. Prefer the LAB `a*` red/green channel because grey and black document text remain neutral. Keep `--scale 1` by default; use `--scale 2` only when the target layout needs more pixels. Upscaling does not restore missing detail.
6. Validate RGBA mode, transparent corners, a non-empty alpha bounding box, and previews on white and dark backgrounds. Compare the extracted seal with the source at the same displayed size. Reject the output if character counters, gaps, or parallel strokes have merged.

## Deliverables

- `*_纯红色透明.png`: red-ink-only version for layering on documents.
- `*_原色优化版.png`: color-faithful version when the original ink tone matters.
- Keep the original crop as an audit fallback; never overwrite the source.

## Clarity command

```bash
python enhance_contract_stamp_v2.py \
  --input /absolute/path/scan.png \
  --output /absolute/path/seal_clear.png \
  --crop LEFT TOP RIGHT BOTTOM \
  --scale 1 --padding 10 --method lab \
  --low 2 --high 52 --gamma 1.25
```

## Important limits

If printed text physically occludes the seal, preserve the visible ink and report the occlusion. Do not use AI inpainting or manually reconstruct legal seal text. A raster seal image is not a legal signature.
