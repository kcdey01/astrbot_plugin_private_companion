# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import re
from copy import deepcopy
from typing import Any

from astrbot.api import logger
from quart import request

PLUGIN_NAME = "astrbot_plugin_private_companion"
PAGE_API_PREFIX = f"/{PLUGIN_NAME}/page"


class PrivateCompanionPageApi:
    """AstrBot 官方插件拓展页面 API。"""

    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin

    def register_routes(self) -> None:
        register = self.plugin.context.register_web_api
        routes = [
            ("/overview", self.get_overview, ["GET"], "Private Companion Page overview"),
            ("/users", self.list_users, ["GET"], "Private Companion Page users"),
            ("/user", self.get_user, ["GET"], "Private Companion Page user detail"),
            ("/user/update", self.update_user, ["POST"], "Private Companion Page update user"),
            ("/groups", self.list_groups, ["GET"], "Private Companion Page groups"),
            ("/group", self.get_group, ["GET"], "Private Companion Page group detail"),
            ("/group/update", self.update_group, ["POST"], "Private Companion Page update group"),
            ("/settings/update", self.update_settings, ["POST"], "Private Companion Page update settings"),
            ("/diagnostics", self.get_diagnostics, ["GET"], "Private Companion Page diagnostics"),
            ("/preset/apply", self.apply_preset, ["POST"], "Private Companion Page apply preset"),
            ("/providers/available", self.list_available_providers, ["GET"], "Private Companion Page available providers"),
            ("/provider/test", self.test_provider, ["POST"], "Private Companion Page test provider"),
        ]
        for path, handler, methods, desc in routes:
            register(f"{PAGE_API_PREFIX}{path}", handler, methods, desc)

    async def get_overview(self) -> dict[str, Any]:
        try:
            async with self.plugin._data_lock:
                data = deepcopy(self.plugin.data)
            users = data.get("users") if isinstance(data.get("users"), dict) else {}
            groups = data.get("groups") if isinstance(data.get("groups"), dict) else {}
            enabled_users = sum(1 for item in users.values() if isinstance(item, dict) and item.get("enabled", True))
            enabled_groups = sum(1 for item in groups.values() if isinstance(item, dict) and item.get("enabled", True))
            return self._ok(
                {
                    "plugin": {
                        "enabled": bool(getattr(self.plugin, "enabled", False)),
                        "bot_name": getattr(self.plugin, "bot_name", ""),
                        "data_file": getattr(self.plugin, "data_file", ""),
                        "data_version": data.get("version"),
                    },
                    "private": {
                        "user_count": len(users),
                        "enabled_user_count": enabled_users,
                        "require_opt_in": bool(getattr(self.plugin, "require_private_opt_in", True)),
                        "max_daily_messages": getattr(self.plugin, "max_daily_messages", 0),
                        "idle_minutes": getattr(self.plugin, "idle_minutes", 0),
                        "min_interval_minutes": getattr(self.plugin, "min_interval_minutes", 0),
                    },
                    "group": {
                        "enabled": bool(getattr(self.plugin, "enable_group_companion", False)),
                        "group_count": len(groups),
                        "enabled_group_count": enabled_groups,
                        "access_mode": getattr(self.plugin, "group_access_mode", "whitelist"),
                        "whitelist": self.plugin._configured_group_ids(),
                        "blacklist": self.plugin._configured_group_blacklist_ids(),
                        "interjection_enabled": bool(getattr(self.plugin, "enable_group_interjection", False)),
                    },
                    "features": self._feature_flags(),
                    "providers": self._provider_settings(),
                    "settings": self._runtime_settings(),
                    "livingmemory": self._livingmemory_summary(),
                    "daily_state": self._daily_state_summary(data.get("daily_state")),
                    "daily_timeline": self._daily_timeline_summary(data),
                }
            )
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取总览失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def list_users(self) -> dict[str, Any]:
        try:
            limit = self._query_int("limit", 80, 1, 300)
            async with self.plugin._data_lock:
                users = deepcopy(self.plugin.data.get("users", {}))
            if not isinstance(users, dict):
                users = {}
            items = [self._user_summary(user_id, user) for user_id, user in users.items() if isinstance(user, dict)]
            items.sort(key=lambda item: item.get("last_seen_ts") or 0, reverse=True)
            return self._ok({"items": items[:limit], "total": len(items)})
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取用户列表失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def get_user(self) -> dict[str, Any]:
        user_id = str(request.args.get("user_id", "")).strip()
        if not user_id:
            return self._error("缺少 user_id")
        try:
            async with self.plugin._data_lock:
                user = deepcopy((self.plugin.data.get("users") or {}).get(user_id))
            if not isinstance(user, dict):
                return self._error("用户不存在")
            detail = self._user_summary(user_id, user)
            detail.update(
                {
                    "memory": user.get("companion_memory") if isinstance(user.get("companion_memory"), dict) else {},
                    "expression_profile": user.get("expression_profile") if isinstance(user.get("expression_profile"), dict) else {},
                    "intent_profile": user.get("intent_profile") if isinstance(user.get("intent_profile"), dict) else {},
                    "relationship_state": user.get("relationship_state") if isinstance(user.get("relationship_state"), dict) else {},
                    "dialogue_episodes": self._limited_list(user.get("dialogue_episodes"), 12),
                    "open_loops": self._limited_list(user.get("open_loops"), 12),
                    "recent_reply_topics": self._limited_list(user.get("recent_reply_topics"), 16),
                    "last_user_message": user.get("last_user_message", ""),
                    "last_companion_message": user.get("last_companion_message", ""),
                    "formatted": {
                        "relationship": self.plugin._format_relationship_summary(user),
                        "action_affinity": self.plugin._format_action_affinity_summary(user),
                        "next_proactive": self.plugin._format_next_proactive(user),
                    },
                }
            )
            return self._ok(detail)
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取用户详情失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def update_user(self) -> dict[str, Any]:
        payload = await request.get_json(silent=True) or {}
        user_id = str(payload.get("user_id", "")).strip()
        if not user_id:
            return self._error("缺少 user_id")
        try:
            async with self.plugin._data_lock:
                user = self.plugin._get_user(user_id)
                if "enabled" in payload:
                    user["enabled"] = bool(payload.get("enabled"))
                if "nickname" in payload:
                    user["nickname"] = self._single_line(payload.get("nickname"), 24)
                if "style" in payload:
                    user["style"] = self._single_line(payload.get("style"), 24)
                if payload.get("reset_daily"):
                    user["sent_today"] = 0
                    user["sent_day"] = ""
                    user["ignored_streak"] = 0
                    user["photo_sent_today"] = 0
                    user["screen_peek_today"] = 0
                if payload.get("clear_schedule"):
                    for key in (
                        "next_proactive_at",
                        "planned_proactive_reason",
                        "planned_proactive_action",
                        "planned_proactive_motive",
                        "planned_proactive_topic",
                        "planned_proactive_source",
                        "planned_event_chain",
                        "planned_opener_mode",
                        "planned_followup_kind",
                    ):
                        user[key] = [] if key == "planned_event_chain" else "" if key != "next_proactive_at" else 0
                if payload.get("clear_learning"):
                    for key, empty in (
                        ("companion_memory", {}),
                        ("expression_profile", {}),
                        ("reply_planner", {}),
                        ("intent_profile", {}),
                        ("relationship_state", {}),
                        ("recent_reply_topics", []),
                        ("dialogue_episodes", []),
                        ("open_loops", []),
                        ("action_preferences", {}),
                    ):
                        user[key] = empty
                    user["episode_message_count"] = 0
                    user["last_episode_refresh_at"] = 0
                    user["last_memory_refresh_at"] = 0
                self.plugin._save_data_sync()
                snapshot = deepcopy(user)
            return self._ok(self._user_summary(user_id, snapshot))
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 更新用户失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def list_groups(self) -> dict[str, Any]:
        try:
            limit = self._query_int("limit", 80, 1, 300)
            async with self.plugin._data_lock:
                groups = deepcopy(self.plugin.data.get("groups", {}))
            if not isinstance(groups, dict):
                groups = {}
            items = [self._group_summary(group_id, group) for group_id, group in groups.items() if isinstance(group, dict)]
            items.sort(key=lambda item: item.get("last_seen_ts") or 0, reverse=True)
            return self._ok({"items": items[:limit], "total": len(items)})
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取群列表失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def get_group(self) -> dict[str, Any]:
        group_id = str(request.args.get("group_id", "")).strip()
        if not group_id:
            return self._error("缺少 group_id")
        try:
            async with self.plugin._data_lock:
                group = deepcopy((self.plugin.data.get("groups") or {}).get(group_id))
            if not isinstance(group, dict):
                return self._error("群不存在")
            detail = self._group_summary(group_id, group)
            detail.update(
                {
                    "members": group.get("members") if isinstance(group.get("members"), dict) else {},
                    "recent_messages": self._limited_list(group.get("recent_messages"), 30),
                    "topic_threads": self._limited_list(group.get("topic_threads"), 16),
                    "group_episodes": self._limited_list(group.get("group_episodes"), 12),
                    "relationship_edges": group.get("relationship_edges") if isinstance(group.get("relationship_edges"), dict) else {},
                    "interjection_feedback": group.get("interjection_feedback") if isinstance(group.get("interjection_feedback"), dict) else {},
                    "last_bot_interjection": group.get("last_bot_interjection") if isinstance(group.get("last_bot_interjection"), dict) else {},
                    "formatted": {
                        "status": self.plugin._format_group_status(group),
                        "feedback": self.plugin._format_group_interjection_feedback(group),
                        "relationship_graph": self.plugin._format_group_relationship_graph_for_prompt(group),
                    },
                }
            )
            return self._ok(detail)
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取群详情失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def update_group(self) -> dict[str, Any]:
        payload = await request.get_json(silent=True) or {}
        group_id = str(payload.get("group_id", "")).strip()
        if not group_id:
            return self._error("缺少 group_id")
        try:
            async with self.plugin._data_lock:
                group = self.plugin._get_group(group_id)
                if "enabled" in payload:
                    group["enabled"] = bool(payload.get("enabled"))
                if payload.get("reset_interjection"):
                    group["last_interject_at"] = 0
                    group["interject_day"] = ""
                    group["interject_today"] = 0
                    group["last_bot_interjection"] = {}
                    group["interjection_feedback"] = {}
                if payload.get("clear_observation"):
                    enabled = bool(group.get("enabled", True))
                    group.clear()
                    group.update(
                        {
                            "enabled": enabled,
                            "group_id": group_id,
                            "message_count": 0,
                            "last_seen": 0,
                            "last_interject_at": 0,
                            "interject_day": "",
                            "interject_today": 0,
                            "recent_messages": [],
                            "members": {},
                            "slang_terms": [],
                            "slang_meanings": {},
                            "topic_signatures": [],
                            "topic_threads": [],
                            "group_episodes": [],
                            "relationship_edges": {},
                            "interjection_feedback": {},
                            "last_bot_interjection": {},
                            "last_speaker": {},
                            "atmosphere": {},
                            "last_summary_at": 0,
                            "last_episode_refresh_at": 0,
                            "last_slang_summary_at": 0,
                        }
                    )
                self.plugin._save_data_sync()
                snapshot = deepcopy(group)
            return self._ok(self._group_summary(group_id, snapshot))
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 更新群失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def update_settings(self) -> dict[str, Any]:
        payload = await request.get_json(silent=True) or {}
        try:
            changed: dict[str, Any] = {}
            if "group_access_mode" in payload:
                mode = str(payload.get("group_access_mode") or "").strip().lower()
                if mode not in {"whitelist", "blacklist"}:
                    return self._error("group_access_mode 只能是 whitelist 或 blacklist")
                changed["group_access_mode"] = mode
            if "group_whitelist_ids" in payload:
                changed["group_whitelist_ids"] = self._normalize_id_list(payload.get("group_whitelist_ids"))
            if "group_blacklist_ids" in payload:
                changed["group_blacklist_ids"] = self._normalize_id_list(payload.get("group_blacklist_ids"))
            for key, value in (payload.get("features") or {}).items():
                if key in self._allowed_feature_keys():
                    changed[key] = bool(value)
            for key, value in (payload.get("providers") or {}).items():
                if key in self._allowed_provider_keys():
                    changed[key] = self._single_line(value, 160)
            for key, value in (payload.get("settings") or {}).items():
                if key in self._allowed_setting_keys():
                    changed[key] = self._normalize_setting_value(key, value)
            for key, value in changed.items():
                self._apply_config_value(key, value)
            if changed:
                self._save_config_if_possible()
            overview = await self.get_overview()
            if overview.get("success"):
                overview["data"]["changed"] = changed
                overview["data"]["config_saved"] = self._can_save_config()
            return overview
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 更新设置失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def get_diagnostics(self) -> dict[str, Any]:
        try:
            async with self.plugin._data_lock:
                data = deepcopy(self.plugin.data)
            users = data.get("users") if isinstance(data.get("users"), dict) else {}
            groups = data.get("groups") if isinstance(data.get("groups"), dict) else {}
            items = self._build_diagnostics(users, groups)
            return self._ok({"items": items})
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取诊断失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def apply_preset(self) -> dict[str, Any]:
        payload = await request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        presets = self._presets()
        if name not in presets:
            return self._error("未知预设")
        preset = presets[name]
        try:
            for key, value in preset.get("settings", {}).items():
                self._apply_config_value(key, self._normalize_setting_value(key, value))
            for key, value in preset.get("features", {}).items():
                if key in self._allowed_feature_keys():
                    self._apply_config_value(key, bool(value))
            self._save_config_if_possible()
            overview = await self.get_overview()
            if overview.get("success"):
                overview["data"]["preset"] = name
                overview["data"]["preset_label"] = preset.get("label", name)
            return overview
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 应用预设失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def list_available_providers(self) -> dict[str, Any]:
        try:
            items = self._available_provider_items()
            return self._ok({"items": items, "total": len(items)})
        except Exception as exc:
            logger.error(f"[PrivateCompanionPage] 获取 Provider 列表失败: {exc}", exc_info=True)
            return self._error(str(exc))

    async def test_provider(self) -> dict[str, Any]:
        payload = await request.get_json(silent=True) or {}
        key = str(payload.get("key", "")).strip()
        provider_id = self._single_line(payload.get("provider_id"), 160)
        if key and key not in self._allowed_provider_keys():
            return self._error("不允许测试该 Provider 配置项")
        start = time.time()
        try:
            text = await self.plugin._llm_call(
                "请只回复两个字：正常",
                max_tokens=16,
                provider_id=provider_id,
            )
            elapsed_ms = int((time.time() - start) * 1000)
            ok = bool(text)
            return self._ok(
                {
                    "ok": ok,
                    "key": key,
                    "provider_id": provider_id,
                    "elapsed_ms": elapsed_ms,
                    "sample": self._single_line(text, 80),
                }
            )
        except Exception as exc:
            return self._ok(
                {
                    "ok": False,
                    "key": key,
                    "provider_id": provider_id,
                    "elapsed_ms": int((time.time() - start) * 1000),
                    "error": str(exc),
                }
            )

    def _user_summary(self, user_id: str, user: dict[str, Any]) -> dict[str, Any]:
        last_seen = user.get("last_seen", 0)
        last_sent = user.get("last_sent", 0)
        return {
            "user_id": str(user_id),
            "enabled": bool(user.get("enabled", True)),
            "nickname": user.get("nickname", ""),
            "style": user.get("style", ""),
            "umo": user.get("umo", ""),
            "last_seen_ts": last_seen,
            "last_seen": self.plugin._format_timestamp_elapsed(last_seen),
            "last_sent_ts": last_sent,
            "last_sent": self.plugin._format_timestamp_elapsed(last_sent),
            "sent_today": user.get("sent_today", 0),
            "inbound_count": user.get("inbound_count", 0),
            "reply_count": user.get("reply_count", 0),
            "proactive_sent_count": user.get("proactive_sent_count", 0),
            "relationship_score": user.get("relationship_score", 0),
            "relationship_stage": (user.get("relationship_state") or {}).get("stage", ""),
            "planned_reason": user.get("planned_proactive_reason", ""),
            "planned_action": user.get("planned_proactive_action", ""),
            "next_proactive_ts": user.get("next_proactive_at", 0),
            "next_proactive": self.plugin._format_next_proactive(user),
            "memory_items": self._memory_item_count(user.get("companion_memory")),
            "dialogue_episode_count": len(user.get("dialogue_episodes") or []),
            "open_loop_count": len(user.get("open_loops") or []),
        }

    def _group_summary(self, group_id: str, group: dict[str, Any]) -> dict[str, Any]:
        atmosphere = group.get("atmosphere") if isinstance(group.get("atmosphere"), dict) else {}
        slang_terms = group.get("slang_terms") if isinstance(group.get("slang_terms"), list) else []
        return {
            "group_id": str(group_id),
            "enabled": bool(group.get("enabled", True)),
            "allowed_by_mode": self.plugin._group_allowed_by_access_mode(str(group_id)),
            "message_count": group.get("message_count", 0),
            "last_seen_ts": group.get("last_seen", 0),
            "last_seen": self.plugin._format_timestamp_elapsed(group.get("last_seen", 0)),
            "member_count": len(group.get("members") or {}),
            "recent_message_count": len(group.get("recent_messages") or []),
            "slang_count": len(slang_terms),
            "slang_terms": slang_terms[:16],
            "topic_count": len(group.get("topic_threads") or []),
            "episode_count": len(group.get("group_episodes") or []),
            "relationship_edge_count": len(group.get("relationship_edges") or {}),
            "interject_today": group.get("interject_today", 0),
            "last_interject": self.plugin._format_timestamp_elapsed(group.get("last_interject_at", 0)),
            "atmosphere": {
                "mood": atmosphere.get("mood", ""),
                "heat": atmosphere.get("heat", ""),
                "last_summary": atmosphere.get("summary", ""),
            },
        }

    def _feature_flags(self) -> dict[str, bool]:
        keys = [
            "enable_mai_style_integration",
            "enable_companion_memory",
            "enable_expression_learning",
            "enable_companion_reply_planner",
            "enable_intent_emotion_analysis",
            "enable_response_self_review",
            "enable_passive_topic_suppression",
            "enable_relationship_state_machine",
            "enable_dialogue_episode_memory",
            "enable_open_loop_tracking",
            "enable_group_companion",
            "enable_group_slang_learning",
            "enable_group_member_profiles",
            "enable_group_context_injection",
            "enable_group_interjection",
            "enable_group_topic_threads",
            "enable_group_episode_memory",
            "enable_group_interjection_feedback",
            "enable_group_slang_meanings",
            "enable_group_relationship_graph",
            "enable_group_privacy_guard",
            "enable_livingmemory_integration",
        ]
        return {key: bool(getattr(self.plugin, key, False)) for key in keys}

    def _provider_settings(self) -> dict[str, str]:
        keys = [
            "LLM_PROVIDER_ID",
            "MAI_STYLE_PROVIDER_ID",
            "RESPONSE_REVIEW_PROVIDER_ID",
            "RELATIONSHIP_ANALYSIS_PROVIDER_ID",
            "COMPANION_MEMORY_PROVIDER_ID",
            "DIALOGUE_EPISODE_PROVIDER_ID",
            "GROUP_INTERJECT_PROVIDER_ID",
            "GROUP_EPISODE_PROVIDER_ID",
            "GROUP_SLANG_PROVIDER_ID",
        ]
        return {key: self._config_get(key) for key in keys}

    def _available_provider_items(self) -> list[dict[str, Any]]:
        providers: list[Any] = []
        context = getattr(self.plugin, "context", None)
        get_all = getattr(context, "get_all_providers", None)
        if callable(get_all):
            try:
                providers = list(get_all() or [])
            except Exception:
                providers = []
        if not providers:
            manager = getattr(context, "provider_manager", None)
            inst_map = getattr(manager, "inst_map", None)
            if isinstance(inst_map, dict):
                providers = list(inst_map.values())

        using_id = ""
        get_using = getattr(context, "get_using_provider", None)
        if callable(get_using):
            try:
                using_id = self._provider_id(get_using())
            except Exception:
                using_id = ""

        items: list[dict[str, str]] = []
        seen: set[str] = set()
        for provider in providers:
            provider_id = self._provider_id(provider)
            if not provider_id or provider_id in seen:
                continue
            seen.add(provider_id)
            items.append(
                {
                    "id": provider_id,
                    "name": self._provider_name(provider, provider_id),
                    "type": self._provider_type(provider),
                    "model": self._provider_model(provider),
                    "is_default": provider_id == using_id,
                }
            )
        items.sort(key=lambda item: (not item["is_default"], item["name"].lower(), item["id"].lower()))
        return items

    @staticmethod
    def _provider_config(provider: Any) -> Any:
        return getattr(provider, "provider_config", None) or getattr(provider, "config", None) or {}

    @classmethod
    def _provider_config_value(cls, provider: Any, *keys: str) -> str:
        config = cls._provider_config(provider)
        for key in keys:
            value = ""
            if isinstance(config, dict):
                value = str(config.get(key, "") or "")
            else:
                value = str(getattr(config, key, "") or "")
            if value:
                return value.strip()
        return ""

    @classmethod
    def _provider_id(cls, provider: Any) -> str:
        if provider is None:
            return ""
        return (
            cls._provider_config_value(provider, "id", "provider_id")
            or str(getattr(provider, "provider_id", "") or "").strip()
            or str(getattr(provider, "id", "") or "").strip()
        )

    @classmethod
    def _provider_name(cls, provider: Any, provider_id: str) -> str:
        return (
            cls._provider_config_value(provider, "name", "display_name", "provider")
            or str(getattr(provider, "name", "") or "").strip()
            or provider_id
        )

    @classmethod
    def _provider_model(cls, provider: Any) -> str:
        return cls._provider_config_value(provider, "model", "model_name", "api_model", "model_id")

    @classmethod
    def _provider_type(cls, provider: Any) -> str:
        return (
            cls._provider_config_value(provider, "type", "provider_type")
            or provider.__class__.__name__
        )

    def _runtime_settings(self) -> dict[str, Any]:
        keys = [
            "bot_name",
            "target_user_ids",
            "target_platform",
            "default_nickname",
            "default_style",
            "quiet_hours",
            "check_interval_seconds",
            "idle_minutes",
            "min_interval_minutes",
            "max_daily_messages",
            "group_interject_min_interval_minutes",
            "group_interject_max_daily",
            "max_group_recent_messages",
            "max_group_slang_terms",
            "memory_refresh_interval_minutes",
            "episode_memory_refresh_messages",
            "episode_memory_refresh_minutes",
            "max_companion_memory_items",
            "max_learned_expression_items",
            "max_dialogue_episodes",
        ]
        return {key: getattr(self.plugin, key, self._config_get(key)) for key in keys}

    def _build_diagnostics(self, users: dict[str, Any], groups: dict[str, Any]) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []

        def add(level: str, title: str, text: str, action: str = "") -> None:
            items.append({"level": level, "title": title, "text": text, "action": action})

        features = self._feature_flags()
        providers = self._provider_settings()
        group_mode = str(getattr(self.plugin, "group_access_mode", "whitelist") or "whitelist")
        whitelist = self.plugin._configured_group_ids()
        blacklist = self.plugin._configured_group_blacklist_ids()
        enabled_users = sum(1 for item in users.values() if isinstance(item, dict) and item.get("enabled", True))
        enabled_groups = sum(1 for item in groups.values() if isinstance(item, dict) and item.get("enabled", True))

        if getattr(self.plugin, "enabled", False):
            add("ok", "插件已启用", "后台主动检查与事件处理会正常运行")
        else:
            add("error", "插件未启用", "当前不会进行私聊主动陪伴或群聊观察", "在配置中打开 enabled")

        if providers.get("LLM_PROVIDER_ID") or getattr(self.plugin, "llm_provider_id", ""):
            add("ok", "主模型可见", providers.get("LLM_PROVIDER_ID") or "运行态已配置")
        else:
            add("info", "主模型留空", "会回退到 AstrBot 默认模型；建议为陪伴插件单独配置主模型")

        if enabled_users:
            add("ok", "私聊对象已就绪", f"已启用 {enabled_users} 个私聊对象")
        else:
            add("warn", "暂无启用的私聊对象", "私聊主动陪伴没有明确目标", "在私聊页新增对象或配置 target_user_ids")

        max_daily = int(getattr(self.plugin, "max_daily_messages", 0) or 0)
        if max_daily > 0:
            add("ok", "私聊主动额度可用", f"每日上限 {max_daily} 条")
        else:
            add("warn", "私聊主动已关闭", "每日主动上限为 0", "在模块配置里调高每日主动上限")

        if features.get("enable_companion_memory") and features.get("enable_expression_learning"):
            add("ok", "私聊学习链路完整", "长期画像与表达学习均已打开")
        else:
            add("warn", "私聊学习链路不完整", "画像记忆或表达学习未开启", "在配置页打开对应功能开关")

        if features.get("enable_livingmemory_integration"):
            living_level = "ok" if self.plugin._livingmemory_available() else "warn"
            living_text = "LivingMemory 插件可被调用" if living_level == "ok" else "已启用协同，但当前未检测到可用工具"
            add(living_level, "LivingMemory 协同", living_text)

        if getattr(self.plugin, "enable_group_companion", False):
            if group_mode == "whitelist" and not whitelist:
                add("warn", "群聊白名单为空", "白名单模式下所有群都会被拦截", "在配置页加入群号或切换为黑名单模式")
            elif group_mode == "blacklist":
                add("ok", "群聊黑名单模式", f"已屏蔽 {len(blacklist)} 个群，其余群可观察")
            else:
                add("ok", "群聊白名单模式", f"允许 {len(whitelist)} 个群")

            if enabled_groups:
                add("ok", "已有群聊观测数据", f"已启用 {enabled_groups} 个群")
            else:
                add("info", "暂无群聊观测数据", "收到群消息后会逐步建立群画像")
        else:
            add("info", "群聊陪伴未开启", "当前不会记录群聊上下文")

        if features.get("enable_group_interjection"):
            limit = int(getattr(self.plugin, "group_interject_max_daily", 0) or 0)
            if limit > 0:
                add("ok", "群聊插话可用", f"每群每日上限 {limit} 次")
            else:
                add("warn", "群聊插话开关已开但额度为 0", "功能不会真正触发", "在模块配置里调高每群每日插话上限")
        elif getattr(self.plugin, "enable_group_companion", False):
            add("info", "群聊以观察为主", "当前只积累群上下文，不主动插话")

        if not features.get("enable_group_privacy_guard"):
            add("warn", "群聊隐私保护未开启", "私聊记忆注入群聊时缺少额外防护", "建议打开 enable_group_privacy_guard")

        refresh_minutes = int(getattr(self.plugin, "memory_refresh_interval_minutes", 0) or 0)
        if refresh_minutes and refresh_minutes < 60:
            add("warn", "长期记忆整理过于频繁", f"当前 {refresh_minutes} 分钟，可能增加模型调用量", "建议设置为 120 分钟以上")

        return items

    @staticmethod
    def _presets() -> dict[str, dict[str, Any]]:
        return {
            "safe": {
                "label": "保守低打扰",
                "settings": {
                    "max_daily_messages": 3,
                    "idle_minutes": 180,
                    "min_interval_minutes": 360,
                    "group_interject_max_daily": 0,
                    "group_interject_min_interval_minutes": 360,
                    "memory_refresh_interval_minutes": 720,
                    "episode_memory_refresh_messages": 12,
                    "episode_memory_refresh_minutes": 180,
                },
                "features": {
                    "enable_group_companion": True,
                    "enable_group_interjection": False,
                    "enable_companion_memory": True,
                    "enable_expression_learning": True,
                    "enable_response_self_review": True,
                    "enable_livingmemory_integration": True,
                },
            },
            "standard": {
                "label": "标准陪伴",
                "settings": {
                    "max_daily_messages": 6,
                    "idle_minutes": 60,
                    "min_interval_minutes": 120,
                    "group_interject_max_daily": 1,
                    "group_interject_min_interval_minutes": 240,
                    "memory_refresh_interval_minutes": 360,
                    "episode_memory_refresh_messages": 8,
                    "episode_memory_refresh_minutes": 90,
                },
                "features": {
                    "enable_group_companion": True,
                    "enable_group_interjection": False,
                    "enable_group_context_injection": True,
                    "enable_companion_memory": True,
                    "enable_expression_learning": True,
                    "enable_dialogue_episode_memory": True,
                    "enable_open_loop_tracking": True,
                    "enable_response_self_review": True,
                },
            },
            "active": {
                "label": "高互动学习",
                "settings": {
                    "max_daily_messages": 10,
                    "idle_minutes": 30,
                    "min_interval_minutes": 60,
                    "group_interject_max_daily": 2,
                    "group_interject_min_interval_minutes": 180,
                    "memory_refresh_interval_minutes": 240,
                    "episode_memory_refresh_messages": 5,
                    "episode_memory_refresh_minutes": 60,
                },
                "features": {
                    "enable_group_companion": True,
                    "enable_companion_memory": True,
                    "enable_expression_learning": True,
                    "enable_companion_reply_planner": True,
                    "enable_intent_emotion_analysis": True,
                    "enable_response_self_review": True,
                    "enable_dialogue_episode_memory": True,
                    "enable_open_loop_tracking": True,
                    "enable_group_interjection": True,
                    "enable_group_interjection_feedback": True,
                },
            },
            "group_observer": {
                "label": "群聊观察优先",
                "settings": {
                    "max_daily_messages": 4,
                    "idle_minutes": 90,
                    "min_interval_minutes": 180,
                    "group_interject_max_daily": 0,
                    "group_interject_min_interval_minutes": 240,
                    "max_group_recent_messages": 120,
                    "max_group_slang_terms": 80,
                },
                "features": {
                    "enable_group_companion": True,
                    "enable_group_context_injection": True,
                    "enable_group_slang_learning": True,
                    "enable_group_member_profiles": True,
                    "enable_group_topic_threads": True,
                    "enable_group_episode_memory": True,
                    "enable_group_slang_meanings": True,
                    "enable_group_relationship_graph": True,
                    "enable_group_privacy_guard": True,
                    "enable_group_interjection": False,
                },
            },
        }

    def _apply_config_value(self, key: str, value: Any) -> None:
        config = getattr(self.plugin, "config", None)
        if isinstance(config, dict):
            config[key] = value
        attr_map = {
            "LLM_PROVIDER_ID": "llm_provider_id",
            "MAI_STYLE_PROVIDER_ID": "mai_style_provider_id",
            "RESPONSE_REVIEW_PROVIDER_ID": "response_review_provider_id",
            "RELATIONSHIP_ANALYSIS_PROVIDER_ID": "relationship_analysis_provider_id",
            "COMPANION_MEMORY_PROVIDER_ID": "companion_memory_provider_id",
            "DIALOGUE_EPISODE_PROVIDER_ID": "dialogue_episode_provider_id",
            "GROUP_INTERJECT_PROVIDER_ID": "group_interject_provider_id",
            "GROUP_EPISODE_PROVIDER_ID": "group_episode_provider_id",
            "GROUP_SLANG_PROVIDER_ID": "group_slang_provider_id",
        }
        if key in attr_map:
            setattr(self.plugin, attr_map[key], str(value or "").strip())
            return
        if key == "group_access_mode":
            self.plugin.group_access_mode = str(value or "whitelist").lower()
            return
        if key == "group_whitelist_ids":
            self.plugin.group_whitelist_ids = list(value or [])
            return
        if key == "group_blacklist_ids":
            self.plugin.group_blacklist_ids = list(value or [])
            return
        if key in self._allowed_feature_keys():
            setattr(self.plugin, key, bool(value))
            return
        if key in self._allowed_setting_keys():
            setattr(self.plugin, key, value)

    def _config_get(self, key: str) -> str:
        config = getattr(self.plugin, "config", None)
        if isinstance(config, dict):
            return str(config.get(key, "") or "")
        return ""

    def _save_config_if_possible(self) -> None:
        config = getattr(self.plugin, "config", None)
        save = getattr(config, "save_config", None)
        if callable(save):
            save()

    def _can_save_config(self) -> bool:
        return callable(getattr(getattr(self.plugin, "config", None), "save_config", None))

    @staticmethod
    def _allowed_feature_keys() -> set[str]:
        return {
            "enable_mai_style_integration",
            "enable_companion_memory",
            "enable_expression_learning",
            "enable_companion_reply_planner",
            "enable_intent_emotion_analysis",
            "enable_response_self_review",
            "enable_passive_topic_suppression",
            "enable_relationship_state_machine",
            "enable_dialogue_episode_memory",
            "enable_open_loop_tracking",
            "enable_group_companion",
            "enable_group_slang_learning",
            "enable_group_member_profiles",
            "enable_group_context_injection",
            "enable_group_interjection",
            "enable_group_topic_threads",
            "enable_group_episode_memory",
            "enable_group_interjection_feedback",
            "enable_group_slang_meanings",
            "enable_group_relationship_graph",
            "enable_group_privacy_guard",
            "enable_livingmemory_integration",
        }

    @staticmethod
    def _allowed_provider_keys() -> set[str]:
        return {
            "LLM_PROVIDER_ID",
            "MAI_STYLE_PROVIDER_ID",
            "RESPONSE_REVIEW_PROVIDER_ID",
            "RELATIONSHIP_ANALYSIS_PROVIDER_ID",
            "COMPANION_MEMORY_PROVIDER_ID",
            "DIALOGUE_EPISODE_PROVIDER_ID",
            "GROUP_INTERJECT_PROVIDER_ID",
            "GROUP_EPISODE_PROVIDER_ID",
            "GROUP_SLANG_PROVIDER_ID",
        }

    @staticmethod
    def _allowed_setting_keys() -> set[str]:
        return {
            "bot_name",
            "target_user_ids",
            "target_platform",
            "default_nickname",
            "default_style",
            "quiet_hours",
            "check_interval_seconds",
            "idle_minutes",
            "min_interval_minutes",
            "max_daily_messages",
            "group_interject_min_interval_minutes",
            "group_interject_max_daily",
            "max_group_recent_messages",
            "max_group_slang_terms",
            "memory_refresh_interval_minutes",
            "episode_memory_refresh_messages",
            "episode_memory_refresh_minutes",
            "max_companion_memory_items",
            "max_learned_expression_items",
            "max_dialogue_episodes",
        }

    def _normalize_setting_value(self, key: str, value: Any) -> Any:
        if key == "target_user_ids":
            return self._normalize_id_list(value)
        if key in {
            "check_interval_seconds",
            "idle_minutes",
            "min_interval_minutes",
            "max_daily_messages",
            "group_interject_min_interval_minutes",
            "group_interject_max_daily",
            "max_group_recent_messages",
            "max_group_slang_terms",
            "memory_refresh_interval_minutes",
            "episode_memory_refresh_messages",
            "episode_memory_refresh_minutes",
            "max_companion_memory_items",
            "max_learned_expression_items",
            "max_dialogue_episodes",
        }:
            try:
                return max(0, int(value))
            except (TypeError, ValueError):
                return 0
        return self._single_line(value, 240)

    def _livingmemory_summary(self) -> dict[str, Any]:
        available = bool(self.plugin._livingmemory_available())
        return {
            "enabled": bool(getattr(self.plugin, "enable_livingmemory_integration", False)),
            "available": available,
            "tool_name": getattr(self.plugin, "livingmemory_tool_name", ""),
            "plugin_dir": str(self.plugin._livingmemory_plugin_dir()),
            "status": self.plugin._format_livingmemory_status(),
        }

    def _daily_state_summary(self, state: Any) -> dict[str, Any]:
        if not isinstance(state, dict):
            return {}
        keys = ["date", "sleep", "dream", "health", "hunger", "body_cycle", "location", "weather", "mood_bias", "energy", "note"]
        return {key: state.get(key, "") for key in keys}

    def _daily_timeline_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        plan = data.get("daily_plan") if isinstance(data.get("daily_plan"), dict) else {}
        enhanced = data.get("detail_enhanced_segments") if isinstance(data.get("detail_enhanced_segments"), dict) else {}
        story = data.get("daily_story_plan") if isinstance(data.get("daily_story_plan"), dict) else {}
        adjustments = data.get("schedule_adjustments") if isinstance(data.get("schedule_adjustments"), list) else []
        presence = data.get("qq_presence_state") if isinstance(data.get("qq_presence_state"), dict) else {}

        segments: list[dict[str, Any]] = []
        for key, snapshot in enhanced.items():
            if not isinstance(snapshot, dict):
                continue
            segment = self._segment_from_key(str(key), plan, snapshot)
            segments.append(
                {
                    "key": str(key),
                    "window": segment.get("window", str(key)),
                    "start": segment.get("start", 99999),
                    "status": snapshot.get("status", ""),
                    "summary": snapshot.get("summary", ""),
                    "state_variables": self._limited_state_variables(snapshot.get("state_variables")),
                    "presence_status": snapshot.get("presence_status") if isinstance(snapshot.get("presence_status"), dict) else {},
                    "interaction_updates": self._limited_interaction_updates(snapshot.get("interaction_updates")),
                    "today_events": self._limited_story_items(snapshot.get("today_events"), 5),
                    "proactive_events": self._limited_story_items(snapshot.get("proactive_events"), 4),
                }
            )
        segments.sort(key=lambda item: item.get("start", 99999))

        return {
            "plan_date": plan.get("date", ""),
            "story_date": story.get("date", ""),
            "detail_day": data.get("detail_enhanced_day", ""),
            "segment_count": len(segments),
            "segments": segments,
            "story_today_events": self._limited_story_items(story.get("today_events"), 12),
            "story_proactive_events": self._limited_story_items(story.get("proactive_events"), 12),
            "adjustments": self._limited_adjustments(adjustments),
            "qq_presence_state": presence,
        }

    def _segment_from_key(self, key: str, plan: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
        keyed = re.fullmatch(r"(\d{4}-\d{2}-\d{2}):(\d+):(\d{1,2}:\d{2})", key)
        if keyed:
            index = int(keyed.group(2))
            start = self.plugin._parse_hhmm_to_minutes(keyed.group(3))
            items = plan.get("items") if isinstance(plan, dict) else []
            end = None
            if isinstance(items, list):
                for next_item in items[index + 1:]:
                    if isinstance(next_item, dict):
                        end = self.plugin._parse_hhmm_to_minutes(next_item.get("time"))
                        if end is not None:
                            break
            if start is not None:
                if end is None:
                    item = items[index] if isinstance(items, list) and index < len(items) and isinstance(items[index], dict) else None
                    end = self.plugin._segment_end_minutes(start, item)
                return {"window": f"{self.plugin._minutes_to_hhmm(start)}-{self.plugin._minutes_to_hhmm(end)}", "start": start}

        inferred = self._segment_from_story_windows(snapshot)
        if inferred:
            return inferred

        match = re.search(r"(?:^|[:|_])(\d{1,4})[-_](\d{1,4})(?:$|[:|_])", key)
        if not match:
            return {"window": key, "start": 99999}
        start = int(match.group(1))
        end = int(match.group(2))
        if not (0 <= start < 24 * 60 and 0 < end <= 28 * 60):
            return {"window": key, "start": 99999}
        return {"window": f"{self.plugin._minutes_to_hhmm(start)}-{self.plugin._minutes_to_hhmm(end)}", "start": start}

    def _segment_from_story_windows(self, snapshot: dict[str, Any]) -> dict[str, Any] | None:
        minutes: list[int] = []
        for key in ("today_events", "proactive_events"):
            items = snapshot.get(key)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                start, end = self.plugin._parse_window_minutes(str(item.get("window") or ""))
                if start is not None:
                    minutes.append(start)
                if end is not None:
                    minutes.append(end)
        if not minutes:
            return None
        start = min(minutes)
        end = max(minutes)
        return {"window": f"{self.plugin._minutes_to_hhmm(start)}-{self.plugin._minutes_to_hhmm(end)}", "start": start}

    @staticmethod
    def _limited_state_variables(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        items: list[dict[str, str]] = []
        for item in value[:8]:
            if not isinstance(item, dict):
                continue
            items.append(
                {
                    "name": PrivateCompanionPageApi._single_line(item.get("name") or item.get("key"), 40),
                    "value": PrivateCompanionPageApi._single_line(item.get("value"), 80),
                    "note": PrivateCompanionPageApi._single_line(item.get("note"), 100),
                }
            )
        return items

    @staticmethod
    def _limited_interaction_updates(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        items: list[dict[str, Any]] = []
        for item in value[-8:]:
            if not isinstance(item, dict):
                continue
            updates = item.get("state_updates")
            items.append(
                {
                    "at": PrivateCompanionPageApi._single_line(item.get("at"), 12),
                    "source": PrivateCompanionPageApi._single_line(item.get("source"), 24),
                    "reaction": PrivateCompanionPageApi._single_line(item.get("reaction"), 140),
                    "state_updates": [
                        PrivateCompanionPageApi._single_line(update, 80)
                        for update in updates[:6]
                        if PrivateCompanionPageApi._single_line(update, 80)
                    ]
                    if isinstance(updates, list)
                    else [],
                }
            )
        return items

    @staticmethod
    def _limited_story_items(value: Any, limit: int) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        items: list[dict[str, str]] = []
        for item in value[:limit]:
            if not isinstance(item, dict):
                continue
            items.append(
                {
                    "window": PrivateCompanionPageApi._single_line(item.get("window") or item.get("time"), 24),
                    "text": PrivateCompanionPageApi._single_line(
                        item.get("event")
                        or item.get("topic")
                        or item.get("summary")
                        or item.get("text")
                        or item.get("content"),
                        160,
                    ),
                    "mood": PrivateCompanionPageApi._single_line(item.get("mood"), 24),
                    "action": PrivateCompanionPageApi._single_line(item.get("action"), 24),
                    "reason": PrivateCompanionPageApi._single_line(item.get("reason"), 32),
                }
            )
        return items

    @staticmethod
    def _limited_adjustments(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        items: list[dict[str, Any]] = []
        for item in value[-10:]:
            if not isinstance(item, dict):
                continue
            updates = item.get("state_updates")
            items.append(
                {
                    "date": PrivateCompanionPageApi._single_line(item.get("date"), 12),
                    "source": PrivateCompanionPageApi._single_line(item.get("source"), 24),
                    "note": PrivateCompanionPageApi._single_line(item.get("note"), 140),
                    "reaction": PrivateCompanionPageApi._single_line(item.get("immediate_reaction"), 140),
                    "state_updates": [
                        PrivateCompanionPageApi._single_line(update, 80)
                        for update in updates[:6]
                        if PrivateCompanionPageApi._single_line(update, 80)
                    ]
                    if isinstance(updates, list)
                    else [],
                }
            )
        return items

    @staticmethod
    def _limited_list(value: Any, limit: int) -> list[Any]:
        return list(value[:limit]) if isinstance(value, list) else []

    @staticmethod
    def _memory_item_count(memory: Any) -> int:
        if not isinstance(memory, dict):
            return 0
        count = 0
        for value in memory.values():
            if isinstance(value, list):
                count += len(value)
            elif value:
                count += 1
        return count

    @staticmethod
    def _query_int(name: str, default: int, minimum: int, maximum: int) -> int:
        raw = request.args.get(name, default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default
        return max(minimum, min(maximum, value))

    @staticmethod
    def _normalize_id_list(value: Any) -> list[str]:
        if isinstance(value, str):
            raw_items = value.replace("，", ",").replace("\n", ",").split(",")
        elif isinstance(value, list):
            raw_items = value
        else:
            raw_items = []
        result: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            text = PrivateCompanionPageApi._single_line(item, 64)
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    @staticmethod
    def _single_line(value: Any, limit: int) -> str:
        text = " ".join(str(value or "").strip().split())
        return text[:limit]

    @staticmethod
    def _ok(data: Any = None) -> dict[str, Any]:
        return {"success": True, "data": data, "ts": int(time.time())}

    @staticmethod
    def _error(message: str) -> dict[str, Any]:
        return {"success": False, "error": str(message), "ts": int(time.time())}
