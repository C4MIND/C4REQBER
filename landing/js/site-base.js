/**
 * GitLab Pages base path — supports:
 * - https://cognitive-functors.gitlab.io/turbo-cdi/  (group path)
 * - https://turbo-cdi-*.gitlab.io/                  (unique domain, root)
 * - http://localhost:8765/                          (local dev)
 */
(function () {
  const parts = location.pathname.split("/").filter(Boolean);
  let prefix = "/";

  if (parts[0] === "turbo-cdi") {
    prefix = "/turbo-cdi/";
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
    return (
      p === "/" ||
      p === "/index.html" ||
      p === "/turbo-cdi" ||
      p === "/turbo-cdi/index.html"
    );
  };

  if (!document.querySelector("base[data-c4r-site-base]")) {
    const base = document.createElement("base");
    base.href = prefix;
    base.setAttribute("data-c4r-site-base", "");
    document.head.insertBefore(base, document.head.firstChild);
  }
})();
