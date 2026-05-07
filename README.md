# 我会永远陪着你

astrbot_plugin_private_companion 是面向 AstrBot 私聊场景的主动陪伴插件。它会让 bot 拥有连续的拟人状态、每天的生活日程、重要日期、日记和低频主动消息。插件的目标不是刷屏,而是让 bot 像一个有自己生活节奏的人一样,在合适的时候轻轻出现一下。

灵感与使用风格参考“我会一直看着你”插件,更偏向长期陪伴、生活连续性和 live2D 桌宠式体验。和识屏插件不同,本插件主要关注私聊关系、日程状态和主动开口。

如果喜欢的话请给个 star 吧。

## 版本

当前版本：`1.0.0`

`1.0.0` 主要整理了私聊主动陪伴的核心体验：拟人状态、日程生活感、主动消息预约、主动消息写回 AstrBot 会话历史、主动回复上下文注入、分段发送、装饰钩子兼容和可选外部插件联动。

## 主要功能

- 私聊主动陪伴：按空闲时间、每日上限、免打扰和关系状态低频主动开口。
- 拟人化状态：每天生成心理能量、情绪底色、睡眠、梦境、健康、饥饿、周期和叠加状态。
- 强化梦境：可选使用单独模型，把最近记忆、日程碎片、天气和重要日期拼成欠逻辑的梦境状态，失败时会自动回退到默认梦境池。
- 生活日程：每天生成 bot 自己的生活日程,被动回复和主动消息都会参考当前日程段。
- 状态连续性：状态会延续、恢复、转移,不是每次启动都像完全重置。
- 生活日记：每天生成 bot 自己的小日记,用于后续状态和生活线索延续。
- 重要日期：记录生日、纪念日、约定和其他日期,临近时可影响回复与主动分享。
- 主动消息预约：支持 LLM 在隐藏 `<timer>` 标签里预约下一次主动开口。
- 主动上下文承接：主动消息会写入 AstrBot 会话历史；用户之后回复时也会注入“你在几点主动发了什么”。
- 被动状态注入：普通私聊回复前会注入当前状态和当前生活背景,但不会把空状态硬塞进去。
- 主动发送链路：支持 AstrBot 装饰钩子、精确平台发送、平台状态预检和发送失败回退。
- 分段发送：可选把短主动文本按正则或分段词拆成多条,并按随机或字数对数间隔发送。
- 可选主动行为：支持发图、看屏幕、戳一戳和语音等行为；缺少依赖时会自动跳过。

## 运行环境

本插件主要面向 AstrBot 私聊场景。推荐环境：

- Windows
- macOS
- Linux

额外说明：

- 需要 AstrBot `>=4.22.0`。
- 主动私聊需要平台适配器支持通过 `unified_msg_origin` 发私聊消息。
- 如果需要主动生图,可以额外配置 ComfyUI 工作流,也可以配置一套 OpenAI 兼容的在线图片 API 作为替代或兜底。
- 如果需要主动看屏幕,需要安装并配置“我会一直看着你”插件。
- 如果需要戳一戳,需要对应 poke 插件和平台能力可用。
- 如果需要语音,需要当前会话有可用 TTS provider。

## 安装

1. 将插件目录放入 AstrBot 插件目录,例如：

```text
C:\Users\你的用户名\.astrbot\data\plugins\astrbot_plugin_private_companion
```

2. 确认目录名就是：

```text
astrbot_plugin_private_companion
```

3. 重启 AstrBot。

4. 在配置页至少确认这些基础配置：

```text
enabled
target_user_ids
target_platform
max_daily_messages
idle_minutes
min_interval_minutes
quiet_hours
LLM_PROVIDER_ID
PHOTO_PROMPT_PROVIDER_ID
```

如果 `target_user_ids` 填了 QQ 号,插件启动时会自动为这些目标开启主动陪伴；也可以在私聊里手动发送 `陪伴 开启`。

## 快速开始

1. 在配置页填写 `target_user_ids` 和 `target_platform`。
2. 确认 `max_daily_messages` 不为 0。
3. 私聊发送 `陪伴 状态`,确认目标已启用。
4. 发送 `陪伴 生成状态` 和 `陪伴 生成日程`,让今天的状态和生活日程先生成出来。
5. 发送 `陪伴 查看提示词 回复注入`,检查被动回复前会注入哪些状态和当前日程。
6. 发送 `陪伴 查看主动判定`,查看当前是否满足主动消息条件。
7. 需要测试主动生成时,使用 `陪伴模拟唤醒 <想模拟的用户消息>`。

## 指令总览

下面指令主要在私聊中使用：

### 开关与状态

- `陪伴 开启`：开启当前私聊的主动陪伴。
- `陪伴 关闭`：关闭当前私聊的主动陪伴。
- `陪伴 状态`：查看插件启用状态、今日发送数、下次候选时间和关系概况。
- `陪伴 查询状态`：查看今天完整拟人状态。
- `陪伴 拟人状态`：同上,查看今日身体/情绪状态。
- `陪伴 刷新状态`：重新生成今天的拟人状态,并清空当天日程等待重建。
- `陪伴 梦境`：查看最近一次梦境、梦后余韵和残留碎片。
- `陪伴 梦境碎片`：查看当前梦境碎片池及权重衰减情况。
- `陪伴 查看主动判定`：查看当前为什么能或不能主动发送。
- `陪伴 重置插件`：清空插件状态并重新初始化。

### 日程、日记与细化

- `陪伴 日程`：查看今天日程。
- `陪伴 生成日程`：重新生成今天日程。
- `陪伴 当前细化`：查看当前时间段已经落地的完整细化结果。
- `陪伴 细化`：查看或触发当前日程段细节强化。
- `陪伴 日记`：查看最近 bot 日记。
- `陪伴 生成日记`：补写或刷新今天日记。

### 提示词检查

- `陪伴 查看提示词 日程`：查看日程生成提示词。
- `陪伴 查看提示词 细化`：查看细节强化提示词。
- `陪伴 查看提示词 主动`：查看主动消息生成提示词。
- `陪伴 查看提示词 回复注入`：查看被动回复前注入的状态、当前日程和主动上下文。
- `陪伴 完整测试`：临时抽一个日程段做真实主动链测试，并把这一段压成每两分钟一条的完整发送流程。
- `陪伴 结束完整测试`：手动结束当前完整测试。

说明：
- `戳一戳` 不再作为单独主动事件存在。
- 如果启用了 poke 联动，bot 会在合适的主动消息发送前，低概率先轻轻戳 0 到 3 下，再接正文。

### 长期信息

- `陪伴 日期列表`：查看重要日期。
- `陪伴 日期添加 <标题> <YYYY-MM-DD或MM-DD> [备注]`：添加重要日期。
- `陪伴 日期删除 <标题关键词>`：删除重要日期。
- `陪伴 可以 <Bot 能做的事>`：添加 bot 可做事项。
- `陪伴 不能 <不希望 Bot 做的事>`：移除或禁止某类可做事项。
- `陪伴 可做事项`：查看当前可做事项。

### 个人偏好

- `陪伴 昵称 <称呼>`：设置 bot 对你的称呼。
- `陪伴 语气 温柔|活泼|工作`：设置主动消息基础语气。
- `陪伴 画像`：查看关系画像、回复率和打扰倾向。
- `陪伴 清空记忆`：清空当前用户的陪伴设置和轻量记忆。

### 测试

- `陪伴模拟唤醒 <想模拟的用户消息>`：用当前会话和人格模拟一次被动唤醒。

## 推荐关注的配置项

### 基础主动陪伴

- `enabled`
- `target_user_ids`
- `target_platform`
- `default_enable_configured_targets`
- `max_daily_messages`
- `idle_minutes`
- `min_interval_minutes`
- `quiet_hours`
- `allow_insomnia_night_message`

### 状态与生活感

- `enable_humanized_states`
- `humanized_state_intensity`
- `inject_passive_states`
- `enable_daily_plan`
- `daily_plan_time`
- `daily_plan_item_count`
- `schedule_persona_prompt`
- `schedule_worldview_prompt`
- `enable_daily_diary`
- `daily_diary_time`
- `enable_detail_enhancement`
- `enable_enhanced_dreams`
- `DREAM_PROVIDER_ID`

### 主动消息与上下文

- `enable_llm_proactive_message`
- `proactive_prompt_template`
- `enable_llm_timer_scheduling`
- `proactive_reply_context_hours`
- `enable_proactive_decorating_hooks`
- `enable_precise_platform_send`
- `max_proactive_plan_lag_minutes`
- `PHOTO_PROMPT_PROVIDER_ID`

### 分段发送

- `enable_segmented_proactive_reply`
- `segmented_proactive_threshold`
- `segmented_proactive_split_mode`
- `segmented_proactive_regex`
- `segmented_proactive_split_words`
- `enable_segmented_proactive_content_cleanup`
- `segmented_proactive_content_cleanup_rule`
- `segmented_proactive_interval_method`
- `segmented_proactive_interval_min`
- `segmented_proactive_interval_max`
- `segmented_proactive_log_base`

### 可选联动

- `enable_weather_context`
- `weather_api_key`
- `weather_city`
- `weather_lat`
- `weather_lon`
- `enable_photo_text_action`
- `enable_screen_glance_action`
- `enable_poke_action`
- `enable_voice_action`
- `PHOTO_PROMPT_PROVIDER_ID`
- `photo_generation_backend`
- `COMFYUI_TEXT2IMG_WORKFLOW_NAME`
- `COMFYUI_SELFIE_WORKFLOW_NAME`
- `EXTERNAL_IMAGE_API_BASE_URL`
- `EXTERNAL_IMAGE_API_MODEL`

## 强化梦境说明

默认情况下，梦境仍然会从内置梦境池里随机抽取一条轻量状态；如果你希望梦更像“把最近生活残片拼起来的一段欠逻辑回放”，可以开启：

- `enable_enhanced_dreams`
- `DREAM_PROVIDER_ID`
- `dream_afterglow_mode`

开启后，插件会优先收集这些碎片来生成梦境：

- 最近几条 bot 日记
- 当天日程和 message seed
- 可做事项
- 近期重要日期
- 天气信息

然后随机挑一个梦境主题，比如：

- 日常错位
- 追赶感
- 空间迷路
- 温柔回放
- 轻微奇幻
- 物品变形

最后交给单独模型生成一句梦境状态描述，并产出梦境情绪、能量影响和持续时间。梦醒后的余韵也会轻量带到第二天前半段，比如更柔和一点、恍惚一点，或者留下一点不安。

建议：

- 留空 `DREAM_PROVIDER_ID` 时，会回退使用每日模型/默认模型。
- `dream_afterglow_mode` 默认为 `auto`，会根据梦的内容和强度自动调节余韵；如果想更淡或更明显，可以改成 `轻`、`标准`、`明显`。
- 如果想控制成本，可以给梦境单独配一个便宜、擅长短文本和 JSON 输出的模型。
- 强化梦境更适合做“早晨刚醒时残留的一点梦感”，不建议把它写得太长、太完整。

## 可选联动说明

### 天气

插件优先使用自己的 OpenWeatherMap 配置。如果没有配置,会尝试复用“我会一直看着你”插件的天气能力。两边都不可用时,只是不注入天气。

### 主动看屏幕

依赖 `astrbot_plugin_screen_companion`。启用后,bot 可能在合适动机下轻轻看一眼屏幕,把结果作为上下文,但会避免暴露隐私细节和完整屏幕文本。

### 主动生图 / 发图

支持两条可选后端：

- `ComfyUI`：适合本地工作流、自拍预置和更强的可控性。
- `OpenAI 兼容在线图片 API`：适合外接第三方平台在线生图,可作为替代或兜底。

如果你觉得 `photo_text` 的画面提示词太平、主体抓得不准，或者不同模型的审美差距比较明显，可以单独配置：

- `PHOTO_PROMPT_PROVIDER_ID`

它只负责生成 `photo_text` 的画面提示词和画面描述，不影响普通聊天、每日日程、日记或梦境模型。比较适合换成更擅长视觉描述、审美更稳定的模型。

通过 `photo_generation_backend` 选择：

- `auto`：优先 ComfyUI,失败或未配置时再尝试在线图片 API
- `comfyui`：只使用本地 ComfyUI
- `external`：只使用在线图片 API

在线图片 API 需要至少配置：

- `EXTERNAL_IMAGE_API_BASE_URL`
- `EXTERNAL_IMAGE_API_KEY`
- `EXTERNAL_IMAGE_API_MODEL`

插件不会在生图失败时假装已经发图。

### 戳一戳

依赖 poke 类插件和平台支持。建议默认关闭,确认平台行为符合预期后再打开。启用后它不会单独触发一整条主动事件,而是作为某些主动消息发送前的小动作前缀。

### 语音

依赖当前会话可用的 TTS provider。默认关闭,适合只在特定角色或私聊环境中开启。

## 常见问题

### 为什么 bot 没有主动发消息

优先检查：

- `陪伴 状态`
- `陪伴 查看主动判定`
- `max_daily_messages` 是否为 0
- 是否处于 `quiet_hours`
- 距离上次用户活跃是否超过 `idle_minutes`
- 距离上次主动是否超过 `min_interval_minutes`
- 当前用户是否已经 `陪伴 开启`

### 为什么回复里没有生活感

可以检查：

```text
陪伴 查看提示词 回复注入
陪伴 日程
陪伴 查询状态
```

`回复注入` 里只会显示当前状态和当前日程段,不会每次塞完整日程。如果今天还没有日程,先执行 `陪伴 生成日程`。

### 为什么主动消息没有出现在上下文里

插件会在主动发送成功后把主动消息写入 AstrBot conversation 历史。同时,用户在主动消息后一定时间内回复时,插件也会注入类似“你在 12:30 主动向用户发送了……”的上下文。可用 `陪伴 查看提示词 回复注入` 检查。

### 为什么分段没有生效

确认：

- `enable_segmented_proactive_reply` 已开启
- 文本长度没有超过 `segmented_proactive_threshold`
- 本次主动消息没有携带图片或附加组件
- 分段正则或分段词配置有效

## 隐私与安全

- 主动私聊请只对明确允许的目标开启。
- 如果启用看屏幕、生图、语音等联动,请确认对应插件和平台环境可信。
- 重要日期、日记和状态都可能包含个人信息,请只在信任的 AstrBot 环境中使用。
- 不建议把调试提示词和日志公开给不可信的人。
- 请合法使用,不要用于骚扰、监控或任何违法用途。

## 开发信息

- 开发者：menglimi（烛雨）
- QQ：995051631
- 这个插件偏长期陪伴和私聊主动性,如果遇到问题,建议先用 `陪伴 查看主动判定`、`陪伴 查看提示词 回复注入` 和 AstrBot 日志定位。
- 欢迎提交 issue 或 pull request,也欢迎分享更自然的主动陪伴配置和提示词改法。
- 给个 star 吧,谢谢。
