# Nano Banana Pro Prompt Schema

最终 prompt 必须是 Nano Banana Pro 友好的短块结构。不要写成一整段长 prompt。

## 默认输出规格

```text
3:4 ratio, 4K output, pure white #FFFFFF background
```

不要再写旧的 `2048x3072` 或 `2:3`，除非用户明确要求。

## 推荐结构

```text
FINAL OUTPUT
Create one high-end fashion ecommerce studio photo, 3:4 ratio, 4K output, pure white #FFFFFF background.

REFERENCE ROLE CONTRACT
PRODUCT SOURCE: ...
LINE_ART SOURCE: ...
MODEL APPEARANCE LOCK: ...
ACCESSORY SOURCES: ...
BOTTOMS SOURCE: ...
DENIED SOURCES: ...

REFERENCE PRIORITY
...

GARMENT HARD LOCK
...

POSE AND BODY HARD LOCK
...

MODEL APPEARANCE HARD LOCK
...

ACCESSORIES AND BOTTOMS
...

LIGHTING AND FINISH
...

DO NOT INCLUDE
...
```

## 写法要求

- 先写角色合同，再写视觉描述。
- 每个来源只控制自己的范围。
- 用 `must match`, `preserve exactly`, `copy only`, `do not borrow`, `ignore` 这类直接控制语言。
- 主商品描述必须非常具体，包括领口、袖型、肩部、腰线、下摆、面料、纹理、五金、花型和长度体量。
- 对动作和构图使用硬锁语言，不让 Nano Banana Pro 自由改姿势。
- 肤色必须来自 `MODEL APPEARANCE LOCK`，不能来自黑白线稿。
- 配饰不允许遮挡主商品关键细节。

## 常见负向约束

```text
No words, letters, numbers, captions, watermarks, logo-like marks, random symbols, unprovided styling items, extra garments, extra jewelry, extra bags, extra shoes, background props, benchmark-background elements, collage layout, multiple models, duplicate limbs, changed pose, changed crop, changed skin tone, changed hairstyle, changed garment design, borrowed benchmark outfit details, borrowed line-art outfit details, mannequin, mannequin stand, or product-reference background.
```
