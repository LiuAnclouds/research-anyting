# Moon-Research System Configuration

## auto_store
Whether to automatically persist session deltas to the knowledge base after each agent completes.
Set via `/mr auto-store on` or `/mr auto-store off`.
Default: off

## default_domain
The default research domain. Set to avoid typing `/GNN` or `/VLA-VLM` every time.
Set via: "set default domain to GNN"
Default: none (must specify domain each time)

## default_venue_tier
The default target venue tier for new ideas.
Set via: "set default tier to CCF-B"
Default: CCF-B

## kb_compression_threshold
The maximum number of entries in an INDEX.md before auto-fusion is triggered.
Default: 500

## context_injection_limit
The maximum number of words to inject from KB context into agent dispatch prompts.
Default: 500

## search_sources
Comma-separated list of default sources for literature survey.
Set via: "set search sources to semantic_scholar,arxiv,dblp,crossref"
Default: all

## alert_frequency
How often the literature-alert agent checks for new papers.
Options: daily, weekly, none
Default: none

## Preferred Venues
User-specified preferred venues for submission. The /mr recommend-venue command prioritizes these.
Format: ["venues/journals/ccf-b/tkdd", "venues/conferences/ccf-b/cikm"]
Set via: "add preferred venue TKDD" or "remove preferred venue CIKM"
Default: []