// Shorts: render from videos.json (refreshed daily by scripts/update_videos.py),
// with a hard-coded fallback. Click-to-load: no YouTube request until play is pressed.
(function () {
  var MAX = 8;
  var FALLBACK = [
    {id: "1nL8qBBYz5o", title: "The most impressive candidate is often the riskiest hire"},
    {id: "nvuOUR2dVsc", title: "It's 2 a.m. and you're replaying that meeting"},
    {id: "ekINMQW9bBo", title: "Bad day or bad pattern? The 3P test"},
    {id: "28CbKL2Wze0", title: "For years I repeated patterns at work I never questioned"},
    {id: "x6a2Gt5MdP4", title: "Someone is rewriting your reputation in meetings you're not in"},
    {id: "WK46BZ5yXKE", title: "In global teams, \"yes\" can mean \"no\""},
    {id: "HFOwQGXHL4E", title: "Your brain has a bouncer (and he's ruining your meetings)"},
    {id: "PtCjaA4wqUM", title: "Your micromanager isn't controlling. They're scared."}
  ];
  var list = document.getElementById("shorts");
  if (!list) return;

  function valid(v) { return v && typeof v.id === "string" && /^[\w-]{6,20}$/.test(v.id); }

  function render(videos) {
    videos = (videos || []).filter(valid).slice(0, MAX);
    if (!videos.length) videos = FALLBACK;
    list.textContent = "";
    videos.forEach(function (v) {
      var title = (v.title || "Video by Cris Calin").trim();
      var li = document.createElement("li");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "short-play";
      btn.setAttribute("aria-label", "Play video: " + title);
      var thumb = document.createElement("span");
      thumb.className = "short-thumb";
      var img = document.createElement("img");
      img.src = "https://i.ytimg.com/vi/" + v.id + "/hqdefault.jpg";
      img.alt = "";
      img.loading = "lazy";
      img.width = 480; img.height = 360;
      thumb.appendChild(img);
      var t = document.createElement("span");
      t.className = "short-title";
      t.textContent = title;
      btn.appendChild(thumb);
      btn.appendChild(t);
      btn.addEventListener("click", function () {
        var f = document.createElement("iframe");
        f.className = "short-frame";
        f.src = "https://www.youtube-nocookie.com/embed/" + v.id + "?autoplay=1&playsinline=1&rel=0";
        f.title = title;
        f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
        f.allowFullscreen = true;
        var cap = document.createElement("span");
        cap.className = "short-title";
        cap.textContent = title;
        li.textContent = "";
        li.appendChild(f);
        li.appendChild(cap);
        f.focus();
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  fetch("videos.json", {cache: "no-cache"})
    .then(function (r) { if (!r.ok) throw 0; return r.json(); })
    .then(function (d) { render(d && d.shorts); })
    .catch(function () { render(FALLBACK); });
})();

/* latest short tag: updated daily from videos.json (GitHub Action) */
(function(){var el=document.getElementById('latest-tag');if(!el||!window.fetch)return;
fetch('videos.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(d){var v=(d.shorts||[])[0];if(!v||!v.published)return;
var days=Math.floor((Date.now()-new Date(v.published).getTime())/864e5);
el.textContent= days<=0?'New today':(days===1?'New · yesterday':(days<8?'New · '+days+' days ago':'Latest short'));}).catch(function(){});})();
