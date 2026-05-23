const HTTP_API = "/astrbot_plugin_private_companion/page";
const PAGE_ENDPOINT_PREFIX = "page";

const state = {
  overview: null,
  users: [],
  groups: [],
  diagnostics: [],
  availableProviders: [],
  selectedUserId: "",
  selectedGroupId: "",
  featureDraft: {},
};

const providerLabels = {
  LLM_PROVIDER_ID: "主模型",
  MAI_STYLE_PROVIDER_ID: "陪伴通用模型",
  RESPONSE_REVIEW_PROVIDER_ID: "回复自检改写",
  RELATIONSHIP_ANALYSIS_PROVIDER_ID: "关系站位分析",
  COMPANION_MEMORY_PROVIDER_ID: "长期画像整理",
  DIALOGUE_EPISODE_PROVIDER_ID: "私聊片段整理",
  GROUP_INTERJECT_PROVIDER_ID: "群聊主动插话",
  GROUP_EPISODE_PROVIDER_ID: "群聊片段整理",
  GROUP_SLANG_PROVIDER_ID: "群内黑话释义",
};

const providerDescriptions = {
  LLM_PROVIDER_ID: "基础兜底模型。主动消息、未指定模型的任务都会向这里回退。",
  MAI_STYLE_PROVIDER_ID: "陪伴风格通用模型。建议选择稳定、便宜、会写自然口语的模型。",
  RESPONSE_REVIEW_PROVIDER_ID: "对生成回复做自检和轻改写，减少生硬、越界、解释提示词等问题。",
  RELATIONSHIP_ANALYSIS_PROVIDER_ID: "分析关系阶段、亲近度和互动边界，调用频率不高但影响语气判断。",
  COMPANION_MEMORY_PROVIDER_ID: "整理长期画像和偏好，适合用便宜但结构化能力好的模型。",
  DIALOGUE_EPISODE_PROVIDER_ID: "把私聊对话压成可复用片段，用于后续自然接话。",
  GROUP_INTERJECT_PROVIDER_ID: "群聊主动插话专用。建议选择短文本质量好、反应稳的模型。",
  GROUP_EPISODE_PROVIDER_ID: "整理群聊片段、群氛围和话题线，主要用于群聊观察。",
  GROUP_SLANG_PROVIDER_ID: "解释群内黑话、梗和成员称呼，适合用小模型。",
};

const featureMeta = {
  enable_mai_style_integration: ["陪伴风格整合", "把关系站位、记忆和自然对话规则注入回复。"],
  enable_companion_memory: ["长期画像", "沉淀用户偏好、边界、关系线索和可复用事实。"],
  enable_expression_learning: ["表达学习", "学习用户常用短句、语气和称呼，提升贴近感。"],
  enable_companion_reply_planner: ["回复规划", "先判断接话策略，再生成回复，减少机械问答。"],
  enable_intent_emotion_analysis: ["意图情绪", "识别用户情绪和真实意图，用于关系与回复策略。"],
  enable_response_self_review: ["回复自检", "发送前检查是否生硬、越界、太像系统提示。"],
  enable_passive_topic_suppression: ["话题抑制", "避免短时间反复主动提同一个话题。"],
  enable_relationship_state_machine: ["关系状态机", "维护陌生、熟悉、亲近等关系阶段。"],
  enable_dialogue_episode_memory: ["私聊片段", "把连续对话整理成共同经历和可续话头。"],
  enable_open_loop_tracking: ["未完话头", "记录用户提到的待办、约定、之后再说的事。"],
  enable_group_companion: ["群聊总开关", "控制是否处理群聊观察、画像、黑话和上下文注入。"],
  enable_group_slang_learning: ["群黑话学习", "记录群内常用梗、简称和特殊表达。"],
  enable_group_member_profiles: ["群成员画像", "记录成员发言习惯和群内角色，帮助判断气氛。"],
  enable_group_context_injection: ["群上下文注入", "在群聊回复时加入群氛围、话题和成员信息。"],
  enable_group_interjection: ["群主动插话", "允许 Bot 在群聊里主动插一句。谨慎开启。"],
  enable_group_topic_threads: ["群话题线", "维护当前群聊正在聊什么，以及话题如何变化。"],
  enable_group_episode_memory: ["群聊片段", "把群聊阶段性内容整理成摘要片段。"],
  enable_group_interjection_feedback: ["插话反馈", "记录群友对主动插话的反应，后续调整频率。"],
  enable_group_slang_meanings: ["黑话释义", "尝试解释黑话含义，方便后续理解群语境。"],
  enable_group_relationship_graph: ["群关系网", "记录成员之间的互动关系和常见组合。"],
  enable_group_privacy_guard: ["群隐私保护", "避免把私聊记忆和私下关系泄露到群聊。建议开启。"],
  enable_livingmemory_integration: ["LivingMemory 协同", "引导模型按需调用长期记忆工具，避免重复造轮子。"],
};

const configLabels = {
  enabled_user_count: "启用私聊对象",
  user_count: "私聊对象总数",
  require_opt_in: "是否需要私聊确认",
  max_daily_messages: "每日主动上限",
  idle_minutes: "空闲门槛分钟",
  min_interval_minutes: "最小主动间隔分钟",
  enabled: "群聊总开关",
  group_count: "群记录总数",
  enabled_group_count: "启用群数量",
  access_mode: "名单模式",
  whitelist: "白名单",
  blacklist: "黑名单",
  interjection_enabled: "群主动插话",
};

const presetCatalog = {
  safe: {
    label: "保守低打扰",
    desc: "降低主动频率，保留学习和自检，适合先稳定观察。",
  },
  standard: {
    label: "标准陪伴",
    desc: "私聊学习、片段记忆和群聊上下文都保持均衡。",
  },
  active: {
    label: "高互动学习",
    desc: "更积极地学习表达和触发主动互动，模型调用量会增加。",
  },
  group_observer: {
    label: "群聊观察优先",
    desc: "强化群画像、黑话、话题线和关系网，默认不主动插话。",
  },
};

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function fetchJson(path, options = {}) {
  const bridge = await waitForBridge();
  const method = (options.method || "GET").toUpperCase();
  let payload;

  if (bridge && typeof bridge.apiGet === "function" && typeof bridge.apiPost === "function") {
    payload = await bridgeRequest(bridge, path, method, options.body);
  } else if (new URLSearchParams(window.location.search).get("debug_http") === "1") {
    const response = await fetch(`${HTTP_API}${path}`, {
      cache: "no-store",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      ...options,
    });
    const text = await response.text();
    try {
      payload = text ? JSON.parse(text) : {};
    } catch (error) {
      throw new Error(response.ok ? "返回内容不是 JSON" : `HTTP ${response.status}: ${text.slice(0, 120)}`);
    }
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  } else {
    throw new Error("未检测到 AstrBot 官方插件 Page 桥接，请从 AstrBot 后台的插件拓展页打开");
  }

  payload = normalizeResponse(payload);
  if (!payload.success) throw new Error(payload.error || "请求失败");
  return payload.data;
}

function getBridge() {
  if (window.AstrBotPluginPage) return window.AstrBotPluginPage;
  try {
    if (window.parent && window.parent !== window && window.parent.AstrBotPluginPage) {
      return window.parent.AstrBotPluginPage;
    }
  } catch (error) {
    return null;
  }
  return null;
}

async function waitForBridge(timeoutMs = 2500) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const bridge = getBridge();
    if (bridge && typeof bridge.apiGet === "function" && typeof bridge.apiPost === "function") {
      return bridge;
    }
    await new Promise((resolve) => setTimeout(resolve, 80));
  }
  return getBridge();
}

async function bridgeRequest(bridge, path, method, body) {
  const url = new URL(path, "https://astrbot-plugin-page.local/");
  const endpoint = `${PAGE_ENDPOINT_PREFIX}/${url.pathname.replace(/^\/+/, "")}`.replace(/\/+/g, "/");

  if (method === "GET") {
    const params = Object.fromEntries(url.searchParams.entries());
    return bridge.apiGet(endpoint, Object.keys(params).length ? params : undefined);
  }

  let payload = body || {};
  if (typeof payload === "string") {
    try {
      payload = JSON.parse(payload);
    } catch (error) {
      payload = {};
    }
  }
  return bridge.apiPost(endpoint, payload);
}

function normalizeResponse(payload) {
  if (payload && typeof payload === "object" && Object.prototype.hasOwnProperty.call(payload, "success")) {
    return payload;
  }
  return { success: true, data: payload };
}

function postJson(path, body) {
  return fetchJson(path, { method: "POST", body: JSON.stringify(body) });
}

async function loadAll() {
  $("#subtitle").textContent = "读取运行态中...";
  try {
    const [overview, users, groups, diagnostics, availableProviders] = await Promise.all([
      fetchJson("/overview"),
      fetchJson("/users?limit=300"),
      fetchJson("/groups?limit=300"),
      fetchJson("/diagnostics"),
      fetchJson("/providers/available"),
    ]);
    state.overview = overview;
    state.users = users.items || [];
    state.groups = groups.items || [];
    state.diagnostics = diagnostics.items || [];
    state.availableProviders = availableProviders.items || [];
    state.featureDraft = { ...(overview.features || {}) };
    if (!state.selectedUserId && state.users[0]) state.selectedUserId = state.users[0].user_id;
    if (!state.selectedGroupId && state.groups[0]) state.selectedGroupId = state.groups[0].group_id;
    renderAll();
    $("#subtitle").textContent = `${overview.plugin.bot_name || "Private Companion"} · ${new Date().toLocaleString()}`;
  } catch (error) {
    $("#subtitle").textContent = `加载失败：${error.message}`;
  }
}

function renderAll() {
  renderStats();
  renderDashboard();
  renderUsers();
  renderGroups();
  renderMemory();
  renderModuleSettings();
  renderConfig();
  renderProviders();
}

function renderStats() {
  const overview = state.overview || {};
  const privateInfo = overview.private || {};
  const groupInfo = overview.group || {};
  const living = overview.livingmemory || {};
  $("#stats").innerHTML = [
    statCard(privateInfo.enabled_user_count || 0, `私聊对象 / 共 ${privateInfo.user_count || 0}`),
    statCard(groupInfo.enabled_group_count || 0, `群聊观测 / 共 ${groupInfo.group_count || 0}`),
    statCard(groupInfo.access_mode || "-", "群聊名单模式"),
    statCard(living.available ? "可用" : "未检测", "LivingMemory"),
  ].join("");
}

function statCard(value, label) {
  return `<article class="stat"><b>${escapeHtml(value)}</b><span>${escapeHtml(label)}</span></article>`;
}

function renderDashboard() {
  renderHealthPanel();
  renderDiagnostics();
  renderRelationshipChart();
  renderGroupBubbleChart();
  renderQuotaChart();
  renderFeatureMatrix();
  renderActivityHeatmap();
}

function renderHealthPanel() {
  const overview = state.overview || {};
  const providers = overview.providers || {};
  const group = overview.group || {};
  const privateInfo = overview.private || {};
  const features = overview.features || {};
  const items = [
    {
      level: providers.LLM_PROVIDER_ID ? "ok" : "warn",
      title: providers.LLM_PROVIDER_ID ? "主模型已配置" : "主模型未单独配置",
      text: providers.LLM_PROVIDER_ID || "会回退到 AstrBot 默认模型",
    },
    {
      level: privateInfo.max_daily_messages > 0 ? "ok" : "warn",
      title: privateInfo.max_daily_messages > 0 ? "私聊主动可用" : "私聊主动已禁用",
      text: `每日主动上限：${privateInfo.max_daily_messages || 0}`,
    },
    {
      level: group.enabled ? "ok" : "warn",
      title: group.enabled ? "群聊观察已开启" : "群聊观察未开启",
      text: `${group.access_mode || "whitelist"} 模式，记录 ${group.group_count || 0} 个群`,
    },
    {
      level: features.enable_livingmemory_integration && overview.livingmemory?.available ? "ok" : "info",
      title: "LivingMemory 协同",
      text: livingMemoryHealthText(overview.livingmemory),
    },
  ];
  $("#healthPanel").innerHTML = items.map((item) => `
    <div class="health-item ${escapeHtml(item.level)}">
      <b>${escapeHtml(item.title)}</b>
      <span>${escapeHtml(item.text)}</span>
    </div>
  `).join("");
}

function livingMemoryHealthText(livingmemory) {
  if (!livingmemory?.enabled) return "协同开关未启用";
  if (!livingmemory?.available) return `未检测到可用插件：${livingmemory?.plugin_dir || "未知路径"}`;
  return `可用 · ${livingmemory.tool_name || "recall_long_term_memory"}`;
}

function renderDiagnostics() {
  const items = state.diagnostics || [];
  $("#diagnosticPanel").innerHTML = items.length
    ? items.map((item) => `
      <div class="diagnostic-item ${escapeHtml(item.level || "info")}">
        <span class="diag-dot"></span>
        <div>
          <b>${escapeHtml(item.title || "")}</b>
          <p>${escapeHtml(item.text || "")}</p>
          ${item.action ? `<small>${escapeHtml(item.action)}</small>` : ""}
        </div>
      </div>
    `).join("")
    : `<div class="empty small">暂无诊断项</div>`;
}

function renderRelationshipChart() {
  const buckets = { 亲近: 0, 熟悉: 0, 陌生: 0, 未分层: 0 };
  state.users.forEach((user) => {
    const stage = user.relationship_stage || "未分层";
    buckets[Object.prototype.hasOwnProperty.call(buckets, stage) ? stage : "未分层"] += 1;
  });
  $("#relationshipChart").innerHTML = horizontalBars(buckets, Math.max(1, state.users.length));
}

function renderQuotaChart() {
  const maxDaily = Number(state.overview?.private?.max_daily_messages || 0);
  const rows = state.users.slice(0, 12).map((user) => {
    const used = Number(user.sent_today || 0);
    const pct = maxDaily > 0 ? Math.min(100, Math.round((used / maxDaily) * 100)) : 0;
    return `
      <div class="meter-row">
        <span>${escapeHtml(user.nickname || user.user_id)}</span>
        <div class="meter"><i style="width:${pct}%"></i></div>
        <b>${escapeHtml(used)}${maxDaily ? `/${escapeHtml(maxDaily)}` : ""}</b>
      </div>
    `;
  });
  $("#quotaChart").innerHTML = rows.length ? rows.join("") : `<div class="empty small">暂无私聊对象</div>`;
}

function renderGroupBubbleChart() {
  const groups = state.groups.slice(0, 12);
  if (!groups.length) {
    $("#groupBubbleChart").innerHTML = `<div class="empty small">暂无群聊数据</div>`;
    return;
  }
  const maxMessages = Math.max(1, ...groups.map((group) => Number(group.message_count || 0)));
  $("#groupBubbleChart").innerHTML = `
    <div class="bubble-wrap">
      ${groups.map((group) => {
        const size = 42 + Math.round((Number(group.message_count || 0) / maxMessages) * 56);
        return `
          <button class="bubble ${group.enabled ? "" : "off"}" data-bubble-group="${escapeHtml(group.group_id)}" style="width:${size}px;height:${size}px">
            <span>${escapeHtml(group.group_id)}</span>
            <small>${escapeHtml(group.message_count || 0)}</small>
          </button>
        `;
      }).join("")}
    </div>
  `;
  document.querySelectorAll("[data-bubble-group]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedGroupId = button.dataset.bubbleGroup;
      switchTab("group");
      renderGroups();
      renderGroupDetail(true);
    });
  });
}

function renderFeatureMatrix() {
  const groups = [
    ["陪伴", ["enable_mai_style_integration", "enable_expression_learning", "enable_response_self_review", "enable_dialogue_episode_memory"]],
    ["群聊", ["enable_group_companion", "enable_group_context_injection", "enable_group_slang_learning", "enable_group_topic_threads", "enable_group_relationship_graph"]],
    ["记忆", ["enable_companion_memory", "enable_open_loop_tracking", "enable_livingmemory_integration"]],
  ];
  $("#featureMatrix").innerHTML = groups.map(([label, keys]) => `
    <section>
      <h3>${escapeHtml(label)}</h3>
      ${keys.map((key) => `<span class="feature-dot ${state.overview?.features?.[key] ? "on" : "off"}" title="${escapeHtml(key)}">${escapeHtml(key.replace(/^enable_/, ""))}</span>`).join("")}
    </section>
  `).join("");
}

function renderActivityHeatmap() {
  const now = Math.floor(Date.now() / 1000);
  const buckets = Array.from({ length: 24 }, (_, hour) => ({ hour, count: 0 }));
  [...state.users, ...state.groups].forEach((item) => {
    const ts = Number(item.last_seen_ts || 0);
    if (!ts || now - ts > 86400) return;
    buckets[new Date(ts * 1000).getHours()].count += 1;
  });
  const max = Math.max(1, ...buckets.map((item) => item.count));
  $("#activityHeatmap").innerHTML = buckets.map((item) => {
    const level = Math.min(4, Math.ceil((item.count / max) * 4));
    return `<span class="heat level-${level}" title="${item.hour}:00-${item.hour + 1}:00 · ${item.count}">${item.hour}</span>`;
  }).join("");
}

function horizontalBars(data, total) {
  return Object.entries(data).map(([label, count]) => {
    const pct = Math.round((count / total) * 100);
    return `
      <div class="meter-row">
        <span>${escapeHtml(label)}</span>
        <div class="meter"><i style="width:${pct}%"></i></div>
        <b>${escapeHtml(count)}</b>
      </div>
    `;
  }).join("");
}

function renderUsers() {
  const keyword = ($("#userFilter").value || "").trim().toLowerCase();
  const rows = state.users.filter((user) => {
    const text = `${user.user_id} ${user.nickname} ${user.umo}`.toLowerCase();
    return !keyword || text.includes(keyword);
  });
  $("#userRows").innerHTML = rows.length
    ? rows.map((user) => `
      <tr data-user-id="${escapeHtml(user.user_id)}" class="${user.user_id === state.selectedUserId ? "is-selected" : ""}">
        <td><strong>${escapeHtml(user.nickname || user.user_id)}</strong><br><span class="muted">${escapeHtml(user.user_id)}</span></td>
        <td><span class="badge ${user.enabled ? "" : "off"}">${escapeHtml(user.enabled ? "启用" : "停用")}</span> <span class="muted">${escapeHtml(user.relationship_stage || "未分层")}</span><br><span>分数 ${escapeHtml(user.relationship_score)}</span></td>
        <td>入站 ${escapeHtml(user.inbound_count)} · 回复 ${escapeHtml(user.reply_count)}<br><span class="muted">记忆 ${escapeHtml(user.memory_items)} 条</span></td>
        <td>今日 ${escapeHtml(user.sent_today)} · 总计 ${escapeHtml(user.proactive_sent_count)}<br><span class="muted">${escapeHtml(user.next_proactive)}</span></td>
        <td>${escapeHtml(user.last_seen)}<br><span class="muted">上次主动 ${escapeHtml(user.last_sent)}</span></td>
      </tr>
    `).join("")
    : `<tr><td class="empty" colspan="5">暂无私聊对象</td></tr>`;
  document.querySelectorAll("[data-user-id]").forEach((row) => {
    row.addEventListener("click", async () => {
      state.selectedUserId = row.dataset.userId;
      renderUsers();
      await renderUserDetail(true);
    });
  });
  renderUserDetail();
}

async function renderUserDetail(forceFetch = false) {
  const box = $("#userDetail");
  if (!state.selectedUserId) {
    box.innerHTML = "";
    return;
  }
  let detail = state.users.find((user) => user.user_id === state.selectedUserId);
  if (forceFetch || !detail?.formatted) {
    try {
      detail = await fetchJson(`/user?user_id=${encodeURIComponent(state.selectedUserId)}`);
    } catch (error) {
      box.innerHTML = `<p class="muted">详情读取失败：${escapeHtml(error.message)}</p>`;
      return;
    }
  }
  box.innerHTML = `
    <div class="toolbar">
      <button data-user-action="toggle">${escapeHtml(detail.enabled ? "停用私聊陪伴" : "启用私聊陪伴")}</button>
      <button data-user-action="reset_daily">重置今日额度</button>
      <button data-user-action="clear_schedule">清空主动计划</button>
      <button data-user-action="clear_learning" class="danger">清空学习记忆</button>
    </div>
    <form id="userEditForm" class="inline-form">
      <label>称呼 <input name="nickname" value="${escapeHtml(detail.nickname || "")}" placeholder="例如 主人 / 名字" /></label>
      <label>语气 <input name="style" value="${escapeHtml(detail.style || "")}" placeholder="温柔 / 活泼 / 工作" /></label>
      <button type="submit">保存</button>
    </form>
    <div class="visual-strip">
      ${scoreGauge("关系分", detail.relationship_score || 0, -20, 40)}
      ${scoreGauge("今日主动", detail.sent_today || 0, 0, Math.max(1, state.overview?.private?.max_daily_messages || 8))}
      ${miniStat("片段", detail.dialogue_episode_count || (detail.dialogue_episodes || []).length)}
      ${miniStat("未完话头", detail.open_loop_count || (detail.open_loops || []).length)}
    </div>
    <div class="detail-grid">
      ${detailBlock("关系和主动", detail.formatted?.relationship || "", [["下次主动", detail.formatted?.next_proactive || detail.next_proactive], ["动作偏好", detail.formatted?.action_affinity || ""]])}
      ${detailBlock("最近对话", "", [["用户", detail.last_user_message || ""], ["陪伴", detail.last_companion_message || ""]])}
      ${detailBlock("对话片段", "", (detail.dialogue_episodes || []).map((item, index) => [`#${index + 1}`, item.summary || item.title || JSON.stringify(item)]))}
      ${detailBlock("未完话头", "", (detail.open_loops || []).map((item, index) => [`#${index + 1}`, item.text || item.topic || JSON.stringify(item)]))}
    </div>
  `;
  bindUserActions(detail);
}

function bindUserActions(detail) {
  $("#userEditForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await runAction(() => postJson("/user/update", {
      user_id: detail.user_id,
      nickname: form.get("nickname"),
      style: form.get("style"),
    }));
  });
  document.querySelectorAll("[data-user-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.userAction;
      const body = { user_id: detail.user_id };
      if (action === "toggle") body.enabled = !detail.enabled;
      if (action === "reset_daily") body.reset_daily = true;
      if (action === "clear_schedule") body.clear_schedule = true;
      if (action === "clear_learning" && !confirm("确定清空该用户的学习记忆、片段和未完话头吗？")) return;
      if (action === "clear_learning") body.clear_learning = true;
      await runAction(() => postJson("/user/update", body));
    });
  });
}

function renderGroups() {
  const keyword = ($("#groupFilter").value || "").trim().toLowerCase();
  const rows = state.groups.filter((group) => !keyword || String(group.group_id).toLowerCase().includes(keyword));
  $("#groupRows").innerHTML = rows.length
    ? rows.map((group) => `
      <tr data-group-id="${escapeHtml(group.group_id)}" class="${group.group_id === state.selectedGroupId ? "is-selected" : ""}">
        <td><strong>${escapeHtml(group.group_id)}</strong><br><span class="muted">${escapeHtml(group.enabled ? "观测中" : "已停用")}</span></td>
        <td><span class="badge ${group.allowed_by_mode ? "" : "off"}">${escapeHtml(group.allowed_by_mode ? "允许" : "名单拦截")}</span><br><span class="muted">今日插话 ${escapeHtml(group.interject_today)}</span></td>
        <td>${escapeHtml(group.atmosphere?.mood || "未判断")}<br><span class="muted">${escapeHtml(group.atmosphere?.last_summary || "")}</span></td>
        <td>消息 ${escapeHtml(group.message_count)} · 群友 ${escapeHtml(group.member_count)}<br><span class="muted">黑话 ${escapeHtml(group.slang_count)} · 话题 ${escapeHtml(group.topic_count)}</span></td>
        <td>${escapeHtml(group.last_seen)}<br><span class="muted">上次插话 ${escapeHtml(group.last_interject)}</span></td>
      </tr>
    `).join("")
    : `<tr><td class="empty" colspan="5">暂无群聊观测数据</td></tr>`;
  document.querySelectorAll("[data-group-id]").forEach((row) => {
    row.addEventListener("click", async () => {
      state.selectedGroupId = row.dataset.groupId;
      renderGroups();
      await renderGroupDetail(true);
    });
  });
  renderGroupDetail();
}

async function renderGroupDetail(forceFetch = false) {
  const box = $("#groupDetail");
  if (!state.selectedGroupId) {
    box.innerHTML = "";
    return;
  }
  let detail = state.groups.find((group) => group.group_id === state.selectedGroupId);
  if (forceFetch || !detail?.formatted) {
    try {
      detail = await fetchJson(`/group?group_id=${encodeURIComponent(state.selectedGroupId)}`);
    } catch (error) {
      box.innerHTML = `<p class="muted">详情读取失败：${escapeHtml(error.message)}</p>`;
      return;
    }
  }
  const topics = (detail.topic_threads || []).map((item, index) => [`#${index + 1}`, item.topic || item.summary || JSON.stringify(item)]);
  const episodes = (detail.group_episodes || []).map((item, index) => [`#${index + 1}`, item.summary || item.title || JSON.stringify(item)]);
  box.innerHTML = `
    <div class="toolbar">
      <button data-group-action="toggle">${escapeHtml(detail.enabled ? "停用群聊观测" : "启用群聊观测")}</button>
      <button data-group-action="reset_interjection">重置插话反馈</button>
      <button data-group-action="clear_observation" class="danger">清空群聊观测</button>
    </div>
    <div class="visual-strip">
      ${miniStat("消息", detail.message_count || 0)}
      ${miniStat("群友", detail.member_count || Object.keys(detail.members || {}).length)}
      ${miniStat("黑话", detail.slang_count || (detail.slang_terms || []).length)}
      ${miniStat("话题", detail.topic_count || (detail.topic_threads || []).length)}
    </div>
    <div class="detail-grid">
      ${detailBlock("群状态", detail.formatted?.status || "", [["常用词", formatSlangTerms(detail.slang_terms || [])]])}
      <section class="detail-block"><h2>关系网</h2>${relationshipGraphSvg(detail.relationship_edges || {})}</section>
      <section class="detail-block"><h2>消息活跃</h2>${messageTimelineSvg(detail.recent_messages || [])}</section>
      ${detailBlock("插话反馈", detail.formatted?.feedback || "", [])}
      ${detailBlock("话题线", "", topics)}
      ${detailBlock("群聊片段", "", episodes)}
      ${detailBlock("关系网摘要", detail.formatted?.relationship_graph || "", [])}
    </div>
  `;
  bindGroupActions(detail);
}

function bindGroupActions(detail) {
  document.querySelectorAll("[data-group-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.groupAction;
      const body = { group_id: detail.group_id };
      if (action === "toggle") body.enabled = !detail.enabled;
      if (action === "reset_interjection") body.reset_interjection = true;
      if (action === "clear_observation" && !confirm("确定清空该群的观测数据、黑话、话题和关系网吗？")) return;
      if (action === "clear_observation") body.clear_observation = true;
      await runAction(() => postJson("/group/update", body));
    });
  });
}

function renderMemory() {
  const overview = state.overview || {};
  $("#livingMemoryBox").textContent = overview.livingmemory?.status || "未读取到 LivingMemory 状态";
  renderDl("#dailyState", overview.daily_state || {});
  renderDailyTimeline();
  renderInteractionImpact();
  renderMemoryComposition();
  renderSlangCloud();
}

function renderDailyTimeline() {
  const timeline = state.overview?.daily_timeline || {};
  const segments = timeline.segments || [];
  if (!segments.length) {
    $("#dailyTimeline").innerHTML = `<div class="empty small">暂无细化时间段。生成今日细化后会展示状态变化。</div>`;
    return;
  }
  $("#dailyTimeline").innerHTML = segments.map((segment) => {
    const vars = (segment.state_variables || []).slice(0, 4);
    const events = (segment.today_events || []).slice(0, 3);
    const presence = segment.presence_status || {};
    return `
      <section class="timeline-item">
        <div class="timeline-time">${escapeHtml(segment.window || segment.key)}</div>
        <div class="timeline-body">
          <div class="timeline-head">
            <b>${escapeHtml(segment.summary || "这一段还没有摘要")}</b>
            <span>${escapeHtml(presenceLabel(presence))}</span>
          </div>
          <div class="state-pills">
            ${vars.length ? vars.map((item) => `
              <span title="${escapeHtml(item.note || "")}">
                <b>${escapeHtml(item.name || "-")}</b>${escapeHtml(item.value || "-")}
              </span>
            `).join("") : `<span>暂无状态变量</span>`}
          </div>
          <ul>
            ${events.length ? events.map((item) => `<li>${escapeHtml(item.window ? `${item.window} · ${item.text}` : item.text)}</li>`).join("") : `<li>暂无细化事件</li>`}
          </ul>
        </div>
      </section>
    `;
  }).join("");
}

function renderInteractionImpact() {
  const timeline = state.overview?.daily_timeline || {};
  const segmentUpdates = [];
  (timeline.segments || []).forEach((segment) => {
    (segment.interaction_updates || []).forEach((item) => {
      segmentUpdates.push({ ...item, window: segment.window });
    });
  });
  const adjustments = (timeline.adjustments || []).map((item) => ({
    at: item.date || "",
    source: item.source,
    reaction: item.reaction || item.note,
    state_updates: item.state_updates || [],
    window: "全局影响",
  }));
  const items = [...segmentUpdates, ...adjustments].filter((item) => item.reaction || item.state_updates?.length);
  if (!items.length) {
    $("#interactionImpact").innerHTML = `<div class="empty small">暂无用户介入影响。用户的关心、提醒、帮助、回应会在这里留下状态偏移。</div>`;
    return;
  }
  $("#interactionImpact").innerHTML = items.slice(-12).reverse().map((item) => `
    <section class="impact-item">
      <div>
        <b>${escapeHtml(item.source || "用户影响")}</b>
        <span>${escapeHtml([item.window, item.at].filter(Boolean).join(" · "))}</span>
      </div>
      <p>${escapeHtml(item.reaction || "")}</p>
      <div class="state-pills">
        ${(item.state_updates || []).map((update) => `<span>${escapeHtml(update)}</span>`).join("")}
      </div>
    </section>
  `).join("");
}

function presenceLabel(presence) {
  const mode = String(presence?.mode || "unchanged");
  const text = presence?.custom_text || presence?.wording || "";
  if (mode === "custom" && text) return `自定义状态：${text}`;
  if (mode === "sleep") return "状态：休息中";
  if (mode === "online") return "状态：在线";
  return "状态：不变";
}

function renderMemoryComposition() {
  const data = {
    "原始记忆": state.users.reduce((sum, user) => sum + Number(user.memory_items || 0), 0),
    "私聊片段": state.users.reduce((sum, user) => sum + Number(user.dialogue_episode_count || 0), 0),
    "未完话头": state.users.reduce((sum, user) => sum + Number(user.open_loop_count || 0), 0),
    "群聊片段": state.groups.reduce((sum, group) => sum + Number(group.episode_count || 0), 0),
    "群聊话题": state.groups.reduce((sum, group) => sum + Number(group.topic_count || 0), 0),
  };
  $("#memoryComposition").innerHTML = donutChart(data);
}

function renderSlangCloud() {
  const counts = new Map();
  state.groups.forEach((group) => {
    (group.slang_terms || []).forEach((item, index) => {
      const term = slangTermText(item);
      if (!term) return;
      counts.set(term, (counts.get(term) || 0) + Math.max(1, 16 - index));
    });
  });
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 36);
  if (!entries.length) {
    $("#slangCloud").innerHTML = `<div class="empty small">暂无群聊黑话</div>`;
    return;
  }
  const max = Math.max(1, ...entries.map(([, count]) => count));
  $("#slangCloud").innerHTML = entries.map(([term, count]) => {
    const size = 12 + Math.round((count / max) * 16);
    return `<span style="font-size:${size}px">${escapeHtml(term)}</span>`;
  }).join("");
}

function slangTermText(item) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return "";
  return String(
    item.term
      || item.word
      || item.text
      || item.name
      || item.key
      || item.phrase
      || item.slang
      || ""
  ).trim();
}

function formatSlangTerms(items) {
  const terms = (Array.isArray(items) ? items : [])
    .map(slangTermText)
    .filter(Boolean);
  return terms.length ? terms.join("、") : "暂无";
}

function renderConfig() {
  const overview = state.overview || {};
  const group = overview.group || {};
  renderDl("#privateConfig", overview.private || {});
  renderDl("#groupConfig", group);
  $("#groupAccessMode").value = group.access_mode || "whitelist";
  $("#groupWhitelist").value = (group.whitelist || []).join("\n");
  $("#groupBlacklist").value = (group.blacklist || []).join("\n");
  renderListCoverage(group);
  $("#featureFlags").innerHTML = Object.entries(state.featureDraft)
    .map(([key, value]) => `
      <label class="switch-chip" title="${escapeHtml(featureDescription(key))}">
        <input type="checkbox" data-feature-key="${escapeHtml(key)}" ${value ? "checked" : ""}>
        <span><b>${escapeHtml(featureLabel(key))}</b><small>${escapeHtml(key)}</small></span>
      </label>
    `).join("");
  document.querySelectorAll("[data-feature-key]").forEach((input) => {
    input.addEventListener("change", () => {
      state.featureDraft[input.dataset.featureKey] = input.checked;
    });
  });
}

function renderModuleSettings() {
  const settings = state.overview?.settings || {};
  fillForm("#quickModuleForm", settings);
  fillForm("#privateModuleForm", settings);
  fillForm("#groupModuleForm", settings);
  fillForm("#memoryModuleForm", settings);
  const targetBox = document.querySelector('#quickModuleForm [name="target_user_ids"]');
  if (targetBox) targetBox.value = Array.isArray(settings.target_user_ids) ? settings.target_user_ids.join("\n") : "";
  renderPresetCards();
}

function renderPresetCards() {
  $("#presetCards").innerHTML = Object.entries(presetCatalog).map(([key, preset]) => `
    <section class="preset-card">
      <div>
        <b>${escapeHtml(preset.label)}</b>
        <p>${escapeHtml(preset.desc)}</p>
      </div>
      <button type="button" data-preset="${escapeHtml(key)}">应用</button>
    </section>
  `).join("");
  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!confirm(`应用“${presetCatalog[button.dataset.preset]?.label || button.dataset.preset}”预设？`)) return;
      await runAction(() => postJson("/preset/apply", { name: button.dataset.preset }));
    });
  });
}

function fillForm(selector, values) {
  const form = $(selector);
  if (!form) return;
  form.querySelectorAll("[name]").forEach((input) => {
    const value = values[input.name];
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
    } else if (Array.isArray(value)) {
      input.value = value.join("\n");
    } else {
      input.value = value ?? "";
    }
  });
}

function collectFormSettings(selector) {
  const form = $(selector);
  const result = {};
  if (!form) return result;
  form.querySelectorAll("[name]").forEach((input) => {
    if (input.type === "checkbox") {
      result[input.name] = input.checked;
    } else if (input.type === "number") {
      result[input.name] = Number(input.value || 0);
    } else {
      result[input.name] = input.value;
    }
  });
  return result;
}

function renderListCoverage(group) {
  const whitelist = new Set(group.whitelist || []);
  const blacklist = new Set(group.blacklist || []);
  const rows = state.groups.map((item) => {
    const inWhite = whitelist.has(item.group_id);
    const inBlack = blacklist.has(item.group_id);
    const allowed = group.access_mode === "blacklist" ? !inBlack : inWhite;
    return `
      <div class="coverage-item ${allowed ? "ok" : "blocked"}">
        <b>${escapeHtml(item.group_id)}</b>
        <span>${escapeHtml(allowed ? "允许" : "拦截")} · ${escapeHtml(inWhite ? "白名单" : inBlack ? "黑名单" : "未列入")}</span>
      </div>
    `;
  });
  $("#listCoverage").innerHTML = rows.length ? rows.join("") : `<div class="empty small">暂无群聊记录</div>`;
}

function renderProviders() {
  const providers = state.overview?.providers || {};
  renderProviderFlow(providers);
  $("#providerForm").innerHTML = Object.entries(providerLabels).map(([key, label]) => `
    <label class="provider-card">
      <span>${escapeHtml(label)}</span>
      <small>${escapeHtml(providerDescriptions[key] || "选择一个 AstrBot 已配置 Provider，或手动输入 Provider ID。")}</small>
      ${providerSelect(key, providers[key] || "")}
      <span class="provider-row">
        <span class="hint">${escapeHtml(key)}</span>
        <button type="button" data-provider-test="${escapeHtml(key)}">测试</button>
      </span>
      <span class="provider-status" data-provider-status="${escapeHtml(key)}"></span>
    </label>
  `).join("");
  bindProviderTests();
}

function providerSelect(key, value) {
  const known = state.availableProviders.some((item) => item.id === value);
  const customValue = value && !known ? value : "";
  const options = [
    `<option value="">留空自动回退</option>`,
    ...state.availableProviders.map((item) => {
      const label = `${item.name || item.id}${item.model ? ` · ${item.model}` : ""}${item.is_default ? " · 默认" : ""}`;
      return `<option value="${escapeHtml(item.id)}" ${item.id === value ? "selected" : ""}>${escapeHtml(label)}</option>`;
    }),
    `<option value="__custom__" ${customValue ? "selected" : ""}>手动输入 Provider ID</option>`,
  ].join("");
  return `
    <select data-provider-select="${escapeHtml(key)}">${options}</select>
    <input data-provider-key="${escapeHtml(key)}" value="${escapeHtml(value || "")}" placeholder="自定义 Provider ID" ${customValue ? "" : "hidden"} />
  `;
}

function currentProviderValues() {
  const values = {};
  document.querySelectorAll("[data-provider-key]").forEach((input) => {
    values[input.dataset.providerKey] = input.value.trim();
  });
  return values;
}

function resolveProviderId(key, values = currentProviderValues()) {
  if (values[key]) return values[key];
  if (key !== "LLM_PROVIDER_ID" && values.MAI_STYLE_PROVIDER_ID) return values.MAI_STYLE_PROVIDER_ID;
  return values.LLM_PROVIDER_ID || "";
}

function setProviderStatus(key, message, level = "info") {
  const status = document.querySelector(`[data-provider-status="${key}"]`);
  if (!status) return;
  status.className = `provider-status ${level}`;
  status.textContent = message;
}

function bindProviderTests() {
  document.querySelectorAll("[data-provider-select]").forEach((select) => {
    syncProviderInput(select);
    select.addEventListener("change", () => syncProviderInput(select));
  });
  document.querySelectorAll("[data-provider-test]").forEach((button) => {
    button.addEventListener("click", async () => {
      await testProvider(button.dataset.providerTest);
    });
  });
}

function syncProviderInput(select) {
  const key = select.dataset.providerSelect;
  const input = document.querySelector(`[data-provider-key="${key}"]`);
  if (!input) return;
  if (select.value === "__custom__") {
    input.hidden = false;
    input.focus();
  } else {
    input.hidden = true;
    input.value = select.value;
  }
}

async function testProvider(key) {
  const providerId = resolveProviderId(key);
  setProviderStatus(key, "测试中...", "info");
  try {
    const result = await postJson("/provider/test", { key, provider_id: providerId });
    if (result.ok) {
      const suffix = result.sample ? ` · ${result.sample}` : "";
      setProviderStatus(key, `正常 ${result.elapsed_ms}ms${suffix}`, "ok");
    } else {
      setProviderStatus(key, result.error || "未返回内容", "warn");
    }
  } catch (error) {
    setProviderStatus(key, error.message, "warn");
  }
}

function renderProviderFlow(providers) {
  const main = providers.LLM_PROVIDER_ID || "AstrBot 默认模型";
  const mai = providers.MAI_STYLE_PROVIDER_ID || main;
  const tasks = Object.entries(providerLabels).filter(([key]) => key !== "LLM_PROVIDER_ID" && key !== "MAI_STYLE_PROVIDER_ID");
  $("#providerFlow").innerHTML = `
    <div class="flow-lane">
      <span class="flow-node primary">主模型<br><b>${escapeHtml(main)}</b></span>
      <span class="flow-arrow">→</span>
      <span class="flow-node">陪伴通用<br><b>${escapeHtml(mai)}</b></span>
    </div>
    <div class="flow-tasks">
      ${tasks.map(([key, label]) => {
        const value = providers[key] || mai;
        const inherited = !providers[key];
        return `<span class="flow-node ${inherited ? "inherited" : "primary"}">${escapeHtml(label)}<br><b>${escapeHtml(value)}</b></span>`;
      }).join("")}
    </div>
  `;
}

function miniStat(label, value) {
  return `<div class="mini-stat"><b>${escapeHtml(value)}</b><span>${escapeHtml(label)}</span></div>`;
}

function scoreGauge(label, value, min, max) {
  const num = Number(value || 0);
  const pct = Math.max(0, Math.min(100, Math.round(((num - min) / Math.max(1, max - min)) * 100)));
  return `
    <div class="gauge">
      <svg viewBox="0 0 120 64" role="img" aria-label="${escapeHtml(label)}">
        <path d="M16 58 A44 44 0 0 1 104 58" class="gauge-bg"></path>
        <path d="M16 58 A44 44 0 0 1 104 58" class="gauge-fg" pathLength="100" style="stroke-dasharray:${pct} 100"></path>
        <text x="60" y="48" text-anchor="middle">${escapeHtml(num)}</text>
      </svg>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

function relationshipGraphSvg(edges) {
  const pairs = Object.entries(edges || {})
    .map(([key, value]) => {
      const parts = key.split(/[-|:>]+/).map((item) => item.trim()).filter(Boolean);
      const weight = Number(value?.count || value?.weight || value || 1);
      return parts.length >= 2 ? { a: parts[0], b: parts[1], weight } : null;
    })
    .filter(Boolean)
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 16);
  if (!pairs.length) return `<div class="empty small">暂无关系边</div>`;

  const names = [...new Set(pairs.flatMap((edge) => [edge.a, edge.b]))].slice(0, 12);
  const center = 120;
  const radius = 76;
  const pos = Object.fromEntries(names.map((name, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(1, names.length) - Math.PI / 2;
    return [name, { x: center + Math.cos(angle) * radius, y: center + Math.sin(angle) * radius }];
  }));
  return `
    <svg class="relation-svg" viewBox="0 0 240 240">
      ${pairs.map((edge) => {
        if (!pos[edge.a] || !pos[edge.b]) return "";
        const width = Math.min(6, 1 + edge.weight / 3);
        return `<line x1="${pos[edge.a].x}" y1="${pos[edge.a].y}" x2="${pos[edge.b].x}" y2="${pos[edge.b].y}" stroke-width="${width}"></line>`;
      }).join("")}
      ${names.map((name) => `
        <g>
          <circle cx="${pos[name].x}" cy="${pos[name].y}" r="18"></circle>
          <text x="${pos[name].x}" y="${pos[name].y + 4}" text-anchor="middle">${escapeHtml(shortName(name, 4))}</text>
        </g>
      `).join("")}
    </svg>
  `;
}

function messageTimelineSvg(messages) {
  const recent = Array.isArray(messages) ? messages.slice(-30) : [];
  if (!recent.length) return `<div class="empty small">暂无最近消息</div>`;
  const buckets = Array.from({ length: 12 }, () => 0);
  const now = Math.floor(Date.now() / 1000);
  recent.forEach((item) => {
    const ts = Number(item.ts || item.time || 0);
    const diffHours = ts ? Math.max(0, Math.min(11, Math.floor((now - ts) / 3600))) : 0;
    buckets[11 - diffHours] += 1;
  });
  const max = Math.max(1, ...buckets);
  return `
    <svg class="timeline-svg" viewBox="0 0 360 120">
      ${buckets.map((value, index) => {
        const height = Math.max(4, Math.round((value / max) * 86));
        const x = 16 + index * 28;
        const y = 100 - height;
        return `<rect x="${x}" y="${y}" width="18" height="${height}" rx="4"></rect>`;
      }).join("")}
      <line x1="12" y1="102" x2="348" y2="102"></line>
      <text x="18" y="116">-12h</text>
      <text x="318" y="116">now</text>
    </svg>
  `;
}

function shortName(value, limit) {
  const text = String(value || "");
  return text.length > limit ? `${text.slice(0, limit)}…` : text;
}

function donutChart(data) {
  const entries = Object.entries(data).filter(([, value]) => Number(value) > 0);
  if (!entries.length) return `<div class="empty small">暂无记忆数据</div>`;
  const total = entries.reduce((sum, [, value]) => sum + Number(value), 0);
  let offset = 0;
  const colors = ["#2f7566", "#8a6f3e", "#4d7ea8", "#a15f26", "#6e7f3f"];
  const circles = entries.map(([label, value], index) => {
    const pct = (Number(value) / total) * 100;
    const circle = `<circle r="42" cx="60" cy="60" pathLength="100" stroke="${colors[index % colors.length]}" stroke-dasharray="${pct} ${100 - pct}" stroke-dashoffset="${-offset}"></circle>`;
    offset += pct;
    return circle;
  }).join("");
  return `
    <div class="donut-wrap">
      <svg class="donut" viewBox="0 0 120 120">
        <circle r="42" cx="60" cy="60" class="donut-bg"></circle>
        ${circles}
        <text x="60" y="64" text-anchor="middle">${escapeHtml(total)}</text>
      </svg>
      <div class="donut-legend">
        ${entries.map(([label, value], index) => `<span><i style="background:${colors[index % colors.length]}"></i>${escapeHtml(label)} ${escapeHtml(value)}</span>`).join("")}
      </div>
    </div>
  `;
}

function detailBlock(title, preText, pairs) {
  const dl = pairs?.length
    ? `<dl>${pairs.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value || "-")}</dd>`).join("")}</dl>`
    : "";
  const pre = preText ? `<pre>${escapeHtml(preText)}</pre>` : "";
  return `<section class="detail-block"><h2>${escapeHtml(title)}</h2>${pre}${dl}</section>`;
}

function renderDl(selector, data) {
  const entries = Object.entries(data || {});
  $(selector).innerHTML = entries.length
    ? entries.map(([key, value]) => `<dt>${escapeHtml(configLabels[key] || key)}</dt><dd>${escapeHtml(formatValue(value))}</dd>`).join("")
    : `<dt>-</dt><dd>暂无数据</dd>`;
}

function featureLabel(key) {
  return featureMeta[key]?.[0] || key.replace(/^enable_/, "");
}

function featureDescription(key) {
  return featureMeta[key]?.[1] || "该功能来自插件配置，可在这里热切换。";
}

function formatValue(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value, null, 2);
  return value ?? "";
}

async function runAction(action) {
  try {
    await action();
    await loadAll();
  } catch (error) {
    alert(`操作失败：${error.message}`);
  }
}

function switchTab(tabName) {
  document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("is-active", item.dataset.tab === tabName));
  document.querySelectorAll(".panel").forEach((item) => item.classList.toggle("is-active", item.id === `panel-${tabName}`));
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    switchTab(button.dataset.tab);
  });
});

$("#refreshBtn").addEventListener("click", loadAll);
$("#userFilter").addEventListener("input", renderUsers);
$("#groupFilter").addEventListener("input", renderGroups);

["quickModuleForm", "privateModuleForm", "groupModuleForm", "memoryModuleForm"].forEach((formId) => {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runAction(() => postJson("/settings/update", {
      settings: collectFormSettings(`#${formId}`),
    }));
  });
});

$("#addUserForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const userId = String(form.get("user_id") || "").trim();
  if (!userId) return;
  state.selectedUserId = userId;
  await runAction(() => postJson("/user/update", {
    user_id: userId,
    enabled: true,
    nickname: form.get("nickname") || "",
  }));
  event.currentTarget.reset();
});

$("#addGroupForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const groupId = String(form.get("group_id") || "").trim();
  const listMode = String(form.get("list_mode") || "none");
  if (!groupId) return;
  state.selectedGroupId = groupId;
  await runAction(async () => {
    await postJson("/group/update", { group_id: groupId, enabled: true });
    if (listMode !== "none") {
      const group = state.overview?.group || {};
      const whitelist = new Set(group.whitelist || []);
      const blacklist = new Set(group.blacklist || []);
      if (listMode === "whitelist") whitelist.add(groupId);
      if (listMode === "blacklist") blacklist.add(groupId);
      await postJson("/settings/update", {
        group_whitelist_ids: [...whitelist],
        group_blacklist_ids: [...blacklist],
      });
    }
  });
  event.currentTarget.reset();
});

$("#exportSnapshotBtn").addEventListener("click", () => {
  const snapshot = {
    exported_at: new Date().toISOString(),
    overview: state.overview,
    users: state.users,
    groups: state.groups,
  };
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `private-companion-snapshot-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
});

$("#accessForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  await runAction(() => postJson("/settings/update", {
    group_access_mode: $("#groupAccessMode").value,
    group_whitelist_ids: $("#groupWhitelist").value,
    group_blacklist_ids: $("#groupBlacklist").value,
  }));
});

$("#saveFeaturesBtn").addEventListener("click", async () => {
  await runAction(() => postJson("/settings/update", { features: state.featureDraft }));
});

$("#saveProvidersBtn").addEventListener("click", async () => {
  const providers = {};
  document.querySelectorAll("[data-provider-key]").forEach((input) => {
    providers[input.dataset.providerKey] = input.value.trim();
  });
  await runAction(() => postJson("/settings/update", { providers }));
});

$("#testAllProvidersBtn").addEventListener("click", async () => {
  for (const key of Object.keys(providerLabels)) {
    await testProvider(key);
  }
});

loadAll();
