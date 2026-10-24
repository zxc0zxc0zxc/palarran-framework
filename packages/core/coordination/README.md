# Core: coordination

[Package](../README.md) · [Instructions](../AGENTS.md)

Optional private cross-machine coordination, not external-action enforcement.

Declared status: `implemented`. Source presence does not establish deployment or operational verification.

- [docs](docs/)
- [templates](templates/)
## Task sharing

[/palarran:core:share](skills/palarran-core-share/SKILL.md) coordinates new subtasks and unfinished checkpoints with two-party consent, exact revisions, generation fencing and separate participant accounting. Read the [workflow and limits](docs/sharing/README.md). The existing bus delivers bounded notifications; local transactions or the inherited Temporal Workflow own the lifecycle. No accounts or subscription limits are transferred.
