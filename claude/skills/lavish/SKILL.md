---
name: lavish
description: Builds an HTML review page with the lavish-axi CLI, opens it in the browser for the user to annotate, then polls for and applies their feedback. Invoke with /lavish. For a plain visual page, use the Artifact tool instead.
argument-hint: <what the artifact should show>
disable-model-invocation: true
author: Kun Chen (kunchenguid)
metadata:
  hermes:
    tags: [html, review, artifacts, visualization]
    category: productivity
---

# Lavish Editor

- No global install needed. Run follow-up commands that the output shows as `lavish-axi ...` as `npx -y lavish-axi ...`.
- If `npx -y` exits opaquely (for example status 216 in a sandbox, CI, or harness), use an installed copy: `node "$(npm root)/lavish-axi/dist/cli.mjs" <html-file>` (local), `node "$(npm root -g)/lavish-axi/dist/cli.mjs" <html-file>` (global), or the bare `lavish-axi <html-file>` bin.

## Request

$ARGUMENTS

If the request above is non-empty, the user invoked `/lavish` explicitly - build an HTML artifact for that request now, following the workflow below.
If it is empty, infer what to visualize from the conversation.

## Workflow

1. Create the artifact at `.lavish/<name>.html` in the working directory unless the user names another location. Put local assets (images, CSS, fonts, scripts) in the same directory and use relative paths, never a leading `/`; a local express server serves the file.
2. Run `npx -y lavish-axi <html-file>` to open or resume the session. If the user ended it from the browser, this refuses to reopen; pass `--reopen` only when the user asks for more review or something important needs their visual attention.
3. Run `npx -y lavish-axi poll <html-file>`. On the first poll, pass `--agent-reply "<one-line summary of what you built and what to review first>"`.
   - The poll stays silent until the user acts or a fatal `artifact_failures` response says the review surface is unusable. Leave it running, never kill it. If it is killed or times out, re-run it; queued feedback is never lost.
   - Layout issues go to the user's Layout issues inbox in the top bar and arrive only as a `layout-warnings` prompt the user queued. Never edit for an issue the user has not queued. Cosmetic, intentional, transient, tiny, and uncertain observations stay silent.
   - Keep the poll in the foreground. Background it only through a harness-native tracked job guaranteed to resume or notify the same agent, never via `nohup`, shell `&`, `disown`, fire-and-forget redirects, or a detached terminal without a verified callback. Otherwise poll in the foreground or first wire a verified wake callback into the supervisor. Do not say the artifact is monitored until that wake path is live.
4. Apply the returned prompts. A `layout-warnings` prompt is an explicit repair request: apply every listed fix in one pass before saving; Lavish re-checks after the next artifact load. A `whiteboard` prompt carries an edit summary plus `scenePath` (.excalidraw JSON) and `previewPath` (PNG): read the summary first, open the files only if needed, then update the Mermaid source (never write the scene back).
5. Poll again with `--agent-reply "<message>"` to reply in the browser, under the same foreground-or-verified-wake-path rule.
6. Run `npx -y lavish-axi end <html-file>` when the review is finished. An agent-ended session can be reopened later without `--reopen`.
7. `Send & End` from the browser ends the session. Its final feedback is delivered once, then polling stops. Do not reopen uninvited; give any remaining updates in this conversation.

## Design source

Lavish injects no design system, so artifacts render the same without it. Before writing HTML, pick the design source in this strict order, moving on only when the current step yields nothing:

1. The look or design system the user asked for.
2. The design system of the project the artifact is about (may differ from the working directory): Tailwind or theme config, CSS tokens, component library, brand assets, styled pages. A mock of an app's UI uses that app's design system.
3. Tailwind CSS browser runtime v4 + DaisyUI v5 via CDN; prefer that snippet over hand-written styles unless the user says otherwise.

`npx -y lavish-axi design` prints a content-to-playbook router, the CDN snippet, a Mermaid CDN snippet/init, and the DaisyUI component reference. When you deliver, state which design source you used and why.

## Visual guidance

- Use visual hierarchy so key decisions, risks, tradeoffs, and next actions show at a glance. Prefer sections, cards, tables, diagrams, annotated snippets, and side-by-side comparisons over prose. Choose typography, spacing, color, and layout deliberately.
- Prevent horizontal overflow at every nesting level: nested grid/flex children need `minmax(0, 1fr)` tracks and `min-width: 0`, especially with wide or monospace badges and labels; wrap, truncate, or contain long unbreakable text.
- To describe existing UI or state, show it: capture screenshots of the real pages (run the app read-only if needed). Keep prose for rationale, trade-offs, and open questions.

## Playbooks

Run `npx -y lavish-axi playbook <id>` for each playbook that matches the artifact before writing HTML. One artifact often needs several (for example a plan with a comparison and a diagram).

- `diagram` - relationships, flows, state, architecture. Do not hand-build boxes and arrows from div/flexbox; use the theme-aware Mermaid snippet from `design`, or SVG for richly annotated nodes.
- `table` - dense records; `comparison` - options, tradeoffs, current vs target; `plan` - product or technical plan; `code` - source, patches, PR diffs, before/after; `slides` - when slides are requested
- `input` - required when collecting decisions, choices, preferences, triage, scope, or other structured feedback in the artifact

## Other commands

- Mermaid diagrams in `.mermaid` containers become editable Excalidraw whiteboards in the browser; edits return as `whiteboard` prompts (step 4).
- `npx -y lavish-axi export <html-file> [--out <path>]` writes one portable HTML file with local assets inlined. Remote CDN/font links stay links.
- `npx -y lavish-axi share <html-file> [--password <pw>] [--token <t>]` publishes to ht-ml.app, a third-party host. Shares are PUBLIC unless `--password` is set. Returns the URL and a secret `update_key`. Use `--token` or `LAVISH_AXI_HTML_APP_TOKEN` only if you have an optional bearer token.
- `npx -y lavish-axi stop` shuts down the background server (it also self-stops when idle).
