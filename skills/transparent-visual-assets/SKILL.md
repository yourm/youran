---
name: transparent-visual-assets
description: Generate transparent-background raster assets with Codex image generation plus deterministic cleanup. Use for PNG stickers, icons, mascots, sprites, web-ready visual elements, and scanned contract or company-seal extraction where the colored seal must be preserved while paper and overprinted grey/black text become transparent.
---

# Transparent Visual Assets

## 核心判断

先让 Codex 生图得到“容易抠干净”的图，再用脚本做确定性清理。不要要求模型直接画棋盘格透明背景；棋盘格会变成图像内容。优先让模型使用纯色背景，例如 `#FF00FF` 或 `#00FF00`，并明确主体不能使用接近背景的颜色。

适合输出：透明 PNG、网页素材、贴纸、图标、单帧 sprite、角色/物体素材。

不适合输出：多帧动画、spritesheet、视频；这些转给 `$sprite-animation-assets`。

## 典型使用场景

- 网站设计素材：Landing page、产品官网、博客插画、功能区装饰、空状态插画。
- PPT / 汇报图表：路演页、数据页、业务复盘、图表旁的视觉解释元素。
- App / 产品引导：onboarding、权限说明、功能引导、发布说明里的产品插画。
- 电商 / 社媒贴纸：商品页角标、促销贴纸、社媒封面、公众号配图元素。
- 游戏 / 互动 UI：小角色、道具、背包图标、按钮素材、单帧 sprite。
- 视频 / 海报叠加：封面人物、栏目贴片、透明 logo-like 装饰、片头片尾元素。

## 工作流

1. 明确素材用途、尺寸、主体边界和禁用元素。
2. 调用 Codex 生图能力生成带纯色背景的候选图。
3. 目视检查：主体完整、没有阴影地面、没有漂浮杂点、主体颜色不接近背景色。
4. 用 `scripts/prepare_transparent_asset.py` 清理纯色背景、裁切透明边缘、输出 PNG。
5. 打开结果或检查报告，确认透明角落、主体不被误删。

## 扫描合同章

当输入是合同扫描件、印章压在正文或签章表格上时，不要直接使用通用模型抠图。读取 [references/contract-stamp.md](references/contract-stamp.md)，按颜色优势分离红色印迹；需要重复处理时运行 `scripts/extract_contract_stamp.py`。如果用户要求“字体清晰/高清”，运行技能目录中的 `enhance_contract_stamp_v2.py`。默认保留原尺寸，只在版面确实需要时输出 2 倍版本；禁止对文字做膨胀、闭运算、模糊、锐化或硬阈值填充。保留原图和原色备份，不补画缺失的印章文字。

## 生图提示词要点

使用简短、强约束的提示词：

```text
Create a single centered web asset of <subject>.
Use a perfectly flat #FF00FF background for later chroma key removal.
The subject must not contain magenta, pink, or colors close to #FF00FF.
No shadows, floor, scenery, text, labels, checkerboard pattern, glow, blur, or detached decorative particles.
Keep the full subject inside the canvas with clear spacing.
```

如果主体天然包含粉色或品红，换成 `#00FF00`、`#00FFFF` 或其他不会出现在主体里的纯色。

更多提示词和 QA 细节见 `references/prompt-and-cleanup.md`。

## 清理脚本

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/transparent-visual-assets/scripts/prepare_transparent_asset.py" \
  --input /absolute/path/source.png \
  --output /absolute/path/asset.png \
  --background "#FF00FF" \
  --threshold 24 \
  --feather-threshold 48 \
  --trim \
  --padding 8 \
  --report /absolute/path/report.json
```

参数说明：

- `--background`：要移除的纯色背景；不传时用四角颜色估算。
- `--threshold`：颜色容差。背景边缘残留就调大；主体被吃掉就调小或重生图换背景色。
- `--feather-threshold`：可选的边缘柔化容差，用来淡化生图抗锯齿留下的背景色毛边。
- `--trim` 和 `--padding`：裁掉透明边缘并保留一点安全留白。

脚本只做背景清理，不会补画、重绘、扩图或创造新素材。

## 验收标准

- 输出必须是 `.png`，并带 alpha 透明通道。
- 四角应透明，主体边缘不缺块。
- 主体外没有阴影、地面、光晕、漂浮符号、文字或背景色残留。
- 素材在深色、浅色、棋盘格背景上都能读清。
- 如果清理后主体明显破损，重新生图或换背景色，不要靠脚本硬修。
