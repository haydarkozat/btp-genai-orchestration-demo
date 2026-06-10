# Screenshots — evidence index

These PNGs are produced (masked) by [`tools/capture`](../../tools/capture/) from a
real SAP BTP trial session. Each one is the evidence for a specific exercise:

| File                 | Page                       | Proves                                                                 |
| -------------------- | -------------------------- | --------------------------------------------------------------------- |
| `ai-launchpad.png`   | AI Launchpad home          | **Launchpad** — a Generative AI Hub instance exists in the trial.     |
| `orchestration.png`  | Orchestration workbook     | **Orchestration** — a prompt-template + model orchestration config/run. |
| `grounding.png`      | Document grounding         | **Grounding** — grounding / context injection is configured.          |
| `playground.png`     | Model playground           | A foundation model responding live (supporting evidence).             |

All screenshots are masked (email/username and tenant identifiers hidden) before
capture. They are committed as evidence; the saved login session that produced them
is **not** (`tools/capture/.auth/` is gitignored).
