# AI Coding Assistant Guidelines

1. **Keep Core Logic Simple (100–200 Lines):** Prefer clear, readable Python over premature abstractions or heavy frameworks.
2. **Every Line Must Be Defensible:** Do not introduce code, dependencies, or `Dockerfile` instructions that cannot be justified line by line.
3. **Strict Specification Alignment:** Implement only requested requirements; document all explicit assumptions in `README.md`.
4. **No Magic Literals:** Use `Enum` and centralized constants in `src/powerplant/config.py`.
5. **Transparent, Tested Errors:** Never swallow or mask real exceptions (`exc_info=True`); write tests for every handled error path.
6. **Human Git Ownership:** Never execute `git add`, `git commit`, `git push`, or history-mutating commands via AI tools.
