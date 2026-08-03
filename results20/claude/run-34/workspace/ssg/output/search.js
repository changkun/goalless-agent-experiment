/* Client-side search: loads search.json and filters posts by query. */
(function () {
  var box = document.getElementById("search-query");
  if (!box) return;
  var results = document.getElementById("search-results");
  var index = [];

  fetch("/search.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { index = data; })
    .catch(function () { /* search offline -> just do nothing */ });

  function score(post, q) {
    var hay = (post.title + " " + post.excerpt + " " + (post.tags || []).join(" ")).toLowerCase();
    var tokens = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!tokens.length) return 0;
    var hits = 0;
    tokens.forEach(function (t) { if (hay.indexOf(t) !== -1) hits += t.length; });
    // title matches weigh more
    tokens.forEach(function (t) { if (post.title.toLowerCase().indexOf(t) !== -1) hits += 3; });
    return hits;
  }

  box.addEventListener("input", function () {
    var q = box.value.trim();
    if (!q) { results.innerHTML = ""; return; }
    var hits = index
      .map(function (p) { return { p: p, s: score(p, q) }; })
      .filter(function (h) { return h.s > 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .slice(0, 6);
    if (!hits.length) {
      results.innerHTML = "<p class='post-meta'>No matches.</p>";
      return;
    }
    results.innerHTML = hits.map(function (h) {
      return "<article class='post-list'><h2><a href='" + h.p.url + "'>" +
        h.p.title + "</a></h2><div class='post-meta'>" + h.p.date + "</div>" +
        "<p>" + h.p.excerpt + "</p></article>";
    }).join("");
  });
})();
