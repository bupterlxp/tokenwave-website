#!/usr/bin/env python3
"""Stage the generated static site as a Cloudflare Worker-compatible Sites build."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CLIENT = DIST / "client"
SERVER = DIST / "server"

ROOT_FILES = (
    "index.html",
    "benchmarks.html",
    "blog.html",
    "careers.html",
    "joinus.html",
    "research.html",
    "robots.txt",
    "sitemap.xml",
)
SITE_DIRS = ("benchmarks", "research", "static")

WORKER = """const worker = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/") url.pathname = "/index.html";
    else if (url.pathname.endsWith("/")) url.pathname += "index.html";

    const assetRequest = new Request(url, request);
    const response = await env.ASSETS.fetch(assetRequest);
    if (response.status !== 404) return response;

    return new Response("Not found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
};

export default worker;
"""


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    CLIENT.mkdir(parents=True)
    SERVER.mkdir(parents=True)

    for name in ROOT_FILES:
        shutil.copy2(ROOT / name, CLIENT / name)
    for name in SITE_DIRS:
        shutil.copytree(ROOT / name, CLIENT / name)

    (SERVER / "index.js").write_text(WORKER, encoding="utf-8")
    files = sum(1 for path in CLIENT.rglob("*") if path.is_file())
    print(f"Sites build staged: {files} static assets + dist/server/index.js")


if __name__ == "__main__":
    main()
