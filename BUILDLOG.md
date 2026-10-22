# Build Log: AI usage

AI (Claude) was used as a mentor and pair programmer for this capstone: design review, code scaffolding, test writing and debugging. This log records where it helped, where it was wrong, and what changed.

## Where AI helped

- Design: proposed the three request paths, the data model, the 404-instead-of-403 rule and the honeypot behaviour; I committed the result as docs/design.md.
- Implementation: scaffolded the layered FastAPI code, the migration runner, the token-bucket limiter, the geo fallback chain and the widget script.
- Tests: wrote the pytest suite that proves rate limiting, the provider fallback chain, the failing email and the honeypot deterministically, so no server restarts were needed.
- Debugging: explained errors (GH007 email privacy, non-fast-forward push, ModuleNotFoundError, connection timeouts) before suggesting fixes.

## Where AI was wrong, and what changed

- Git author email: AI gave config commands with placeholder text (ID, YOUR_REAL_ID, your-id). Placeholders ended up committed as the author email several times. Fixed by computing the real GitHub noreply address in PowerShell instead of typing it. Published history was rewritten once, while the repo had a single commit and no other users.
- A commit titled "Add public submission endpoint..." actually contained the auth and widget CRUD files, because the file-writing step was skipped before the commit step. The message was left as is rather than rewriting published history; the next commit message matches its content.
- The design document said preflight returns 204; Starlette's CORS middleware returns 200. Documented in the README rather than changing behaviour.
- A pip freeze was taken from the wrong virtual environment (a different project's). Caught by checking the interpreter path and the fastapi version before committing; the file was regenerated.
- Pasting a block containing Read-Host fed later lines into the prompt, leaving empty API keys. Fixed by capturing keys from the seed output with a regular expression.
- A test run took over an hour because Docker Desktop was not running and each database connection waited for the operating system timeout. Fixed by adding connect_timeout=5 to the database URL.
- Long README text pasted into the terminal was cut off at its first code fence, and a later edit deleted half of it. Fixed by editing the file in the editor and verifying its headings.

- The test page (test-site/index.html) contained the text of a closing script tag inside a JavaScript comment. The HTML parser ended the script there, so no widget rendered and half the code showed up as page text. Found from a screenshot, fixed by rewording the comment; the rule is never to write a literal closing script tag inside a script.

## Changes I made myself

(Add your own entries here: what you changed, what you chose differently, and what you learned. The evaluator may ask you to explain any 2-3 lines of the code.)