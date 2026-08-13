# 全身延展图模板

来源：飞书《2.1生图工作流-背景延展图》“4、全身延展图”。

## 输入角色

- 图1：模特人物图。
- 图2：产品图。
- 图3：场景参考图。
- 图4：鞋子搭配图；不得误判为构图图。`图4`描述的是原始素材角色，不代表 Lovart 上传后的第4张。

## 硬性构图

- 必须是完整全身图，从头发/头顶最高点到双脚最低点连续完整入镜，保留完整头部、完整脸部、身体、裙摆、双脚和鞋底。
- 头顶上方与鞋底下方必须保留可见安全边距；头发、下巴、脚踝、脚趾、鞋子均不得触碰或越过画面边缘。
- 鞋子和脚趾完整露出，不能被裙摆遮挡或裁切。
- 图2是服装结构唯一来源，图4是鞋履唯一来源。
- 侧面动作角度不超过30度，脸部保持可见并按动作朝向镜头。
- 人物与场景光向、环境反射、地面投影和色温统一。
- 英文执行提示词使用 `SHOES ACCESSORY SOURCE` 等语义角色名，不使用 `Image 4` 等上传序号。

## 五个动作

1. **正面标准机位**：完整头到脚；可自然手提图1已有且允许的包，另一手置于腰侧，双腿自然交叉或错步。
2. **正面偏左微侧**：约20度，脸转回镜头；包可单肩携带，一手扶包，另一手弯曲置胯。
3. **正面近景完整全身，不拿包**：不得携带任何包；一手轻触发丝，另一手轻搭裙侧；完整头脚仍在画面内。
4. **右侧微侧**：约25度且不超过30度，脸朝镜头；可手提包，另一手扶裙侧，展示正面结构和侧面垂坠。
5. **左侧微侧，不拿包**：约30度且不得超过；脸朝镜头；不得携带任何包，一手轻扶领口或上身细节，另一手搭裙侧。

前三段为正面或接近正面的动作；最后两段为侧面动作。第3和第5段强制不拿包。

场景在五个机位间只能做多角度延伸，保持图3核心元素不变。根据实际场景调整前景、海岸线、街道、建筑或其他元素的可见范围，不能替换背景。

## 通用负面提示词

```text
(text, logo, watermark, signature, words, military stance, both hands hanging down, standing at attention:1.5), (pasted on, cutout, photo composite, mismatched lighting, edge glow, halo around person, green screen, chroma key, fake background, white outline:1.4), cropped head, no full head, missing face, bag on ground, bag placed on floor, holding phone, selfie, blurry fabric, distorted limbs, extra fingers, deformed body, oversaturated color, low detail, ugly, grainy, cartoon, illustration, white background
```

## 输出参数

`4K resolution, 2:3 aspect ratio, model: nano banana pro`
