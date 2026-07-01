export const meta = {
  name: 'cross-domain-exploration',
  description: 'Explore cross-domain research directions combining GNN and VLA-VLM modules',
  phases: [
    { title: 'Module Discovery', detail: 'Identify compatible modules across domains' },
    { title: 'Combination Assessment', detail: 'Evaluate K-way cross-domain combinations' },
    { title: 'Venue Recommendation', detail: 'Recommend venues for cross-domain ideas' },
  ],
}

phase('Module Discovery')

// Query both domains' modules in parallel — independent KB lookups
// (per shared/references/parallelism-doctrine.md: no data dep, MUST fan out).
const [gnnModules, vlavlmModules] = await parallel([
  () => agent(
    'List all validated and partially-validated GNN modules from the knowledge base. ' +
    'For each module, report: name, category, assumptions, composable_with, and limitations.',
    { phase: 'Module Discovery', schema: null }
  ),
  () => agent(
    'List all validated and partially-validated VLA-VLM modules from the knowledge base. ' +
    'For each module, report: name, category, assumptions, composable_with, and limitations.',
    { phase: 'Module Discovery', schema: null }
  ),
])

phase('Combination Assessment')

const crossDomainIdeas = await agent(
  'Evaluate cross-domain module combinations. Criteria: ' +
  '(1) Shared abstraction: modules from different domains address the same abstract challenge. ' +
  '(2) Data modality bridge: concrete way to map data between domains exists. ' +
  '(3) Joint contribution: combination produces something neither domain could alone. ' +
  'For each valid combination, generate a falsifiable hypothesis and novelty assessment.',
  { phase: 'Combination Assessment', schema: null }
)

phase('Venue Recommendation')

const venueRecs = await agent(
  'For each cross-domain idea, recommend target venues. Cross-domain ideas may not fit ' +
  'neatly into a single community. Consider: (a) venues that publish cross-domain work, ' +
  '(b) which community would be the primary audience, (c) whether the contribution is ' +
  'stronger in one domain than the other. Use the venue database.',
  { phase: 'Venue Recommendation', schema: null }
)

log('Cross-domain exploration complete.')
return { gnnModules, vlavlmModules, crossDomainIdeas, venueRecs }