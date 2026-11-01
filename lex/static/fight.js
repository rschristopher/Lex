// The combat screen. Every tablet in the fight shows both groups, the order, hit points, and armor.
// Lex asks for rolls; the dice stay on the table. Rules live on the server; this only shows and sends.
const $ = (id) => document.getElementById(id);
const fid = new URLSearchParams(location.search).get("id");
let me = null;
let st = null;
let picked = { use: null };

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function showError(t) {
  $("err").hidden = !t;
  $("err").textContent = t || "";
}

async function send(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    showError(data.detail || `${r.status}`);
    return null;
  }
  showError("");
  return data;
}

function mine(cid) {
  if (!me || !st) return false;
  if (me.role === "gm") return true;
  const c = st.groups.flatMap((g) => g.combatants).find((x) => x.id === cid);
  return Boolean(c && c.owner === me.username);
}

function nameOf(cid) {
  const c = st.groups.flatMap((g) => g.combatants).find((x) => x.id === cid);
  return c ? c.name : cid || "";
}

function renderCombatant(c) {
  const box = el("div", `combatant ${c.status}${st.current === c.id ? " current" : ""}`);
  box.append(el("strong", null, c.name));
  const bar = el("div", "bar");
  const segs = (c.defense && c.defense.segments) || [];
  const total = segs.reduce((n, s) => n + Math.max(1, s.total), 0) || 1;
  for (const s of segs) {
    const span = el("span", s.id === "hit_points" ? "flesh" : "");
    span.style.flex = String(Math.max(1, s.total) / total);
    span.style.opacity = String(0.25 + 0.75 * (s.total ? s.value / s.total : 0));
    span.title = `${s.name}: ${s.value}/${s.total} ${s.prefix_label || ""}`;
    bar.append(span);
  }
  box.append(bar);
  const parts = segs.map((s) => `${s.name} ${s.value}/${s.total}${s.prefix_label ? " " + s.prefix_label : ""}`);
  if (c.anima) parts.push(`${c.anima.label} ${c.anima.current}/${c.anima.total}`);
  parts.push(c.initiative == null ? "initiative ?" : `initiative ${c.init_roll}`);
  if (st.status === "melee") parts.push(`${c.actions_left} actions`);
  if (c.status !== "in") parts.push(c.status === "down" ? "down" : "left combat");
  box.append(el("div", "meta", parts.join(" · ")));
  if (st.status === "initiative" && c.initiative == null && mine(c.id)) {
    const b = el("button", null, "Roll initiative");
    b.addEventListener("click", () => openRoll({ ask: `${c.name}: initiative, roll ${st.die}`, kind: "initiative", cid: c.id }));
    box.append(b);
  }
  if (picked.use && st.current && mine(st.current) && c.status === "in" && c.id !== st.current) {
    const b = el("button", null, "Target");
    b.addEventListener("click", () => act({ use: picked.use, target: c.id }));
    box.append(b);
  }
  return box;
}

async function act(extra) {
  const data = await send(`/fights/${fid}/act`, { actor: st.current, ...extra });
  picked = { use: null };
  if (data) show(data);
}

function renderTurn() {
  const t = $("turn");
  t.replaceChildren();
  if (st.status !== "melee" || !st.current || st.pending) return;
  t.append(el("h3", null, `Melee ${st.melee}: ${nameOf(st.current)}'s action`));
  if (!mine(st.current)) return;
  for (const o of st.options) {
    const label = o.kind === "attack" ? `${o.name} (${o.damage} ${o.prefix})` : `Switch on ${o.name}`;
    const b = el("button", picked.use === o.id ? "on" : "", o.cost ? `${label} · ${o.cost} M` : label);
    b.addEventListener("click", () => {
      if (o.kind === "attack") {
        picked = { use: o.id };
        render();
      } else act({ use: o.id });
    });
    t.append(b);
  }
  const leave = el("button", null, "Leave combat");
  leave.addEventListener("click", () => act({ leave: true }));
  t.append(leave);
}

function openRoll(spec) {
  const m = $("modal");
  $("ask").textContent = spec.ask;
  const choices = $("choices");
  const inputs = $("inputs");
  choices.replaceChildren();
  inputs.replaceChildren();
  let choice = null;
  for (const ch of spec.choices || []) {
    const b = el("button", null, ch[0].toUpperCase() + ch.slice(1));
    b.type = "button";
    b.addEventListener("click", async () => {
      if (ch === "pass") {
        m.close();
        const d = await send(`/fights/${fid}/roll`, { choice: "pass" });
        if (d) show(d);
        return;
      }
      choice = ch;
      [...choices.children].forEach((x) => x.classList.toggle("on", x === b));
    });
    choices.append(b);
  }
  const n = spec.dice ? spec.dice.length : 1;
  for (let i = 0; i < n; i++) {
    const inp = document.createElement("input");
    inp.type = "number";
    inp.placeholder = spec.dice ? spec.dice[i] : st.die;
    inputs.append(inp);
  }
  const submit = async (auto) => {
    if (spec.choices && !choice) return showError("choose dodge, parry, or pass");
    const nums = [...inputs.querySelectorAll("input")].map((x) => parseInt(x.value, 10));
    if (!auto && nums.some(Number.isNaN)) return;
    let body;
    let url = `/fights/${fid}/roll`;
    if (spec.kind === "initiative") {
      url = `/fights/${fid}/initiative`;
      body = { character: spec.cid, ...(auto ? {} : { value: nums[0] }) };
    } else if (spec.dice) body = auto ? {} : { values: nums };
    else body = { choice, ...(auto ? {} : { value: nums[0] }) };
    m.close();
    const d = await send(url, body);
    if (d) show(d);
  };
  $("roll-form").onsubmit = (e) => { e.preventDefault(); submit(false); };
  $("auto").onclick = () => submit(true);
  if (!m.open) m.showModal();
}

function renderPending() {
  const p = st.pending;
  const m = $("modal");
  if (!p || !mine(p.roller)) {
    if (m.open && !p) m.close();
    return;
  }
  if (m.open) return;
  const spec = { ask: `${nameOf(p.roller)}: ${p.ask}` };
  if (p.step === "damage") spec.dice = p.damage.map((c) => c.dice);
  if (p.step === "defense") spec.choices = p.choices;
  openRoll(spec);
}

function render() {
  $("fight").hidden = false;
  $("status").textContent = st.status === "ended"
    ? `The fight is over: ${st.ended}.`
    : st.status === "initiative" ? "Roll initiative." : `Melee ${st.melee} · die ${st.die}${st.low ? " (low)" : ""}`;
  const g = $("groups");
  g.replaceChildren();
  for (const grp of st.groups) {
    const col = el("div", "group");
    col.append(el("h3", null, grp.name));
    const order = st.order;
    const members = [...grp.combatants].sort((a, b) => (order.indexOf(a.id) + 1 || 999) - (order.indexOf(b.id) + 1 || 999));
    members.forEach((c) => col.append(renderCombatant(c)));
    g.append(col);
  }
  renderTurn();
  renderPending();
  $("gm").hidden = !(me && me.role === "gm");
  $("end").hidden = st.status === "ended";
  const log = $("log");
  log.replaceChildren();
  for (const e of st.log) {
    const bits = [e.kind, nameOf(e.actor)];
    if (e.name) bits.push(e.name);
    if (e.target) bits.push(`→ ${nameOf(e.target)}`);
    if (e.roll != null) bits.push(`rolled ${e.roll}${e.needed != null ? ` (needed ${e.needed})` : ""}`);
    if (e.rolls) bits.push(`rolled ${e.rolls.join(" + ")}`);
    for (const t of e.then || []) for (const h of t.hits || []) bits.push(`${h.layer} −${h.taken}`);
    log.append(el("li", null, bits.filter(Boolean).join(" ")));
  }
}

function show(data) {
  st = data;
  render();
}

async function poll() {
  if (!fid) return;
  const r = await fetch(`/fights/${fid}`);
  if (r.ok) show(await r.json());
}

async function setup() {
  const chars = await (await fetch("/characters")).json();
  const pick = $("pick");
  for (const c of chars) {
    const row = el("label", null, `${c.name} `);
    const sel = document.createElement("select");
    sel.dataset.id = c.id;
    for (const [v, t] of [["", "—"], ["0", "Group 1"], ["1", "Group 2"]]) {
      const o = el("option", null, t);
      o.value = v;
      sel.append(o);
    }
    row.append(sel);
    pick.append(row);
  }
  $("setup").hidden = false;
  $("setup").addEventListener("submit", async (e) => {
    e.preventDefault();
    const groups = [{ name: "Group 1", characters: [] }, { name: "Group 2", characters: [] }];
    for (const s of pick.querySelectorAll("select")) if (s.value) groups[+s.value].characters.push(s.dataset.id);
    const d = await send("/fights", { groups, die: $("die").value, low: $("low").checked, pull_rule: $("pull-rule").checked });
    if (d) location.search = `?id=${d.id}`;
  });
}

$("undo").addEventListener("click", async () => { const d = await send(`/fights/${fid}/undo`, { count: 1 }); if (d) show(d); });
$("fresh").addEventListener("click", async () => { const d = await send(`/fights/${fid}/initiative/fresh`); if (d) show(d); });
$("end").addEventListener("click", async () => { const d = await send(`/fights/${fid}/end`); if (d) show(d); });

(async () => {
  me = await (await fetch("/me")).json();
  $("who").textContent = me ? `${me.username}${me.role === "gm" ? " (GM)" : ""}` : "sign in on the roster first";
  if (fid) {
    await poll();
    setInterval(poll, 2000);
  } else if (me && me.role === "gm") {
    await setup();
  } else {
    const open = (await (await fetch("/fights")).json()).find((f) => f.status !== "ended");
    if (open) location.search = `?id=${open.id}`;
    else showError("No fight right now.");
  }
})();
