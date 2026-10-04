---
name: accidental-data-loss-prevention
description: |
  STOP AND VERIFY: Before executing any command or tool that results in irreversible data loss, you MUST obtain explicit affirmative user consent.
license: Apache-2.0
---

# Accidental Data Loss Prevention Protocol

> [!CAUTION]
> **STOP AND VERIFY**: Before running any command or tool that results in irreversible data loss or unrecoverable state modification, you **MUST** obtain explicit affirmative user consent.

## Mandatory Rules:
1. **Destructive Operations Strictly Blocked**:
   - Git operations: git reset --hard, git clean -fdx, force pushes (git push --force).
   - File deletions: Bulk recursive deletions (
mdir /s /q, 
m -rf, deleting .agents/memory/ or database archives).
   - SQL operations: DROP TABLE, DROP DATABASE, TRUNCATE, or bulk unconstrained DELETE.
2. **Explicit Consent Protocol**:
   - Halt execution immediately.
   - Explain what files/data will be permanently deleted and why.
   - Ask for direct confirmation and wait for user response before proceeding.
