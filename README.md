# LeetCode prep kit

A coding-interview course in Python that you work through with Claude as your coach. It has eleven modules (from Big-O up to dynamic programming and heaps), a timed diagnostic, and reference sheets. Claude keeps your notes, scores your progress and plans your weeks. It won't write your solutions unless you ask for one.

## Before you start

- [Claude Code](https://claude.com/claude-code) installed.
- Python 3 on your machine: Claude runs your code in every review.
- A LeetCode account. Premium is optional: each 🔒 row in a drill table says what to do if it's locked, and the 🔒 problems on the app's practice list can be solved in the app without it.
- This folder on your machine (clone it or unzip it).

## How to start

Open Claude Code in this folder and say *"let's start"*. Claude reads [CLAUDE.md](CLAUDE.md), sets up your notes and asks you a few questions. In a later session, say *"let's start"* again and it picks up where you stopped.

## The process

| Step | What happens | Where |
|---|---|---|
| **1. Discovery** | A short conversation about your target, timeline, experience and goals. It sets the pace and the priorities | `my-prep/profile.md` |
| **2. Module 00 self-check** | Short questions on the basics; you read the sections behind any you miss, then write two toolkit sections from memory | [course/modules/00-before-you-start.md](course/modules/00-before-you-start.md) |
| **3. Diagnostic** | Seven timed problems, written without running the code, about 2h50 | [course/diagnostic.md](course/diagnostic.md) |
| **4. Scoring and plan** | Claude runs your answers, fills your skills matrix and writes your plan | `my-prep/skills-matrix.md`, `my-prep/plan.md` |
| **5. Blocks 01–10** | For each module: read its §0 → answer its self-check → drills, cold → a four-part submission per problem → Claude's review, by running your code → your lesson | [course/README.md](course/README.md), `my-prep/lessons/` |

## Two folders

- `course/` is the same for everyone: the modules, the diagnostic, the reference sheets and the templates. It isn't edited while you train.
- `my-prep/` is yours, and everything about you and your work goes there. It is made from the templates the first time you start the app, or by Claude at your first session if you start there.

## The app

The kit also has a local practice app: your lessons, your progress and a code editor in one web page. It uses only the Python standard library, so there is nothing to install. It needs Python 3.9 or later.

```
python3 app/setup.py     # once: downloads the problem statements
python3 app/server.py    # starts the app and opens your browser
```

`setup.py` is also a button on the app's Home page. The statement text is saved to `app/data/statements/`, which git ignores. Nothing personal is sent and no cookies are used. `server.py` takes `--port N` and `--no-open`. It listens on port 8765, or the next free port up to 8775, and only on 127.0.0.1.

| Page | What it does |
|---|---|
| Home | A daily warm-up, your totals and your progress per module |
| Review | Your skills matrix, with filter chips and links to your notes pages. The lessons are under the module links in the menu |
| Practice | The problem on the left, an editor in the middle, the coach on the right |

118 problems from modules 01–10 can be solved in the app. The other drills in the lessons stay links to LeetCode. The coach uses the `claude` command-line tool (Claude Code) if it is installed; everything else works without it.

**What it stores.** Your code goes in `my-prep/solutions/<slug>.py` and the app's state in `my-prep/app/state.json` (git-ignored; don't edit it by hand). It appends to `my-prep/learnings.md` and to the log table in `my-prep/bugs.md`. It updates three columns (Now, Evidence, Last tested) of topic rows in `my-prep/skills-matrix.md`, and fills Start too the first time, while that cell is `?`. It never lowers a level it didn't write itself. In the Evidence cell it owns only the part that ends in `(app)`: each final submit replaces that part and keeps any other text, yours or Claude's, in place. If `my-prep/` is missing on first start, it creates it from `course/templates/`.

**Known limits.**

- Passing the app's tests is not the same as being accepted on LeetCode. The tests are the kit's, not LeetCode's.
- Your code runs on your machine with your permissions. It has a time limit and no sandbox, and the time limit is the only guard: a solution that allocates without bound can slow your machine until it stops.
- Coach replies use Claude on your own account, so they count against your usage.
- `my-prep/` must be a real folder, not a symlink. If it is a symlink, the app refuses to start.
- If your code starts a child process of its own, that process can keep running after the time limit stops your code.
- Several runs can go at once, for example from two tabs.
- Start the app once. A second start finds the first and opens it, but two starts in the same instant can both run, and then the later save wins. If that happens, stop both and start one.
- The scratch tab and the "coach hidden" choice are kept by your browser for each address. They do not follow you to another port or another browser.
- Only one `.prev.py` is kept per problem. A new Redo or Reset replaces the older one.
