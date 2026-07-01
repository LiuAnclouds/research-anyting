export const meta = {
  name: 'vlavlm-full-pipeline',
  description: 'Execute the complete VLA/VLM research pipeline: Exploration -> Construction -> Validation',
  phases: [
    { title: 'Exploration', detail: 'Idea Broker -> Literature Survey -> Paper Reader' },
    { title: 'Construction', detail: 'Theory Crafter -> Rapid Prototype -> Experiment Engineer' },
    { title: 'Validation', detail: 'Insight Analyzer -> Deep Verification -> Review Simulator' },
  ],
}

phase('Exploration')

const ideaReport = await agent(
  'Generate 3-5 candidate research directions for the specified VLA/VLM topic. ' +
  'Use the vla-vlm-idea-broker agent definition. Each direction must include ' +
  'a falsifiable hypothesis, >=3 cited papers, and novelty/feasibility/impact scores.',
  { phase: 'Exploration', agentType: 'vla-vlm-idea-broker', schema: null }
)

const surveyReport = await agent(
  'Conduct a systematic literature survey for the VLA/VLM research direction. ' +
  'Use the literature-survey agent definition. Cover relevant venues (RSS, CoRL, ICRA for VLA; ' +
  'CVPR, ICCV, ECCV for VLM). Screen >=50 papers, deep-analyze >=20.',
  { phase: 'Exploration', agentType: 'literature-survey', schema: null }
)

phase('Construction')

const theoryReport = await agent(
  'Design the mathematical formulation for the VLA/VLM approach. Use the theory-crafter ' +
  'agent definition. VLA-specific: action space formulation, embodiment modeling. ' +
  'VLM-specific: resolution modeling, hallucination bounds.',
  { phase: 'Construction', agentType: 'theory-crafter', schema: null }
)

const protoReport = await agent(
  'Execute a minimal viable experiment. Use the vla-vlm-rapid-prototype agent definition. ' +
  'VLA: LIBERO-Spatial, 1-2 baselines, 1 embodiment, 1-2 GPU-days. ' +
  'VLM: MME + POPE, 1-2 baselines, single resolution, 1-2 GPU-days. ' +
  'Pre-register success criterion before execution.',
  { phase: 'Construction', agentType: 'vla-vlm-rapid-prototype', schema: null }
)

const expReport = await agent(
  'Execute comprehensive experimental validation. Use the experiment-engineer agent definition. ' +
  'VLA: >=4 benchmarks (LIBERO, CALVIN, SimplerEnv, RLBench), >=7 baselines. ' +
  'VLM: >=6 benchmarks (MME, MMBench, SEED-Bench, MM-Vet, POPE, HallusionBench), >=7 baselines.',
  { phase: 'Construction', agentType: 'experiment-engineer', schema: null }
)

phase('Validation')

// Insight, deep-verification, and review-simulator all consume the experiment
// outputs from disk; none reads the others' content. Per
// shared/references/parallelism-doctrine.md they MUST fan out.
const [insightReport, verifyReport, reviewReport] = await parallel([
  () => agent(
    'Extract causal explanations for experimental outcomes. Use the vla-vlm-insight-analyzer ' +
    'agent definition. VLA: success rate decomposition, failure mode taxonomy. ' +
    'VLM: hallucination decomposition, capability profiling.',
    { phase: 'Validation', agentType: 'vla-vlm-insight-analyzer', schema: null }
  ),
  () => agent(
    'Independently verify every claim. Use the deep-verification agent definition. ' +
    'VLA-specific: sim-to-real gap, embodiment overfitting. ' +
    'VLM-specific: hallucination decomposition, prompt sensitivity.',
    { phase: 'Validation', agentType: 'deep-verification', schema: null }
  ),
  () => agent(
    'Simulate multi-role peer review. Use the review-simulator agent definition. ' +
    'Include VLA/VLM-specific checklist items.',
    { phase: 'Validation', agentType: 'review-simulator', schema: null }
  ),
])

log('VLA/VLM Full Pipeline complete.')
return { ideaReport, surveyReport, theoryReport, protoReport, expReport, insightReport, verifyReport, reviewReport }