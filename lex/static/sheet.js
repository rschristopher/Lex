const home = document.getElementById("home");
const adapterEl = document.getElementById("adapter");
const scaleEl = document.getElementById("scale");
const err = document.getElementById("err");
const root = document.getElementById("sheet");

const boot = new URLSearchParams(location.search);
let charId = boot.get("id") || "";
let adapterId = boot.get("adapter") || localStorage.getItem("lex.adapter") || "universal";
let scaleId = localStorage.getItem("lex.scale") || "auto";
let adapters = [];
let roster = [];
let payload = null;

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function syncUrl() {
  const u = new URL(location.href);
  if (charId) u.searchParams.set("id", charId);
  else u.searchParams.delete("id");
  if (adapterId && adapterId !== "universal") u.searchParams.set("adapter", adapterId);
  else u.searchParams.delete("adapter");
  history.replaceState(null, "", u);
  localStorage.setItem("lex.adapter", adapterId);
}

function renderPortrait(src, name) {
  const pic = el("div", "portrait");
  if (src) {
    const img = document.createElement("img");
    img.src = src;
    img.alt = name || "";
    img.addEventListener("error", () => img.remove());
    pic.append(img);
  }
  return pic;
}

function fmtBonus(n) {
  const v = Number(n);
  if (Number.isNaN(v)) return String(n ?? "—");
  if (v > 0) return `+${v}`;
  return String(v);
}

function prefixMeta(s, id) {
  return (s.prefixes || []).find((p) => p.id === id) || null;
}

function prefixFactor(s, id) {
  const p = prefixMeta(s, id);
  return p ? Number(p.factor) || 1 : 1;
}

function colorBand(f) {
  const x = Number(f) || 1;
  if (x < 0.1) return "centi";
  if (x < 1) return "deci";
  if (x < 10) return "unit";
  if (x < 100) return "deka";
  if (x < 1000) return "hecto";
  if (x < 1e6) return "kilo";
  if (x < 1e9) return "mega";
  if (x < 1e12) return "giga";
  return "tera";
}

function remainingPrefix(segs, s) {
  let best = "unit";
  let bestF = -1;
  for (const seg of segs) {
    if (!(Number(seg.value) > 0)) continue;
    const f = prefixFactor(s, seg.prefix || "unit");
    if (f > bestF) {
      bestF = f;
      best = seg.prefix || "unit";
    }
  }
  return best;
}

function outerThreshold(segs) {
  for (const seg of segs) {
    if (Number(seg.value) > 0) return Math.max(1, Number(seg.threshold) || 1);
  }
  return 1;
}

function scaledHits(def, s) {
  const segs = def?.armor?.segments || [];
  if (!segs.length) return null;
  const band = remainingPrefix(segs, s);
  const bandF = prefixFactor(s, band);
  const display = scaleId === "auto" ? band : scaleId;
  const df = prefixFactor(s, display);
  const scaled = segs.map((seg) => {
    const f = prefixFactor(s, seg.prefix || "unit");
    const grow = (Number(seg.value) || 0) * f / df;
    return { ...seg, grow, band: colorBand(f) };
  });
  const total = scaled.reduce((n, x) => n + x.grow, 0);
  const meta = prefixMeta(s, display);
  return {
    total,
    print: Math.trunc(total),
    prefix_label: meta?.armor || "",
    segments: scaled,
    band: colorBand(bandF),
    scale: bandF,
    threshold: outerThreshold(segs),
    high: bandF >= 100,
  };
}

function glowTier(n) {
  const v = Number(n) || 0;
  if (v < 100) return 0;
  return Math.min(5, Math.floor(v / 100));
}

function renderStack(bar, label, cls) {
  if (!bar || !(bar.segments || []).length) return null;
  const wrap = el("div", "row" + (cls ? ` ${cls}` : "") + (bar.band ? ` ${bar.band}` : ""));
  wrap.append(el("div", "lab", label));
  const track = el("div", "track");
  const glow = glowTier(bar.print != null ? bar.print : bar.total);
  if (glow) track.classList.add(`glow-${glow}`);
  const fill = el("div", "fill");
  const total = Number(bar.total) || 0;
  const scale = Number(bar.scale) || 1;
  const extra = Number(bar.threshold) || 1;
  const bounce = Math.max(scale, extra);
  const useBlack = bounce <= 1;
  if (!useBlack && total < 100) {
    fill.style.width = "100%";
  } else {
    fill.style.width = `${Math.min(100, total)}%`;
  }
  const innerFirst = [...bar.segments].reverse();
  for (const seg of innerFirst) {
    const grow = seg.grow != null ? Number(seg.grow) : Number(seg.value) || 0;
    if (grow <= 0) continue;
    const s = el("span", `seg ${seg.band || seg.style || ""}`);
    s.style.flexGrow = String(grow);
    const pl = seg.prefix_label ? ` ${seg.prefix_label}` : "";
    s.title = `${seg.name} ${seg.value}${pl}`;
    fill.append(s);
  }
  if (!useBlack && total < 100) {
    const dim = el("span", `seg dim ${bar.band || ""}`);
    dim.style.flexGrow = String(Math.max(0, 100 - total));
    dim.title = `Damage threshold ${Math.round(bounce)}`;
    fill.append(dim);
  }
  const amt = el("div", "amt");
  const current = bar.print != null ? bar.print : (bar.current != null ? Number(bar.current) : total);
  amt.append(el("b", "", String(current)));
  if (bar.prefix_label) amt.append(el("span", "u", bar.prefix_label));
  track.append(fill, amt);
  wrap.append(track);
  return wrap;
}

function renderAnima(anima) {
  if (!anima || !(Number(anima.total) > 0)) return null;
  const wrap = el("div", "row anima");
  wrap.append(el("div", "lab", anima.label || "Anima"));
  const track = el("div", "track");
  const fill = el("div", "fill");
  const cur = anima.current != null ? Number(anima.current) : Number(anima.total) || 0;
  fill.style.width = `${Math.min(100, cur)}%`;
  const seg = el("span", "seg anima");
  seg.style.flexGrow = "1";
  fill.append(seg);
  const glow = glowTier(cur);
  if (glow) track.classList.add(`glow-${glow}`);
  const amt = el("div", "amt");
  amt.append(el("b", "", String(cur)));
  track.append(fill, amt);
  wrap.append(track);
  return wrap;
}

function renderGauges(s) {
  const hp = el("div", "hp");
  const bars = el("div", "bars");
  const hits = scaledHits(s.defense || {}, s);
  const hitsBar = renderStack(hits, "Hit Points", hits?.high ? "high" : "");
  if (hitsBar) bars.append(hitsBar);
  const animaBar = renderAnima(s.anima);
  if (animaBar) bars.append(animaBar);
  hp.append(bars);
  return hp;
}

function fillScale(s) {
  if (!scaleEl) return;
  const prefixes = s?.prefixes || roster.find((r) => r.sheet?.prefixes)?.sheet?.prefixes || [];
  const keep = scaleId;
  scaleEl.replaceChildren();
  const auto = document.createElement("option");
  auto.value = "auto";
  auto.textContent = "Auto";
  scaleEl.append(auto);
  for (const p of prefixes) {
    const o = document.createElement("option");
    o.value = p.id;
    o.textContent = p.armor || p.id;
    scaleEl.append(o);
  }
  if (keep !== "auto" && ![...scaleEl.options].some((o) => o.value === keep)) scaleId = "auto";
  scaleEl.value = scaleId;
}

function renderHud(s, stacked) {
  const hud = el("div", stacked ? "hud stack" : "hud");
  hud.append(renderGauges(s));
  const bar = el("div", "bar");
  const ch = s.channels || [];
  bar.style.gridTemplateColumns = `repeat(${Math.max(ch.length, 1)}, minmax(0, 1fr))`;
  for (const c of ch) {
    const st = el("div", "stat" + (c.automatic ? " automatic" : ""));
    const lab = el("b", "", c.label);
    if (c.automatic) lab.title = "automatic";
    st.append(lab);
    const n = c.id === "actions" ? String(c.value) : fmtBonus(c.value);
    st.append(el("span", "", n));
    bar.append(st);
  }
  hud.append(bar);
  const act = el("div", "act");
  const using = s.using;
  act.append(el("div", "name", using?.name || "Punch"));
  if (using?.damage) {
    const dmg = el("div", "dmg" + (using.prefix ? ` ${using.prefix}` : ""), using.damage);
    if (using.prefix_label) dmg.append(el("span", "u", using.prefix_label));
    act.append(dmg);
  }
  hud.append(act);
  return hud;
}

function nextActivated(row) {
  const slot = row.slot || "body";
  const rows = (payload?.groups || []).flatMap((g) => g.rows || []);
  const slotOf = (id) => (rows.find((r) => r.id === id) || {}).slot || "body";
  let cur = new Set(payload?.activated || []);
  if (!row.id) {
    return [...cur].filter((id) => slotOf(id) !== slot);
  }
  if (cur.has(row.id)) cur.delete(row.id);
  else {
    if (slot === "body") {
      for (const id of [...cur]) {
        if (slotOf(id) === "body") cur.delete(id);
      }
    }
    cur.add(row.id);
  }
  return [...cur];
}

function pickRow(name, qty, unit, on, click, prefix) {
  const b = el("button", on ? "on" : "");
  b.type = "button";
  b.append(el("span", "", name || ""));
  if (qty != null && qty !== "") {
    b.append(el("span", "d" + (prefix ? ` ${prefix}` : ""), String(qty)));
  }
  if (unit) b.append(el("span", "t", unit));
  b.addEventListener("click", (e) => {
    e.stopPropagation();
    click();
  });
  return b;
}

function renderGroups(s, colA, colW) {
  for (const g of s.groups || []) {
    const col = g.pane === "armor" ? colA : colW;
    col.append(el("h3", "", g.name));
    if (!g.select) {
      const list = el("div", "skills");
      for (const row of g.rows || []) {
        list.append(el("span", "", row.name || ""), el("span", "", String(row.qty || "")));
      }
      col.append(list);
      continue;
    }
    const box = el("div", "actions");
    for (const row of g.rows || []) {
      const mode = row.select || g.select;
      const click = mode === "activated"
        ? () => persist({ activated: nextActivated(row) })
        : mode === "attack"
          ? () => persist({ attack: row.id })
          : null;
      if (!click) {
        const line = el("div", "skills");
        line.append(el("span", "", row.name || ""), el("span", "", String(row.qty || "")));
        box.append(line);
        continue;
      }
      box.append(pickRow(row.name, row.qty, row.unit, Boolean(row.on), click, row.prefix || ""));
    }
    col.append(box);
  }
}

function renderPlay(s) {
  payload = s;
  fillScale(s);
  document.body.classList.remove("index");
  root.className = "sheet";
  if (home) home.hidden = false;
  const left = el("aside");
  const whoBox = el("div", "who");
  whoBox.append(renderPortrait(s.portrait, s.name));
  const ident = el("div");
  ident.append(el("h1", "", s.name || s.id));
  const bits = [s.ancestry?.name, s.class?.name, s.level != null ? `Level ${s.level}` : ""].filter(Boolean);
  ident.append(el("p", "occ", bits.join(" · ")));
  whoBox.append(ident);
  left.append(whoBox);
  const list = s.attrs || [];
  const attrs = el("div", "attrs" + (list.length === 6 ? " six" : " nine"));
  for (const a of list) {
    const d = el("div", a.boosted ? "boost" : "");
    d.append(el("b", "", a.label), el("span", "", String(a.value)));
    if (a.mod != null) {
      const m = el("i", "mod", fmtBonus(a.mod));
      d.append(m);
    }
    attrs.append(d);
  }
  left.append(attrs);
  if ((s.person || []).length) {
    const person = el("div", "person");
    for (const f of s.person) {
      const d = el("div");
      d.append(el("b", "", f.name), el("span", "", String(f.value)));
      person.append(d);
    }
    left.append(person);
  }
  const colA = el("div", "pane");
  const colW = el("div", "pane");
  renderGroups(s, colA, colW);
  root.replaceChildren();
  root.append(renderHud(s), left, colA, colW);
}

async function persist(patch) {
  if (!charId) return;
  const q = new URLSearchParams({ adapter: adapterId });
  const r = await fetch(`/characters/${charId}?${q}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!r.ok) {
    if (err) {
      err.hidden = false;
      err.textContent = `save ${r.status}`;
    }
    return;
  }
  renderPlay(await r.json());
}

function renderCard(row) {
  const s = row.sheet || {};
  const b = el("button", "card");
  b.type = "button";
  const line = el("div", "who-line");
  line.append(el("div", "name", s.name || row.name || row.id));
  const meta = [s.class?.name || row.class?.name, s.level != null ? `L${s.level}` : ""].filter(Boolean).join(" · ");
  if (meta) line.append(el("div", "meta", meta));
  b.append(line, renderPortrait(s.portrait || row.portrait, s.name));
  if (row.sheet) b.append(renderHud(row.sheet, true));
  b.addEventListener("click", () => openCharacter(row.id));
  return b;
}

function renderIndex() {
  fillScale(roster[0]?.sheet);
  document.body.classList.add("index");
  root.className = "roster";
  if (home) home.hidden = true;
  root.replaceChildren();
  for (const row of roster) root.append(renderCard(row));
}

async function loadRoster() {
  const q = new URLSearchParams({ sheet: "true", adapter: adapterId });
  const r = await fetch(`/characters?${q}`);
  roster = r.ok ? await r.json() : [];
}

async function showIndex() {
  charId = "";
  syncUrl();
  await loadRoster();
  renderIndex();
}

async function openCharacter(id) {
  charId = id;
  syncUrl();
  await load();
}

async function load() {
  if (err) err.hidden = true;
  if (!charId) {
    await showIndex();
    return;
  }
  const q = new URLSearchParams({ adapter: adapterId });
  const r = await fetch(`/characters/${charId}/sheet?${q}`);
  if (!r.ok) {
    if (err) {
      err.hidden = false;
      err.textContent = `sheet ${r.status}`;
    }
    await showIndex();
    return;
  }
  renderPlay(await r.json());
}

function fillAdapters() {
  adapterEl.replaceChildren();
  for (const a of adapters) {
    const o = document.createElement("option");
    o.value = a.id;
    o.textContent = a.name;
    adapterEl.append(o);
  }
  if (![...adapterEl.options].some((o) => o.value === adapterId)) adapterId = "universal";
  adapterEl.value = adapterId;
}

adapterEl.addEventListener("change", () => {
  adapterId = adapterEl.value;
  syncUrl();
  if (charId) load();
  else showIndex();
});

if (scaleEl) {
  scaleEl.addEventListener("change", () => {
    scaleId = scaleEl.value;
    localStorage.setItem("lex.scale", scaleId);
    if (payload && !document.body.classList.contains("index")) renderPlay(payload);
    else renderIndex();
  });
}

if (home) {
  home.addEventListener("click", (e) => {
    e.preventDefault();
    showIndex();
  });
}

const listed = await fetch("/adapters");
adapters = listed.ok ? await listed.json() : [{ id: "universal", name: "Universal" }];
fillAdapters();
if (charId) await load();
else await showIndex();
