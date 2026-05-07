# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .constants import DEFAULT_DAILY_PLAN_ITEMS
from .helpers import _safe_int, _single_line, _today_key


def pick_detail_segment(plugin, plan: dict[str, Any], enhanced: dict[str, Any]) -> dict[str, Any] | None:
    parsed_segments = plugin._collect_detail_segments(plan, enhanced)
    if not parsed_segments:
        return None
    now_minutes = plugin._effective_plan_now_minutes(str(plan.get("date") or ""))
    if now_minutes is None:
        return parsed_segments[0] if parsed_segments else None
    lead = plugin.detail_enhancement_lead_minutes
    for segment in parsed_segments:
        start = _safe_int(segment.get("start"), 0)
        next_start = _safe_int(segment.get("end"), plugin._segment_end_minutes(start, segment.get("item")))
        in_lead = start - lead <= now_minutes <= start
        in_segment = start <= now_minutes < next_start
        if in_lead or in_segment:
            return segment
    return None


async def generate_detail_enhancement(
    plugin,
    segment: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    await plugin._ensure_weather_context()
    prompt = plugin._build_detail_enhancement_prompt(segment, plan, state)
    raw_text = await plugin._llm_call(
        prompt,
        max_tokens=700,
        provider_id=plugin.detail_enhancement_provider_id,
    )
    payload = plugin._extract_json_payload(raw_text or "")
    if not isinstance(payload, dict):
        payload = {
            "summary": "这一段按原日程慢慢推进。",
            "today_events": [],
            "proactive_events": [],
        }
    normalized = plugin._normalize_story_plan(
        {
            "today_events": payload.get("today_events", []),
            "proactive_events": payload.get("proactive_events", []),
            "long_term_events": [],
        }
    )
    normalized["summary"] = _single_line(payload.get("summary"), 160)
    return normalized


def normalize_story_plan(plugin, payload: dict[str, Any]) -> dict[str, Any]:
    today_events = plugin._normalize_story_items(payload.get("today_events"), "event")
    proactive_events = plugin._normalize_story_items(payload.get("proactive_events"), "topic")
    long_term_events = plugin._normalize_long_term_events(payload.get("long_term_events"))
    long_term_events.extend(plugin._generate_state_linked_long_term_events())
    long_term_events = plugin._dedupe_long_term_events(long_term_events)
    proactive_events.extend(plugin._generate_weather_linked_proactive_events())
    proactive_events.extend(plugin._generate_morning_linked_proactive_events())
    proactive_events.extend(plugin._generate_daypart_linked_proactive_events())
    proactive_events = plugin._dedupe_proactive_events(proactive_events)
    allowed_reasons = {
        "insomnia_night",
        "state_share",
        "quiet_care",
        "activity_share",
        "diary_share",
        "important_date_share",
        "background_schedule",
        "check_in",
        "morning_greeting",
        "noon_greeting",
        "evening_greeting",
    }
    normalized_proactive = []
    for item in proactive_events:
        reason = str(item.get("reason") or "").strip()
        if reason not in allowed_reasons:
            reason = "diary_share"
        if reason == "state_share":
            reason = "quiet_care"
        item["reason"] = reason
        action = str(item.get("action") or "message").strip()
        if action not in {"message", "screen_peek", "photo_text", "voice"}:
            action = "message"
        if action == "screen_peek" and not plugin.allow_screen_peek_action:
            action = "message"
        if action == "photo_text" and not plugin.allow_photo_text_action:
            action = "message"
        if action == "voice" and not plugin.allow_voice_action:
            action = "message"
        item["action"] = action
        item["why"] = _single_line(item.get("why"), 100)
        item["motive"] = plugin._normalize_event_motive(item)
        item["scene"] = _single_line(item.get("scene"), 60)
        item["tone"] = _single_line(item.get("tone"), 24)
        item["impulse"] = _single_line(item.get("impulse"), 80)
        if not isinstance(item.get("chain"), list):
            item["chain"] = []
        normalized_proactive.append(item)
    normalized_proactive = plugin._balance_proactive_events_for_day(normalized_proactive, limit=10)
    return {
        "date": _today_key(),
        "today_events": today_events[:8],
        "proactive_events": normalized_proactive,
        "long_term_events": long_term_events[:3],
    }


def normalize_story_items(plugin, raw_items: Any, text_key: str) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        window = _single_line(raw.get("window"), 20)
        if not re.fullmatch(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", window):
            continue
        item = {
            "window": window,
            text_key: _single_line(raw.get(text_key), 100),
            "mood": _single_line(raw.get("mood"), 30),
        }
        for key in ("reason", "why", "topic", "motive", "scene", "tone", "impulse"):
            if key in raw:
                item[key] = _single_line(raw.get(key), 100)
        if "action" in raw:
            item["action"] = _single_line(raw.get("action"), 40)
        raw_chain = raw.get("chain")
        normalized_chain = plugin._normalize_chain_steps(raw_chain)
        if normalized_chain:
            item["chain"] = normalized_chain
        items.append(item)
    return items


def normalize_long_term_events(plugin, raw_items: Any) -> list[dict[str, str]]:
    if not isinstance(raw_items, list):
        return []
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        title = _single_line(raw.get("title"), 80)
        if not title:
            continue
        items.append(
            {
                "title": title,
                "status": _single_line(raw.get("status"), 80),
                "next_hint": _single_line(raw.get("next_hint"), 100),
                "phase": _single_line(raw.get("phase"), 24),
                "tendency": _single_line(raw.get("tendency"), 60),
            }
        )
    return items


def format_plan_for_diary(plugin, plan: dict[str, Any]) -> str:
    if not isinstance(plan, dict) or not isinstance(plan.get("items"), list):
        return "（暂无）"
    lines = []
    for item in plan.get("items", [])[:6]:
        if isinstance(item, dict):
            lines.append(f"- {item.get('time', '')} {item.get('activity', '')}")
    return "\n".join(lines) if lines else "（暂无）"


async def generate_daily_plan(plugin) -> dict[str, Any]:
    today = _today_key()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    await plugin._ensure_weather_context()
    prompt = plugin._build_daily_plan_prompt(now)
    raw_text = await plugin._llm_call(prompt, max_tokens=900)
    items = plugin._parse_plan_items(raw_text or "")
    if items and plugin._plan_has_excess_micro_segments(items):
        retry_prompt = (
            prompt
            + "\n\n【额外纠偏】\n"
            + "每个日程段都应该代表一小段连续生活,而不是一个几秒钟就结束的动作。"
            + "不要把“看一眼、拍一下、翻个身、关掉闹钟”这种瞬时动作单独立成一项；"
            + "如果要写到这些动作,要把它们嵌进更完整的时段里,比如“起床后赖床一会儿,顺手看了一眼窗外”。"
        )
        retry_raw_text = await plugin._llm_call(retry_prompt, max_tokens=900)
        retry_items = plugin._parse_plan_items(retry_raw_text or "")
        if retry_items and not plugin._plan_has_excess_micro_segments(retry_items):
            raw_text = retry_raw_text
            items = retry_items
    if items and plugin._plan_has_excess_abstract_segments(items):
        retry_prompt = (
            prompt
            + "\n\n【额外纠偏】\n"
            + "减少“漂亮但空”的句子。不要只写“思绪飘忽、梦里全是模糊碎片、心情随着光线变软、脑海里闪过今天的画面”这类抽象描述；"
            + "每个日程段都先给出一个能看见的动作、位置或手边的小东西，再让情绪贴在上面。"
        )
        retry_raw_text = await plugin._llm_call(retry_prompt, max_tokens=900)
        retry_items = plugin._parse_plan_items(retry_raw_text or "")
        if retry_items and not plugin._plan_has_excess_abstract_segments(retry_items):
            raw_text = retry_raw_text
            items = retry_items
    if items and plugin._plan_conflicts_with_calendar(items):
        retry_prompt = (
            prompt
            + "\n\n【额外纠偏】\n"
            + "今天属于周末或节假日语境。除非上面的设定、重要日期或备注明确写了调休、补课、补班、考试、值班等例外，"
            + "否则不要安排上课、放学、作业、教室、食堂、上班、下班、会议这类普通工作日主线。"
        )
        retry_raw_text = await plugin._llm_call(retry_prompt, max_tokens=900)
        retry_items = plugin._parse_plan_items(retry_raw_text or "")
        if retry_items and not plugin._plan_conflicts_with_calendar(retry_items):
            raw_text = retry_raw_text
            items = retry_items
    source = "llm" if items else "fallback"
    if not items or plugin._plan_conflicts_with_calendar(items):
        items = [dict(item) for item in DEFAULT_DAILY_PLAN_ITEMS]
        raw_text = "fallback"
        source = "fallback"
    return {
        "date": today,
        "generated_at": now,
        "source": source,
        "provider_id": plugin.llm_provider_id,
        "raw": raw_text,
        "items": items,
    }


def get_schedule_planning_prompt(plugin) -> str:
    persona = plugin._get_default_persona_prompt()
    schedule_persona = plugin.schedule_persona_prompt
    worldview = plugin.schedule_worldview_prompt
    parts = []
    if schedule_persona:
        parts.append("【日程专用角色设定】\n" + schedule_persona)
    if worldview:
        parts.append("【日程专用世界观/生活背景】\n" + worldview)
    if not parts:
        parts.append("【AstrBot 默认人格（回退）】\n" + persona)
    else:
        parts.append(
            "【AstrBot 默认人格（仅作补充参考）】\n"
            + persona
            + "\n如果上面的日程专用角色设定/世界观与默认人格存在重叠,优先按日程专用内容理解生活设定；聊天时仍以 AstrBot 默认人格为准。"
        )
    return "\n\n".join(parts)


def build_daily_plan_prompt(plugin, now: str) -> str:
    custom = plugin.daily_plan_prompt
    schedule_prompt = plugin._get_schedule_planning_prompt()
    can_do_text = plugin._format_can_do_for_prompt()
    humanized_state = plugin._format_state_for_prompt(plugin.data.get("daily_state", {}))
    recent_diaries = plugin._recent_diary_context()
    weather_info = plugin._weather_summary_text(plugin.data.get("daily_weather", {}))
    calendar_context = plugin._format_calendar_context_for_prompt()
    schedule_adjustments = plugin._format_schedule_adjustments_for_prompt()
    try:
        now_dt = datetime.strptime(now, "%Y-%m-%d %H:%M")
        weekday_text = "一二三四五六日"[now_dt.weekday()]
    except Exception:
        weekday_text = ""
    weekday_hint = f"今天是星期{weekday_text}。" if weekday_text else ""
    if custom:
        return custom.format(
            now=now,
            bot_name=plugin.bot_name,
            astrbot_persona=plugin._get_default_persona_prompt(),
            schedule_persona=schedule_prompt,
            can_do=can_do_text,
            humanized_state=humanized_state,
            schedule_adjustments=schedule_adjustments,
            calendar_context=calendar_context,
            recent_diaries=recent_diaries,
            important_dates=plugin._format_important_dates_for_prompt(),
            weather_info=weather_info,
            daily_plan_item_count=plugin.daily_plan_item_count,
        )
    return f"""
现在时间：{now}
{weekday_hint}
Bot 名字：{plugin.bot_name}
日期语境：
{calendar_context}

日程生成参考设定：
{schedule_prompt}

用户允许/告诉 Bot 可以做的事情：
{can_do_text}

今天的拟人化状态：
{humanized_state}

今日互动造成的日程偏移：
{schedule_adjustments}

今天天气：
{weather_info}

最近日记：
{recent_diaries}

近期重要日期：
{plugin._format_important_dates_for_prompt()}

请为这个拟人化 Bot 生成今天的一日生活日程,让它像真实存在的人在过这一天,而不是在执行模板。日程要先像“这个人”的生活,再像“某个身份”的生活；身份只是底色,不要把它写成校园/职场通用作文。

生成时按这个优先顺序理解信息：
1. 先看日期语境：今天是普通日、周末、节假日、假期,还是有明确例外（调休、补课、考试、值班）。
2. 再看日程参考设定：年龄、身份、作息、生活背景决定今天的大主线。
3. 再看拟人状态和天气：决定节奏快慢、出门意愿、情绪收放和户外时刻。
4. 再看今日互动造成的日程偏移：它只影响当前与后续状态走向,不要重写整个人设和一天主线。
5. 最后参考可做事项、最近日记、重要日期：只拿来补充细节,不要反客为主。

【生成要求】
1. 用第三人称写 activity,像旁观这个人过日子：写「午休后靠着桌沿醒神」「傍晚出门慢慢走一段」,不要写第一人称自述、任务标签或功能词。
2. 日程主线必须跟身份一致：学生才写校园,上班族才写工作,居家或非人设定就写对应的生活节奏。可做事项只能安插在缝隙里。
3. 必须区分普通日和假期：如果今天是周末或节假日,且没有明确例外,就不要安排上课、放学、作业、教室、食堂、上班、下班、会议这类普通工作日主线。
4. 状态和天气必须真的影响安排：低能量时密度更松,困倦时上午起步更慢,天气舒服时更容易出门或看窗外。
5. 生活感来自“有选择的具体”,不是动作清单：动作要能透露她的习惯、迟疑、偏好或当天状态。不要连续堆“揉头发、系鞋带、转笔、理刘海”这类谁都能做的通用动作；每段最好有一个独属于此刻的小原因、小物件或小偏差。
6. 一天要有轻微走向：早上怎么启动,白天被什么拖住或松开,晚上为什么收声。不要只是从困倦一路写到疲惫；让情绪有一点转折、回弹或压下去的过程。
7. 如果身份是学生,校园段也要具体到“哪类课/哪件小事/哪种迟到或作业压力”,不要只写老师讲课、记笔记、食堂吃饭、数学题较劲这种默认校园模板。其他身份同理,少写职业通用动作。
8. 至少让 3 个时间点自然带出和用户的关系伏笔：可以是想起对方、忍住没发、看到某物想吐槽给对方、睡前打开对话框又删掉。关系伏笔要轻,藏在 message_seed 或 activity 末尾,不要每次直说“想你”。
9. 温柔或内敛的人设可以有烦躁、委屈、低落,但表达要收着：写成沉默、停顿、把东西放远、攥着笔、少说两句、绕开争执；不要写“想砸东西、想摔东西、想打人、报复、毁掉”这类破坏性或攻击性冲动,除非人格设定明确要求。
10. 消极状态只是当天的天气,不是身份本身。最近日记里的低落/失眠/烦躁只能作为淡淡余波,不能连续放大成全天负面；至少安排一两处回稳、松开或被用户互动带来的柔和偏移。
11. 安排 {plugin.daily_plan_item_count} 个时间点,覆盖起床到睡前；每项都要有 time、activity、mood、message_seed。
12. message_seed 是如果这一刻想顺手找用户说一句,嘴边最先冒出来的话。它可以是第一人称口语,要短,像私聊碎片；不要用它解释背景,让背景藏在语气和话题里。少一点“我突然想到你了”,多一点“刚刚那一下也太离谱了”“窗外这会儿挺好看”。
13. message_seed 也要遵守状态转译：不要写“今天状态/心情/情绪/能量怎么样”,而是写能承载状态的小画面、小吐槽、小动作或一句轻轻的问题。
14. 每个日程段都应该是一小段连续生活,而不是一个瞬时动作。不要把“看一眼、拍一下、翻个身、关掉闹钟”这种几秒钟就结束的动作单独立成一项；如果写到它们,要把它们嵌进更完整的时段里。
15. 如果多条参考信息冲突,优先服从日期语境和身份主线,再服从状态与天气,再服从今日互动偏移,最后才参考日记和可做事项。
16. 只输出 JSON,不要 Markdown,不要解释。

格式：
{{
  "schedule": [
    {{"time": "09:10", "activity": "闹钟响过以后又在被窝里赖了几分钟,看到今天是星期一才慢慢坐起来,一边找校服一边想今天第一节别又点名。", "mood": "启动困难", "message_seed": "星期一真的有点难开机。"}},
    {{"time": "17:20", "activity": "放学后没有立刻回消息,先在校门口被风吹了一会儿,看到路边水洼里反着天色,才摸出手机想拍给用户看。", "mood": "松一口气", "message_seed": "刚刚那个水洼反光还挺像电影里的。"}}
  ]
}}
""".strip()


def build_detail_enhancement_prompt(
    plugin,
    segment: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
) -> str:
    item = segment.get("item") if isinstance(segment, dict) else {}
    previous_item = segment.get("previous_item") if isinstance(segment, dict) else {}
    next_item = segment.get("next_item") if isinstance(segment, dict) else {}
    start_text = plugin._minutes_to_hhmm(_safe_int(segment.get("start"), 0))
    end_text = plugin._minutes_to_hhmm(_safe_int(segment.get("end"), 0))
    persona = plugin._get_default_persona_prompt()
    weather_info = plugin._weather_summary_text(plugin.data.get("daily_weather", {}))
    calendar_context = plugin._format_calendar_context_for_prompt()
    schedule_adjustments = plugin._format_schedule_adjustments_for_prompt()
    return f"""
现在时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

【日期语境】
{calendar_context}

【AstrBot 默认人格】
{persona}

【今日粗日程】
{plugin._format_daily_plan(plan)}

【即将强化的日程段】
时间段：{start_text}-{end_text}
当前事项：{_single_line(item.get('activity'), 100)}
情绪：{_single_line(item.get('mood'), 40)}
可分享种子：{_single_line(item.get('message_seed'), 120)}

【上下节点衔接】
上一段：{plugin._format_plan_item_for_prompt(previous_item) if isinstance(previous_item, dict) else '（无）'}
下一段：{plugin._format_plan_item_for_prompt(next_item) if isinstance(next_item, dict) else '（无）'}
衔接要求：当前段要承接上一段的身体余味、情绪惯性或未收住的小动作,同时自然滑向下一段；不要像三个互不相干的短剧。可以让上一段只留下很淡的影响,但不要忽略时间推进。

【拟人状态】
{plugin._format_state_for_prompt(state)}

【状态走向摘要】
{plugin._format_state_transition_overview(state)}

【今日互动造成的日程偏移】
{schedule_adjustments}

【天气】
{weather_info}

【轻量记忆】
{plugin._recent_diary_context()}

【重要日期】
{plugin._format_important_dates_for_prompt()}

你现在要站在角色的角度,把 {start_text}-{end_text} 这个时段的生活放大来看。不要当成策划会,要当成你亲历了这一小段。

核心思路：先有一个真实的生活瞬间,再判断那一刻想不想找用户。如果不适合开口,就安静待着。如果适合,说一句什么？用户回了怎么接？用户没回过一阵怎么变？要的是逻辑链,不是菜单。

【约束】
· 严格遵守人格和当前时段,不出戏。
· 当前段必须和上下节点有连续性：today_events 里至少一条体现“从上一段过来”的余味,至少一条为下一段留下自然过渡；不要复述粗日程原句。
· 如果“今日互动造成的日程偏移”不是空,当前段和后续主动契机可以在情绪与动作上偏离粗日程一点：让偏移藏在语气、动作选择、节奏变慢/变软里,不要直说“因为用户刚才……所以……”。
· 依据日期语境调整节奏：周末/节假日/假期不要写成普通工作日,除非设定里明确有补课、补班、值班、考试等例外。
· 温柔或内敛的人设可以烦躁,但要写成收着的动作和微小摩擦；不要写想砸、想摔、想打人、报复、毁掉这类破坏性或攻击性冲动。
· 消极状态不能滚雪球式升级。最近日记和拟人状态只提供余波,当前段需要给出一点自然回稳、压下去、被接住或转移注意的可能。
· 用第三人称旁观：today_events 和 why/scene 都像在看这个人过日子,不是角色自己写日记。
· 主动意愿要真实——不是每段都要发消息,允许“想了想算了”。
· screen_peek 用来看用户在干嘛,photo_text 用来拍风景或自拍,message 就是普通文字。只在合适的场景用。
· proactive_events 的 window 必须落在 {start_text}-{end_text} 内,且窗口要有随机范围,不要整点。
· proactive_events 不必每段很多,但当前段如果自然适合主动,至少给 1 个可执行契机；如果不适合,也要让 today_events 足够具体,方便普通回复承接。
· 不要把一天的主动契机都堆到睡前或最后一个时间段。早安/午安可以是固定问候,其他主动更像生活缝隙里长出来的小分享、小试探或安静关心；允许有疏有密,但上午、下午、傍晚、夜里不要只剩夜里。
· 除非当前段确实是睡前问候,傍晚或晚间的小分享不要都写成 evening_greeting,可以使用 activity_share、check_in 或 quiet_care。
· 不要把主动消息写成“汇报状态”：避免“今天心情好多了”“我一整天没发脾气”“我是不是不正常”这类自我评价。状态变化要落到具体生活物件或动作里。
· 状态转译规则：先把状态变成可看见/可触碰/可听见的小片段,再决定要不要发消息。比如回暖写“袖口晒得暖”“饭菜没翻车”,低落写“话到嘴边停住”,烦躁写“把东西放远一点”；不要写状态结论。
· proactive_events 不要全部写成 message。看见画面/食物/窗光时优先 photo_text；想确认用户在不在时可用 screen_peek；很短的贴近感可用 voice 或 poke。只有确实没有动作契机时才用 message。
· motive 是心里一闪而过的念头,10–40 字。
· scene / tone / impulse 是可选的抽象引导：scene 是当时场景,tone 是语气底色,impulse 是想靠近的那股劲。
· 如果是起床/早安/试探,可以带 chain 做分支逻辑：先只叫名字,没回->隔一阵轻轻抱怨,还没回->更久后换更熟的催促。
· 只输出 JSON。

格式：
{{
  "summary": "这一段的生活氛围一句话",
  "today_events": [
    {{"window": "10:00-10:12", "event": "靠在桌边发了一会儿呆,慢慢把状态找回来", "mood": "困"}}
  ],
  "proactive_events": [
    {{"window": "10:05-10:18", "reason": "check_in", "action": "screen_peek", "why": "手头刚好空了一小会儿,忽然好奇用户在做什么", "topic": "空档偷看一眼", "motive": "这一小会儿有点空,想偷偷看你在干嘛", "scene": "上午空出来的一小段", "tone": "百无聊赖", "impulse": "想确认你那边是不是也正好有空"}},
    {{"window": "08:18-09:05", "reason": "morning_greeting", "action": "message", "why": "刚醒来那一下还有点迷糊,想先轻轻叫对方一声", "topic": "刚醒那会儿", "motive": "被窝里还暖着,手已经先点到你这边了", "scene": "刚醒来还蜷在被子里", "tone": "迷糊", "impulse": "想先轻轻碰你一下", "chain": [{{"kind": "name_only_opener"}}, {{"kind": "if_no_reply", "after_minutes": 12, "reason": "check_in", "topic": "早安没后续", "motive": "刚才叫了你一声,你那边怎么还没动静", "tone": "轻轻抱怨"}}, {{"kind": "if_still_no_reply", "after_minutes": 55, "reason": "morning_greeting", "topic": "第二次叫起床", "motive": "都这个点了,再不喊你一下有点说不过去", "tone": "熟一点的催促"}}]}}
  ]
}}
""".strip()
