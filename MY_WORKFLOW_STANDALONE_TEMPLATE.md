# My Cursor Workflow — Quick Reference

**Your daily workflow for [Project Name]**  
**Updated:** [Date]

---

## 🌅 START OF SESSION

### 1️⃣ (Optional) Pull Latest from Git
```bash
git pull origin main
```

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

*This is your ONE workflow reference. Everything else is for the AI or detailed reference.*

