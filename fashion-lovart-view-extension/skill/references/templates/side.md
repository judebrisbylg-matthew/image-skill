# 侧面延展图模板

来源：飞书《2.1生图工作流-背景延展图》“2、侧面延展图”。

## 输入角色

> The Feishu 图1/图2/图3 labels below are logical role labels, not Lovart upload index values. In every ASCII package, `identity_model_01` (`正面/1.jpg`) is physically first; a separate local side pose/composition source follows only when its hash differs.

- `IDENTITY MODEL SOURCE = 正面/1.jpg`：唯一身份依据，只提取 `identity_profile`。
- 图1：本视角侧面人物参考，作为 `POSE/COMPOSITION SOURCE`，仅提供姿势、裁切、身体方向和构图。
- 图2：产品侧面款式图，是侧面版型唯一标准。
- 图3：场景参考图。

IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。

Noncanonical local pose/composition sources must not control or override `body_profile`; copy that value only from the active canonical identity profile.

## 图像综合分析

填写 canonical identity、产品侧面、场景、构图和光影。侧面产品分析必须覆盖侧面廓形厚度、袖管侧面形态、裙摆侧面垂坠和面料。本视角 POSE/COMPOSITION SOURCE 控制构图，必须明确半身或全身以及截头边界。

每个动作的中文融合说明必须明确：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2继续作为侧面服装唯一标准，图3继续控制场景与光影。

五张图保持同一背景核心要素，仅根据左右侧、机位远近与前后偏移调整透视。所有人物侧转角度不超过30度。

## 五个动作

1. **左侧标准角度**：身体向左偏转不超过30度；视野均衡，姿态优雅松弛。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
2. **左侧微前移角度**：左侧微前移机位，强化侧面廓形和裙摆垂坠；重心在一条腿上。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
3. **左侧近景，不拿包**：左侧近景，背景略虚化；不得携带任何包，双手均不垂下。 When the garment frame lock applies, move the camera farther away. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
4. **右侧标准角度**：身体向右偏转不超过30度；产品右侧按图2侧面版型镜像还原，不发明结构。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
5. **右侧微后移，不拿包**：右侧微后移机位、视野更开阔；不得携带任何包，双手均不垂下。 `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

前3段为左侧动作，后2段为右侧动作。第3和第5段强制不拿包。

## 英文提示词必含

- The canonical IDENTITY MODEL SOURCE controls identity only.
- The local POSE/COMPOSITION SOURCE controls crop and subject scale in the frame without overriding identity; it must not control or override `body_profile`.
- The PRODUCT SOURCE is the sole side-garment authority.
- The SCENE SOURCE controls scene and lighting evidence.
- `body turned no more than 30 degrees to the left/right`。
- 人物光向、环境反射与地面投影匹配背景；不得出现贴图、白边或轮廓光晕。

## 通用负面提示词

Negative Prompt is script-generated and immutable. Derive the `side` contract with `view_contract_from_manifest`; it activates footwear only from an explicit validated `footwear_contract`, never from a generic bag, jewelry, or other `accessory_source`. Set every action's `negative_prompt` to the unmodified result of `render_negative_prompt(view_contract, identity_contract, garment_contract)`. Do not compose, paraphrase, reorder, trim, append, or remove negative-prompt text in this Markdown template.

## 输出参数

`4K resolution, 2:3 aspect ratio, model: nano banana pro`
