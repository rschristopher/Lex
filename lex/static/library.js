// The library: browse and search every imported pack like reading the book. It only calls the REST API.

const side = document.getElementById("side");
const view = document.getElementById("view");
const search = document.querySelector(".gsearch input");
const PAGE = 40;
let menu = { packs: [], sections: [] };
let adapter = localStorage.getItem("lex.adapter") || "";

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function state() {
  const p = new URLSearchParams(location.search);
  return { q: p.get("q") || "", c: p.get("c") || "", pack: p.get("pack") || "", r: p.get("r") || "", tag: p.get("tag") || "" };
}

function href(s) {
  const p = new URLSearchParams();
  for (const k of ["r", "c", "tag", "q", "pack"]) if (s[k]) p.set(k, s[k]);
  const qs = p.toString();
  return "/browse" + (qs ? `?${qs}` : "");
}

function go(s, replace = false) {
  const url = href(s);
  if (url !== location.pathname + location.search) history[replace ? "replaceState" : "pushState"](null, "", url);
  render();
}

function link(s, cls, text) {
  const a = el("a", cls, text);
  a.href = href(s);
  a.addEventListener("click", (e) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    e.preventDefault();
    go(s);
    window.scrollTo({ top: 0 });
  });
  return a;
}

function rowHref(row) {
  if (row.table === "characters") {
    const a = el("a", "chip person", row.name);
    a.href = `/?id=${encodeURIComponent(row.id)}`;
    return a;
  }
  const a = link({ r: `${row.table}/${row.pack}/${row.id}` }, "chip" + (row.missing ? " missing" : ""), row.name);
  if (row.note) a.append(el("small", "", row.note));
  a.title = row.category_label || "";
  return a;
}

async function api(path, params = {}) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== "" && v != null) p.set(k, v);
  if (adapter) p.set("adapter", adapter);
  const r = await fetch(path + (p.toString() ? `?${p}` : ""));
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

function tagLabel(id) {
  return (menu.tags || []).find((t) => t.id === id)?.label || id;
}

function catLabel(id) {
  for (const s of menu.sections) for (const c of s.categories) if (c.id === id) return c.label;
  return id;
}

function packSelect(s) {
  const sel = el("select", "packsel");
  sel.setAttribute("aria-label", "Pack");
  sel.append(new Option(`All packs`, ""));
  for (const p of menu.packs) sel.append(new Option(`${p.name} (${p.count})`, p.id));
  sel.value = s.pack;
  sel.addEventListener("change", () => go({ ...s, r: "", pack: sel.value }));
  return sel;
}

function renderSide(s) {
  side.replaceChildren();
  const head = el("div", "side-head");
  head.append(link({ pack: s.pack }, "side-home" + (!s.c && !s.q && !s.r ? " on" : ""), "Library"), packSelect(s));
  side.append(head);
  for (const sec of menu.sections) {
    const box = el("section", "side-sec");
    box.append(el("h3", "", sec.label));
    for (const c of sec.categories) {
      const a = link({ c: c.id, pack: s.pack }, "side-cat" + (s.c === c.id ? " on" : ""));
      a.append(el("span", "", c.label), el("span", "n", String(c.count)));
      box.append(a);
    }
    side.append(box);
  }
  if ((menu.tags || []).length) {
    const box = el("section", "side-sec");
    box.append(el("h3", "", "Item categories"));
    for (const t of menu.tags) {
      const a = link({ tag: t.id, pack: s.pack }, "side-cat" + (s.tag === t.id ? " on" : ""));
      a.append(el("span", "", t.label), el("span", "n", String(t.count)));
      box.append(a);
    }
    side.append(box);
  }
}

function tagChips(cats) {
  const box = el("div", "links");
  for (const c of cats) box.append(link({ tag: c.id }, "chip tagchip", c.label));
  return box;
}

function chipsBar(s) {
  // Phone: categories as a sideways-scrolling strip.
  const bar = el("nav", "catbar");
  bar.setAttribute("aria-label", "Categories");
  bar.append(link({ pack: s.pack }, "pill" + (!s.c && !s.q ? " on" : ""), "All"));
  for (const sec of menu.sections) for (const c of sec.categories) {
    bar.append(link({ c: c.id, pack: s.pack }, "pill" + (s.c === c.id ? " on" : ""), c.label));
  }
  queueMicrotask(() => bar.querySelector(".on")?.scrollIntoView({ inline: "center", block: "nearest" }));
  return bar;
}

function renderHome(s) {
  const total = menu.sections.reduce((n, sec) => n + sec.categories.reduce((m, c) => m + c.count, 0), 0);
  const hero = el("div", "hero");
  hero.append(el("h1", "", "Library"));
  hero.append(el("p", "muted", menu.packs.length
    ? `${total} entries across ${menu.packs.length} pack${menu.packs.length === 1 ? "" : "s"}. Pick a chapter or search above.`
    : "No packs are imported yet. Run `lex import` and they show up here."));
  const packs = el("div", "packs");
  packs.append(link({}, "pill" + (!s.pack ? " on" : ""), "All packs"));
  for (const p of menu.packs) packs.append(link({ pack: p.id }, "pill" + (s.pack === p.id ? " on" : ""), `${p.name} · ${p.count}`));
  hero.append(packs);
  view.replaceChildren(hero);
  for (const sec of menu.sections) {
    const box = el("section", "chapter");
    box.append(el("h2", "", sec.label));
    const grid = el("div", "lcards");
    for (const c of sec.categories) {
      const a = link({ c: c.id, pack: s.pack }, "lcard");
      a.append(el("span", "lcard-label", c.label), el("span", "lcard-n", `${c.count} ${c.count === 1 ? "entry" : "entries"}`));
      grid.append(a);
    }
    box.append(grid);
    view.append(box);
  }
  if ((menu.tags || []).length) {
    const box = el("section", "chapter");
    box.append(el("h2", "", "Item categories"));
    const chips = el("div", "links");
    for (const t of menu.tags) chips.append(link({ tag: t.id, pack: s.pack }, "chip tagchip", `${t.label} · ${t.count}`));
    box.append(chips);
    view.append(box);
  }
}

function rowCard(row, showCat) {
  const a = link({ r: `${row.table}/${row.pack}/${row.id}` }, "row");
  const top = el("div", "row-top");
  top.append(el("span", "row-name", row.name));
  const tags = el("span", "tags");
  if (showCat) tags.append(el("span", "tag cat", row.category_label));
  if (menu.packs.length > 1) tags.append(el("span", "tag", row.pack_name));
  top.append(tags);
  a.append(top);
  if (row.summary) a.append(el("p", "row-sum", row.summary));
  if ((row.categories || []).length) {
    const t = el("div", "row-cats");
    for (const c of row.categories) t.append(el("span", "tag", c.label));
    a.append(t);
  }
  return a;
}

async function renderList(s) {
  const head = el("div", "list-head");
  const crumbs = el("nav", "crumbs");
  crumbs.append(link({ pack: s.pack }, "", "Library"));
  if (s.c && s.q) crumbs.append(el("span", "sep", "›"), link({ c: s.c, pack: s.pack }, "", catLabel(s.c)));
  head.append(crumbs);
  const h1 = el("h1", "", s.q ? `“${s.q}”` : s.tag ? tagLabel(s.tag) : catLabel(s.c));
  const count = el("p", "muted", "Loading…");
  head.append(h1, count);
  const tools = el("div", "tools");
  const filter = el("input", "filter");
  filter.type = "search";
  filter.placeholder = s.c ? `Filter ${catLabel(s.c).toLowerCase()}…` : "Refine…";
  filter.value = s.q;
  filter.hidden = !s.c; // a search across everything uses the header box
  let t;
  filter.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => {
      history.replaceState(null, "", href({ ...s, q: filter.value.trim() }));
      if (search) search.value = filter.value.trim();
      refresh({ ...s, q: filter.value.trim() });
    }, 180);
  });
  tools.append(filter, packSelect(s));
  head.append(tools);
  const facets = el("div", "facets");
  const tagBonuses = el("section", "block");
  tagBonuses.hidden = true;
  const list = el("div", "rows");
  const more = el("button", "more", "Show more");
  more.type = "button";
  more.hidden = true;
  view.replaceChildren(chipsBar(s), head, facets, tagBonuses, list, more);

  let offset = 0;
  let cur = s;
  async function page(reset) {
    if (reset) offset = 0;
    const data = await api("/library/rows", { q: cur.q, category: cur.c, tag: cur.tag, pack: cur.pack, limit: PAGE, offset });
    if (reset && data.bonuses) {
      tagBonuses.replaceChildren(el("h2", "", `Bonuses with ${data.tag_label}`));
      const ul = el("ul", "tagb");
      for (const b of data.bonuses) {
        const li = el("li");
        li.append(el("span", "", b.text), rowHref(b.from));
        ul.append(li);
      }
      if (!data.bonuses.length) ul.append(el("li", "muted", "No bonus names this category yet."));
      tagBonuses.append(ul);
      tagBonuses.hidden = false;
    }
    if (reset) list.replaceChildren();
    for (const row of data.rows) list.append(rowCard(row, !cur.c));
    offset += data.rows.length;
    more.hidden = offset >= data.total;
    count.textContent = `${data.total} ${data.total === 1 ? "entry" : "entries"}` + (cur.q && cur.c ? ` in ${catLabel(cur.c)}` : "");
    if (!data.total) list.append(el("p", "empty", cur.q ? "Nothing matches. Try fewer or different words." : "Nothing here yet."));
    facets.replaceChildren();
    if (cur.q && data.facets.length > 1 || (cur.q && cur.c)) {
      const all = data.facets.reduce((n, f) => n + f.count, 0);
      facets.append(link({ q: cur.q, pack: cur.pack }, "pill" + (!cur.c ? " on" : ""), `All ${all}`));
      for (const f of data.facets) facets.append(link({ q: cur.q, c: f.id, pack: cur.pack }, "pill" + (cur.c === f.id ? " on" : ""), `${f.label} ${f.count}`));
    }
  }
  async function refresh(next) {
    cur = next;
    h1.textContent = cur.q ? `“${cur.q}”` : cur.tag ? tagLabel(cur.tag) : catLabel(cur.c) || "Everything";
    await page(true);
  }
  more.addEventListener("click", () => page(false));
  await refresh(s);
}

function section(title, ...kids) {
  const box = el("section", "block");
  box.append(el("h2", "", title), ...kids);
  return box;
}

function effectList(effects) {
  const ul = el("ul", "effects");
  for (const e of effects) {
    const li = el("li", "effect");
    const m = /^([+-]\d[\d.]*)\s+(.*)$/.exec(e.text);
    const words = e.condition ? (m ? m[2] : e.text).replace(` ${e.condition}`, "") : (m ? m[2] : e.text);
    if (m) li.append(el("b", Number(m[1]) < 0 ? "neg" : "", m[1]));
    li.append(el("span", "", words));
    if (e.condition) {
      li.classList.add("cond");
      li.append(el("em", "", e.condition));
    }
    ul.append(li);
  }
  return ul;
}

function factsList(facts) {
  const dl = el("dl", "facts");
  for (const f of facts) {
    dl.append(el("dt", "", f.label));
    const dd = el("dd");
    if (f.rows) {
      const ul = el("ul", "sub");
      for (const r of f.rows) ul.append(el("li", "", r));
      dd.append(ul);
    } else dd.textContent = f.value;
    dl.append(dd);
  }
  return dl;
}

async function renderDetail(s) {
  const [table, pack, ...rest] = s.r.split("/");
  const id = rest.join("/");
  let d;
  try {
    d = await api(`/library/${encodeURIComponent(table)}/${encodeURIComponent(pack)}/${encodeURIComponent(id)}`);
  } catch {
    view.replaceChildren(el("p", "empty", "That entry is not in the library."));
    return;
  }
  document.title = `${d.name} · Lex`;
  renderSide({ ...s, c: d.category });
  const art = el("article", "detail");
  const crumbs = el("nav", "crumbs");
  crumbs.append(link({}, "", "Library"), el("span", "sep", "›"), link({ c: d.category }, "", d.category_label));
  art.append(crumbs);
  const head = el("header", "d-head");
  head.append(el("h1", "", d.name));
  const tags = el("div", "tags");
  tags.append(el("span", "tag cat", d.category_label), el("span", "tag", d.pack_name));
  head.append(tags);
  art.append(head);
  if ((d.categories || []).length) art.append(section("Categories", tagChips(d.categories)));
  if (d.text) for (const para of d.text.split(/\n\s*\n/)) art.append(el("p", "prose", para));
  if ((d.categories || []).length) art.append(section("Categories", tagChips(d.categories)));
  if (d.effects.length) art.append(section("Effects", effectList(d.effects)));
  if (d.requires.length) {
    const ul = el("ul", "reqs");
    for (const rq of d.requires) {
      const li = el("li");
      if (rq.link) {
        const words = rq.text.split(rq.link.name);
        li.append(words[0] || "", rowHref(rq.link), words.slice(1).join(rq.link.name));
      } else li.textContent = rq.text;
      ul.append(li);
    }
    art.append(section("Requirements", ul));
  }
  if (d.levels.length) {
    if (d.levels_rule) art.append(el("p", "levels-rule", d.levels_rule));
    const ol = el("ol", "levels");
    for (const lv of d.levels) {
      const li = el("li", "level");
      const top = el("div", "lv-top");
      top.append(el("span", "lv-n", String(lv.level)), el("span", "lv-name", lv.name));
      if (lv.price != null) top.append(el("span", "lv-price", `${lv.price} XP`));
      li.append(top);
      if (lv.effects.length) li.append(effectList(lv.effects));
      if (lv.facts.length) li.append(factsList(lv.facts));
      ol.append(li);
    }
    art.append(section("Levels", el("p", "muted small", "Bought in order; every level up to the one owned applies."), ol));
  }
  if (d.facts.length) art.append(section("Details", factsList(d.facts)));
  for (const rel of d.related) {
    const box = el("div", "links");
    for (const row of rel.rows) box.append(rowHref(row));
    art.append(section(rel.title, box));
  }
  if (d.source) art.append(el("p", "source", `Source: ${d.source}`));
  view.replaceChildren(art);
}

async function render() {
  const s = state();
  if (search && document.activeElement !== search) search.value = s.q;
  document.body.dataset.view = s.r ? "detail" : s.c || s.q || s.tag ? "list" : "home";
  document.title = "Lex · Library";
  try {
    menu = await api("/library", { pack: s.pack });
    renderSide(s);
    if (s.r) await renderDetail(s);
    else if (s.c || s.q || s.tag) await renderList(s);
    else renderHome(s);
  } catch (e) {
    view.replaceChildren(el("p", "empty", `Could not load the library (${e.message}).`));
  }
}

if (search) {
  let t;
  search.form.addEventListener("submit", (e) => {
    e.preventDefault();
    go({ ...state(), r: "", q: search.value.trim() });
  });
  search.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => {
      const s = state();
      const q = search.value.trim();
      if (q === s.q) return;
      go({ q, c: s.r ? "" : s.c, pack: s.pack, r: "" }, Boolean(s.q) && Boolean(q));
    }, 250);
  });
}
window.addEventListener("popstate", render);
render();
