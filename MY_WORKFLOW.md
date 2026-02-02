# My Cursor Workflow — Quick Reference

**Your daily workflow for [Project Name]**  
**Updated:** [Date]

---

## 🚀 FIRST TIME SETUP COMMAND

**When starting a new project or onboarding a new AI agent, use this command:**

```
Read MY_WORKFLOW.md, PROJECT_MASTER_PLAN.md, PROGRESS_LOG.md, and .cursorrules to understand this project's workflow, context, and documentation system. Then check if all required documentation files exist and help set up any missing ones.
```

**What this does:**
- ✅ Reads the workflow (this file)
- ✅ Understands project context and roadmap
- ✅ Sees recent activity and current status
- ✅ Learns all safety rules and protocols
- ✅ Verifies documentation system is complete
- ✅ Helps set up any missing files

**After running this command, the agent will:**
- Know your daily workflow
- Understand project priorities
- Know what to document at session end
- Follow all safety constraints
- Be ready to help with your work

---

## 🌅 START OF SESSION

### 1️⃣ (Optional) Pull Latest from Git
```bash
git pull origin main
```

**First time setting up this project?** See "Initial Git Setup" section below.

---

### 2️⃣ Start Working in Cursor
**You do:** Just start chatting with Cursor. No special prompt needed.

**Cursor automatically:**
- ✅ Reads `.cursorrules` (knows all protocols)
- ✅ Reads `PROGRESS_LOG.md` (sees recent work)
- ✅ Reads `PROJECT_MASTER_PLAN.md` (knows context)

**You don't need to:**
- ❌ Copy/paste any protocols
- ❌ Remind Cursor of the rules
- ❌ Tell Cursor what files to read

---

## 💻 DURING SESSION

**You:** Work normally — ask questions, run analyses, write, make decisions

**Cursor:** Helps you work and mentally notes what to document at the end

---

## 🌙 END OF SESSION

### 1️⃣ Update All Documentation
**Prompt Cursor with ONE sentence:**

```
Update the logs with this session's work
```

**OR the full version:**
```
Update the progress log, project master plan, and decision log with this session's work
```

**Cursor will automatically:**
- ✅ Update `PROGRESS_LOG.md` (what, why, insights, next steps)
- ✅ Update `PROJECT_MASTER_PLAN.md` (if roadmap progress)
- ✅ Update `DECISION_LOG.md` (if decisions made)
- ✅ Update `TECHNICAL_SPECS.md` (if specs changed)
- ✅ Update "Current Status" section

---

### 2️⃣ (Optional) Push to Git
```bash
git add -A
git commit -m "Session: [brief description]"
git push origin main
```

---

---

## 🔧 GIT IN ANTIGRAVITY

### Is it always connected?
**YES.** You only need to initialize once (which is already done). Antigravity has persistent access to the repository.

### Daily Routine in Antigravity

**1. Start of Session (Optional)**
If you worked on another computer, ask the agent:
> "Pull the latest changes from git"

**2. End of Session**
Ask the agent:
> "Push my work to git"

The agent will run:
```bash
git add .
git commit -m "Update work"
git push
```

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

## 📊 VISUAL WORKFLOW

```
Session Start:
┌─────────────────────────────────────────┐
│  Start chatting with Cursor             │  ← No special prompt needed
│  (Cursor auto-reads .cursorrules)       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Work normally                          │  ← Ask, analyze, write, decide
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  "Update the logs with this             │  ← One sentence prompt
│   session's work"                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Cursor updates 2-4 files automatically │  ← Documentation complete
└─────────────────────────────────────────┘

Session complete!
```

---

## ⏱️ TIME PER SESSION

| Task | Time | What You Do |
|------|------|-------------|
| **Start working** | 0 seconds | Just start chatting |
| **Working** | Variable | Normal work |
| **Documentation** | 5 seconds | "Update the logs" |

**Total overhead:** ~5 seconds per session

---

## 🎯 KEY REMINDERS

### What's AUTOMATIC (Cursor does without asking):
- ✅ Reads `.cursorrules` at session start
- ✅ Reads `PROGRESS_LOG.md` and `PROJECT_MASTER_PLAN.md`
- ✅ Knows the documentation protocol
- ✅ Updates all relevant files when you prompt at end

### What YOU need to do:
- ☑️ Work normally during session
- ☑️ "Update the logs" at end (5 sec)

---

## 🆘 TROUBLESHOOTING

**Cursor seems to have forgotten context**  
→ Prompt: "Read the progress log and project master plan"

**Not sure what to work on next**  
→ Look at `PROGRESS_LOG.md` "Next Steps" section (top of file)

**Need to understand a past decision**  
→ Check `DECISION_LOG.md`

---

## 💡 ALTERNATE END-OF-SESSION PROMPTS

Any of these will trigger the full update:

- "Update the logs with this session's work" ✅ **Shortest**
- "Update the progress log, project master plan, and decision log with this session's work" ✅ Most explicit
- "Document this session" ✅ Alternative
- "Follow the session completion protocol" ✅ Formal

**Pick whichever feels natural!**

---

## 📝 GIT COMMANDS QUICK REFERENCE

| Task | Command |
|------|---------|
| **Check status** | `git status` |
| **See what changed** | `git diff` |
| **Stage all changes** | `git add -A` |
| **Commit changes** | `git commit -m "Your message"` |
| **Push to GitHub** | `git push origin main` |
| **Pull from GitHub** | `git pull origin main` |
| **Check remote** | `git remote -v` |
| **View commit history** | `git log --oneline` |

---

*This is your ONE workflow reference. Everything else is for the AI or detailed reference.*

