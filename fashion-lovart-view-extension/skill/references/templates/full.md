# 四图融合延展图全身生图方案（______）

---

## 一、图像综合分析

> **动态分析总规则**：必须根据本次实际提供的全部参考图以及飞书的四个逻辑角色，重新分析身份、姿势/构图、产品、场景、鞋履和光影，不得直接复用其他案例中的人物特征、服装款式、鞋履、场景元素、色调或动作细节。标题括号中的内容应根据图2产品特征和图3场景风格概括填写，建议格式为“产品核心特征・场景/风格定位”。

> The Feishu 图1/图2/图3/图4 labels below are logical role labels, not Lovart upload index values. In every ASCII package, `identity_model_01` (`正面/1.jpg`) is physically first; a separate local full-body pose/composition source follows only when its hash differs. Keep the four-source fusion logic in each action while naming sources semantically in the executable prompt.

IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。

Noncanonical local pose/composition sources must not control or override `body_profile`; copy that value only from the active canonical identity profile.

### 0. IDENTITY MODEL SOURCE（正面/1.jpg）分析
* **可见身份特征**：______
* **可见肤色与 ancestry cues**：______
* **可见脸部与发型证据**：______
* **年龄印象与 body profile**：______
* **身份使用边界**：只建立 `identity_profile`，不从其他视角人物参考补写或覆盖身份

### 1. 图1（本视角 POSE/COMPOSITION SOURCE）分析
* **姿势与重心**：______
* **裁切与主体比例**：______
* **身体方向与机位关系**：______
* **构图和空间位置**：______
* **来源使用边界**：仅控制姿势、裁切、身体方向和构图，不得控制或覆盖身份；最终服装颜色、版型、结构和细节必须以图2产品图为准

### 2. 图2（产品款式图）分析
* **产品类别与主色**：______
* **核心服装（完整保留项）**：______
* **领口结构**：______
* **袖型与袖口结构**：______
* **服装廓形与长度**：______
* **下摆与装饰细节**：______
* **产品展示价值**：______
* **面料质感**：______
* **禁止改变项**：不得改变产品颜色、版型、领口、袖型、长度、面料、装饰位置、开合方式或其他设计结构

### 3. 图3（场景参考图）分析
* **场景类型与风格定位**：______
* **背景环境提取规则**：______
* **核心背景元素**：______、______、______、______
* **前景与地面元素**：______
* **光源方向**：______
* **光影软硬程度**：______
* **环境反射色**：______
* **整体色调与色温**：______
* **地面投影特征**：______
* **强制剔除元素**：移除图3中的原有人物、文字、logo、水印、签名、贴纸、店铺标识、路牌文字和其他无关人造标识
* **场景多角度延伸规则**：5个方案分别对应**正面标准机位、正面偏左微侧机位、正面稍近完整全身机位、右侧微侧机位、左侧微侧机位**五个拍摄角度，背景核心要素（______、______、______、______）保持一致，仅根据机位远近、左右偏移和微侧角度调整画面可见范围、透视关系及前景分布，不得替换或重新设计背景

### 4. 图4（鞋子搭配图）分析
* **鞋履类别**：______
* **鞋履颜色**：______
* **鞋履材质**：______
* **鞋面结构与装饰**：______
* **鞋底与鞋跟结构**：______
* **鞋履完整保留项**：______
* **鞋履与服装搭配关系**：______
* **鞋履展示硬性规则**：两只鞋、脚趾和鞋底必须完整可见，不得被服装下摆、地面、前景物体或画面边缘遮挡、覆盖或裁切

### 5. 完整全身构图专项规则
* **完整全身构图最高优先级**：以下规则为全部5个方案不可被动作、产品展示、近景要求、构图参考或场景要求覆盖的最高优先级规则
* **完整头部强制要求**：必须保留模特完整头部，包括完整头发、头发最高点、完整头顶、完整脸部、下巴和颈部
* **头顶到脚底强制要求**：必须从模特头发/头顶最高点开始，经过完整头部、脸部、下巴、颈部、身体、服装下摆、双腿、脚踝、双脚和鞋子，直到两只鞋底最低点，全部连续、完整地呈现在画面中
* **安全边距要求**：头顶上方和鞋底下方必须保留清晰可见的安全边距，头发、头顶、脸部、下巴、脚踝、脚趾、鞋子和鞋底均不得触碰、越过或被画面边缘裁切
* **构图禁止项**：不得使用半身图、七分身图、接近全身图或任何头部、脚部不完整的构图代替完整全身图
* **机位冲突处理规则**：如果近景、动作或机位要求与完整全身构图发生冲突，必须通过拉远摄影机解决，优先保证完整头部以及头顶到脚底全部入镜，不得裁切人物
* **画面主体占比要求**：模特及服装约占画面______%的核心区域，在保持完整头顶到脚底构图的前提下，让产品主体饱满清晰，不得因人物过小而降低产品展示价值
* **构图核心目的**：在同一画面中完整展示模特、图2产品和图4鞋履，同时保证服装结构、下摆垂坠、双脚和鞋履细节清晰可辨
* **不合格判定规则**：任何未完整呈现模特头顶至脚底范围的图片，都必须直接判定为不合格并重新生成

### 6. 光影统一专项规则（防贴图感核心）
* **受光方向统一**：人物主光源方向必须与图3一致（______），人物受光面与阴影面过渡自然，并与场景投影方向匹配
* **环境光融合**：人物皮肤、服装边缘和鞋履带有图3场景中的______环境反射光，面料褶皱自然融入环境色调，边缘无抠图感
* **投影真实**：模特脚边及身下必须具有自然地面投影，投影方向、长度、颜色和软硬程度与图3场景完全一致
* **色调统一**：整体画面统一为______色调，人物、产品、鞋履和背景色温一致
* **边缘融合**：禁止出现人物边缘发光、异常轮廓光、抠图白边、绿色溢色、贴图感或悬浮感
* **空间纵深**：人物主体保持清晰，背景根据实际摄影景深自然虚化，人物与背景之间具有真实空气透视和空间层次

---

## 二、通用负面提示词（Negative Prompt，全方案共用）

Negative Prompt is script-generated and immutable. Set every action's `negative_prompt` to the unmodified result of `render_negative_prompt(view_contract, identity_contract, garment_contract)`, where `view_contract.name` is `full` and `footwear_required` comes from the active validated manifest view. Do not compose, paraphrase, reorder, trim, append, or remove negative-prompt text in this Markdown template.

---

## 三、5组正向生图提示词方案

### 【方案一：正面标准角度・自然携带与本次造型匹配的包袋】
* **四图融合逻辑说明**：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。服装颜色、版型、结构和面料严格参照图2；______场景取自图3，使用正面标准机位；鞋履颜色、款式、材质和结构严格参照图4。完整头部以及从头顶到脚底的全部范围必须清晰可见
* **模特动作设定**：根据本次服装风格和已确认的配饰/包袋来源选择合适的单手携带方式；另一只手自然放置于腰侧、胯侧或轻扶服装；双腿自然交叉或错步站立，姿态自然松弛，禁止站军姿和双手同时垂下

**中文提示词：**

根据以上图像分析生成一段完整、可独立执行的中文提示词。必须清晰说明 IDENTITY MODEL SOURCE 仅控制身份、本视角 POSE/COMPOSITION SOURCE 仅控制姿势/裁切/身体方向/构图，以及图2产品、图3场景和图4鞋履之间的融合关系，并准确写出模特、服装、鞋履、动作、场景、光源方向、环境反射、地面投影和整体色调。必须完整保留模特头部，画面从头发/头顶最高点连续呈现至两只鞋底最低点，头顶上方与鞋底下方保留安全边距，人物任何部位均不得被裁切。如果动作或机位与完整全身构图冲突，必须拉远摄影机。

输出参数：4K像素，2:3尺寸比例，模型：nano banana pro

---

**英文提示词：**

Generate one complete and independently executable English prompt. Clearly explain the fusion of the IDENTITY MODEL SOURCE from 正面/1.jpg, the local POSE/COMPOSITION SOURCE, PRODUCT SOURCE, SCENE SOURCE and SHOES ACCESSORY SOURCE.  Accurately describe the model, garment, footwear, action, scene, lighting direction, environmental reflection, ground shadow and color temperature. MANDATORY COMPLETE FULL-BODY FRAMING — HIGHEST PRIORITY: Show the model's complete head and entire body continuously inside the frame, from the highest point of the hair and top of the head to the lowest point of both feet and shoe soles. The complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, toes, shoes and soles must all be fully visible. Leave clear visible safety margin above the hair and below the footwear. No body part may touch, cross or be cropped by any image edge. If the pose or camera distance conflicts with this requirement, move the camera farther away. Nano Banana Pro, 4K, 2:3. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `FULL-BODY HEAD COMPLETION:` Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

---

### 【方案二：正面偏左微侧角度・自然调整包袋或配饰】
* **四图融合逻辑说明**：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2是服装款式和结构的唯一标准，微侧机位同时展示产品正面廓形与轻微侧面垂坠；图3控制场景、光影和环境色；图4控制鞋履。身体向左偏转约15°至20°，脸部转回朝向镜头，完整头部以及从头顶到脚底的全部范围必须清晰可见
* **模特动作设定**：根据本次造型和已确认的配饰/包袋来源决定是否单肩携带包袋；一只手自然调整包带、配饰或轻扶腰胯，另一只手弯曲形成自然动作；重心落在一条腿上，双手不得同时垂下

**中文提示词：**

根据以上图像分析生成一段完整、可独立执行的中文提示词。必须说明 IDENTITY MODEL SOURCE 仅控制身份、本视角 POSE/COMPOSITION SOURCE 仅控制姿势/裁切/身体方向/构图，以及图2产品、图3场景和图4鞋履之间的融合关系。身体向左微侧约15°至20°且不得超过20°，脸部朝向镜头。必须完整呈现头发最高点、头顶、完整脸部、身体、服装下摆、双脚和鞋底，并在头顶与鞋底外保留安全边距；任何人物部位均不得被裁切。

输出参数：4K像素，2:3尺寸比例，模型：nano banana pro

---

**英文提示词：**

Generate one complete and independently executable English prompt. Clearly define the IDENTITY MODEL SOURCE from 正面/1.jpg, local POSE/COMPOSITION SOURCE, PRODUCT SOURCE, SCENE SOURCE and SHOES ACCESSORY SOURCE.  Show the model at a slight left-facing angle of approximately 15 to 20 degrees, with the face turned toward the camera. MANDATORY COMPLETE FULL-BODY FRAMING — HIGHEST PRIORITY: Show the complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, toes, shoes and soles continuously inside the frame. Leave clear safety margin above the hair and below the footwear. No body part may touch or cross any image edge. Move the camera farther away rather than crop the model. Nano Banana Pro, 4K, 2:3. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `FULL-BODY HEAD COMPLETION:` Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

---

### 【方案三：正面稍近完整全身角度・不拿任何包包】
* **四图融合逻辑说明**：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。产品颜色、版型、领口、袖型、长度、面料和装饰严格参照图2；图3场景可适度虚化以突出产品，但不得替换背景；鞋履严格参照图4。虽然使用稍近机位，仍必须通过调整摄影机距离保证完整头部以及从头顶到脚底的全部范围清晰可见
* **模特动作设定**：不得携带任何包包；一只手可轻触发丝、耳侧、项链或领口附近，另一只手轻搭服装侧面、腰胯或下摆；双腿自然站立或轻微错步，姿态精致自然

**中文提示词：**

根据以上图像分析生成一段完整、可独立执行的中文提示词。突出图2产品的领口、面料、袖口、装饰、廓形和下摆细节，同时准确融合 IDENTITY MODEL SOURCE 的身份、本视角 POSE/COMPOSITION SOURCE 的姿势/裁切/身体方向/构图、图3场景和图4鞋履。模特不得携带任何包包。稍近机位不得造成头部、脚部或鞋履裁切；必须完整呈现从头顶最高点到鞋底最低点的全部范围，并保留上下安全边距。

输出参数：4K像素，2:3尺寸比例，模型：nano banana pro

---

**英文提示词：**

Generate one complete and independently executable English prompt. Emphasize the PRODUCT SOURCE neckline, fabric, sleeves, decorative details, silhouette and hem while preserving the IDENTITY MODEL SOURCE from 正面/1.jpg, local POSE/COMPOSITION SOURCE, SCENE SOURCE and SHOES ACCESSORY SOURCE.  The model must carry no bag. MANDATORY COMPLETE FULL-BODY FRAMING — HIGHEST PRIORITY: Show the complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, toes, shoes and soles continuously inside the frame with visible safety margins. A closer camera position is allowed only when the complete head-to-toe framing remains intact. Nano Banana Pro, 4K, 2:3. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `FULL-BODY HEAD COMPLETION:` Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

---

### 【方案四：右侧微侧角度・自然携带与本次造型匹配的包袋】
* **四图融合逻辑说明**：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2控制服装正面结构与右侧垂坠关系；图3控制同一场景的右侧微侧机位、光影和环境色；图4控制鞋履。身体向右偏转约20°至25°且不得超过30°，脸部保持朝向镜头，完整头部以及从头顶到脚底的全部范围必须清晰可见
* **模特动作设定**：根据本次造型和已确认的配饰/包袋来源决定是否手提或挎包；另一只手轻扶服装侧面、腰胯或袖口；身体重心放在后腿或单腿，姿态自然松弛，双手不得同时垂下

**中文提示词：**

根据以上图像分析生成一段完整、可独立执行的中文提示词。必须说明 IDENTITY MODEL SOURCE 仅控制身份、本视角 POSE/COMPOSITION SOURCE 仅控制姿势/裁切/身体方向/构图，以及图2产品、图3场景和图4鞋履之间的融合关系。右侧微侧机位同时展示产品正面结构和侧面垂坠，身体向右偏转约20°至25°且不得超过30°，脸部朝向镜头。完整头部、身体、服装下摆、双脚及鞋底必须全部位于画面内，并保留上下安全边距。

输出参数：4K像素，2:3尺寸比例，模型：nano banana pro

---

**英文提示词：**

Generate one complete and independently executable English prompt. Clearly explain the fusion of the IDENTITY MODEL SOURCE from 正面/1.jpg, local POSE/COMPOSITION SOURCE, PRODUCT SOURCE, SCENE SOURCE and SHOES ACCESSORY SOURCE.  Show the model at a slight right-facing angle of approximately 20 to 25 degrees and never more than 30 degrees, with the face toward the camera. MANDATORY COMPLETE FULL-BODY FRAMING — HIGHEST PRIORITY: Keep the complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, toes, shoes and soles continuously inside the frame with visible safety margins. Never crop the model. Nano Banana Pro, 4K, 2:3. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `FULL-BODY HEAD COMPLETION:` Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

---

### 【方案五：左侧微侧角度・不拿任何包包】
* **四图融合逻辑说明**：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2控制产品正面结构和左侧垂坠；图3控制同一场景的左侧微侧机位、环境光和投影；图4控制鞋履。身体向左偏转约25°至30°且不得超过30°，脸部保持朝向镜头，完整头部以及从头顶到脚底的全部范围必须清晰可见
* **模特动作设定**：不得携带任何包包；一只手轻扶领口、项链、袖口或上身产品细节，另一只手轻搭服装侧面、腰胯或下摆；双腿自然错步，姿态优雅自然，禁止双手同时垂下

**中文提示词：**

根据以上图像分析生成一段完整、可独立执行的中文提示词。必须说明 IDENTITY MODEL SOURCE 仅控制身份、本视角 POSE/COMPOSITION SOURCE 仅控制姿势/裁切/身体方向/构图，以及图2产品、图3场景和图4鞋履之间的融合关系。左侧微侧机位展示产品正面结构和侧面垂坠，身体向左偏转约25°至30°且不得超过30°，脸部朝向镜头。模特不得携带任何包包。必须完整呈现头发最高点、完整头部、脸部、身体、服装下摆、双脚、鞋子和鞋底，并保留上下安全边距。

输出参数：4K像素，2:3尺寸比例，模型：nano banana pro

---

**英文提示词：**

Generate one complete and independently executable English prompt. Clearly explain the fusion of the IDENTITY MODEL SOURCE from 正面/1.jpg, local POSE/COMPOSITION SOURCE, PRODUCT SOURCE, SCENE SOURCE and SHOES ACCESSORY SOURCE.  Show the model at a slight left-facing angle of approximately 25 to 30 degrees and never more than 30 degrees, with the face toward the camera. The model must carry no bag. MANDATORY COMPLETE FULL-BODY FRAMING — HIGHEST PRIORITY: Keep the complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, toes, shoes and soles continuously inside the frame with visible safety margins. Never crop the model. Nano Banana Pro, 4K, 2:3. `FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.` `IDENTITY LOCK:` canonical_source=正面/1.jpg; head_visibility=<active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile. `FULL-BODY HEAD COMPLETION:` Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics. `GARMENT FRAME LOCK:` Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.

---

## 四、提示词使用说明
- 方案一、方案二、方案三为正面或接近正面的展示角度；
- 方案四为右侧约20°至25°微侧角度，身体偏转不得超过30°；
- 方案五为左侧约25°至30°微侧角度，身体偏转不得超过30°；
- 方案三和方案五明确不携带任何包包；
- 其他方案是否携带包袋，应根据已确认的配饰/包袋来源和本次产品风格决定；任何包袋均不得放在地面；
- 五张图的动作、手部姿势、身体重心、拍摄距离和机位角度必须具有明显差异；
- 五张图只能在图3同一场景中进行多角度延展，背景核心元素必须保持一致；
- 中文融合说明必须明确：IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份。图2控制产品结构，图3控制场景与光影，图4控制鞋履；
- 所有方案均必须为完整全身图，从头发/头顶最高点连续呈现至两只鞋底最低点，头顶上方与鞋底下方保留安全边距；
- 头发、头顶、脸部、下巴、脚踝、脚趾、鞋子和鞋底均不得触碰、越过或被画面边缘裁切；
- 如果动作、近景或机位与完整全身构图冲突，必须拉远摄影机；任何未完整呈现头顶至脚底范围的图片都必须判定为不合格；
- 所有方案统一使用2:3比例、4K画质和Nano Banana Pro模型；
- 每个动作的 Negative Prompt 必须直接使用 `render_negative_prompt` 的 script-generated and immutable 返回值；
- 画面中禁止出现文字、logo、水印、签名、拼图、多画面、多人、贴图白边、异常轮廓光、抠图痕迹、站军姿、双手同时垂下、头部裁切或脚部裁切。
