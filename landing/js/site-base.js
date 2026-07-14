/**
 * GitLab Pages base path — supports:
 * - https://cognitive-functors.gitlab.io/c4reqber/  (group path, current)
 * - https://cognitive-functors.gitlab.io/turbo-cdi/ (legacy slug)
 * - https://turbo-cdi-*.gitlab.io/                  (unique domain, root)
 * - http://localhost:8765/                          (local dev)
 */
(function () {
  const PAGE_SLUGS = ["c4reqber", "turbo-cdi"];
  const parts = location.pathname.split("/").filter(Boolean);
  let prefix = "/";

  if (PAGE_SLUGS.includes(parts[0])) {
    prefix = `/${parts[0]}/`;
  } else if (/^turbo-cdi-[a-z0-9]+\.gitlab\.io$/i.test(location.hostname)) {
    prefix = "/";
  }

  window.C4R_PAGES_PREFIX = prefix;
  window.C4R_SITE_ORIGIN = location.origin;

  window.c4rSiteUrl = function (relative) {
    const rel = String(relative || "").replace(/^\//, "");
    return prefix === "/" ? `/${rel}` : `${prefix}${rel}`;
  };

  window.c4rIsHomePath = function () {
    const p = location.pathname.replace(/\/$/, "") || "/";
    if (p === "/" || p === "/index.html") return true;
    return PAGE_SLUGS.some(
      (slug) => p === `/${slug}` || p === `/${slug}/index.html`
    );
  };

  if (!document.querySelector("base[data-c4r-site-base]")) {
    const base = document.createElement("base");
    base.href = prefix;
    base.setAttribute("data-c4r-site-base", "");
    document.head.insertBefore(base, document.head.firstChild);
  }
})();
