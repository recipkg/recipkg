# Feedback and requirements format

[简体中文](FEEDBACK_FORMAT.zh-CN.md)

Follow project conventions; a small task can use one Markdown file. Preserve the chain from observation to behavior without inventing numbers or problems to meet a quota.

## Scope and evidence

- Software/recipe version, environment, date, running entry point, and scope.
- Roles, goals, and constraints; recipe facts versus assumptions.
- Per task: starting state → actual operations → final-result verification; expected/observed outcomes, pass/fail/blocked, and evidence location.
- Issue projects, selection reasons, search scope/date, access limitations, and empty results.
- Evidence IDs linking to reproduction steps, screenshots/logs, or issue permalinks. Omit secrets and unrelated personal information.

## Candidate requirements

| Field | Content |
| --- | --- |
| ID and title | Stable identifier and user problem |
| Type | Defect / usability / new feature / aesthetic preference / hypothesis |
| Role and scenario | Who wants to do what, under which conditions |
| Current obstacle | Recipe promise or expectation versus observed behavior |
| Evidence and status | Local test / own-project issue / related-project issue / inference; version, source, and local reproduction status |
| Impact and priority | Effect on tasks, data, or recovery; ordering rationale and workaround, without invented prevalence |
| Behavior and scope | Minimum observable change, behavior to preserve, options and undecided tradeoffs |
| Acceptance | Preconditions, inputs, action, observable result, and relevant failure/recovery/regression scenarios |
| Next step | Ready for recipe / needs validation / deferred; missing evidence or decisions |

An external issue establishes a reported concern, not a defect in this project's current version. Simulated users do not provide human satisfaction scores or population coverage.

## Two different evidence states

These are format examples, not findings about a real product.

- **Reproduced usability problem:** a novice receives an error code without the finite allowed choices. Evidence includes actual entry point, input, and response. A candidate change shows allowed values and a working example. Acceptance covers valid success and correction after invalid input, not merely a sentence in an error.
- **Unverified external lead:** a related project reports duplicate submission on a slow connection. Preserve version, discussion outcome, and relevance. Without local testing, do not call it reproduced. Test result count, feedback, and retries under controlled network conditions before changing the contract.

## Handoff

Summarize completed tasks, findings, and priorities. Preserve counterexamples, unreproduced reports, successful paths, and blockers. State untested platforms/roles, source limitations, and whether requirements entered the recipe or remain proposals. One clean test does not prove all usage is correct.
