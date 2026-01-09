---
description: "Start Ralph Wiggum loop in current session"
argument-hint: "PROMPT [--max-iterations N] [--completion-promise TEXT]"
---

# Ralph Loop Command

Initialize a Ralph Wiggum self-referential development loop. This command will set up a loop where you work on a task iteratively until completion.

Usage:
```
/ralph-loop "Your task description" --max-iterations 5 --completion-promise "DONE"
```

When you complete the task, output: `<promise>DONE</promise>`

To start the loop, run:
```
/home/ubuntu/WebPDTool/.claude/ralph-wrapper.sh "根據專案的codebase,重新整理分析結果到 README.md內容中" --max-iterations 5
```
