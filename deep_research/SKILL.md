---
name: deep-research-pro
description: "Use this skill for web research, technical fact-checking, competitive analysis, and sourcing. Triggers: 'research', 'search', 'find', 'check', 'latest news', 'documentation', 'specs', 'comparison', 'who is', 'what is the best', 'current trends', or requests for 'citations' and 'links'."
---

# Deep Research & Fact-Grounding Playbook

## Overview
Eliminates hallucinations by grounding every claim in 2026 real-world data. This skill prioritizes primary sources (Docs, GitHub, Academic Papers) over secondary blogs or AI-generated summaries.

## Available Search Tools
- **Engines**: Tavily, Exa, Google Search
- **Verification**: DeepWiki MCP (for technical verification)

## Research Protocol
1. **Query Expansion**: Convert one user query into 3-5 specific sub-queries (e.g., instead of "UAS batteries," search for "LiIon vs LiPo energy density 2026" and "UAS battery discharge rates").
2. **Diversity Filter**: Must source from at least 3 different domains (e.g., .gov, .edu, .io, .org).
3. **Recency Check**: For tech (AI, UAS, Home Lab), discard data older than 18 months unless it is a fundamental law or standard.
4. **Triangulation**: A fact is only "Confirmed" if found in two independent, reputable sources.

## Compound Operations
- **Market Analysis**: Search for competitors, pricing, and user sentiment for a new product or software tool.
- **Spec Verification**: Confirm the exact weight, power, and dimensions of a UAS component or hardware part.
- **Literature Review**: Summarize the current state of a specific AI hardware field (e.g., Blackwell vs. Gaudi 3 performance benchmarks).
- **OSINT Fusion**: Connect disparate data points from news, social media, and official reports for situational awareness.

## Output Format
- **Confidence Score**: Provide a score (1-10) based on source quality and consistency.
- **Source List**: Hyperlinked markdown list of all sites visited during the research pass.
- **Synthesis**: A "TL;DR" followed by detailed findings categorized by sub-topic.