export const meta = {
  name: 'paper-writing-pipeline',
  description: 'Execute the paper writing pipeline: Insight Analysis -> Draft -> Review -> Revise',
  phases: [
    { title: 'Analyze', detail: 'Extract insights and narrative from experimental results' },
    { title: 'Write', detail: 'Generate manuscript sections' },
    { title: 'Review', detail: 'Simulate peer review and identify weaknesses' },
    { title: 'Revise', detail: 'Address review comments and polish' },
  ],
}

phase('Analyze')

const insightReport = await agent(
  'Analyze the experimental results and extract: (1) performance attribution per component, ' +
  '(2) failure case taxonomy, (3) condition analysis, (4) paper narrative. ' +
  'Use the appropriate insight-analyzer agent definition for the domain.',
  { phase: 'Analyze', schema: null }
)

phase('Write')

const sections = ['abstract', 'introduction', 'related-work', 'method', 'experiments', 'conclusion']
const manuscript = await pipeline(
  sections,
  (section) => agent(
    `Write the ${section} section for the paper. Use the paper-writer agent definition. ` +
    `Target venue specifications from the idea's target_venues field. ` +
    `Follow all writing standards from shared/references/writing-standards.md. ` +
    `Prohibited: "To the best of our knowledge", "significantly" without numbers, ` +
    `"very/extremely/completely", "we prove" without proof.`,
    { label: `write-${section}`, phase: 'Write', schema: null }
  )
)

phase('Review')

const reviewReport = await agent(
  'Review the complete manuscript. Use the review-simulator agent definition. ' +
  'Four roles: EIC, Reviewer#1 (Methodology), Reviewer#2 (Experiments), Skeptic. ' +
  'Calibrate assessment to the target venue tier.',
  { phase: 'Review', schema: null }
)

// Gate: Manuscript must score >=70/100
const score = reviewReport?.match(/Score:\s*(\d+)/)?.[1]
if (score && parseInt(score) < 70) {
  log(`Review score ${score}/100 < 70. Major revisions needed.`)
}

phase('Revise')

const revised = await agent(
  'Revise the manuscript based on all review comments. Address every critical issue. ' +
  'Document all changes with section/page/line references. ' +
  'Use the paper-writer agent definition.',
  { phase: 'Revise', schema: null }
)

log('Paper writing pipeline complete.')
return { insightReport, manuscript, reviewReport, revised }