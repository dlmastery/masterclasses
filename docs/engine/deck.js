/* ==========================================================================
   Signal deck engine — runtime
   Declarative: slides describe what appears and when; the engine animates it.

   Authoring contract (see engine/AUTHORING.md):
     <section class="slide" id="..." data-tone="agent|tool|state|model|human|risk" data-title="...">
     data-step="n"          element appears at step n (1-based). Step 0 = slide entry.
     data-fx="up|fade|left|right|scale|pop|blur|draw|type|count|mask|stagger|bar|none"
     data-on="n:cls"        add class cls when step >= n   (several: "2:hot 4:dim")
     data-until="n"         element visible only while step < n
     .diagram[data-wires]   "a>b; b>c@2 :flow :dash [label] {model}"  (ids of .node)
     pre.code[data-focus]   "1:3-5, 2:8-9"  highlight lines at steps
     .stat .n[data-to]      count-up target, with data-dec / data-pre / data-suf
     Deck.register(id, {enter(slide), step(slide, n), leave(slide)}) for custom JS
   ========================================================================== */
(() => {
  "use strict";
  const W = 1600, H = 900;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const G = window.gsap;
  if (window.SplitText) G.registerPlugin(window.SplitText);
  if (window.MotionPathPlugin) G.registerPlugin(window.MotionPathPlugin);

  const root = document.documentElement;
  const stage = document.querySelector(".stage");
  const deck = document.querySelector(".deck");
  const slides = [...deck.querySelectorAll(":scope > .slide")];
  const hooks = {};
  let cur = -1, step = 0, busy = false;

  const D = (s) => (reduce ? 0.01 : s);

  /* ---------- scale to viewport ---------- */
  function fit() {
    const s = Math.min(innerWidth / W, innerHeight / H);
    deck.style.transform = `translate(-50%, -50%) scale(${s})`;
  }
  addEventListener("resize", fit);
  fit();

  /* ---------- per-slide preparation (once) ---------- */
  function parseOn(str) {
    return str.trim().split(/\s+/).map((t) => {
      const [n, cls] = t.split(":");
      return { n: +n, cls };
    });
  }

  function prepare(slide) {
    if (slide._prepared) return;
    slide._prepared = true;

    // code: prism highlight + focus bands
    slide.querySelectorAll("pre.code").forEach((pre) => {
      const lang = pre.dataset.lang || "python";
      const codeEl = pre.querySelector("code") || pre;
      if (window.Prism && Prism.languages[lang] && !pre._hl) {
        const raw = codeEl.textContent.replace(/^\n/, "").replace(/\s+$/, "");
        codeEl.innerHTML = Prism.highlight(raw, Prism.languages[lang], lang);
        pre._hl = true;
      }
      if (pre.dataset.focus) {
        const wrap = pre.closest(".code-wrap");
        const band = document.createElement("div");
        band.className = "band";
        wrap.appendChild(band);
        pre._band = band;
        pre._focus = pre.dataset.focus.split(",").map((p) => {
          const [n, range] = p.trim().split(":");
          const [a, b] = range.split("-").map(Number);
          return { n: +n, a, b: b || a };
        });
      }
    });

    // terminal prompt rendering: lines starting with "$ " get a prompt span
    slide.querySelectorAll(".term pre.code").forEach((pre) => {
      if (pre._term) return;
      pre._term = true;
      const lines = pre.textContent.replace(/^\n/, "").replace(/\s+$/, "").split("\n");
      pre.innerHTML = lines.map((l) => {
        const esc = l.replace(/&/g, "&amp;").replace(/</g, "&lt;");
        if (esc.startsWith("$ ")) return `<span class="prompt">$ </span>${esc.slice(2)}`;
        return `<span class="out">${esc}</span>`;
      }).join("\n");
    });

    // collect steps
    let max = 0;
    slide.querySelectorAll("[data-step]").forEach((el) => (max = Math.max(max, +el.dataset.step)));
    slide.querySelectorAll("[data-on]").forEach((el) => {
      el._on = parseOn(el.dataset.on);
      el._on.forEach((o) => (max = Math.max(max, o.n)));
    });
    slide.querySelectorAll("[data-until]").forEach((el) => (max = Math.max(max, +el.dataset.until)));
    slide.querySelectorAll("pre.code[data-focus]").forEach((pre) => pre._focus.forEach((f) => (max = Math.max(max, f.n))));
    slide.querySelectorAll(".diagram[data-wires]").forEach((d) => {
      d._wires = parseWires(d.dataset.wires);
      d._wires.forEach((w) => (max = Math.max(max, w.step)));
    });
    slide._max = max;

    // initial hidden state for stepped elements
    slide.querySelectorAll("[data-step]").forEach((el) => G.set(el, { autoAlpha: 0 }));
  }

  /* ---------- wires ---------- */
  function parseWires(spec) {
    return spec.split(";").map((s) => s.trim()).filter(Boolean).map((s) => {
      const m = s.match(/^([\w-]+)\s*(<?>|<?->|--)\s*([\w-]+)/);
      if (!m) return null;
      const w = { from: m[1], to: m[3], both: m[2].startsWith("<"), arrow: m[2] !== "--", step: 0, flow: false, dash: false, label: "", tone: "", bend: 0 };
      const st = s.match(/@(\d+)/); if (st) w.step = +st[1];
      if (/:flow/.test(s)) w.flow = true;
      if (/:dash/.test(s)) w.dash = true;
      if (/:hot/.test(s)) w.hot = true;
      const b = s.match(/:bend(-?\d+)/); if (b) w.bend = +b[1];
      const side = s.match(/:(lr|rl|tb|bt|rt|lt|rb|lb|tr|tl|br|bl)\b/); if (side) w.sides = side[1];
      const lb = s.match(/\[([^\]]*)\]/); if (lb) w.label = lb[1];
      const tn = s.match(/\{(\w+)\}/); if (tn) { w.tone = tn[1]; w.hot = true; }
      return w;
    }).filter(Boolean);
  }

  function box(el, d) {
    // layout box relative to diagram, in unscaled px
    let x = 0, y = 0, n = el;
    while (n && n !== d) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight, cx: x + el.offsetWidth / 2, cy: y + el.offsetHeight / 2 };
  }

  function anchor(b, side) {
    switch (side) {
      case "l": return [b.x, b.cy, -1, 0];
      case "r": return [b.x + b.w, b.cy, 1, 0];
      case "t": return [b.cx, b.y, 0, -1];
      default: return [b.cx, b.y + b.h, 0, 1];
    }
  }

  function drawWires(d) {
    let svg = d.querySelector(":scope > svg.wires");
    if (!svg) {
      svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "wires");
      d.prepend(svg);
    }
    svg.innerHTML = "";
    const NS = "http://www.w3.org/2000/svg";
    d._wireEls = [];
    const labels = [];
    d._wires.forEach((w) => {
      const a = d.querySelector("#" + CSS.escape(w.from));
      const b = d.querySelector("#" + CSS.escape(w.to));
      if (!a || !b) return;
      const A = box(a, d), B = box(b, d);
      let sa, sb;
      if (w.sides) { sa = w.sides[0]; sb = w.sides[1]; }
      else {
        const dx = B.cx - A.cx, dy = B.cy - A.cy;
        if (Math.abs(dx) * 0.75 > Math.abs(dy)) { sa = dx > 0 ? "r" : "l"; sb = dx > 0 ? "l" : "r"; }
        else { sa = dy > 0 ? "b" : "t"; sb = dy > 0 ? "t" : "b"; }
      }
      const [x1, y1, ux1, uy1] = anchor(A, sa);
      const [x2, y2, ux2, uy2] = anchor(B, sb);
      const gap = w.arrow ? 10 : 0;
      const ex = x2 + ux2 * gap, ey = y2 + uy2 * gap;
      const sx = x1 + (w.both ? ux1 * gap : 0), sy = y1 + (w.both ? uy1 * gap : 0);
      const dist = Math.hypot(ex - sx, ey - sy);
      const k = Math.max(40, dist * 0.42);
      const c1x = sx + ux1 * k + (uy1 !== 0 ? w.bend : 0), c1y = sy + uy1 * k + (ux1 !== 0 ? w.bend : 0);
      const c2x = ex + ux2 * k + (uy2 !== 0 ? w.bend : 0), c2y = ey + uy2 * k + (ux2 !== 0 ? w.bend : 0);
      const dstr = `M${sx},${sy} C${c1x},${c1y} ${c2x},${c2y} ${ex},${ey}`;

      const g = document.createElementNS(NS, "g");
      if (w.tone) g.style.setProperty("--wc", `var(--${w.tone})`);
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", dstr);
      p.setAttribute("class", "w" + (w.dash ? " dash" : "") + (w.hot ? " hot" : ""));
      g.appendChild(p);

      const mkArrow = (x, y, ux, uy) => {
        const ar = document.createElementNS(NS, "path");
        const s = 9;
        // arrow points opposite to anchor normal (into the node)
        const ax = -ux, ay = -uy, px = -ay, py = ax;
        ar.setAttribute("d", `M${x + ax * 0},${y + ay * 0} L${x - ax * s + px * s * 0.7},${y - ay * s + py * s * 0.7} L${x - ax * s - px * s * 0.7},${y - ay * s - py * s * 0.7} Z`);
        ar.setAttribute("class", "arrow" + (w.hot ? " hot" : ""));
        return ar;
      };
      if (w.arrow) g.appendChild(mkArrow(x2 + ux2 * 2, y2 + uy2 * 2, ux2, uy2));
      if (w.both) g.appendChild(mkArrow(x1 + ux1 * 2, y1 + uy1 * 2, ux1, uy1));

      if (w.label) labels.push({ g, text: w.label, P: [sx, sy, c1x, c1y, c2x, c2y, ex, ey] });
      svg.appendChild(g);
      d._wireEls.push({ w, g, p });
      G.set(g, { autoAlpha: 0 });
    });
    placeLabels(d, svg, labels);
  }

  // Place wire labels on their curve where they hit no node and no other label.
  function placeLabels(d, svg, labels) {
    const NS = "http://www.w3.org/2000/svg";
    const pad = 5;
    const taken = [...d.querySelectorAll(".node")].map((n) => { const b = box(n, d); return { x: b.x - pad, y: b.y - pad, r: b.x + b.w + pad, b: b.y + b.h + pad }; });
    const hit = (q) => taken.some((o) => q.x < o.r && q.r > o.x && q.y < o.b && q.b > o.y);
    const at = (P, t) => { const u = 1 - t, a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, e = t * t * t; return [a * P[0] + b * P[2] + c * P[4] + e * P[6], a * P[1] + b * P[3] + c * P[5] + e * P[7]]; };
    const TS = [0.5, 0.38, 0.62, 0.28, 0.72, 0.2, 0.8, 0.14, 0.86];
    labels.forEach((L) => {
      const w = L.text.length * 8.6 + 14, h = 22;
      let best = null;
      for (const t of TS) {
        const [x, y] = at(L.P, t);
        const q = { x: x - w / 2, y: y - h / 2, r: x + w / 2, b: y + h / 2 };
        if (!hit(q)) { best = q; break; }
      }
      if (!best) { const [x, y] = at(L.P, 0.5); best = { x: x - w / 2, y: y - h / 2, r: x + w / 2, b: y + h / 2 }; }
      taken.push(best);
      const bg = document.createElementNS(NS, "rect");
      bg.setAttribute("x", best.x); bg.setAttribute("y", best.y); bg.setAttribute("width", w); bg.setAttribute("height", h);
      bg.setAttribute("rx", 6); bg.setAttribute("class", "wlb");
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", best.x + w / 2); t.setAttribute("y", best.y + h / 2 + 5);
      t.setAttribute("text-anchor", "middle"); t.setAttribute("class", "wl");
      t.textContent = L.text;
      const lg = document.createElementNS(NS, "g");
      lg.setAttribute("class", "wlg");
      lg.appendChild(bg); lg.appendChild(t);
      svg.appendChild(lg); // top layer: no later wire draws over a label
      L.g._label = lg;
      G.set(lg, { autoAlpha: 0 });
    });
  }

  function showWire(slide, we, animate) {
    if (we.shown) return;
    we.shown = true;
    const len = we.p.getTotalLength();
    G.set(we.g, { autoAlpha: 1 });
    if (we.g._label) { G.set(we.g._label, { autoAlpha: 1 }); if (animate && !reduce) G.from(we.g._label, { autoAlpha: 0, duration: 0.4, delay: 0.7 }); }
    if (animate && !reduce) {
      const dashed = we.w.dash;
      if (!dashed) {
        G.fromTo(we.p, { strokeDasharray: len, strokeDashoffset: len }, { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut", onComplete: () => G.set(we.p, { clearProps: "strokeDasharray,strokeDashoffset" }) });
      } else G.from(we.p, { autoAlpha: 0, duration: 0.6 });
      G.from(we.g.querySelectorAll(".arrow, text, .wlb"), { autoAlpha: 0, duration: 0.4, delay: 0.7 });
    }
    if (we.w.flow && !reduce) startPulse(slide, we, len);
  }
  function hideWire(we) {
    if (!we.shown) return;
    we.shown = false;
    G.to(we.g, { autoAlpha: 0, duration: D(0.25) });
    if (we.g._label) G.to(we.g._label, { autoAlpha: 0, duration: D(0.25) });
    if (we.pulses) { we.pulses.forEach((t) => t.kill()); we.pulses = null; we.g.querySelectorAll(".pulse").forEach((c) => c.remove()); }
  }
  function startPulse(slide, we, len) {
    const NS = "http://www.w3.org/2000/svg";
    we.pulses = [];
    const n = len > 380 ? 2 : 1;
    for (let i = 0; i < n; i++) {
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("r", 5);
      c.setAttribute("class", "pulse");
      we.g.appendChild(c);
      const proxy = { t: 0 };
      const tw = G.to(proxy, {
        t: 1, duration: Math.max(1.2, len / 260), ease: "none", repeat: -1, delay: 0.8 + i * (len / 260 / n),
        onUpdate: () => {
          const pt = we.p.getPointAtLength(proxy.t * len);
          c.setAttribute("cx", pt.x); c.setAttribute("cy", pt.y);
          c.setAttribute("opacity", Math.sin(proxy.t * Math.PI).toFixed(2));
        },
      });
      we.pulses.push(tw);
      (slide._loops = slide._loops || []).push(tw);
    }
  }

  /* ---------- element effects ---------- */
  function fxIn(el, delay = 0) {
    const fx = el.dataset.fx || "up";
    const base = { delay, overwrite: "auto" };
    G.set(el, { autoAlpha: 1 });
    if (reduce || fx === "none") { G.set(el, { clearProps: "transform,filter" }); return; }
    switch (fx) {
      case "fade": G.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.6, ...base }); break;
      case "left": G.fromTo(el, { x: -50, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.75, ease: "power3.out", ...base }); break;
      case "right": G.fromTo(el, { x: 50, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.75, ease: "power3.out", ...base }); break;
      case "scale": G.fromTo(el, { scale: 0.92, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.7, ease: "power3.out", ...base }); break;
      case "pop": G.fromTo(el, { scale: 0.6, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.6, ease: "back.out(1.8)", ...base }); break;
      case "blur": G.fromTo(el, { filter: "blur(14px)", autoAlpha: 0 }, { filter: "blur(0px)", autoAlpha: 1, duration: 0.9, ease: "power2.out", ...base }); break;
      case "draw": {
        G.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3, ...base });
        el.querySelectorAll("path, line, polyline, circle, rect").forEach((p, i) => {
          if (!p.getTotalLength) return;
          const L = p.getTotalLength();
          G.fromTo(p, { strokeDasharray: L, strokeDashoffset: L }, { strokeDashoffset: 0, duration: 1.1, ease: "power2.inOut", delay: delay + i * 0.06 });
        });
        break;
      }
      case "type": {
        const full = el._full ?? (el._full = el.textContent);
        const proxy = { n: 0 };
        el.textContent = "";
        G.to(proxy, { n: full.length, duration: Math.min(2.4, full.length * 0.022), ease: "none", ...base, onUpdate: () => (el.textContent = full.slice(0, Math.round(proxy.n))) });
        break;
      }
      case "count": {
        const t = el.matches("[data-to]") ? el : el.querySelector("[data-to]");
        if (t) countUp(t, delay);
        G.fromTo(el, { y: 20, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.6, ease: "power3.out", ...base });
        break;
      }
      case "mask": maskIn(el, delay); break;
      case "stagger": {
        const kids = [...el.children];
        G.fromTo(kids, { y: 26, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.6, ease: "power3.out", stagger: 0.08, ...base });
        break;
      }
      case "bar": {
        G.fromTo(el, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3, ...base });
        el.querySelectorAll(".bar > i").forEach((i, k) => G.fromTo(i, { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: "power3.out", delay: delay + 0.1 + k * 0.08 }));
        break;
      }
      default:
        G.fromTo(el, { y: 28, autoAlpha: 0, filter: "blur(6px)" }, { y: 0, autoAlpha: 1, filter: "blur(0px)", duration: 0.75, ease: "power3.out", ...base, onComplete: () => G.set(el, { clearProps: "filter" }) });
    }
    el.querySelectorAll("[data-to]").forEach((t) => { if (fx !== "count") countUp(t, delay + 0.15); });
  }

  function countUp(t, delay) {
    const to = parseFloat(t.dataset.to), dec = +(t.dataset.dec || 0);
    const pre = t.dataset.pre || "", suf = t.dataset.suf || "";
    const fmt = (v) => pre + v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
    if (reduce) { t.textContent = fmt(to); return; }
    const p = { v: 0 };
    G.to(p, { v: to, duration: 1.4, ease: "power3.out", delay, onUpdate: () => (t.textContent = fmt(p.v)) });
  }

  function maskIn(el, delay) {
    G.set(el, { autoAlpha: 1 });
    if (reduce) return;
    if (window.SplitText) {
      if (!el._split) el._split = new SplitText(el, { type: "lines,words", linesClass: "sl", mask: "lines" });
      G.fromTo(el._split.words, { yPercent: 110 }, { yPercent: 0, duration: 0.9, ease: "power4.out", stagger: 0.035, delay });
    } else {
      G.fromTo(el, { y: 30, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.8, ease: "power3.out", delay });
    }
  }

  function fxOut(el) {
    G.to(el, { autoAlpha: 0, y: 0, duration: D(0.25), overwrite: "auto" });
  }

  /* ---------- step application ---------- */
  function applyStep(slide, n, animate) {
    // stepped + until elements: ONE visibility rule, so the two attributes never fight.
    // visible <=> (no data-step or step <= n) and (no data-until or n < until)
    let d = 0;
    slide.querySelectorAll("[data-step], [data-until]").forEach((el) => {
      const s = el.dataset.step !== undefined ? +el.dataset.step : -1;
      const u = el.dataset.until !== undefined ? +el.dataset.until : Infinity;
      const vis = s <= n && n < u;
      if (vis && !el._shown) { el._shown = true; animate ? fxIn(el, (d++) * 0.08) : instant(el); }
      else if (!vis && el._shown) { el._shown = false; animate ? fxOut(el) : (G.killTweensOf(el), G.set(el, { autoAlpha: 0 })); }
      else if (!vis) G.set(el, { autoAlpha: 0 });
    });
    // class toggles
    slide.querySelectorAll("[data-on]").forEach((el) => el._on.forEach((o) => el.classList.toggle(o.cls, n >= o.n)));
    // wires
    slide.querySelectorAll(".diagram[data-wires]").forEach((dg) => {
      (dg._wireEls || []).forEach((we, i) => {
        if (we.w.step <= n) {
          if (!we.shown) {
            const entry = we.w.step === 0;
            if (animate && entry) setTimeout(() => slide.classList.contains("active") && showWire(slide, we, true), 350 + i * 90);
            else showWire(slide, we, animate);
          }
        } else hideWire(we);
      });
    });
    // code focus
    slide.querySelectorAll("pre.code[data-focus]").forEach((pre) => {
      let f = null;
      pre._focus.forEach((x) => { if (x.n <= n) f = x; });
      const wrap = pre.closest(".code-wrap");
      if (!f) { G.to(pre._band, { autoAlpha: 0, duration: D(0.3) }); wrap.classList.remove("focusing"); return; }
      const cs = getComputedStyle(pre);
      const lh = parseFloat(cs.lineHeight), pt = parseFloat(cs.paddingTop);
      const top = pre.offsetTop + pt + (f.a - 1) * lh - 2;
      const h = (f.b - f.a + 1) * lh + 4;
      G.to(pre._band, { autoAlpha: 1, top, height: h, duration: D(0.45), ease: "power3.inOut" });
    });
    const h = hooks[slide.id];
    if (h && h.step) h.step(slide, n, animate);
  }

  function instant(el) {
    G.set(el, { autoAlpha: 1, x: 0, y: 0, scale: 1, filter: "none" });
    el.querySelectorAll("[data-to]").forEach((t) => {
      const dec = +(t.dataset.dec || 0);
      t.textContent = (t.dataset.pre || "") + parseFloat(t.dataset.to).toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (t.dataset.suf || "");
    });
    if (el.dataset.fx === "type" && el._full) el.textContent = el._full;
  }

  /* ---------- slide entry ---------- */
  function entry(slide, animate) {
    // auto choreography for unstepped elements
    const auto = [];
    slide.querySelectorAll(".title, .display").forEach((el) => { if (!el.dataset.step && !el.dataset.fx) el.dataset.fx = "mask"; });
    slide.querySelectorAll("[data-fx]:not([data-step])").forEach((el) => auto.push(el));
    const nodes = [...slide.querySelectorAll(".diagram .node:not([data-step]):not([data-fx]), .diagram .group:not([data-step]):not([data-fx])")];

    if (!animate) {
      auto.forEach(instant);
      return;
    }
    auto.forEach((el, i) => fxIn(el, 0.12 + i * 0.09));
    if (nodes.length && !reduce) {
      G.fromTo(nodes, { scale: 0.85, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.55, ease: "back.out(1.6)", stagger: 0.06, delay: 0.25 });
    }
    // count-ups not inside stepped/fx elements
    slide.querySelectorAll("[data-to]").forEach((t) => { if (!t.closest("[data-step],[data-fx]")) countUp(t, 0.3); });
  }

  /* ---------- navigation ---------- */
  function go(idx, toStep = 0, dir = 1) {
    idx = Math.max(0, Math.min(slides.length - 1, idx));
    const next = slides[idx];
    const prev = slides[cur];
    if (idx === cur) { setStep(toStep === "max" ? slides[cur]._max : toStep, true); return; }
    prepare(next);

    if (prev) {
      const h = hooks[prev.id];
      if (h && h.leave) h.leave(prev);
      (prev._loops || []).forEach((t) => t.kill());
      prev._loops = [];
      prev.classList.remove("active");
      prev.classList.add("leaving");
      G.to(prev, { autoAlpha: 0, scale: 0.985, filter: reduce ? "none" : "blur(4px)", duration: D(0.45), ease: "power2.in", onComplete: () => { prev.classList.remove("leaving"); G.set(prev, { clearProps: "transform,filter" }); } });
    }

    cur = idx;
    next.classList.add("active");
    G.fromTo(next, { autoAlpha: 0, scale: 1.012 }, { autoAlpha: 1, scale: 1, duration: D(0.6), ease: "power2.out", delay: prev ? D(0.18) : 0, clearProps: "transform" });

    // tone drives the ambient aurora
    const tone = next.dataset.tone || "agent";
    root.style.setProperty("--aurora", `var(--${tone})`);

    // reset reveal state
    next.querySelectorAll("[data-step], [data-until]").forEach((el) => { el._shown = el.dataset.step === undefined; G.killTweensOf(el); G.set(el, { autoAlpha: el._shown ? 1 : 0 }); });
    next.querySelectorAll(".diagram[data-wires]").forEach(drawWires);

    const animate = toStep === 0 || dir > 0;
    entry(next, animate);
    step = toStep === "max" ? next._max : toStep;
    applyStep(next, step, step === 0 && animate);
    const h = hooks[next.id];
    if (h && h.enter) h.enter(next, step);

    updateChrome();
  }

  function setStep(n, animate) {
    const s = slides[cur];
    step = Math.max(0, Math.min(s._max, n));
    applyStep(s, step, animate);
    updateChrome();
  }

  function next() {
    const s = slides[cur];
    if (step < s._max) setStep(step + 1, true);
    else if (cur < slides.length - 1) go(cur + 1, 0, 1);
  }
  function prev() {
    if (step > 0) setStep(step - 1, false);
    else if (cur > 0) go(cur - 1, "max", -1);
  }

  /* ---------- chrome ---------- */
  const progress = Object.assign(document.createElement("div"), { className: "chrome-progress" });
  const outline = Object.assign(document.createElement("nav"), { className: "outline" });
  const notes = Object.assign(document.createElement("div"), { className: "notes-pane" });
  const hint = Object.assign(document.createElement("div"), { className: "hint", textContent: "← → navigate · O outline · N notes · F fullscreen · T theme" });
  document.body.append(progress, outline, notes, hint);

  function buildOutline() {
    let html = `<h5>${document.title}</h5>`;
    slides.forEach((s, i) => {
      if (s.classList.contains("chapter")) html += `<h5>${(s.dataset.title || s.querySelector(".display")?.textContent || "").trim()}</h5>`;
      else {
        const t = (s.dataset.title || s.querySelector(".title, .display")?.textContent || s.id || "").trim();
        html += `<button data-i="${i}">${t}</button>`;
      }
    });
    outline.innerHTML = html;
    outline.querySelectorAll("button").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); go(+b.dataset.i); outline.classList.remove("open"); }));
  }

  function updateChrome() {
    progress.style.transform = `scaleX(${(cur + 1) / slides.length})`;
    outline.querySelectorAll("button").forEach((b) => b.classList.toggle("cur", +b.dataset.i === cur));
    const n = slides[cur].querySelector(".notes");
    notes.innerHTML = n ? n.innerHTML : "<span class='muted'>No notes for this slide.</span>";
    const id = slides[cur].id || String(cur + 1);
    history.replaceState(null, "", "#" + id + (step ? "/" + step : ""));
  }

  let mouseT;
  addEventListener("mousemove", () => {
    document.body.classList.add("mouse-active");
    clearTimeout(mouseT);
    mouseT = setTimeout(() => document.body.classList.remove("mouse-active"), 1800);
  });

  /* ---------- input ---------- */
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select, [contenteditable]")) return;
    const k = e.key;
    if (["ArrowRight", "PageDown", " ", "Enter", "ArrowDown"].includes(k)) { e.preventDefault(); e.shiftKey ? go(cur + 1) : next(); }
    else if (["ArrowLeft", "PageUp", "Backspace", "ArrowUp"].includes(k)) { e.preventDefault(); e.shiftKey ? go(cur - 1) : prev(); }
    else if (k === "Home") go(0);
    else if (k === "End") go(slides.length - 1);
    else if (k === "o" || k === "O" || k === "g") outline.classList.toggle("open");
    else if (k === "n" || k === "N") notes.classList.toggle("open");
    else if (k === "f" || k === "F") { document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen?.(); }
    else if (k === "t" || k === "T") { root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light"; try { localStorage.setItem("deck-theme", root.dataset.theme); } catch (_) {} }
    else if (k === "Escape") { outline.classList.remove("open"); notes.classList.remove("open"); }
  });

  stage.addEventListener("click", (e) => {
    if (e.target.closest("a, button, input, select, textarea, label, .interactive, .outline")) return;
    if (outline.classList.contains("open")) { outline.classList.remove("open"); return; }
    e.clientX < innerWidth * 0.25 ? prev() : next();
  });

  let tx = 0, ty = 0;
  stage.addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  stage.addEventListener("touchend", (e) => {
    const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) dx < 0 ? next() : prev();
  });

  /* ---------- boot ---------- */
  try { const t = localStorage.getItem("deck-theme"); if (t) root.dataset.theme = t; } catch (_) {}
  if (!root.dataset.theme) root.dataset.theme = "light";

  window.Deck = {
    register(id, h) { hooks[id] = h; },
    go, next, prev,
    get index() { return cur; },
    get step() { return step; },
    slides,
  };

  function boot() {
    buildOutline();
    const hash = decodeURIComponent(location.hash.slice(1));
    let idx = 0, st = 0;
    if (hash) {
      const [id, s] = hash.split("/");
      const found = slides.findIndex((x) => x.id === id);
      idx = found >= 0 ? found : Math.max(0, (+id || 1) - 1);
      st = +s || 0;
    }
    go(idx, 0, 1);
    if (st) setStep(st, false);
  }
  addEventListener("hashchange", () => {
    const [id, s] = decodeURIComponent(location.hash.slice(1)).split("/");
    const i = slides.findIndex((x) => x.id === id);
    if (i >= 0 && (i !== cur || (+s || 0) !== step)) { go(i, 0, 1); if (+s) setStep(+s, false); }
  });
  Promise.race([document.fonts ? document.fonts.ready : Promise.resolve(), new Promise((r) => setTimeout(r, 2500))]).then(() => requestAnimationFrame(boot));
})();
