// Watch page for every client video. The page next to video.json is a copy of
// _template/index.html; everything specific to a video comes from its video.json.
(async () => {
  const $ = id => document.getElementById(id);
  let meta;
  try {
    meta = await (await fetch("video.json", {cache: "no-cache"})).json();
  } catch {
    $("page").innerHTML = '<p class="error wrap">This video could not be loaded.</p>';
    return;
  }

  document.title = `${meta.title} · UniQCAI`;
  // "Video 1 · Admin role": number and role come from video.json.
  $("eyebrow").textContent = meta.eyebrow ||
    [meta.number && `Video ${meta.number}`, meta.role && `${meta.role} role`].filter(Boolean).join(" · ") ||
    "Digital Upshot";
  $("headline").textContent = meta.headline || meta.title;
  $("summary").textContent = meta.summary || "";
  const steps = meta.steps || [];
  const counted = steps.filter(s => !s.intro);
  const facts = [meta.duration, "Narrated, subtitles available", counted.length && `${counted.length} steps`];
  for (const f of facts.filter(Boolean)) $("facts").append(Object.assign(document.createElement("li"), {textContent: f}));

  const video = $("video");
  const dl = $("download");
  dl.setAttribute("download", meta.download_name || "video.mp4");
  dl.textContent = `Download video (MP4${meta.size_mb ? `, ${meta.size_mb} MB` : ""})`;
  $("footer").textContent = `UniQCAI · Digital Upshot Pvt Ltd. ${meta.footer || ""}`;

  const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  const seek = t => { video.currentTime = t; video.play().catch(() => {}); video.focus(); };

  if (!steps.length) { $("chapters-box").hidden = true; $("steps-section").hidden = true; }
  let n = 0;
  for (const s of steps) {
    const b = document.createElement("button");
    b.type = "button";
    b.innerHTML = "<time></time><span></span>";
    b.querySelector("time").textContent = fmt(s.t);
    b.querySelector("span").textContent = s.title;
    b.addEventListener("click", () => seek(s.t));
    const li = document.createElement("li");
    li.append(b);
    $("chapters").append(li);
    s.btn = b;
    if (s.intro) continue;

    n += 1;
    const c = document.createElement("li");
    if (s.muted) c.className = "muted";
    c.innerHTML = '<div class="n"><span></span><button type="button"></button></div><h3></h3><p></p>';
    c.querySelector(".n span").textContent = `Step ${n}`;
    const play = c.querySelector(".n button");
    play.textContent = `▶ ${fmt(s.t)}`;
    play.setAttribute("aria-label", `Play from ${fmt(s.t)}`);
    play.addEventListener("click", () => { seek(s.t); video.scrollIntoView({behavior: "smooth", block: "center"}); });
    c.querySelector("h3").textContent = s.title;
    c.querySelector("p").textContent = s.text || "";
    $("steps").append(c);
  }

  let current = null;
  const mark = () => {
    let active = steps[0];
    for (const s of steps) if (video.currentTime + 0.25 >= s.t) active = s;
    if (!active || active === current) return;
    current?.btn.removeAttribute("aria-current");
    active.btn.setAttribute("aria-current", "true");
    current = active;
  };
  video.addEventListener("timeupdate", mark);
  video.addEventListener("seeked", mark);
  mark();
})();
