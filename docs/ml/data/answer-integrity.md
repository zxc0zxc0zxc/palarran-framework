# Preserving general capabilities and complete answers

Two different problems: forgetting general skills after narrow adaptation and mechanically truncated/overly brief answers. Data composition affects both but guarantees neither solution. [Luo et al.](sources.md) and [Tülu 3](sources.md) ground general-regression/multi-skill evaluation; [LIMA](sources.md) grounds example quality. For formatting use actual [chat-template and SFT semantics](sources.md), not a universal EOS string.

## Data and objective

Preserve substantive task-appropriate answers: short where sufficient, long where explanation, proof, code or multiple steps are needed. Do not impose one word limit on every answer or discard “too long” content for attractive throughput. Length alone is not quality; evaluate completeness and correctness separately.

General anchors must cover actually needed skills/languages; domain corpora need full solutions and difficult edges. Do not train on unfinished teacher generations: `finish_reason=length`, lost tails, truncated code/JSON and incomplete exports belong in quarantine/regeneration with a separate budget, not automatic EOS/complete labels. Metadata complete=true is a producer assertion, not semantic text review.

Compare domain-only, domain+general replay and adaptation/LR/epoch settings on dev only at equal compute/exposure. LoRA/QLoRA do not guarantee no forgetting. Do not choose checkpoints by domain loss alone: freeze allowed general regressions and complete-answer criteria beforehand.

## From raw messages to labels

1. Freeze model/tokenizer revisions, actual tokenizer files/template SHA, role mapping, trainer/collator version and objective. Training templates have no generation suffix; generation templates use the required assistant prefix. Do not add special tokens twice after template rendering.
2. Measure actual `input_ids`, `attention_mask`, assistant-span mask and **unshifted** labels after the collator; a decoder-only trainer may shift inside the model. Tool v1 checks this unshifted layout, not every trainer format.
3. Assistant-only SFT: user/system/padding labels=-100, assistant target labels=input_ids. Causal pretraining has a different objective; do not require assistant masks there. Zero supervised tokens or training only on EOS/EOT without non-end targets is a blocker, not a good zero loss.
4. Determine padding by attention_mask/position, not ID equality: pad_id sometimes equals eos_id. Real EOT/EOS at the end of a complete assistant turn must remain supervised. Check model end_token_ids: EOS, EOT and turn delimiters are not always one token.
5. `prompt + response + required special tokens` must fit the context window. Do not apply generic truncation=True then append an “end” to a fragment. First use buckets/smaller prompts/authorized semantic chunking; preserve a complete SFT answer intact or reject/reprepare it. Code/tool/multi-turn chunks retain dependencies and group lineage. Count excess samples/lost target tokens by language/domain/length.
6. Packing is an optimization needing boundary/EOS checks, attention isolation or an explicitly accepted cross-example objective, position IDs and loss masks. v1 token auditing is **unpacked only**, inspecting every input example separately; packing integration is NOT_RUN. One EOS does not prove protection from cross-example leakage.

## Generation and benchmarking

After training separately check max_new_tokens/stop strings/eos_token_id, template compatibility, repetition/length penalties and finish_reason. An inference cap can truncate answers even with a perfect training corpus. Falling average answer length is a signal, not automatic FAIL: correctness/completeness need matched prompts and task-dependent expected lengths.

The frozen suite includes short factual answers, complete multipart answers, long code+tests, schema JSON, multi-turn recall, multilingual/code switching, long input+complete answer, benign controversial questions where allowed, and domain edges. Count truncation/finish_reason=length, missing sections/invalid JSON, incomplete code/tests, unsolicited refusal, factuality and verbosity separately. General acceptance requires predefined non-inferiority bounds by slice, N/uncertainty and base versus adapted exact-checkpoint comparison. Our data gate does not replace this benchmark or claim “general answers are no longer truncated” without training/inference evidence.
