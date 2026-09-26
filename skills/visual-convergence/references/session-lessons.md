# Session lessons — draft case study

The project produced a usable, user-retained interactive eye and several modest visual improvements. It did **not** reach photographic acceptance. These lessons support better decisions and narrower claims; they do not demonstrate a reliable path to photorealism or transfer to other subjects.

Evidence labels used here:

- **Observed/recorded:** supported by inspected source, available user corrections or experiment records. A recorded critic judgment remains that critic's judgment.
- **Derived rule:** a proposed response to an observed failure. Its benefit outside this case remains untested.
- **Hypothesis:** plausible explanation or process improvement without a controlled counterfactual.
- **Case constraint:** a decision for this commission, not a universal rule.

This skill was published from the [reviewed eye-project draft](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/skills/visual-convergence/SKILL.md). The procedure and case study are self-contained. Links to `Drew-Goddyn/the-eye` point to optional supporting records in a private repository and require access; they are not prerequisites for using the skill. Its [independent draft review](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/skill-review.json) checked the cited records and considered a moving mechanism and an interactive material scene as tabletop cases, not empirical validation.

The [curated evidence](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/session/episode-records.json) contains exact selected JSON fields, original relative paths and SHA-256 identities from Dreams revision `2fea7c6d608f2fc999485b614831700f5baad27a`, plus short relevant user corrections. IDs below name those records. The [current family comparison](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/checkpoint/current-state.png) shows the remaining visual gap. Earlier rejected assets and raw logs stay in their archive; the checkpoint includes the actual retained assets.

Available history included the current conversation's successive user handoffs, retrieved portions of this task's earlier messages, committed experiment records, source, captures and critic reports. Some retrieved turns contained no message bodies. The full rejected Threshold/video history and every intermediate artifact were not re-reviewed, nor were all recordings watched at normal speed. Reported earlier outcomes are labelled accordingly. No raw chat, account diagnostics or unrelated context is published here.

<a id="e1"></a>
## E1 — Representation and independent state

**Decision/test:** Earlier video-pose work was rejected according to the user-provided review; its full implementation was not reproduced here. The retained implementation uses a deforming mesh, adjacent corrective blending and an explicit controller. Its tests exercise takeover, reversal continuity, cancellation and idle behavior. The user accepted the controllable experience.

**Result:** The retained controller keeps visible closure separate from deliberate hold progress. Idle does not earn deliberate progress; input takes over the current visible state. The [controller](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/controller.js) and [checks](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/controller.test.mjs) demonstrate that specific state design. They do not prove photographic rendering or continuous perceptual smoothness.

**Future decision:** Test the representation against interruption and independent-state requirements before expensive appearance work. Determine which motions need independent clocks and which need shared continuity. “Use meshes,” “always separate every clock,” and “video cannot work” are not supported general conclusions. A better-looking initial still would not have answered the interaction question. Static work needs an inspectable result, not an invented interruption test. **Derived rule; earlier video failure is reported history.**

<a id="e2"></a>
## E2 — A still was not a state-family contract

**Decision/test:** After single-image rounds, the user identified the target as underconstrained and approved a locked family at closure 0.00, 0.20, 0.45, 0.70, 0.90 and 1.00. The next loop compared every pose and both layouts. Records: `target-pack`, `single-target`, `pose-loop`.

**Result:** The family review exposed how a reflection gain at the first two poses did nothing for the four more closed poses. A subsequent more visible margin did not yield a convincing family gain. The target family made those distinctions inspectable; it did not solve contact, lashes or skin realism. The generated references have approximate registration and do not prove a feasible continuous deformation between them.

**Future decision:** Define expectations across states relevant to the experience and preserve their identity during comparison. Add transition evidence where stills cannot answer the question. Flag contradictions instead of moving the reference to fit a candidate. Six poses and this particular camera are **case constraints**; improved coverage is **observed**, successful convergence is not.

<a id="e3"></a>
## E3 — Source quality and conversion loss were different problems

**Decision/test:** An authored scan was tested as source material. The user rejected its game-character appearance and requested an unchanged-open-pose comparison of reproducible supplied-source shading, browser shading and the locked target. Record: `scan-conversion`.

**Result:** Disabling native scattering produced a related harsh pore appearance; restoring effective eye-colour density and a dielectric reflection improved the browser. The recorded conversion reduced eye-colour tile density from roughly 4096 to 1005 pixels. The strongest reproduced native view still looked synthetic, so faithful conversion alone would not meet the target. Native and browser tone mapping differed, preventing calibrated attribution of every tonal change.

**Future decision:** Establish the source's attainable appearance and the runtime loss before investing in deformation or increasingly complex materials. A source's scan origin or anatomical richness does not qualify the final image. The record supports particular recoverable losses; it does not show that scans, real-time rendering or the source asset category cannot succeed. **Observed local result; general diagnostic is a derived rule.**

<a id="e4"></a>
## E4 — Protect the visible behavior, not merely its controller

**Decision/test:** The scan kept the accepted controls, yet its fold descended as a padded ridge. The user required comparison with the retained broad covering surface. An initial correction introduced a sharp transition and was rejected; a completed re-authoring broadened the centre slightly without removing the ridge. Record: `scan-closure`.

**Result:** Both versions closed the aperture, but neither reproduced the preferred changing tissue form. Improvement over the previous scan was insufficient against the retained eye and target. The scan was parked. This is evidence against that completed replacement, not against scans generally.

**Future decision:** Preserve behavior as visible state/transition evidence alongside code checks. Qualify an alternative against the current best before letting source detail or novelty displace it. The earlier instruction to freeze fallback files applied during the scan study; the user later explicitly allowed visual-file changes. Turning that temporary boundary into a permanent geometry freeze would have contradicted the commission. **Observed failure; broad late closure is a case constraint.**

<a id="e5"></a>
## E5 — Making a feature clearer sometimes made the eye worse

**Decision/test:** Repeated repairs pursued thicker margins, stronger folds, finer lashes or richer corners. A quieter skin treatment revealed a regular dark groove and graphic lashes. Finer lashes exposed the rim and fragmented at small size. Added wet relief read as a bead and was restored. Records: `form-material`, `junction`, `open-mid`, `connected-opening`.

**Result:** Two retained passes produced small integrated-corner and lash/corner gains while preserving broad closure. The open-to-mid pass retained a coherent result after four unretained internal variants; its 0.45 gain was weakest. The later connected-opening candidate narrowed the lower strip but introduced a dark inner split. It passed interaction checks and preserved late geometry, yet failed the user's complete-eye gain criterion at 0.45 and was rejected.

**Future decision:** Treat a symptom as an observation, not an instruction to exaggerate its nearest structure. Judge the whole deliverable at intended size and against the retained best. Allow rough intermediate work; apply promotion gates to the completed candidate. Local improvement, invariant preservation and final acceptance are different outcomes. **Observed tradeoffs; no universal ban on prominent rims, folds or coordinated changes.**

<a id="e6"></a>
## E6 — A rejected rendering change still answered a useful question

**Decision/test:** The renderer disabled cavity reception and lash casting and applied an analytic cavity-darkening multiplier. With retained geometry, A was current, B removed only that scalar, C added configured eyelid shadows, and D tested lash casting separately. Framing, exposure, maps and pose stayed fixed. Records: `renderer-diagnostic`, `renderer-audit`; [causal comparison](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/session/renderer-causal.png).

**Result:** B lifted pockets and broad border darkness but left a hard upper line and lower strip. C added a broad hard inner-globe shadow; D added comb-like hair projections, especially midway closed. Coverage, bias brackets, two resolutions and a caster-off control established a meaningful test. None earned replacement. Resolution sensitivity remained, and the fixed directional key limited the conclusion.

**Future decision:** When compounded edits stall, isolate competing causes and verify that the tested mechanism functions before assessing it. Distinguish brightness from believable contact. Preserve the finding even when the candidate is rejected. This experiment rejects this shadow substitution under held lighting; it does not reject physical shadows or prove geometry is the sole cause. **Observed partial cause; remaining causes are hypotheses.**

<a id="e7"></a>
## E7 — Stop rules and narrow steering also needed criticism

**Decision/test:** The early procedure limited repair rounds. A later two-round recurrence rule returned persistent family defects for review. The user superseded it, asking for a different approach instead of repeatedly returning the same problems. An asset-level attempt then completed three unretained variants; a subsequent source-asset test also failed to beat the retained closure. Records: `single-target`, `pose-loop`, `asset-attempt`, `scan-closure`, and the curated user corrections.

**Result:** The strict rules bounded effort and prevented replacing the best with regressions. They did not resolve the repeated defect. Looser authorization also did not produce photographic success. A repeated symptom count alone does not tell whether the next useful action is an ablation, a new source, a coherent reconstruction or a stop.

**Future decision:** Use the user's actual budget and stop rule. Within that budget, recurring symptoms should change the question or approach; avoid spending another round on an indistinguishable tweak. Permit incomplete intermediates, then apply a whole-result gate. Pause when a next approach needs authority or presents a protected-behavior tradeoff. **Derived calibration, not evidence for an optimal number of rounds.**

**What may have been wrong in our steering:** repeated narrowly named fixes, compound constraints and many successive handoffs may have narrowed exploration or encouraged small administratively complete batches. The record shows recurring defects and corrections, but no controlled alternative workflow or cost accounting. Reduced handoff churn and broader coherent attempts are **hypotheses**, not proven cures. Neither rigid micromanagement nor unlimited autonomous iteration is justified by this case.

<a id="e8"></a>
## E8 — Evidence categories cannot certify one another

**Decision/test:** Controller tests and callback traces repeatedly passed while appearance remained blocked. A form/material reviewer inspected 389 consecutive recorded frames in selected windows and found ordered motion, but reported an isolated whole-image quality change at a keyframe. The baseline contained the same event. Record: `form-material`.

**Result:** Matching baseline behavior and keyframe timing supported a capture/encoding explanation, but pre-encoding output was unavailable. Continuous normal-speed quality remained unobserved. Synthetic focus handling and portrait emulation also had narrower scope than native input and physical-device claims. Later corrected matched stills reset residual gaze before exact poses; comparing nominal closure alone had allowed a small mismatch.

**Future decision:** Match evidence to image, motion, control, conversion and taste claims separately. Diagnose suspect recording frames before attributing them to geometry. Label the actual observation method. A passing test, low callback gap or attractive still cannot certify unseen motion. Define which observations are needed for the next retention decision versus final acceptance. Missing motion evidence blocks a motion-dependent promotion, while an independent diagnostic can still be useful within scope. Limited appearance retention does not waive an affected protected motion requirement. **Observed evidence limits; perceptual quality remains unproven.**

<a id="e9"></a>
## E9 — Independent authorship was not always blind review

**Decision/test:** Fresh critics compared candidates and sometimes rejected improvements claimed by implementation narratives. However, some calls inherited the parent conversation; the renderer review explicitly used a full-history fork. That exposed preceding commentary even though it was a separate reviewer. The record does not measure how much this affected any verdict.

**Result:** Another single-target review scored the retained image 6.0; a later critic scored retained and rejected images 4.0 each. Those were within-review comparisons, not evidence of a calibrated two-point decline. Records: `single-target` and the curated review-process observation.

**Future decision:** Give a reviewer a clean context and a minimal artifact packet when claiming a blind comparison. State expected outcomes and protected constraints, then obtain the artifact judgment before the builder's explanation. Separate independence from blinding and incremental retention from human approval. Keep causes tentative until tested. **Information exposure is observed; reduced bias and better future judgments are hypotheses.**

<a id="e10"></a>
## E10 — Recoverability matters; packaging is not visual progress

**Decision/test:** Review packages grew to include repeated runtime snapshots, many comparisons and extensive checks. One external review explicitly lacked actual `.blend`, `.glb` and texture bytes despite recorded paths/hashes. The user asked for minimal visual review ZIPs and later for a standalone published checkpoint.

**Result:** The renderer diagnostic yielded useful attribution with no new visual improvement. Its large local evidence set did not change that status. The extraction copied the actual retained assets, matched twelve browser screenshots, reproduced the exact GLB from the saved source, replayed the interaction sequence, then verified a fresh GitHub clone. [Origin](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/checkpoint/origin.json), [verification](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/checkpoint/verification.json), [fresh clone](https://github.com/Drew-Goddyn/the-eye/blob/2648810452d555af4d4225c17934c3b72903161c/evidence/checkpoint/fresh-clone.json).

**Future decision:** Identify which artifact was actually reviewed and retain a runnable source/asset recovery path. Provide one decision-bearing comparison with concise evidence and limits. Full distributable checkpoints need real essential assets; routine iteration handoffs can refer to a recoverable checkpoint plus deltas. Keep visible improvement, diagnostic learning and administrative completion distinct. Reduced duplication is a **plausible efficiency improvement**, not a measured realism benefit.

<a id="attribution"></a>
## Attribution and limits of adaptation

This draft draws its implementation → capture → independent critique → revision structure from [achimala/dream-loop Pro](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/references/pro-mode/workflow.md), inspected at revision `9bddb901f7d071cfefdd21e264267c757177a9df`. Its [asset guidance](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/references/pro-mode/assets-3d.md) was also consulted. [MIT notice](notices/dream-loop-MIT.txt).

Upstream starts from one target image, uses an image score and acceptable FPS as its completion gate, and responds to repeated gaps with a major reconsideration before a stalled stop. This project added a locked pose family, separate evidence categories, visible-behavior protection and changing user-authorized budgets. The local two-round stop rules and their later reversal are **not** attributed to upstream. This draft does not adopt upstream's exact-pixel objective, numeric acceptance threshold, provider order or generation-permission assumptions. None is demonstrated here as a generally effective rule for interactive work.

Instruction structure follows the requested [writing-for-agents](https://github.com/Drew-Goddyn/skills/blob/53470415ea92f1644ecff9523125c813e86cc791/skills/chatgpt%20web/writing-for-agents/SKILL.md) and [SKILL-MECHANICS](https://github.com/Drew-Goddyn/skills/blob/53470415ea92f1644ecff9523125c813e86cc791/skills/chatgpt%20web/writing-for-agents/SKILL-MECHANICS.md), with the available local Codex skill-creator guidance used for the actual frontmatter contract. [Original MIT notice](notices/writing-for-agents-MIT.txt). ChatGPT-specific routing in the reference is not imposed on this local draft.

The main procedure links every consequential decision rule to an episode above. Support comes from one mixed-outcome eye project. Transfer to other visual domains, an optimal budget, the benefit of clean-context critics, and the effect of less prescriptive steering remain unvalidated. A review of hypothetical non-eye cases is a transfer/readability check, not empirical validation.
