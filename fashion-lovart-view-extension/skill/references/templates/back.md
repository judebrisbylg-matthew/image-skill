# 背面延展图模板

来源：飞书《2.1生图工作流-背景延展图》“3、背面延展图”。

## 输入角色

> The Feishu 图1/图2/图3 labels below are logical role labels, not Lovart upload index values. In every ASCII package, `identity_model_01` (`正面/1.jpg`) is physically first; a separate local back pose/composition source follows only when its hash differs.

- `IDENTITY MODEL SOURCE = 正面/1.jpg`：唯一身份依据，只提取 `identity_profile`。
- 图1：本视角背面人物参考，作为 `POSE/COMPOSITION SOURCE`，仅提供姿势、裁切、身体方向和构图。
- 图2：服装背面参考，是背面剪裁、后领、袖型、下摆和面料结构的唯一标准。
- 图3：场景背景参考。

IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。

Noncanonical local pose/composition sources must not control or override `body_profile`; copy that value only from the active canonical identity profile.

## 图像综合分析

填写 canonical identity 的可见身份特征、本视角 POSE/COMPOSITION SOURCE 的姿势与构图、图2背面核心版型，以及图3环境固定元素、实际光影方向和场景延展逻辑。清除场景里的文字、店铺招牌和品牌标识；包不得放在地面。

每个动作的中文融合说明必须明确：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2继续作为背面服装唯一标准，图3继续控制场景与光影。

五段提示词对应同一场景的近景、中景、纵深、街角和入口等机位变化。核心建筑、道具、路面、植被保持一致。光影描述必须从实际图3提取，不把示例场景的法式街头设定硬套到其他素材。

## 五个动作

1. **侧后方3/4转身，单手轻扶包肩带**：露出完整衣背，另一手搭腰侧，重心偏单腿；场景使用适合当前素材的近景前景角度。`IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
2. **正侧后方，单手插袋，不拿包**：移除所有包袋；后背完整朝镜头稍带侧面，另一手搭胯，双腿错开。`IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
3. **侧后方轻靠可用场景结构，单手握包带**：仅当图3确有安全可依靠的墙面或结构时使用；否则改为同等侧后方松弛站姿，不虚构建筑。`IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
4. **背面微侧，单手整理袖口**：另一手挎包；街角/转折机位仅在图3允许时使用，否则以同一场景的侧向纵深替代。`IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
5. **半侧身背面，单手扶场景结构**：仅使用图3确有的栏杆、门框或等价结构；若没有，改为一手置腰后的自然动作，不虚构道具。`IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

每段必须以图2背面款式为最高服装优先级，禁止出现服装正面主视图。

## 通用负面提示词

```text
no text, no logo, no watermark, eyes, stiff military standing pose, both hands hanging down, distorted limbs, extra fingers, blurry fabric, low resolution, ugly body proportions, bag on ground, shop sign text, street sign text, front view of top
```

## 输出参数

`4K resolution, 2:3 aspect ratio, model: nano banana pro`
