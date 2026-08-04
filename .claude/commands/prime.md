# Prime — prt (ARCHIVED)
> This repo is being archived. Priming here is for **harvesting**, not building.

## Read first
CLAUDE.md    # the banner at the top explains what remains to be done and why

## The only sanctioned task
Substantive development stopped **2026-01-12**. `prt` is superseded by
[prm](https://github.com/social-network-health/prm). **If you were sent here to build a
feature, you are in the wrong repo.**

What remains is the harvest pass, and it has three parts because the issues alone miss a
third of the value:

## Run
git ls-files
gh issue list --repo social-network-health/prt --state open --limit 25

## Read — for the harvest
ROADMAP.md                          # self-declared obsolete; the "FUN FACTORS" section is
                                    # transcribed brainstorm material worth mining
docs/Database/schema_plan.md        # v3 relationship-types work is concept material
README.md                           # § Motivation/Purpose is the clearest statement of intent

**The code, not the backlog, holds the import-pipeline work.** Every import issue is already
closed, so reading issues will miss it entirely: `prt_src/google_takeout.py`,
`prt_src/google_contacts.py`, `prt_src/cli_modules/services/import_google.py`, and the Google
People schema docs under `docs/Database/`.

Highest-value open issues: **#147** (CRT/PRT notification protocol — unbuilt, captured
nowhere else), **#145** (small models can't chain bespoke per-lookup tools), **#69** (confirm
a relationship against a rendered diagram), **#37** (why SQLCipher was rejected).

## Before summarizing
Say what you are harvesting and where it should land — `prm`, the PNA Toolkit, or the hub's
org-level plans. Do not propose new development here.
