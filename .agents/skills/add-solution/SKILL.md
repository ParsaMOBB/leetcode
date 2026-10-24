---
name: add-solution
description: Add an accepted LeetCode solution to this repo with a theoretical, visual write-up, then hand back a title, tags and a paste-ready post. Use when the user runs /add-solution or asks to add / write up a LeetCode solution.
argument-hint: "<problem link | slug | number> [optional context about the approach]"
---

# add-solution

Turn an accepted LeetCode solution into a folder in this repo: the code, a `Solution.md` write-up with visuals, and a README row. Then give the user a title and tags, and the post text ready to paste into LeetCode.

## Input

- **Problem**: a LeetCode link, slug, or problem number. This is the first argument.
- **Code**: the user's accepted code. It is either pasted in the message or already in the problem folder (`Solution*.{cpp,py,...}`). If there is none, ask for it. There is no way to fetch submissions.
- **Context** (optional): everything after the first argument, plus anything in the message. This is the user's own reasoning: how they found the idea, the proofs they have in mind, the order of the solutions. It is the backbone of the write-up.

## Ground rules

- **Never assume.** If the idea behind a step, the reason a solution is correct, the order of the narrative, or anything else is unclear from the context and the code, **ask the user** before writing it. Never invent a story ("I first tried…"), a proof step or a claim about the user that they did not give. Collect the open questions and ask them together, with AskUserQuestion when the options are clear-cut.
- **Do not test or benchmark the code.** It is already Accepted on LeetCode. Keep it byte-for-byte, comments included.
- **Ask before outward actions.** Commit and push only after the user approves what you show them.

## Steps

### 1. Fetch the problem

```bash
python3 .agents/skills/add-solution/lc.py fetch <link|slug|number>
```

This prints JSON with `id`, `title`, `slug`, `difficulty`, `topic_tags`, `url`, `folder` (`<id>-<slug>`) and `statement` (Markdown). The statement is for your understanding only. Never write it into the repo (no `Problem.md`).

### 2. Set up the folder

- The folder is `<id>-<slug>/` at the repo root. If the user already made a folder named only `<id>/`, rename it.
- One solution goes in `Solution.<ext>`. Several go in `Solution-1.<ext>`, `Solution-2.<ext>`, … in the user's order.
- If a stray `Problem.md` exists there, leave it alone and never stage it.

### 3. Understand, then ask

Read the statement, the code and the context. Work out the full argument: the model, the key lemma(s), why each solution is correct, and the complexity. List every point you cannot justify from what the user gave and ask about it (see Ground rules). Wait for the answers.

### 4. Write `Solution.md`

Use LeetCode's solution template, in English:

```
# Intuition
# Approach
# Complexity
# Code
```

Style (the user cares a lot about this):
- **Intuition**: 2–3 sentences. The user's own story and the key idea. No roadmap paragraph.
- **Approach** opens with one natural framing sentence (e.g. "Only some pairs can be swapped, so it is natural to model the problem with a graph."). Then numbered `###` sections.
- The tone is theoretical but still a **solution**: definitions, **Lemma / Theorem** with short *Proof* … $\blacksquare$, and a clear characterization before the algorithm. Write it in the user's voice, sober and precise.
- **No emoji**, except the heading `### Edge case ⚠️` when there is an edge case. No hype or marketing phrasing ("hiding somewhere", "gave it away", "the magic"). State facts plainly.
- Use LaTeX (`$…$`, `$$…$$`) for math and tables where they help (for example a greedy trace on an example).
- Check the statement's examples against the final characterization in a short list.
- **Complexity**: `- Time complexity: $$O(...)$$` with a one-line reason, the same for space, and one block per solution.
- **Code**: the code exactly as submitted. With several solutions, use consecutive fenced blocks with labels, which LeetCode shows as tabs: ```` ```cpp [Solution 1 - O(n log n)] ````.
- **Images use relative paths** (`![Lemma 1](images/lemma.gif)`), so they render in the local preview and on GitHub. They are pinned to absolute URLs only at post time (step 8).

### 5. Visuals

Make 2–5 visuals that carry the argument (a lemma in motion, a transformation, the key structure on an example). They should not be decoration. Write one script, `<folder>/images/make_images.py` (Pillow, run as `python3 make_images.py .` from `images/`), and commit it with its outputs.

- Reuse the house style and helpers from `3644-maximum-k-to-sort-a-permutation/images/make_images.py`: dark background `(24,24,37)`, the value gradient, Avenir Next + Menlo, 2× supersampling, `save_gif` with per-frame durations, and `Canvas` / `Row`.
- Titles and captions are neutral and descriptive, with no dramatic phrasing. ✓ / ✗ marks are fine.
- **Look at the result**: extract a few frames per GIF (start, mid-animation, end) to the scratchpad, Read them, and fix overlaps, clipped text and missing glyphs before going on.

### 6. README row

Append a row to the index table in `README.md`:

```
| <id> | [<title>](<url>) | <difficulty> | [C++](<folder>/Solution.cpp) | [<post title, with \| escaped>](<folder>/Solution.md) |
```

With several solutions: `[C++ O(n log n)](…/Solution-1.cpp) · [C++ O(n)](…/Solution-2.cpp)`.

### 7. Show and get approval

Open `Solution.md` for the user (VS Code: Markdown preview, which renders the relative images). Then give them:
- a short summary of the write-up's structure,
- **Title**: one recommendation plus up to two alternatives, in the form `<main result> | <method/proof> | <complexity>`, with no emoji (e.g. `k Is the AND of the Misplaced Values | Graph Proof | O(n log n) and O(n)`). The README row uses the chosen one.
- **Tags** for the LeetCode post: the language plus the topics the write-up actually uses. Start from `topic_tags`, drop the ones the solution doesn't use, and add any the approach relies on that LeetCode didn't list (e.g. Graph).

Iterate on their feedback. When the feedback shows a lasting preference about style, record it in this skill's Style section or in memory.

### 8. On approval: commit, push, post text

```bash
git add <folder>/Solution*.* <folder>/images README.md   # never Problem.md
git commit -m "Add <id> <title> with write-up"           # plus the attribution trailer
git push
python3 .agents/skills/add-solution/lc.py post-md <folder>
```

`post-md` refuses to run until HEAD is pushed. It prints the write-up with every relative image link turned into a `raw.githubusercontent.com/<owner>/<repo>/<commit-sha>/…` URL, pinned to that commit so later renames can't break the post, and copies it to the clipboard. Tell the user the post text is on the clipboard, and repeat the final title and tags so they can publish it on LeetCode.
