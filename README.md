# 我会永远陪着你

`astrbot_plugin_private_companion` 是一个面向 AstrBot 私聊场景的主动陪伴插件。它会为 Bot 建立连续的生活状态、日程、梦境、日记、重要日期、关系记忆和低频主动消息，让 Bot 不只是被动回答，而是像一个有自己生活节奏的私聊伙伴。

- 插件名：`astrbot_plugin_private_companion`
- 当前版本：`2.0.0`
- 适配平台：`aiocqhttp`
- AstrBot 版本：`>=4.22.0`
- 编码要求：UTF-8

## 功能简介

本插件的核心目标是“自然陪伴”，不是固定模板刷存在感。它会根据用户最近互动、当天状态、日程、天气、梦境、日记和关系状态，判断什么时候适合轻轻发一句、什么时候应该安静。

主要能力：

- 私聊主动陪伴：按每日上限、最小间隔、免打扰时间、用户活跃度和关系状态决定是否主动开口。
- 拟人生活状态：维护睡眠、梦境、体力、心情、饥饿、身体小状态、天气和当前位置感。
- 今日日程：每天生成从起床到睡前的生活框架。
- 当前细化：临近时间段时，把粗日程展开成具体细节、状态变量和主动契机。
- 梦境与日记：生成完整梦境、梦境碎片和日记，让第二天有自然残留。
- 重要日期：记录生日、纪念日、考试、约定等日期，并影响主动话题。
- 陪伴记忆：记录称呼、偏好、边界、共同经历、未完成话头和关系线索。
- 回复质感增强：回复前规划、情绪意图识别、表达学习、话题抑制和回复自检。
- 群聊观察：在允许的群内学习群气氛、黑话、群友轻画像、话题线和关系网。
- 多能力主动行为：可选使用文字、图片、语音、戳一戳、轻窥屏、正在输入和 QQ 状态同步。
- 插件扩展页：在 AstrBot WebUI 中查看和管理私聊、群聊、记忆、额度和能力开关。

常用命令：

```text
陪伴 状态
陪伴 查看主动判定
陪伴 生成状态
陪伴 查看今日日程
陪伴 重置日程
陪伴 当前细化
陪伴 梦境
陪伴 日记
陪伴 日期列表
陪伴 日期添加 <标题> <YYYY-MM-DD或MM-DD> [备注]
陪伴 昵称 <称呼>
陪伴 语气 温柔|活泼|工作
陪伴 长期记忆
陪伴 能力列表
```

群聊命令：

```text
陪伴群 状态
陪伴群 黑话
陪伴群 群友
陪伴群 话题
陪伴群 片段
陪伴群 插话反馈
陪伴群 关系网
陪伴群 开启
陪伴群 关闭
```

## 安装方式

### 方式一：AstrBot 插件市场安装

在 AstrBot WebUI 的插件市场中搜索：

```text
astrbot_plugin_private_companion
```

安装后重启 AstrBot，并进入插件配置页填写目标用户和模型配置。

### 方式二：从 GitHub 安装

在 AstrBot WebUI 中进入“插件管理”，选择从 Git 安装，填写仓库地址：

```text
https://github.com/menglimi/astrbot_plugin_private_companion
```

### 方式三：手动安装

将插件目录放入 AstrBot 插件目录，并确保目录名为：

```text
astrbot_plugin_private_companion
```

Windows 常见路径：

```text
C:\Users\你的用户名\.astrbot\data\plugins\astrbot_plugin_private_companion
```

安装完成后重启 AstrBot。

### 最小配置

首次使用建议至少配置：

- `target_user_ids`：需要启用私聊陪伴的 QQ 号。
- `target_platform`：目标平台，通常为 QQ/aiocqhttp 对应平台。
- `LLM_PROVIDER_ID`：主模型 Provider。
- `max_daily_messages`：每日主动消息上限。
- `idle_minutes`：用户空闲多久后才允许主动。
- `min_interval_minutes`：两次主动之间的最小间隔。
- `quiet_hours`：免打扰时间。

`target_user_ids` 中的用户会在插件启动时自动初始化私聊陪伴，不需要额外发送开启命令。

## 可选联动

下面这些插件或服务不是必需项。没有安装时，本插件会自动跳过对应能力或回退成普通文字。若存在 `menglimi` 维护版，建议优先使用 `menglimi` 版本，和本插件的联动适配通常更完整。

### 屏幕陪伴

- 用途：支持主动 `screen_peek` 轻窥屏、屏幕状态上下文、天气能力回退。
- 首选仓库：<https://github.com/menglimi/astrbot_plugin_screen_companion>
- 对应配置：`enable_screen_glance_action`、`screen_peek_max_daily`、`screen_peek_cooldown_minutes`

### TTS 语音

- 用途：支持主动 `voice` 短语音，并兼容 `<tts>...</tts>`、日语、双语或特殊 TTS 人格规则。
- 首选仓库：<https://github.com/menglimi/astrbot_plugin_tts_modify-fishaudio->
- 原始仓库：<https://github.com/L1ke40oz/astrbot_plugin_tts_modify>
- 对应配置：`enable_voice_action`、`voice_action_max_chars`

### ComfyUI 生图

- 用途：支持主动 `photo_text` 图片分享，可根据日程、梦境、当前场景生成图片。
- AstrBot ComfyUI 插件仓库：<https://github.com/cjxzdzh/astrbot_plugin_comfyui>
- ComfyUI 官方仓库：<https://github.com/comfyanonymous/ComfyUI>
- 对应配置：`enable_photo_text_action`、`photo_generation_backend`、`COMFYUI_TEXT2IMG_WORKFLOW_NAME`、`COMFYUI_SELFIE_WORKFLOW_NAME`

如果不使用 ComfyUI，也可以配置外部图片 API：

- `EXTERNAL_IMAGE_API_BASE_URL`
- `EXTERNAL_IMAGE_API_KEY`
- `EXTERNAL_IMAGE_API_MODEL`
- `external_image_api_size`

### 戳一戳

- 用途：支持主动 `poke`，或在部分主动消息前先轻轻戳一下。
- 可用仓库：<https://github.com/Zhalslar/astrbot_plugin_pokepro>
- 对应配置：`enable_poke_action`、`poke_action_max_times`

### LivingMemory 长期记忆

- 用途：提供大规模长期记忆、向量检索、图谱记忆和 `recall_long_term_memory` 工具。
- 可用仓库：<https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory>
- 对应配置：`enable_livingmemory_integration`、`livingmemory_tool_name`

本插件不会重复实现 LivingMemory 的向量库能力。检测到 LivingMemory 后，本插件会把“何时需要召回长期记忆”的判断注入给模型，同时继续负责生活状态、主动行为、关系站位和群聊隐私边界。

## 扩展页介绍

本插件提供 AstrBot 官方 Pages 扩展页：

```text
pages/陪伴面板/
```

如果当前 AstrBot 版本支持 `context.register_web_api()`，插件会注册后端接口：

```text
/astrbot_plugin_private_companion/page/*
```

扩展页主要用于把“看不见的陪伴状态”可视化：

- 总览私聊对象、群聊观察、名单模式和 LivingMemory 状态。
- 查看单个私聊用户的启用状态、称呼、语气、关系状态、今日主动计数和下次主动候选。
- 查看用户记忆、对话片段、未完成话头、主动计划和能力额度。
- 查看群气氛、黑话、话题线、群聊片段、插话反馈和关系网摘要。
- 启停单个私聊或群聊对象。
- 保存用户称呼、语气、名单配置和关键功能开关。
- 重置今日额度、清空主动计划或清空学习记忆。
- 配置分项模型 Provider，例如回复自检、关系分析、记忆整理、群聊黑话释义和生图提示词模型。

扩展页适合用来排查“为什么她今天没有主动来找我”“群聊上下文有没有学到”“图片/语音/识屏额度是否用完”等问题。

## 实现原理

插件由几层状态和决策链组成。

### 1. 用户状态层

每个目标用户都有独立状态，包括：

- 是否启用陪伴。
- 昵称和语气偏好。
- 今日主动次数和最近主动时间。
- 最近用户消息和最近陪伴消息。
- 关系分数、关系状态和忽略次数。
- 记忆、表达学习、对话片段和未完成话头。
- 图片、识屏等主动能力的每日额度。

这些状态会持久化保存，重启后继续延续。

### 2. 生活模拟层

每天会生成或维护：

- 拟人状态。
- 今日日程。
- 当前时间段细化。
- 梦境和梦境碎片。
- 日记。
- 重要日期。
- 昨日完整对话摘要。

日程不是简单模板，而是参考日期、天气、人格、状态、记忆、昨日对话和重要日期后生成。当前细化只负责当前时间段，让 Bot 的“正在做什么”随时间推进。

### 3. 主动判定层

主动消息发送前会经过多重限制：

- 插件和用户是否启用。
- 是否达到候选主动时间。
- 是否超过每日主动上限。
- 是否处于免打扰时间。
- 用户是否刚刚活跃。
- 距离上次主动是否过近。
- 当前日程是否适合开口。
- 关系状态是否需要后退。
- 目标能力是否可用。

只有条件满足时，才会进入主动内容生成。

### 4. 主动内容层

主动内容生成时会明确告诉模型：这是 Bot 主动开口，不是用户刚刚发来消息。历史对话只作为关系和话题背景，不能误当作当前用户输入。

模型会先判断这次更适合：

- 普通文字。
- 图片加一句话。
- 轻窥屏后再说。
- 短语音。
- 戳一戳。
- 组合动作。

执行层会再次检查能力可用性和额度，避免模型想用但实际不能用。

### 5. 回复增强层

用户主动来聊时，插件会在 AstrBot 原人格之外补充私聊陪伴上下文：

- 用户关系站位。
- 当前生活状态。
- 今日细化场景。
- 用户记忆和未完成话头。
- 表达节奏参考。
- 情绪意图判断。
- LivingMemory 召回提示。

回复后还会做自检，减少助手腔、长篇结构化、内部状态泄露和重复关心。

### 6. 群聊观察层

群聊层默认按白名单或黑名单工作。它会静默学习群内公开信息，包括：

- 常见词和黑话。
- 群友轻画像。
- 当前气氛。
- 话题线。
- 群聊片段。
- 插话反馈。
- 群友关系网。

群聊上下文与私聊记忆隔离。插件不会把私聊关系、私下称呼或私人记忆带进群聊。

## 常见问题

### 为什么没有主动发消息？

先发送：

```text
陪伴 查看主动判定
```

重点检查：

- `target_user_ids` 是否包含当前用户。
- `max_daily_messages` 是否已经用完。
- 当前时间是否处于 `quiet_hours`。
- 用户是否刚刚发过消息，还没有达到 `idle_minutes`。
- 距离上次主动是否小于 `min_interval_minutes`。
- 用户状态是否被暂停，或关系状态处于回退。
- 主动计划是否被清空后还没重新安排。

### 为什么图片没有发出来？

检查：

- `enable_photo_text_action` 是否开启。
- `photo_generation_backend` 是否设置正确。
- ComfyUI 插件或外部图片 API 是否可用。
- 工作流名称是否填写。
- `photo_action_max_daily` 是否达到上限。
- 当前平台是否支持发送本地图片。

注意：`photo_action_max_daily = 0` 表示不限制，不是禁用。

### 为什么识屏没有触发？

检查：

- 是否安装并启用 `astrbot_plugin_screen_companion`。
- `enable_screen_glance_action` 是否开启。
- `screen_peek_max_daily` 是否大于 0。
- 是否仍在 `screen_peek_cooldown_minutes` 冷却中。
- 屏幕陪伴插件是否能正常执行 `_invoke_screen_skill`。

### 为什么语音没有触发？

检查：

- `enable_voice_action` 是否开启。
- 当前会话是否配置可用 TTS provider。
- 如果使用 `<tts>...</tts>` 规则，是否安装了兼容的 `tts_modify` 版本。
- `voice_action_max_chars` 是否过短，导致文本被裁剪得不自然。

### 为什么戳一戳失败？

检查：

- 是否安装 `astrbot_plugin_pokepro`。
- `enable_poke_action` 是否开启。
- 当前平台和适配器是否支持 QQ 戳一戳。
- Bot 是否能正确拿到目标 QQ 号和客户端对象。

### 为什么群聊没有学习上下文？

检查：

- `enable_group_companion` 是否开启。
- 当前群是否在 `group_whitelist_ids` 中，或是否被 `group_blacklist_ids` 排除。
- `group_access_mode` 是否符合预期。
- `enable_group_context_injection` 是否开启。
- 群内消息是否足够多。

### 会不会刷屏？

正常配置下不会。插件有每日主动上限、最小间隔、免打扰时间、用户活跃检测、关系状态回退和能力额度。建议一开始把 `max_daily_messages` 设为 2 到 5，稳定后再调整。

### 会不会泄露私聊记忆到群里？

设计上会尽量避免。私聊记忆和群聊观察分层处理，群聊只使用当前群公开上下文。启用 LivingMemory 协同时，群聊也只提示召回当前群相关记忆。

### 可以只用文字，不开图片语音识屏吗？

可以。图片、语音、识屏、戳一戳、QQ 状态同步都是可选能力。不开启时，插件仍能完成日程、状态、记忆、被动回复增强和普通文字主动陪伴。

## 开发者信息

- 开发者：`menglimi`
- 插件仓库：<https://github.com/menglimi/astrbot_plugin_private_companion>
- 插件版本：`2.0.0`
- 主要文件：
  - `main.py`：插件主体、主动判定、回复注入、能力执行。
  - `planning.py`：日程与规划相关逻辑。
  - `dreaming.py`：梦境生成与梦境碎片。
  - `page_api.py`：扩展页后端 API。
  - `pages/陪伴面板/`：扩展页前端。
  - `_conf_schema.json`：AstrBot 配置项。
  - `metadata.yaml`：插件元数据。

本插件面向长期私聊陪伴体验，建议在测试新能力时先降低主动频率，并优先确认文字、日程、状态和记忆稳定后，再逐步开启图片、语音、识屏等真实外部动作。

