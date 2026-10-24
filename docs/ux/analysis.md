# Analyze reference UX

## Compare equivalent tasks

For every priority business journey, define a task script: initial state/role → goal → minimum input → success criterion. Exercise/study the scenario in selected products according to access; mark unsupported tasks inapplicable. Do not compare anonymous search in one product with another's paid onboarding as a single metric.

Comparison matrix:

| Journey | Product / evidence ID | Entry and action order | What is visible/clear | Friction/recovery | Our conclusion and confidence |
|---|---|---|---|---|---|
| J1 | R1 / R1-O01 | Observed flow | What supports the task | Where context can be lost | reuse/adapt/reject + reason |

Count steps only within actually exercised/documented scope. Time-on-task, conversion, error rate and “users prefer” require measurement; screenshots do not provide these metrics. Expert evaluation is a qualitative hypothesis, not fabricated user research.

## Screen analysis

Look beyond whether buttons exist:

- Are the goal, current context/status and next main step clear?
- Are necessary inputs, result and action close together? Which fields/blocks distract or appear too early?
- Are navigation, back/cancel/close and preservation of entered data predictable? Is there an explicit escape from dead ends?
- What happens during loading/empty results/errors/permission denial/success? Which states were actually observed, and which does our product need independently of the reference?
- Are the same tasks available on mobile/touch/keyboard? Screenshot-only keyboard behavior remains unknown.
- Is registration required before value is delivered, and does our business justify it? Do not automatically copy another product's paywall/upsell.

Expert questions draw on [NN/G usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/): feedback, user control, consistency, error prevention/recovery and necessary information. This is a diagnostic lens, not blanket approval of every popular pattern.

## From observations to our concept

Describe each adopted pattern through `business need → reference observation → applicability → adaptation → Screen/Block/State ID → ADR → verification method`. If advice follows our reasoning rather than observation, explicitly label it hypothesis/agent judgment. Do not claim “Google does this” after studying only a retelling or old screenshot.

Choose a coherent flow instead of blindly mixing four interfaces. For conflicting patterns, explain the choice through our audience, task frequency, necessary information, errors and device constraints. Do not import dark patterns: hidden costs, concealed subscriptions, preselected consent or obstructed refusal. Describe business goals and usability together; more clicks/time on site is not success by itself.

For each Screen ID, provide concise rationale: task served, why blocks are ordered this way, reuse, supporting evidence and what to verify. A long analysis report must not turn into long screen copy.

## Expert review and subsequent validation

Prioritize problems by impact on the key task, frequency when known, recoverability and evidence confidence. Do not assign precise damage percentages without data. A concept can be coherent and review-ready before user testing while remaining a hypothesis.

Usability-validation plan: task success, errors, finding actions, label comprehension, return/recovery on mobile and desktop; actual participants/observations are separate. Do not write “validated” after one agent review of diagrams. Preserve review questions and choice context for the next task.
