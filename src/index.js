/**
 * coc-tabletop MCP server (Cloudflare Worker, zero-dep)
 *
 * Remote MCP bridge that turns GitHub Issues into a tabletop RPG table.
 * The Keeper and the player AIs each connect from their own client and share
 * the same GitHub repo as the table through this worker.
 *
 * If you already have a group chat (Discord / Telegram...), you don't need this
 * worker: just give the SKILL.md files in skills/ to your AI. The worker is for
 * people without a group chat, or who want sessions recorded on GitHub.
 *
 * Transport: Streamable HTTP, single endpoint /mcp (POST handles JSON-RPC, GET/DELETE for compatibility)
 * Auth: query param ?token=<AUTH_TOKEN>
 *
 * CF environment variables (set in the CF dashboard, never exposed to any AI context):
 *   AUTH_TOKEN     connection password
 *   GITHUB_TOKEN   GitHub fine-grained PAT
 *   GITHUB_REPO    target repo, e.g. yourname/coc-tabletop
 *   DEFAULT_BRANCH default branch, defaults to main
 */

const PROTOCOL_VERSION = "2024-11-05";

// ---------- GitHub API ----------

function gh(env) {
  const repo = env.GITHUB_REPO || "yourname/coc-tabletop";
  const branch = env.DEFAULT_BRANCH || "main";
  const base = "https://api.github.com";
  const headers = {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: "application/vnd.github+json",
    "User-Agent": "coc-tabletop-worker",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  // Raw file content (text), for files of up to 100 MB (the JSON API stops at 1 MB).
  async function raw(path) {
    const res = await fetch(
      `${base}/repos/${repo}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}?ref=${branch}`,
      { headers: { ...headers, Accept: "application/vnd.github.raw" } }
    );
    const text = await res.text();
    if (!res.ok) {
      let msg = res.statusText;
      try { msg = JSON.parse(text).message || msg; } catch { /* not JSON */ }
      throw new Error(`GitHub GET ${path} -> ${res.status}: ${msg}`);
    }
    if ((res.headers.get("content-type") || "").includes("json") && text.startsWith("[")) {
      throw new Error("path is a directory, use book_list");
    }
    return text;
  }

  async function req(method, path, body) {
    const res = await fetch(base + path, {
      method,
      headers: { ...headers, ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await res.text();
    let data;
    try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
    if (!res.ok) {
      const msg = data && data.message ? data.message : res.statusText;
      throw new Error(`GitHub ${method} ${path} -> ${res.status}: ${msg}`);
    }
    return data;
  }

  return { repo, branch, req, raw };
}

function encodeBase64Utf8(str) {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(str);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function decodeBase64Utf8(b64) {
  const binary = atob(b64.replace(/\s/g, ""));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder("utf-8").decode(bytes);
}

// ---------- Bookshelf tools (repo files: scenarios, character sheets, logs, rules) ----------

// A book PDF is read through its extracted text: scripts/library.py extract writes
// assets/<path>.pdf to library/<path>.txt, with a "=== page N ===" line before each page.
function textPath(path) {
  let p = String(path || "").trim().replace(/^\/+|\/+$/g, "");
  if (p.includes("..")) throw new Error("invalid path");
  if (/\.pdf$/i.test(p)) p = p.replace(/\.pdf$/i, ".txt");
  if (p === "assets" || p.startsWith("assets/")) p = "library" + p.slice("assets".length);
  return p;
}

const PAGE_MARK = /^=== page (\d+) ===$/;
const MAX = 80000;

function cap(text) {
  return text.length > MAX ? text.slice(0, MAX) + "\n\n[truncated]" : text;
}

async function bookSearch(env, { query, limit, path }) {
  const g = gh(env);
  const q = String(query || "").trim();
  if (!q) throw new Error("query is required");
  if (!path) {
    const n = Math.max(1, Math.min(parseInt(limit, 10) || 8, 25));
    const data = await g.req(
      "GET",
      `/search/code?q=${encodeURIComponent(`${q} repo:${g.repo} extension:md`)}&per_page=${n}`
    );
    const items = (data.items || []).slice(0, n);
    if (!items.length) return `No matches for: ${q} (to search the books, pass a path such as "library/" or a book)`;
    return items.map((it) => `${it.path}`).join("\n");
  }

  // Search the extracted text of one book or of every book under a folder.
  const p = textPath(path);
  let files;
  if (p.endsWith(".txt")) {
    files = [p];
  } else {
    const prefix = p ? p + "/" : "";
    const tree = await g.req("GET", `/repos/${g.repo}/git/trees/${g.branch}?recursive=1`);
    files = (tree.tree || [])
      .filter((e) => e.type === "blob" && e.path.startsWith(prefix) && e.path.endsWith(".txt"))
      .map((e) => e.path);
    if (!files.length) return `No extracted text under ${p || "/"} (run scripts/library.py extract and commit library/)`;
    if (files.length > 20) {
      return `${files.length} books under ${p}: narrow the path to a subfolder or one book:\n` + files.slice(0, 50).join("\n");
    }
  }
  let rx;
  try { rx = new RegExp(q, "i"); } catch { rx = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"); }
  const n = Math.max(1, Math.min(parseInt(limit, 10) || 20, 50));
  const hits = [];
  for (const f of files) {
    const text = await g.raw(f);
    let page = 0;
    for (const line of text.split("\n")) {
      const m = PAGE_MARK.exec(line);
      if (m) { page = parseInt(m[1], 10); continue; }
      if (rx.test(line)) {
        hits.push(`${f} ${page ? `p.${page}` : "bookmarks"}: ${line.trim().slice(0, 200)}`);
        if (hits.length >= n) return hits.join("\n") + "\n[limit reached]";
      }
    }
  }
  return hits.length ? hits.join("\n") : `No matches for: ${q} in ${p}`;
}

async function bookRead(env, { path, pages }) {
  const g = gh(env);
  if (!String(path || "").trim()) throw new Error("path is required");
  const p = textPath(path);
  if (!p) throw new Error("path is required");
  const text = await g.raw(p);
  const parts = text.split(/\n=== page (\d+) ===\n/);
  if (parts.length < 3) return cap(text);

  // parts: [header (source, page count, bookmarks), n1, page1, n2, page2, ...]
  const header = parts[0].trim();
  if (!pages) {
    if (text.length <= MAX) return text;
    return cap(header) + `\n\n[This book is long: read it by pages, e.g. pages "12-14". Find them with book_search and this path.]`;
  }
  const m = /^\s*(\d+)\s*(?:-\s*(\d+))?\s*$/.exec(String(pages));
  if (!m) throw new Error('pages must look like "12" or "12-14"');
  const from = parseInt(m[1], 10);
  const to = m[2] ? parseInt(m[2], 10) : from;
  const out = [header.split("\n")[0]];
  for (let i = 1; i < parts.length; i += 2) {
    const n = parseInt(parts[i], 10);
    if (n >= from && n <= to) out.push(`=== page ${n} ===\n${parts[i + 1]}`);
  }
  if (out.length === 1) throw new Error(`no pages ${pages} in ${p}`);
  return cap(out.join("\n"));
}

async function bookList(env, { path }) {
  const g = gh(env);
  const p = String(path || "").trim().replace(/^\/+|\/+$/g, "");
  const url = p
    ? `/repos/${g.repo}/contents/${encodeURIComponent(p).replace(/%2F/g, "/")}?ref=${g.branch}`
    : `/repos/${g.repo}/contents?ref=${g.branch}`;
  const data = await g.req("GET", url);
  if (!Array.isArray(data)) throw new Error("path is a file, use book_read");
  return data.map((e) => `${e.type === "dir" ? "📁" : "📄"} ${e.path}`).join("\n");
}

async function bookWrite(env, { path, content, message }) {
  const g = gh(env);
  const p = String(path || "").trim();
  if (!p) throw new Error("path is required");
  if (p.includes("..") || p.startsWith("/")) throw new Error("invalid path");
  if (typeof content !== "string") throw new Error("content is required");
  let sha;
  try {
    const existing = await g.req(
      "GET",
      `/repos/${g.repo}/contents/${encodeURIComponent(p).replace(/%2F/g, "/")}?ref=${g.branch}`
    );
    if (!Array.isArray(existing)) sha = existing.sha;
  } catch { /* file doesn't exist yet, create it */ }
  const body = {
    message: message || `table: update ${p}`,
    content: encodeBase64Utf8(content),
    branch: g.branch,
    ...(sha ? { sha } : {}),
  };
  let data;
  try {
    data = await g.req(
      "PUT",
      `/repos/${g.repo}/contents/${encodeURIComponent(p).replace(/%2F/g, "/")}`,
      body
    );
  } catch (e) {
    if (/-> 403:/.test(e.message)) {
      throw new Error(`This worker's GitHub token is read-only on Contents, so it cannot write ${p}. Push the file from a local clone instead.`);
    }
    throw e;
  }
  return `Wrote ${p} (commit ${data.commit && data.commit.sha ? data.commit.sha.slice(0, 7) : "?"})`;
}

// ---------- Table tools (GitHub Issues: session topics, character topics, logs, OOC) ----------

async function tableList(env, { state, labels, limit }) {
  const g = gh(env);
  const n = Math.max(1, Math.min(parseInt(limit, 10) || 20, 50));
  const st = ["open", "closed", "all"].includes(state) ? state : "open";
  let url = `/repos/${g.repo}/issues?state=${st}&per_page=${n}`;
  if (labels) url += `&labels=${encodeURIComponent(labels)}`;
  const data = await g.req("GET", url);
  const issues = (data || []).filter((i) => !i.pull_request);
  if (!issues.length) return "No table topics.";
  return issues
    .map((i) => {
      const lbl = (i.labels || []).map((l) => l.name).join(", ");
      return `#${i.number} [${i.state}] ${i.title}${lbl ? ` (${lbl})` : ""}`;
    })
    .join("\n");
}

async function tableRead(env, { number }) {
  const g = gh(env);
  const num = parseInt(number, 10);
  if (!num) throw new Error("number is required");
  const issue = await g.req("GET", `/repos/${g.repo}/issues/${num}`);
  const comments = await g.req("GET", `/repos/${g.repo}/issues/${num}/comments?per_page=50`);
  let out = `#${issue.number} ${issue.title} [${issue.state}]\n`;
  out += `labels: ${(issue.labels || []).map((l) => l.name).join(", ") || "none"}\n\n`;
  out += `${issue.body || "(no body)"}\n`;
  for (const c of comments || []) {
    out += `\n--- ${c.user && c.user.login} ---\n${c.body || ""}\n`;
  }
  return out;
}

async function tablePost(env, { title, body, labels }) {
  const g = gh(env);
  if (!title) throw new Error("title is required");
  const payload = { title, body: body || "" };
  if (labels) {
    payload.labels = Array.isArray(labels)
      ? labels
      : String(labels).split(",").map((s) => s.trim()).filter(Boolean);
  }
  const data = await g.req("POST", `/repos/${g.repo}/issues`, payload);
  return `Opened table topic #${data.number}: ${data.title}\n${data.html_url}`;
}

async function tableReply(env, { number, body }) {
  const g = gh(env);
  const num = parseInt(number, 10);
  if (!num) throw new Error("number is required");
  if (!body) throw new Error("body is required");
  const data = await g.req("POST", `/repos/${g.repo}/issues/${num}/comments`, { body });
  return `Replied on #${num}\n${data.html_url}`;
}

async function tableUpdate(env, { number, title, body }) {
  const g = gh(env);
  const num = parseInt(number, 10);
  if (!num) throw new Error("number is required");
  if (!title && body === undefined) throw new Error("provide title and/or body to update");
  const payload = {};
  if (title !== undefined) payload.title = String(title);
  if (body !== undefined) payload.body = String(body);
  if (Object.keys(payload).length === 0) throw new Error("nothing to update");
  const data = await g.req("PATCH", `/repos/${g.repo}/issues/${num}`, payload);
  const parts = [];
  if (title !== undefined) parts.push(`title → ${data.title}`);
  if (body !== undefined) parts.push("body updated");
  return `Updated table topic #${num}: ${parts.join(", ")}`;
}

async function tableTags(env, { number, action, labels }) {
  const g = gh(env);
  const num = parseInt(number, 10);
  if (!num) throw new Error("number is required");
  const act = ["add", "remove", "set"].includes(action) ? action : "add";
  let labelList;
  if (Array.isArray(labels)) {
    labelList = labels.map(s => String(s).trim()).filter(Boolean);
  } else {
    labelList = String(labels || "").split(",").map(s => s.trim()).filter(Boolean);
  }
  if (!labelList.length) throw new Error("labels is required");

  const results = [];
  if (act === "add") {
    for (const label of labelList) {
      try {
        await g.req("POST", `/repos/${g.repo}/issues/${num}/labels`, { labels: [label] });
        results.push(`✅ added: ${label}`);
      } catch (e) {
        results.push(`❌ failed add: ${label} — ${e.message}`);
      }
    }
  } else if (act === "remove") {
    for (const label of labelList) {
      try {
        const encoded = encodeURIComponent(label);
        await g.req("DELETE", `/repos/${g.repo}/issues/${num}/labels/${encoded}`);
        results.push(`✅ removed: ${label}`);
      } catch (e) {
        results.push(`❌ failed remove: ${label} — ${e.message}`);
      }
    }
  } else {
    try {
      const data = await g.req("PUT", `/repos/${g.repo}/issues/${num}/labels`, { labels: labelList });
      const finalLabels = (data || []).map(l => l.name || l).join(", ");
      results.push(`✅ set labels: ${finalLabels || "(none)"}`);
    } catch (e) {
      results.push(`❌ failed set labels — ${e.message}`);
    }
  }
  return results.join("\n");
}

async function tableClose(env, { number, action }) {
  const g = gh(env);
  const num = parseInt(number, 10);
  if (!num) throw new Error("number is required");
  const state = action === "reopen" ? "open" : "closed";
  const data = await g.req("PATCH", `/repos/${g.repo}/issues/${num}`, { state });
  return `Table topic #${num} ${state === "open" ? "reopened" : "closed"}\n${data.html_url}`;
}

// ---------- Tool registry ----------

const TOOLS = [
  {
    name: "book_search",
    description: "Search the repository. Without path: markdown files (sheets, recaps, notes), returns file paths. With path: the extracted text of the books (a book's .pdf or .txt path, or a folder such as library/EN), returns <file> p.<page>: <line>.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Words, or a case-insensitive regex such as \"Sanity|Cordura\"." },
        path: { type: "string", description: "Book or folder to search, e.g. assets/EN/Investigator_Handbook.pdf or library/ES. Omit to search markdown files." },
        limit: { type: "integer", description: "Max results: files without path (up to 25), lines with path (up to 50)." },
      },
      required: ["query"],
    },
    handler: bookSearch,
  },
  {
    name: "book_read",
    description: "Read one file by relative path. A book's .pdf path reads its extracted text (library/<path>.txt); pass pages to read part of it.",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Relative path, e.g. table/my-scenario/recap-1.md or assets/EN/Investigator_Handbook.pdf." },
        pages: { type: "string", description: "PDF page or range of a book, e.g. \"12\" or \"12-14\" (page indices as in book_search results)." },
      },
      required: ["path"],
    },
    handler: bookRead,
  },
  {
    name: "book_list",
    description: "List files and folders in the campaign library.",
    inputSchema: {
      type: "object",
      properties: { path: { type: "string", description: "Relative dir path, empty for root." } },
    },
    handler: bookList,
  },
  {
    name: "book_write",
    description: "Write a text file to the repository (character sheets, session recaps). Everyone with access to the repository can read it. Fails if the worker's token is read-only on Contents.",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Relative path, e.g. campaigns/my-scenario/session-1.md" },
        content: { type: "string", description: "Full file content (overwrites)." },
        message: { type: "string", description: "Commit message." },
      },
      required: ["path", "content"],
    },
    handler: bookWrite,
  },
  {
    name: "table_list",
    description: "List topics on the table (GitHub Issues). Use state: open/closed/all to filter.",
    inputSchema: {
      type: "object",
      properties: {
        state: { type: "string", description: "open, closed, or all." },
        labels: { type: "string", description: "Comma-separated label filter." },
        limit: { type: "integer", description: "Max topics, up to 50." },
      },
    },
    handler: tableList,
  },
  {
    name: "table_read",
    description: "Read one table topic and all its replies by number.",
    inputSchema: {
      type: "object",
      properties: { number: { type: "integer", description: "Issue number." } },
      required: ["number"],
    },
    handler: tableRead,
  },
  {
    name: "table_post",
    description: "Open a new table topic (start a session, recruitment, OOC discussion).",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string", description: "Topic title." },
        body: { type: "string", description: "Topic body (markdown)." },
        labels: { type: "string", description: "Comma-separated labels." },
      },
      required: ["title"],
    },
    handler: tablePost,
  },
  {
    name: "table_reply",
    description: "Reply to a table topic (your turn in the game, or OOC comment).",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "integer", description: "Issue number." },
        body: { type: "string", description: "Reply body (markdown)." },
      },
      required: ["number", "body"],
    },
    handler: tableReply,
  },
  {
    name: "table_update",
    description: "Update a table topic's title and/or body.",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "integer", description: "Issue number." },
        title: { type: "string", description: "New title (optional)." },
        body: { type: "string", description: "New body markdown (optional)." },
      },
      required: ["number"],
    },
    handler: tableUpdate,
  },
  {
    name: "table_tags",
    description: "Add, remove, or set labels on a table topic. action: add | remove | set.",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "integer", description: "Issue number." },
        action: { type: "string", description: "add, remove, or set. Default: add." },
        labels: {
          description: "Label names: comma-separated string or array of strings.",
          oneOf: [
            { type: "string" },
            { type: "array", items: { type: "string" } },
          ],
        },
      },
      required: ["number", "labels"],
    },
    handler: tableTags,
  },
  {
    name: "table_close",
    description: "Close or reopen a table topic. action: close (default) | reopen.",
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "integer", description: "Issue number." },
        action: { type: "string", description: "close or reopen. Default: close." },
      },
      required: ["number"],
    },
    handler: tableClose,
  },
];

const TOOL_MAP = Object.fromEntries(TOOLS.map((t) => [t.name, t]));

// ---------- MCP JSON-RPC ----------

async function handleRpc(msg, env) {
  const { id, method, params = {} } = msg;

  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: params.protocolVersion || PROTOCOL_VERSION,
        capabilities: { tools: {} },
        serverInfo: { name: "coc-tabletop", version: "1.0.0" },
      },
    };
  }

  if (method === "notifications/initialized") {
    return null;
  }

  if (method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        tools: TOOLS.map((t) => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema,
        })),
      },
    };
  }

  if (method === "tools/call") {
    const tool = TOOL_MAP[params.name];
    if (!tool) {
      return { jsonrpc: "2.0", id, error: { code: -32602, message: `Unknown tool: ${params.name}` } };
    }
    try {
      const args = params.arguments || {};
      const text = await tool.handler(env, args);
      return {
        jsonrpc: "2.0",
        id,
        result: { content: [{ type: "text", text }] },
      };
    } catch (e) {
      return {
        jsonrpc: "2.0",
        id,
        result: { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true },
      };
    }
  }

  return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } };
}

// ---------- HTTP entry point ----------

async function handleRequest(request, env) {
  const url = new URL(request.url);

  if (url.pathname === "/" || url.pathname === "") {
    return new Response("coc-tabletop worker alive", {
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  if (url.pathname === "/mcp") {
    const token = url.searchParams.get("token");
    if (!token || token !== env.AUTH_TOKEN) {
      return new Response("Unauthorized", { status: 401 });
    }

    if (request.method === "GET") {
      const sessionId = crypto.randomUUID();
      return new Response(
        `event: endpoint\ndata: /mcp?token=${token}&session=${sessionId}\n\n`,
        {
          headers: {
            "content-type": "text/event-stream",
            "cache-control": "no-cache",
            connection: "keep-alive",
          },
        }
      );
    }

    if (request.method === "DELETE") {
      return new Response("", { status: 200 });
    }

    if (request.method === "POST") {
      try {
        const body = await request.json();
        if (Array.isArray(body)) {
          const results = [];
          for (const msg of body) {
            const result = await handleRpc(msg, env);
            if (result !== null) results.push(result);
          }
          if (results.length === 0) return new Response("", { status: 202 });
          return new Response(JSON.stringify(results), {
            headers: { "content-type": "application/json" },
          });
        }
        const result = await handleRpc(body, env);
        if (result === null) return new Response("", { status: 202 });
        return new Response(JSON.stringify(result), {
          headers: { "content-type": "application/json" },
        });
      } catch (e) {
        return new Response(
          JSON.stringify({ jsonrpc: "2.0", error: { code: -32700, message: `Parse error: ${e.message}` } }),
          { status: 400, headers: { "content-type": "application/json" } }
        );
      }
    }

    return new Response("Method not allowed", { status: 405 });
  }

  return new Response("Not found", { status: 404 });
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};
