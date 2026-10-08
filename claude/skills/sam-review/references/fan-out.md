# Large Diff Fan-Out Protocol

For a small/medium diff, review it directly — do not spawn sub-agents.  
Applies the same way whether the diff came from a PR or a local diff/branch.

Fan out only when a single pass would blur attention across unrelated  
components (rule of thumb: >500 changed lines, or files spanning more than  
two domains/components from the Domain Routing table in `SKILL.md`).

1. **Split by component, not by line count.** Group changed files into
  coherent slices (e.g. "CI/CD + deploy config", "core resolver logic",  
   "new utils package + its tests") — each slice should be reviewable on  
   its own without missing shared context. Write each slice to its own  
   diff file (`/tmp/pr<number>_<slice>.diff` for a PR, `/tmp/review-local_<slice>.diff`  
   for a local diff/branch). This grouping is pattern-matching against the  
   Domain Routing table — do it yourself, it doesn't need a model call.
2. **Dispatch one `pr-slice-reviewer` sub-agent per slice, in parallel** —
  not `general-purpose`. It's scoped to read only the diff file it's  
   given (no Bash, and told not to read the local checkout), which avoids a  
   failure mode general-purpose agents hit: reading the local checkout  
   instead of the reviewed branch and reporting findings that don't exist on  
   it. Give each agent:
  - The path to its diff file.
  - The path to the relevant `references/<domain>.md` file(s) — point at  
  the file, don't paste the checklist inline.
  - Nothing else; its system prompt already has the core checklist and  
  output format baked in.
3. **Reconcile before consolidating** — do not just concatenate sub-agent
  outputs into the final report:
  - Re-verify every 🔴/🟡 finding against the actual diff text yourself  
  before including it. A sub-agent flagging something you're not fully  
  sure of is a signal to check, not a fact to pass through.
  - If you can't independently verify a sub-agent-sourced finding against  
  the diff text, keep it but suffix its `Issue` cell with ` (unverified)`  
  — don't add `(verified)` to the rows you did confirm.
  - Check for cross-slice issues no single slice-scoped agent could see:  
  a shared module changed in one slice and consumed in another, a  
  schema/contract produced in one slice and read in another, logic  
  duplicated across slices.
  - If a slice renames or drops a column/field that the "Downstream  
  contract impact" bullet (`references/data-engineering.md`) is concerned  
  with, run `rg -lwF '<column-name>' ~/code/` across sibling repos  
  yourself before finalizing — the slice reviewer has no Bash  
  and reads only its diff file — and fold any hit into the Architectural findings  
  table.
  - Deduplicate findings raised by more than one slice.
  - Emit exactly one consolidated report in the Output Format from `SKILL.md` —  
  never return the per-slice tables as-is.

## Model & cost guidance

- Splitting the diff into slices (step 1) is pattern-matching, not  
judgment — do it directly rather than spending a model call on it.
- Section reviews (step 2) need the same reasoning tier as the main  
review. Missing a subtle correctness/security/architecture issue costs  
far more (a bad merge, or rework re-reviewing) than a smaller model  
saves in tokens — don't downgrade these.
- The reconciliation step (step 3) is where cross-slice issues and  
sub-agent misreads get caught — keep it on the main review thread, not  
delegated to another agent.
