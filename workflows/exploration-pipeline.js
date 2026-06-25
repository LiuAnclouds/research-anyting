export const meta = {
  name: 'exploration-pipeline',
  description: 'Execute the exploration layer: Idea Broker -> Literature Survey -> Paper Reader',
  phases: [
    { title: 'Ideate', detail: 'Generate and evaluate research directions' },
    { title: 'Survey', detail: 'Systematic literature survey with gap analysis' },
    { title: 'Deep Read', detail: 'Deep reading of top papers with hypothesis generation' },
  ],
}

phase('Ideate')
const ideaReport = await agent(
  'Generate 3-5 candidate research directions. Use the appropriate idea-broker agent definition. ' +
  'Each direction: falsifiable hypothesis, >=3 cited papers, novelty/feasibility/impact scores.',
  { phase: 'Ideate', schema: null }
)

phase('Survey')
const surveyReport = await agent(
  'Conduct systematic literature survey. Use the literature-survey agent definition. ' +
  'Multi-source search, snowball sampling, taxonomic classification, gap analysis.',
  { phase: 'Survey', schema: null }
)

// Extract top papers from survey for deep reading
const topPapers = surveyReport?.match(/\[\[paper-[^\]]+\]\]/g)?.slice(0, 5) || []

phase('Deep Read')
const paperReports = await pipeline(
  topPapers,
  (paper, idx) => agent(
    `Deep read: ${paper}. Use the paper-reader agent definition. ` +
    'Three-pass protocol. Produce structured notes, critical analysis, generated hypotheses.',
    { label: `read-${idx + 1}`, phase: 'Deep Read', schema: null }
  )
)

log(`Exploration complete. ${topPapers.length} papers deep-read.`)
return { ideaReport, surveyReport, paperReports }