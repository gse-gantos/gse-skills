# gse-skills

GSE Construction's internal Claude Code skills marketplace. One plugin (`gse-skills`),
containing all company skills, distributed as a single install. Update the repo, everyone's
plugin updates.

## Install (one time, per person)

In Claude Code:

```
/plugin marketplace add gse-gantos/gse-skills
/plugin install gse-skills@gse-skills
```

(the second command is `<plugin-name>@<marketplace-name>` — both happen to be named
`gse-skills` here; run `/plugin marketplace list` if you need to confirm the marketplace name)

Claude Code will pull the latest skills from this repo. To pick up future updates:

```
/plugin marketplace update gse-skills
```

## What's in here

| Skill | Purpose |
| --- | --- |
| `gse-cartographer` | Maintains a Project File Map (boot diff-scan, classification, view regeneration) for a job folder. |
| `gse-drawing-engine` | Processes construction drawing sets into a provenance-tracked drawing database and answers RFI/query lookups against it. |
| `gse-spec-library` | Converts spec PDFs (project manuals, individual sections, addenda) into per-section markdown plus a master index. |
| `gse-wiki-audit` | Audits a job wiki for health, consistency, sourcing, and link-mesh quality. |
| `gse-wiki-ingest` | Ingests source material (specs, drawings, meeting notes, etc.) into a job wiki. |
| `gse-wiki-promote` | Promotes an explicitly-approved output into durable wiki knowledge. |
| `gse-wiki-query` | Answers questions from a job wiki, map-aware (knows what exists but is unprocessed). |
| `submittal-reviewer` | Classifies a submittal, routes it to specs/drawings/wiki, runs a check-lens review pass, and produces a ranked issues file. |
| `grill-me` | Interviews you relentlessly about a plan or design, resolving each branch of the decision tree, until you reach shared understanding. |

## Status

These skills have been generalized for cross-job use — they contain no job-specific specs,
documents, rulings, or identifiers. Each job supplies its own via its folder structure and
`Claude/_Memory/AGENTS.md`; the skills only describe how to find and use them. Treat this repo
as the one source of truth going forward: don't hand-maintain a personal copy of any of these
skills.

## Repo layout

```
.claude-plugin/
  marketplace.json   # registers this repo as a marketplace
  plugin.json         # the gse-skills plugin manifest
skills/
  <skill-name>/
    SKILL.md
    references/       # optional supporting docs
    scripts/           # optional helper scripts
```

## Updating a skill

Edit the skill's files directly in `skills/<skill-name>/`, commit, and push. Bump the
`version` in `.claude-plugin/plugin.json` for meaningful changes so people can tell an update
happened.
