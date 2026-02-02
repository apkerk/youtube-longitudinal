# My Cursor Workflow — Quick Reference

---

## 🌅 START OF SESSION (Morning)

### 1️⃣ Pull Latest from Git

**In Cursor:**
**Just tell your agent:**
```
Pull from Git
```
**OR:**
```
Pull the latest changes from git
```

**The agent will handle:** Pulling latest changes, then automatically reading documentation files (`.cursorrules` is auto-read at session start).

---

**In Anti-gravity:**
**Tell your agent:**
1. "Read ANTIGRAVITY_RULES.md"
2. "Pull from Git" (or "Pull the latest changes from git")

**The agent will handle:** Reading rules, pulling latest changes, then reading documentation files.

**First time setting up this project?** See "Initial Git Setup" section below.

---

### 2️⃣ Start Working

**You do:** Just start chatting with Cursor. No special prompt needed.

**Cursor automatically:**
- ✅ Reads `.cursorrules` (knows all protocols)
- ✅ Reads `PROGRESS_LOG.md` or `task.md` (sees recent work)
- ✅ Reads `PROJECT_MASTER_PLAN.md` (knows context)

**You don't need to:**
- ❌ Copy/paste any protocols
- ❌ Remind Cursor of the rules
- ❌ Tell Cursor what files to read

---

## 💻 DURING SESSION (Working)

**You:** Work normally—ask questions, run analyses, write code, make decisions

**Cursor:** Helps you work and mentally notes what to document at the end

---

## 🌙 END OF SESSION (Evening)

### 1️⃣ Push to Git

**Just tell your agent:**
```
Push to Git
```
**OR:**
```
Push my work to git
```

**The agent will handle:** Staging changes, committing with appropriate message, pushing to remote

**OR with custom message:**
```
Push to Git with message: "your commit message here"
```

---

## 📊 VISUAL WORKFLOW

```
Session Start (Cursor):
┌─────────────────────────────────────────┐
│  "Pull from Git"                        │  ← Simple prompt
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Agent automatically:                   │
│  • Pulls from git                       │
│  • Reads .cursorrules (auto), then      │
│    MY_WORKFLOW.md, PROGRESS_LOG.md,     │
│    PROJECT_MASTER_PLAN.md               │
└────────┬────────────────────────────────┘

Session Start (Anti-gravity):
┌─────────────────────────────────────────┐
│  1. "Read ANTIGRAVITY_RULES.md"         │
│  2. "Pull from Git"                     │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Agent automatically:                   │
│  • Pulls from git                       │
│  • Reads MY_WORKFLOW.md, PROGRESS_LOG.md│
│    PROJECT_MASTER_PLAN.md               │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Work normally                          │  ← Ask, analyze, write, decide
│  (Ask questions, run analyses, etc.)    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  "Push to Git"                          │  ← Simple prompt
└─────────────────────────────────────────┘

Session complete!
```

---

## ⏱️ TIME PER SESSION

| Task | Time | What You Do |
|------|------|-------------|
| **Pull from Git** | 2 seconds | "Pull from Git" |
| **Start working** | 0 seconds | Just start chatting |
| **Working** | Variable | Normal work |
| **Push to Git** | 2 seconds | "Push to Git" |

**Total overhead:** ~4 seconds per session

---

## 🎯 KEY REMINDERS

### What's AUTOMATIC (Agent does without asking):
- ✅ Reads `.cursorrules` at session start (Cursor)
- ✅ Reads documentation files after pulling
- ✅ Handles all git operations (staging, committing, pushing)

### What YOU need to do:
- ☑️ **In Cursor:** "Pull from Git" at beginning (2 sec)
- ☑️ **In Anti-gravity:** "Read ANTIGRAVITY_RULES.md" then "Pull from Git" at beginning
- ☑️ Work normally during session
- ☑️ "Push to Git" at end (2 sec)
- ☑️ Optional: Use "Push to Git with message: 'your message'" for custom commit messages

---

## 🆘 TROUBLESHOOTING

**Agent seems to have forgotten context**  
→ Just say "Pull from Git" again - it will re-read all documentation

**Not sure what to work on next**  
→ Look at `PROGRESS_LOG.md` or `task.md` "Next Steps" section (top of file)

**Need to understand a past decision**  
→ Check `DECISION_LOG.md`

**Git issues**  
→ Just tell the agent: "Pull from Git" or "Push to Git" and let it handle the details

---

## 📚 DETAILED REFERENCES (Optional Reading)

If you need more details, see:
- **`.cursorrules`** or **`AI_RULES.md`** — Full protocols that agents follow
- **`PROJECT_MASTER_PLAN.md`** — Big picture roadmap and context
- **`DECISION_LOG.md`** — History of analytical decisions
- **`TECHNICAL_SPECS.md`** — All technical specifications

But for daily work, **this one file is all you need**.

---

## 📝 GIT WORKFLOW

**Just tell your agent what you want:**

- **"Pull from Git"** or **"Pull the latest changes from git"** → Agent pulls latest changes
- **"Push to Git"** or **"Push my work to git"** → Agent commits and pushes with default message
- **"Push to Git with message: 'your message'"** → Agent commits with your custom message

**The agent handles all the details** (staging, committing, pushing, conflict resolution, etc.)

---

## 🔧 INITIAL GIT SETUP (One-Time Per Project)

### If Starting a New Project

**1. Initialize Git repository:**
```bash
# Navigate to your project root
cd /path/to/your/project

# Initialize Git
git init

# Create initial commit
git add .cursorrules AI_RULES.md PROJECT_MASTER_PLAN.md PROGRESS_LOG.md DECISION_LOG.md TECHNICAL_SPECS.md MY_WORKFLOW.md writing-patterns.md deck.md .gitignore
git commit -m "Initial commit: Project documentation setup"
```

**2. Create repository on GitHub:**
- Go to GitHub.com
- Click "New repository"
- Name it (e.g., `project-name`)
- **Do NOT** initialize with README (you already have files)
- Click "Create repository"

**3. Connect local repository to GitHub:**
```bash
# Add remote (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Or if using SSH:
git remote add origin git@github.com:yourusername/your-repo-name.git

# Set main branch and push
git branch -M main
git push -u origin main
```

**Replace:**
- `yourusername` → Your GitHub username
- `your-repo-name` → Your repository name

**4. Verify connection:**
```bash
git remote -v
# Should show your GitHub repository URL
```

---

*This is your ONE workflow reference. Everything else is for the AI or detailed reference.*
