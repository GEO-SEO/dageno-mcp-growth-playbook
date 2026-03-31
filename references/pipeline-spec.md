# Dageno Content Factory Pipeline Spec

This reference describes the current skill logic:

- start from Dageno content opportunities
- analyze response detail and citation URLs
- make a **new-content** decision
- output an SEO + GEO blueprint or draft

It also notes future extensions without making them required for the current skill.

## Goal

Turn one Dageno content opportunity into one new content asset.

## Product Framing

The system should follow this model:

- `prompt` = monitored opportunity surface
- `response detail` = evidence of the current AI narrative
- `citation URLs` = evidence of the sources AI trusts
- `new content asset` = the output to produce

Do not model the workflow as:

- one keyword = one article
- or one chat = one article

The response detail and citation URLs are evidence inputs, not direct output units.

## Current Scope

Included now:

- choose a content opportunity
- inspect response detail
- inspect citation URLs
- translate prompt to keyword cluster
- enrich with SEO metrics when available
- classify intentions
- choose a new content asset type
- generate a blueprint or draft

Not included yet:

- existing-content refresh logic
- content inventory matching
- post-publish monitoring loop

## Demand Principles

### 1. GEO demand and SEO demand are different

- `observed_prompt_volume` = real prompt demand for the seed prompt from Dageno
- `estimated_prompt_volume` = proxy demand for fanout prompts when direct prompt data is unavailable
- `search_volume` = keyword demand from SEO connector
- `keyword_difficulty` = keyword competition from SEO connector

### 2. Fanout demand must be labeled honestly

If fanout prompts do not have direct prompt data, do not store them as observed prompt volume.

Use:

- `estimated_prompt_volume`
- `volume_estimation_method`
- `volume_confidence`

### 3. Intentions should follow Dageno categories

Use:

- `Transactional`
- `Commercial`
- `Navigational`
- `Informational`

Recommended structure:

```json
{
  "intentions": [
    {
      "score": 86,
      "intention": "Commercial"
    }
  ]
}
```

## Main Workflow

### Step 1: select one opportunity

Input:

- `get_content_opportunities`

Selection factors:

- priority
- brand gap
- source gap
- platform spread

Output:

- `opportunity_id`
- `seed_prompt`

### Step 2: inspect response detail

Input:

- `Get response detail by prompt`

Goal:

- explain how AI currently frames the prompt

Questions to answer:

- what did AI emphasize
- what did AI omit
- which competitors were mentioned
- what claims, product categories, proof points, or use cases were absent

Output:

- `response_gap_summary`

### Step 3: inspect citation URLs

Input:

- `List citation URLs`

Goal:

- explain what sources AI relied on

Preferred mode:

- fetch cited pages with Jina or Firecrawl

Fallback mode:

- infer from domain, URL, title, and page-type hints

Questions to answer:

- what source types were cited
- what content structure they used
- what evidence style made them citable

Output:

- `citation_summary`

### Step 4: add prompt-side demand

Input:

- seed prompt
- Dageno prompt data

Goal:

- record real prompt demand for the seed opportunity

Output:

- `observed_prompt_volume`

### Step 5: translate the prompt into SEO language

Input:

- seed prompt

Goal:

- create a usable SEO topic model

Output:

- `primary_keyword`
- `keyword_cluster`

### Step 6: add SEO metrics

Input:

- keyword cluster
- SEO metrics connector

Output:

- `search_volume`
- `keyword_difficulty`

If unavailable:

- mark metrics as pending and continue

### Step 7: add intentions

Input:

- keyword cluster

Output:

- keyword-level `intentions`
- cluster-level `dominant_intention`

### Step 8: build the unified opportunity object

Combine:

- opportunity metadata
- response-gap evidence
- citation evidence
- prompt demand
- keyword demand
- intentions

This object is the input to the final decision engine.

### Step 9: decide the new content asset

Current allowed decisions:

- `Pillar`
- `Standard`
- `Lightweight`

This stage does not ask whether an existing page should be updated.

It asks:

- what new asset should be created from this opportunity

### Step 10: generate the blueprint

Output:

- title
- H1
- H2/H3
- FAQ
- citation-informed writing guidance
- chunk plan
- schema recommendations

### Step 11: optional draft generation

If requested, turn the blueprint into a draft.

## Optional Enhancements

### Citation page fetching

Plan A:

- Jina or Firecrawl

Plan B:

- metadata-only citation inference

### SERP enrichment

Plan A:

- approved SERP API or user-provided export

Plan B:

- skip SERP enrichment

SERP is not a hard dependency for the current skill.

## Future Product Extension

Later, this same workflow can be extended into a monitoring loop:

1. publish content
2. monitor the same prompt again
3. check whether brand gap or source gap shrinks
4. decide whether to add more new content or update existing content

That loop is useful product direction, but it is not required for the current skill.

## Suggested Unified Data Model

```json
{
  "opportunity_id": "opp_001",
  "seed_prompt": "GEO implementation guide for technical teams",
  "source": "dageno:get_content_opportunities",
  "prompt_snapshot": {
    "priority": "high",
    "brand_gap": 100,
    "source_gap": 100
  },
  "response_gap_summary": {
    "competitors_mentioned": ["CSP"],
    "brand_missing": true,
    "missing_angles": [
      "brand-specific implementation narrative",
      "enterprise monitoring use case",
      "proof-oriented product framing"
    ]
  },
  "citation_summary": {
    "citation_urls": [
      "https://example.com/guide"
    ],
    "common_source_types": [
      "guide",
      "blog post"
    ]
  },
  "prompt_demand": {
    "observed_prompt_volume": 820
  },
  "keyword_candidates": [
    {
      "keyword": "geo implementation guide",
      "role": "primary",
      "search_volume": 1200,
      "keyword_difficulty": 28,
      "intentions": [
        {
          "score": 82,
          "intention": "Informational"
        },
        {
          "score": 18,
          "intention": "Commercial"
        }
      ]
    }
  ],
  "aggregates": {
    "primary_keyword": "geo implementation guide",
    "dominant_intention": "Informational",
    "recommended_asset_type": "Standard"
  }
}
```
