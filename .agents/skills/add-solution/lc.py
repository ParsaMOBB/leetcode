#!/usr/bin/env python3
"""LeetCode helper for the add-solution skill (stdlib + curl, no login).

  lc.py fetch <problem-url | slug | number>   JSON: problem metadata + statement
  lc.py post-md <problem-folder>              Solution.md with image links pinned
                                              to the pushed commit, for pasting
                                              into LeetCode (also copied to clipboard)
"""
import html, json, os, re, subprocess, sys, time
from html.parser import HTMLParser

GQL = "https://leetcode.com/graphql"


def gql(query, variables, tries=4):
    # curl, not urllib: LeetCode's edge often resets Python's TLS connections.
    body = json.dumps({"query": query, "variables": variables})
    cmd = ["curl", "-sS", "-m", "20", "-X", "POST", GQL, "-H", "Content-Type: application/json",
           "-H", "Referer: https://leetcode.com", "-H", "User-Agent: Mozilla/5.0", "--data-binary", "@-"]
    for attempt in range(tries):
        r = subprocess.run(cmd, input=body, capture_output=True, text=True)
        try:
            out = json.loads(r.stdout)
            break
        except ValueError:
            if attempt == tries - 1:
                sys.exit(f"error: LeetCode did not answer after {tries} tries "
                         f"({r.stderr.strip() or r.stdout[:200]})")
            time.sleep(2 ** attempt)
    if out.get("errors"):
        sys.exit("error: " + json.dumps(out["errors"]))
    return out["data"]


class ToMarkdown(HTMLParser):
    """Just enough HTML → Markdown for LeetCode problem statements."""
    def __init__(self):
        super().__init__(); self.out = []; self.pre = False
    def handle_starttag(self, tag, attrs):
        if tag == "pre": self.pre = True; self.out.append("\n```\n")
        elif tag in ("strong", "b") and not self.pre: self.out.append("**")
        elif tag in ("em", "i") and not self.pre: self.out.append("*")
        elif tag == "code" and not self.pre: self.out.append("`")
        elif tag == "sup": self.out.append("^")
        elif tag == "li": self.out.append("\n- ")
        elif tag == "img": self.out.append(f"![]({dict(attrs).get('src', '')})")
        elif tag in ("p", "div", "ul", "ol", "br"): self.out.append("\n")
    def handle_endtag(self, tag):
        if tag == "pre": self.pre = False; self.out.append("\n```\n")
        elif tag in ("strong", "b") and not self.pre: self.out.append("**")
        elif tag in ("em", "i") and not self.pre: self.out.append("*")
        elif tag == "code" and not self.pre: self.out.append("`")
        elif tag == "p": self.out.append("\n")
    def handle_data(self, data): self.out.append(data)
    def text(self):
        s = html.unescape("".join(self.out)).replace("\xa0", " ")
        return re.sub(r"\n{3,}", "\n\n", s).strip()


def problem(slug):
    q = """query q($slug: String!) { question(titleSlug: $slug) {
        questionFrontendId title titleSlug difficulty content topicTags { name } } }"""
    d = gql(q, {"slug": slug})["question"]
    if not d:
        sys.exit(f"error: no problem with slug {slug!r}")
    p = ToMarkdown(); p.feed(d["content"] or "")
    return {"id": d["questionFrontendId"], "title": d["title"], "slug": d["titleSlug"],
            "difficulty": d["difficulty"], "topic_tags": [t["name"] for t in d["topicTags"]],
            "url": f"https://leetcode.com/problems/{d['titleSlug']}/",
            "folder": f"{d['questionFrontendId']}-{d['titleSlug']}",
            "statement": p.text()}


def slug_of(arg):
    """Problem URL, slug, or frontend number → slug."""
    m = re.search(r"problems/([\w-]+)", arg)
    if m:
        return m.group(1)
    if not arg.isdigit():
        return arg
    q = """query q($k: String!) { questionList(categorySlug: "", limit: 20, skip: 0,
        filters: { searchKeywords: $k }) { data { questionFrontendId titleSlug } } }"""
    for item in gql(q, {"k": arg})["questionList"]["data"]:
        if item["questionFrontendId"] == arg:
            return item["titleSlug"]
    sys.exit(f"error: no problem with number {arg}")


def post_md(folder):
    folder = folder.rstrip("/")
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    owner_repo = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote).group(1)
    pushed = subprocess.run(["git", "branch", "-r", "--contains", sha],
                            capture_output=True, text=True, cwd=root).stdout.strip()
    if not pushed:
        sys.exit("error: HEAD is not pushed yet, image links would be broken")
    rel = os.path.relpath(os.path.abspath(folder), root)
    base = f"https://raw.githubusercontent.com/{owner_repo}/{sha}/{rel}/"
    md = open(os.path.join(folder, "Solution.md")).read()
    md = re.sub(r"\]\((?!https?://)([^)]+)\)", lambda m: f"]({base}{m.group(1)})", md)
    subprocess.run(["pbcopy"], input=md, text=True)
    print(md)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "fetch":
        print(json.dumps(problem(slug_of(sys.argv[2])), indent=2, ensure_ascii=False))
    elif len(sys.argv) == 3 and sys.argv[1] == "post-md":
        post_md(sys.argv[2])
    else:
        sys.exit(__doc__)
