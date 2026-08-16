# 正面延展图模板

来源：飞书《2.1生图工作流-背景延展图》“1、正面延展图”。

## 输入角色

> The Feishu 图1/图2/图3/图4 labels below are logical role labels, not Lovart upload index values. In every ASCII package, `identity_model_01` (`正面/1.jpg`) is physically first; a separate local pose/composition source follows only when its hash differs.

- `IDENTITY MODEL SOURCE = 正面/1.jpg`：唯一身份依据，只提取 `identity_profile`。
- 图1：本视角人物姿势参考，作为 `POSE/COMPOSITION SOURCE`，仅提供姿势、裁切、身体方向和构图。
- 图2：产品正面款式图。
- 图3：场景参考图。
- 图4：人物构图参考图；与图1重复时使用逻辑角色，不重复上传。

IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。

Noncanonical local pose/composition sources must not control or override `body_profile`; copy that value only from the active canonical identity profile.

> **Typed execution contract:** Convert each方案 into scanner-backed `source_bindings` plus `action_directives` containing supported controlled code values for `action`, `camera`, `composition`, and `scene`. Use the action codes in exact order: `catalogue-neutral`, `weight-shift`, `controlled-step`, `detail-gesture`, `soft-turn`; select camera/composition/scene only from `validate_manifest.py` render maps. Set strict integer `attempt`, use `correction: null` for attempt 1, or exact rejection-code `fix` plus `preserve: accepted-contracts` on retry, then call `render_positive_prompt`. Its exact output is the only executable positive prompt: no free authority prose and no hand edits.

## 图像综合分析

填写：canonical IDENTITY MODEL SOURCE 的可见身份特征；本视角 POSE/COMPOSITION SOURCE 的姿势、裁切、身体方向、主体占比与构图目的；产品完整保留项、展示价值、面料质感；场景提取、光影、剔除元素；受光方向、环境反射、真实投影、统一色调与空间纵深。

场景只做同一背景的多角度延伸。核心背景要素保持一致，仅根据机位远近、左右偏移调整可见范围与透视。

## 五个动作

1. **正面标准角度**：正面标准机位，均衡显示核心背景要素和服装正面；自然动作，禁止站军姿或双手同时垂下。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
2. **正面微侧角度**：正面偏左或偏右轻微侧转，同时显示服装正面廓形与轻微侧面层次。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
3. **正面近景特写角度**：背景略微虚化，突出胸前细节、领口、袖口和面料质感，仍遵循构图参考。 When the garment frame lock applies, move the camera farther away. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
4. **正面稍远角度，不拿包**：展示整体穿搭比例；不携带任何包，双手均不垂下。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
5. **正面低机位角度，不拿包**：突出下摆垂坠与整体气场；不携带任何包，双手均不垂下。`FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `HEAD CROP FLOOR:` The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

每个动作的中文融合说明必须明确：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。另行说明图2正面产品、图3场景与图4构图的融合关系，并输出完整中文分析和完整英文执行提示词。

## 通用负面提示词

Negative Prompt is script-generated and immutable. Derive the `front` contract with `view_contract_from_manifest`; it activates footwear only from an explicit validated `footwear_contract`, never from a generic bag, jewelry, or other `accessory_source`. Set every action's `negative_prompt` to the unmodified result of `render_negative_prompt(view_contract, identity_contract, garment_contract)`. Do not compose, paraphrase, reorder, trim, append, or remove negative-prompt text in this Markdown template.

## 输出参数

`4K resolution, 2:3 aspect ratio, model: nano banana pro`
