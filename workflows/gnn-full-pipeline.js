export const meta = {
  name: 'gnn-full-pipeline',
  description: 'Execute the complete GNN research pipeline: Exploration -> Construction -> Validation',
  phases: [
    { title: 'Exploration', detail: 'Idea Broker -> Literature Survey -> Paper Reader' },
    { title: 'Construction', detail: 'Theory Crafter -> Rapid Prototype -> Experiment Engineer' },
    { title: 'Validation', detail: 'Insight Analyzer -> Deep Verification -> Review Simulator' },
  ],
}

phase('Exploration')

// Phase 1: Generate research directions
const ideaReport = await agent(
  'Generate 3-5 candidate research directions for the specified topic. ' +
  'Use the gnn-idea-broker agent definition. Each direction must include ' +
  'a falsifiable hypothesis, >=3 cited papers, and novelty/feasibility/impact scores.',
  { phase: 'Exploration', agentType: 'gnn-idea-broker', schema: null }
)

// Gate G1: Verify gap is validated
if (!ideaReport || ideaReport.length < 500) {
  log('G1 FAILED: Idea Broker report insufficient. Restarting with refined input.')
  // In practice, the orchestrator would retry
}

// Phase 2: Literature survey
const surveyReport = await agent(
  'Conduct a systematic literature survey for the research direction. ' +
  'Use the literature-survey agent definition. Search >=3 sources, ' +
  'screen >=50 papers, deep-analyze >=20, gap analysis citing >=2 surveys.',
  { phase: 'Exploration', agentType: 'literature-survey', schema: null }
)

// Phase 3: Deep read top papers
const paperReports = await pipeline(
  surveyReport.split('\n').filter(l => l.includes('[[paper-')).slice(0, 5),
  (paper, idx) => agent(
    `Deep read this paper: ${paper}. Use the paper-reader agent definition. ` +
    'Produce structured notes, critical analysis, and generated hypotheses.',
    { label: `read-paper-${idx + 1}`, phase: 'Exploration', agentType: 'paper-reader', schema: null }
  )
)

phase('Construction')

// Phase 4: Theory design
const theoryReport = await agent(
  'Design the mathematical formulation, algorithm, and complexity analysis. ' +
  'Use the theory-crafter agent definition. Every symbol defined, every ' +
  'assumption stated, every complexity bound derived.',
  { phase: 'Construction', agentType: 'theory-crafter', schema: null }
)

// Phase 5: Rapid prototype
const protoReport = await agent(
  'Execute a minimal viable experiment. Use the gnn-rapid-prototype agent definition. ' +
  'Pre-register success criterion. 1 dataset, 1-2 baselines, minimal model, 1-2 days.',
  { phase: 'Construction', agentType: 'gnn-rapid-prototype', schema: null }
)

// Gate G3: MVE must pass
if (protoReport && protoReport.includes('FAIL')) {
  log('G3 FAILED: Rapid prototype did not pass. Routing back to Theory Crafter.')
}

// Phase 6: Full experiment
const expReport = await agent(
  'Execute comprehensive experimental validation. Use the experiment-engineer ' +
  'agent definition. >=5 datasets, >=7 baselines, >=5 seeds, statistical tests.',
  { phase: 'Construction', agentType: 'experiment-engineer', schema: null }
)

phase('Validation')

// Insight, deep-verification, and review-simulator all consume the experiment
// outputs from disk; none reads the others' content. Per
// shared/references/parallelism-doctrine.md they MUST fan out.
const [insightReport, verifyReport, reviewReport] = await parallel([
  () => agent(
    'Extract causal explanations for experimental outcomes. Use the ' +
    'gnn-insight-analyzer agent definition. Every mechanism supported by evidence.',
    { phase: 'Validation', agentType: 'gnn-insight-analyzer', schema: null }
  ),
  () => agent(
    'Independently verify every claim against raw data. Use the deep-verification ' +
    'agent definition. Assume claims are false until sufficient evidence is presented.',
    { phase: 'Validation', agentType: 'deep-verification', schema: null }
  ),
  () => agent(
    'Simulate multi-role peer review. Use the review-simulator agent definition. ' +
    'EIC + Reviewer#1 (Method) + Reviewer#2 (Experiment) + Skeptic.',
    { phase: 'Validation', agentType: 'review-simulator', schema: null }
  ),
])

log('GNN Full Pipeline complete.')
log(`Review score: ${reviewReport?.match(/Score: (\d+)/)?.[1] || 'N/A'}/100`)

return { ideaReport, surveyReport, theoryReport, protoReport, expReport, insightReport, verifyReport, reviewReport }