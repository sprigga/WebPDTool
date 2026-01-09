#!/bin/bash

# Ralph Wiggum Loop Wrapper Script
# This script wraps the setup-ralph-loop.sh to handle permission issues

# Execute the setup script with arguments
"/home/ubuntu/.claude/plugins/cache/claude-plugins-official/ralph-wiggum/6d3752c000e2/scripts/setup-ralph-loop.sh" "$@"

# Extract and display completion promise if set
if [ -f .claude/ralph-loop.local.md ]; then
  PROMISE=$(grep '^completion_promise:' .claude/ralph-loop.local.md | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')
  if [ -n "$PROMISE" ] && [ "$PROMISE" != "null" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "CRITICAL - Ralph Loop Completion Promise"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "To complete this loop, output this EXACT text:"
    echo "  <promise>$PROMISE</promise>"
    echo ""
    echo "STRICT REQUIREMENTS (DO NOT VIOLATE):"
    echo "  ✓ Use <promise> XML tags EXACTLY as shown above"
    echo "  ✓ The statement MUST be completely and unequivocally TRUE"
    echo "  ✓ Do NOT output false promises to exit the loop"
    echo "  ✓ Do NOT lie even if you think you should exit"
    echo ""
    echo "IMPORTANT - Do not circumvent the loop:"
    echo "  Even if you believe you're stuck, the task is impossible,"
    echo "  or you've been running too long - you MUST NOT output a"
    echo "  false promise statement. The loop is designed to continue"
    echo "  until the promise is GENUINELY TRUE. Trust the process."
    echo ""
    echo "  If the loop should stop, the promise statement will become"
    echo "  true naturally. Do not force it by lying."
    echo "═══════════════════════════════════════════════════════════"
  fi
fi
