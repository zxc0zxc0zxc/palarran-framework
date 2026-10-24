# Infrastructure source register

Retrieved and checked **2026-10-24**. Summaries are selective paraphrases. Company descriptions, vendor product guidance and our audit procedure have different evidentiary weight; none certifies the target under review.

| ID | Primary source and date | Evidence and applicability |
| --- | --- | --- |
| INF-1 | [Google, BeyondProd](https://docs.cloud.google.com/docs/security/beyondprod); page states updated September 2026 | Google's account of its production architecture: service identity, code provenance and authorization beyond network location. Apply the trust-boundary questions at any scale; do not require Borg/Google-specific mechanisms on a VPS. |
| INF-2 | [AWS Well-Architected, Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html); no publication date established in this retrieval | Vendor architecture guidance on network layers, controlled traffic and protection. Separate desired firewall rules, actual exposure and application authorization. Applicability is conceptual outside AWS. |
| INF-3 | [Microsoft SDL, Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling); no publication date established | Microsoft describes requirements, diagrams, threat identification, mitigation and validation. Supports a boundary-oriented review; does not make a diagram operational evidence. |
| INF-4 | [AWS Reliability Pillar, Back up data](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/back-up-data.html); no publication date established | Vendor reliability guidance supporting backup/recovery questions. The target's RPO/RTO and actual restore evidence must come from its own requirements and observations. |
| INF-5 | [Kubernetes project, Security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/); living documentation, retrieved date above | Primary platform guidance for cluster controls. Relevant only to deployed cluster/version/network capabilities; not a requirement to adopt Kubernetes or proof that a manifest is enforced. |

The row structure, scope gates, evidence statuses and scale-dependent review order in [the guide](README.md) are Palarran's synthesis. Refresh sources when a recommendation depends on a changed provider/platform feature; preserve the previous source date and explain the revision. No attack, restore or reachability check was performed while writing this register.
