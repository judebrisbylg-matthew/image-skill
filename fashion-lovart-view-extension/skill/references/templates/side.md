# 侧面延展图模板

来源：飞书《2.1生图工作流-背景延展图》“2、侧面延展图”。

## 输入角色

- 图1：模特人物图，同时控制构图裁切。
- 图2：产品侧面款式图，是侧面版型唯一标准。
- 图3：场景参考图。

## 图像综合分析

填写模特、产品侧面、场景、构图和光影。侧面产品分析必须覆盖侧面廓形厚度、袖管侧面形态、裙摆侧面垂坠和面料。构图以图1为准，必须明确半身或全身以及截头边界。

五张图保持同一背景核心要素，仅根据左右侧、机位远近与前后偏移调整透视。所有人物侧转角度不超过30度。

## 五个动作

1. **左侧标准角度**：身体向左偏转不超过30度；视野均衡，姿态优雅松弛。
2. **左侧微前移角度**：左侧微前移机位，强化侧面廓形和裙摆垂坠；重心在一条腿上。
3. **左侧近景，不拿包**：左侧近景，背景略虚化；不得携带任何包，双手均不垂下。
4. **右侧标准角度**：身体向右偏转不超过30度；产品右侧按图2侧面版型镜像还原，不发明结构。
5. **右侧微后移，不拿包**：右侧微后移机位、视野更开阔；不得携带任何包，双手均不垂下。

前3段为左侧动作，后2段为右侧动作。第3和第5段强制不拿包。

## 英文提示词必含

- Image 1 controls the model, crop and body scale.
- Image 2 is the sole side-garment authority.
- Image 3 controls the scene and lighting evidence.
- `body turned no more than 30 degrees to the left/right`。
- 人物光向、环境反射与地面投影匹配背景；不得出现贴图、白边或轮廓光晕。

## 通用负面提示词

```text
(text, logo, watermark, signature, words, military stance, both hands hanging down, standing at attention:1.5), (pasted on, cutout, photo composite, mismatched lighting, edge glow, halo around person, green screen, chroma key, fake background, white outline:1.4), full head, complete face, holding phone, selfie, bag on ground, bag placed on floor, blurry fabric, distorted limbs, extra fingers, deformed body, oversaturated color, low detail, ugly, grainy, cartoon, illustration, white background, mannequin, dress form, stand, pole
```

## 输出参数

`4K resolution, 2:3 aspect ratio, model: nano banana pro`
