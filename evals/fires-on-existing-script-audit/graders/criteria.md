---
type: llm
weight: 1
---

PASS if the response (a) says it will read and run the script once before changing anything, (b) identifies at least three of: login every run causing the lockout, sleep-based waits, Selenium where a request would do, missing dedupe key causing duplicates, no failure notification, password stored in the code, (c) says it will fix one thing at a time and verify same input gives same output, and (d) does not propose a full rewrite. FAIL if it proposes rewriting from scratch, ignores the lockout or the duplicates, or asks for the code without any plan.
