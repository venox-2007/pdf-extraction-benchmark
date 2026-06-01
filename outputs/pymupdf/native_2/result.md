Are Tools All We Need? Unveiling the Tool-Use Tax in LLM Agents


                     Kaituo Zhang1 Zhen Xiong2,3 Mingyu Zhong1 Zhimeng Jiang4
                           Zhouyuan Yuan5 Zhecheng Li5 Ying Lin1

                  1University of Houston 2University of Southern California 3New York University
                          4Texas A&M University 5University of California, San Diego



                          Abstract                      information that is topically relevant, linguistically
                                                                         natural, and superficially plausible, yet unhelpful or
                Tool-augmented reasoning has become a pop-
                                                             misleading for the target reasoning chain. Recent                    ular direction for LLM-based agents, and it is
                 widely assumed to improve reasoning and reli-        studies show that such distractors can substantially2026               ability. However, we demonstrate that this con-        disrupt reasoning-path selection and final accuracy,
                 sensus does not always hold: in the presence      and that noisy external information may even am-
                   of semantic distractors, tool-augmented reason-        plify failures in reasoning and search-augmentedApr            ing does not necessarily outperform native CoT.       systems (Xiong et al., 2025; Yang et al., 2025; Lee
               To explain this performance gap, we propose
30           a Factorized Intervention Framework that        et al., 2026; Pham et al., 2026). These findings                                                               suggest that semantic distractors are a particularly
                     isolates the cost of prompt formatting, the over-
                                                                   revealing stress test for tool-conditioned reasoning,                 head of the tool-calling protocol, and the actual
                  gain from executing tools. Our analysis reveals       because they simultaneously challenge evidence
                 a critical tradeoff: under semantic noise, the        selection, tool invocation, and the integration of
                  gains from tools often fail to offset the "tool-       external results.[cs.AI]
                 use tax", which is the performance degrada-        At the same time, existing evaluations provide
                    tion introduced by the tool-calling protocol it-                                                                  limited insight into this failure mode.  Tool-use
                      self. To address this, we introduce G-STEP,
                                                       benchmarks mainly measure whether models can
                 a lightweight inference-time gate to mitigate
                                                                 successfully call tools, while recent work on rea-                  protocol-induced errors. While this yields par-
                        tial recovery, our findings suggest that more       soning and agent evaluation increasingly argues
                    substantial improvements still require strength-        that final-answer accuracy alone is insufficient for
                 ening the model’s intrinsic reasoning and tool-       diagnosing intermediate failures (Chen et al., 2025;
                    interaction capabilities.                       Lee and Hockenmaier, 2025; Zhou et al., 2025;
                                              Hwang et al., 2025; Ou et al., 2025; Winston and
          1  Introduction
                                                                           Just, 2025). Yet these lines of work still stop short
             In recent years, augmenting large language mod-   of explaining a basic question that arises in noisy
               els (LLMs) with external tools has become a cen-   semantic settings: why can native chain-of-thought
                tral paradigm for extending reasoning and real-   (CoT) outperform a full tool-augmented protocol,arXiv:2605.00136v1
            world task-solving capabilities. Function calling,   even when tools are available in principle? This
             search augmentation, and tool-augmented agents   gap is especially important for deployment, since
             are widely regarded as effective ways to provide    failures in tool-augmented systems may stem not
           models with up-to-date information, precise com-   only from missing capabilities, but also from the
              putation, and access to external services (Zhang   mechanics of tool invocation and interaction itself
               et al., 2026; Chen et al., 2023; Liu et al., 2025;   (Cheng et al., 2026; Wang et al., 2026c).
          Chen et al., 2025; Patil et al., 2025). Across re-      In this work, we study the CoT–Tool gap un-
             cent progress in tool-use training and evaluation, a    der semantic distractors through four sequential
          common assumption has emerged: tool use should    research questions:  whether the gap emerges,
            improve performance and reliability.             where the expected gains from tool use are lost,
             However, this assumption has mostly been es-   what mechanism explains when tool use helps
             tablished under relatively clean input conditions.   or hurts, and whether such failures can be miti-
             In realistic settings, model inputs often contain se-   gated by lightweight inference-time control. To an-
             mantically related but reasoning-irrelevant context:   swer these questions, we construct two benchmark


                                                    1

datasets, GSM8K-Sem-Distractor and HotPotQA-   negatives; and Hedged Uncertainty (HU), which
Sem-Distractor, propose a factorized intervention   adds hedging cues such as “reportedly” to simulate
framework that decomposes the gap into style    uncertain information sources.
cost (∆sty), function-calling protocol overhead      Rather than treating semantic distractors as
(∆frc), and computation gain (∆cmp), introduce    generic data augmentation, we use them as a con-
the capability overlap principle to explain why    trolled stress test to probe whether tool-conditioned
tool gains are often redundant with capabilities    reasoning remains beneficial under semantically
already present in native CoT, and validate this    relevant but logically unhelpful noise. This setting
account with a lightweight G-STEP intervention.   allows us to study not only whether tool use helps,
Rather than arguing that tools are broadly ineffec-   but also when the protocol itself becomes a source
tive, our goal is to identify when tool augmentation    of degradation.
breaks down under semantically noisy conditions
                                                    2.2 A Factorized Intervention Frameworkand to explain why, complementing recent work on
inference-time correction and robustness (Tie et al.,  We begin by comparing standard CoT and Agent-
2025).                                              Full on the semantic distractor benchmarks, and
  We summarize our contributions as follows:       define their end-to-end performance gap as the dif-
                                                    ference in final-answer accuracy. The direction and
    • We introduce a CoT-centered view of tool-use                                             magnitude of this gap are determined empirically.
     tax, using native CoT as the reference point                                            However, this comparison only captures the net
     to analyze when tool augmentation provides                                                 accuracy difference and doesn’t reveal which com-
     marginal benefit or incurs additional cost un-                                                ponents of the agentic pipeline drive the observed
     der semantic distractors.                                                 change. To disentangle these effects, we introduce
                                                     the factorized intervention framework in Figure 1.
    • We propose a factorized intervention frame-
                                                   Figure 1 summarizes our seven-condition in-
    work that decomposes the CoT–Tool gap into
                                                    tervention framework.   It consists of a primary
    Function Calling (FC)-style formatting cost,
                                               decomposition chain from native reasoning to
     tool-use protocol overhead, and real tool-
                                                             full tool-augmented reasoning: NoTool-CoT →
     execution gain.
                                           NoTool-FCStyle →Agent-NoopTool →Agent-
                                                      Full. Each transition adds one component of the    • We identify a capability-overlap pattern be-
                                                     tool-use pipeline: NoTool-FCStyle isolates the    hind the CoT–Tool gap: many apparent tool
                                                     cost of adopting the function-calling prompt for-     gains occur on cases already solvable by na-
                                            mat without tool access; Agent-NoopTool adds the     tive CoT, so redundant tool benefits may fail
                                                     tool-use interaction protocol while replacing tool     to offset protocol-induced failures.
                                                    outputs with a no-op stub, estimating protocol over-
2  Methodology                             head before useful tool execution; and Agent-Full
                                                      restores real tool execution, measuring the gain
2.1  Problem Setting: Semantic Distractor                                            from actual tool logic.
     Stress Test                                           The remaining conditions serve as diagnostic
Most prior work evaluates models on clean bench-   probes around Agent-Full.  Agent-OracleCalc
marks, whereas real-world inputs often contain se-   replaces  tool  outputs  with  the  gold answer
mantically related noise. To better reflect this set-    to bound  computation-related  losses;  Agent-
ting, we build a controllable augmentation pipeline   OracleEvidence provides clean evidence to isolate
that injects semantically relevant context into    distractor-sensitive evidence-selection failures; and
benchmark samples; we call the resulting data Sem-  Agent-Max1Turn restricts the agent to a single
Distractor.                           FC turn to assess whether additional turns help or
  We consider four distractor types (examples in   mainly add protocol overhead. Detailed definitions
Appendix E): Thematic Background (TB), which    of all seven conditions are provided in Appendix C.
adds topic-related but logically unhelpful back-
                                                    2.3  Gap Decomposition Metricsground; Semantic Paraphrase (SP), which para-
phrases evidence while preserving meaning; Par-   Degradation chain and ∆decomposition.  We
allel Entity Distractor (PED), which introduces    define a degradation chain over four conditions that
semantically similar but entity-confounding hard    share the same noisy context but differ in protocol


                                         2

Environment Setup & Observation       Tool-use Tax Decomposition        Diagnosis, Explanation & Validation
   Perturbed           Case                     Factorized Intervention Framework                                Agent-Full errors by first failure point
  Benchmark          Study                                                                                                       Genuine Gap: wrong @ Cot
                                                                                                                                          $                                                                                                            69.7%                                                                                                                                                                                                                                                         :                                                                                                                                         wrong                                                                                    @                                                                                                                                                      FCStyle                                                                                                                                                              30.3%         ∆!"#        Base                                                                               CoT                                                                                                Structure                                                                              Tool Call             Dataset          Noisy                            GSM8K                                           example                                                                                                                                          $                                                                                                                                              57.6% Protocol-                                                                                                                                                                                                                                                          :                                                                                                                                          wrong                                                                                    @                                                                                                                                                 NoopTool                                            Natalia                                                    sold 48                                                                    clips                                                                                                                                                                        ∆%&'        GSM8K                                                                            in April and         CoT                                                                                                                   Induced                                             half                                              as many                                                                   in May.                                                                                                                                          $                                                                                                Tool                                                                                                                        Call                                                                                                             Protocol                                                                                                                                                                                                                                                           :                                                                                                                                          wrong                                                                                    @                                                                                                                                               Agent                                                                                                                                           ∆'()                                                                                                                                                                                 12.1%        HotPotQA                                   Distractor:
     Distractor Types              AlexJune.planned to sell 5 clips in                                         Oracle Feedback                               Protocol-induced errors dominate.
        Thematic       Semantic     Q: Total clips sold?                          Feedback
       Background      Paraphrase                                                         ONLYw/Tools            LargeOverlap
        Parelle              Entity
                           Uncertainty        Distractor                       Hedged          CoT/Tool-Use Gap                 Agent Tool-use Receipt                                         (tool-benefit ∩CoT-solved)

                                                                       Native CoT                                                                                                            90.72                              CoT-Solved                                                                                                         Cases           Acc.    overhead                                                            Δ𝑠𝑡𝑦                            86.76                                          Redundant tool-use                                                                                                                                                                                                                           Accuracy     Native CoT w/o Tools       Agent with Tools                                                                        tax            76.60                             paysunnecessary tax.                                                            CoT (FCStyle)
    Focus on real sales         Using calculator protocol
  à Ignore the       à Attends to                    Δ𝑓𝑟𝑐
       distracting number 5       distracting number 5                                                 Gate Mechanism Mitigation
  à May = 48 ÷ 2 = 24    à Tool interaction                CoT + NoopTool                        48.84                                            Protocol-induced tax/
                à                            ÷                          May                                     =                                48                                    2                                             = 24                                                                                                                                                                       ∆frc                                                                                                                                                                       failure                                                                                                             G-STEP  à Total = 48 + 24 = 72                à                                  Total                                      =                                 48                                             +                                    24                                                                                                                                                                           recoverable                                                                                  à Partially                                                                                                                        Gate
                           77                                                                                                                                                   by                                                                                                                                                               extra                                                                                                                                             FC steps                                                  + 5 =               Δcmp        CoT        Agent
                                                                    Agent
    CoT resolves the noisy         Tool-use introduces                                                                                                FCStyleNoopTool                    Agent-Full              Genuine capability gap                                                                                       Native
      instance                             failure.                                                                                             Continue /   à Not recoverable by gate;
                                                𝒕𝒂𝒙= 𝛥𝑠𝑡𝑦+ 𝛥𝑓𝑟𝑐+ 𝛥𝑐𝑚𝑝                           Commit         Needs stronger model /           performance degradation                                                                                                                              training


Figure 1: Factorized intervention framework for diagnosing the CoT–Tool gap under semantic distractors. The
framework identifies when tool-augmented reasoning underperforms native CoT, decomposes the gap into FC-style
formatting cost, function-calling protocol overhead, and real tool-execution gain, and explains the gap through
capability overlap and recoverability analysis.


complexity:                                  which identifies where it first arises on the degra-
                                                    dation chain. We therefore introduce a three-stage
         ∆sty                 ∆frc               ∆cmp
CoT −−−→FCStyle −−−→NoopTool −−−−→Full   analytical protocol:  (i) a trajectory-level failure
                                                 (1)   taxonomy that identifies the dominant symptom
Here,  Acc(x)  denotes  Accuracy.    ∆sty  ≜    of each failed trajectory, (ii) a sample-level attri-
Acc(FCStyle) −Acc(CoT)  isolates the perfor-   bution scheme that maps each failure to its ear-
mance cost of strict FC-style prompt formatting     liest degradation point on the chain, and (iii) a
in the absence of actual tool access.  ∆frc ≜    capability-overlap analysis that measures whether
Acc(NoopTool) −Acc(FCStyle) measures  the    tool-derived gains are redundant with the model’s
function-calling protocol overhead incurred before    native reasoning ability.
useful tool execution can provide any gain. Finally,
∆cmp ≜Acc(Full) −Acc(NoopTool) captures the   Trajectory-Level Failure Taxonomy.  For each
net impact of executing real tool logic. Together,    incorrect Agent-Full trajectory, we assign a pri-
these components yield a strict additive decompo-   mary failure label under a fixed priority order:
sition of the total performance gap:
                                                                 • Type A (Under-computation): too few suc-
 Acc(Full)−Acc(CoT) = ∆cmp +∆frc +∆sty (2)         cessful tool steps to complete the gold compu-
                                                                 tation.
  We additionally define two auxiliary oracle
probes for later bottleneck localization: ∆oracle ≜                                                                 • Type B (Tool-execution error): at least one
Acc(OracleCalc)−Acc(Full), which upper-bounds                                                             tool call fails or returns invalid output.
computation-related  losses,  and  ∆context  ≜
Acc(OracleEvid) −Acc(Full),  which  isolates        • Type C (Evidence drift): Evidence-F1 < 0.5,
distractor-sensitive evidence-selection losses.             indicating substantial reliance on irrelevant
                                                            context.
2.4  Analytical Protocol for Root-Cause
     Diagnosis
                                                                 • Type D (Integration failure): the final tool
We move from aggregate decomposition to finer-        output is correct, but the final prediction is
grained diagnosis of individual failures through         not.
two complementary views: a trajectory-level view,
which characterizes how a failure manifests in        • Type E (No successful output): no tool call
the execution trajectory, and a sample-level view,        produces a usable result.


                                         3

• Type F (Planning mismatch): the model fol-   also solvable through the model’s native reasoning
    lows a coherent but incorrect computation    path, suggesting substantial overlap between real-
     plan despite adequate evidence and function-   ized tool gains and the model’s internal capability.
     ing tools.                                    This quantity therefore serves as a diagnostic signal
                                                         for whether tool use contributes unique external ca-
  This taxonomy captures the observable symptom
                                                         pability or primarily recovers performance already
of a failed trajectory rather than its root cause.
                                                   achievable without external calls.
Sample-Level Attribution.  While Types A–F
                                                    2.5  Gate-Augmented Inference
characterize the surface symptom of a failed trajec-
tory, they do not by themselves identify the prin-   Building on the analysis from Section 2.4, we hy-
cipal source of degradation. We therefore further    pothesize that for tasks dominated by protocol-
attribute each incorrect Agent-Full case to the ear-   induced failures, especially premature termina-
liest stage at which the sample becomes unsolved    tion or under-computation within the FC loop, a
along the degradation chain in Eq. (1). This yields    lightweight gate may help mitigate these errors.
four mutually exclusive categories:                                         Gate  Design. We  introduce  G-STEP,  a
    • Genuine: the sample is already incorrect un-   lightweight binary gate inserted at the termination
     der CoT;                                      point of the FC loop. When the model attempts
                                                      to produce a final answer with no further tool
    • ∆−sty: the sample first becomes incorrect in    calls, G-STEP  decides whether  to  continue
     FCStyle;                                      tool-conditioned  interaction or commit  to the
                                                    current answer.  The gate is trained to capture
    • ∆−frc: the sample first becomes incorrect in                                                  protocol-induced failures using CoT-fixability as
    NoopTool;
                                                    the primary supervision signal: cases where the
    • ∆−cmp: the sample remains correct up to Noop-  FC agent fails but standard CoT succeeds are
    Tool but becomes incorrect only in Agent-    treated as instances where additional protocol-level
     Full.                                           intervention may still help.  If the gate predicts
                                                     continue, the system injects a continuation prompt
  This attribution scheme complements the A–
                                            and requires one additional tool-conditioned step
F taxonomy by separating failure symptom from
                                                   before re-attempting the answer. We also evaluate
degradation source. The former describes how an
                                                a +CRITIC variant, inspired by CRITIC (Gou
execution trace fails; the latter identifies where the
                                                           et al., 2024), which adds an explicit reflection
failure is introduced in the sequence of controlled
                                                     step after calculator calls before the next tool
interventions.
                                                         action. This is motivated by our earlier finding that
Capability Overlap Analysis.  To quantify the   computation-chain errors dominate on GSM8K.
extent to which tool-derived gains provide capa-   Full details are provided in Appendix I.
bility beyond the model’s native reasoning path,
                                       3  Result & Analysiswe identify tool-benefited samples—cases where
Agent-Full succeeds but the corresponding Noop-   3.1  Experiment Settings
Tool control fails—and measure the fraction of
                                                  This section summarizes the common experimental
such samples that are also solved by CoT. Let
                                                         settings include the models, datasets, tool environ-
Full(x), NoopTool(x), and CoT(x) denote binary
                                                ments, and evaluation metrics. All prompts are
correctness indicators for sample x under the cor-
                                                 provided in Appendix K.
responding settings. We define
                                            Models. We evaluate Qwen3-4B, Qwen3-32B,
  Btool = {x | Full(x) = 1, NoopTool(x) = 0},     and GPT-4.1-mini as tool-enabled LLMs, covering
                                                  open-source models at different scales and a closed-
and compute the overlap ratio as
                                                 source counterpart. All models follow the same
               |{x ∈Btool | CoT(x) = 1}|        CoT, tool-augmented, and intervention protocols
    Overlap =                                         .
                                |Btool|                  under a unified function-calling setup.

 A high overlap ratio indicates that many sam-   Datasets  Using  the method  in  Section  2.1,
ples apparently helped by real tool execution are   we augment GSM8K (Cobbe et al., 2021) and


                                         4

HotpotQA (Yang  et  al., 2018) with GPT-4o-    consistent effects, with only occasional small gains
mini-generated distractors, yielding GSM8K-Sem-   under Agent-Full for Qwen3-4B.
Distractor and HotpotQA-Sem-Distractor.  For      Overall, the CoT–Tool gap persists across mod-
brevity, we refer to these two augmented bench-    els and distractor variants, indicating that tool-
marks as GSM8K and HotpotQA in the rest of   augmented reasoning can become vulnerable when
the paper, unless otherwise specified. Details are   semantic noise interacts with the tool-use proto-
provided in Appendix F.                               col. We therefore turn to controlled interventions
                                              and mechanism-level analysis to explain where this
Tools & Metrics We use task-specific toolsets.                                                   degradation arises.
For GSM8K-Sem-Distractor benchmark, the agent
is equipped only with a calculator. For HotpotQA-   3.3  Identify the CoT-Tool Gap from the
Sem-Distractor benchmark, the agent is equipped         Intervention Framework
with search sentences, read sentences, compare
                                            Based on the Factorized Intervention Framework,
values, and calculator.
                                                Table 2 reports overall Accuracy and Evidence-
  We evaluate performance with Accuracy and
                                        F1 across the seven experimental conditions. We
Evidence-F1.
                                                 analyze the average performance across all noisy
                                                         variants. Detailed results for individual noise con-
3.2  Semantic Distractor Stress Test
                                                        ditions are provided in Appendix L.
We evaluate Qwen3-4B, Qwen3-32B, and GPT-     Three observations emerge from Table 2. First,
4.1-mini on GSM8K-Sem-Distractor under two   NoTool-CoT achieves the best non-oracle ac-
settings: Agent-Full, which solves problems with   curacy across all task–model pairs, confirming
tool use, and CoT, which relies on direct chain-of-    that tool augmentation does not automatically im-
thought reasoning. Implementation details of tool   prove robustness under semantic distractors. Sec-
use are provided in Appendix G.                    ond, the oracle probes suggest that the main bottle-
                                             neck lies in the computation and tool-interaction
 Model           Setting  Base   TB   PED  HU   SP    Overall    chain rather than in evidence quality alone. For
  GPT-4.1-MINI  AF      75.40  76.00  76.60  77.80  77.20    76.60     example, Agent-OracleCalc yields large gains
  GPT-4.1-MINI  CoT     93.20  91.00  89.20  90.40  89.80    90.72
                                                 over Agent-Full on Qwen3-4B, improving accu-
 QWEN3-4B    AF      51.20  54.20  48.00  57.40  49.60    52.08
                                                    racy from 52.08% to 89.20% on GSM8K and from QWEN3-4B    CoT     91.00  86.80  81.40  83.60  84.40    85.44
                                          72.32% to 93.05% on HotPotQA, whereas Agent-
 QWEN3-32B   AF      77.60  76.60  73.80  73.20  77.60    75.76
 QWEN3-32B   CoT     94.00  92.80  89.40  89.80  91.00    91.40     OracleEvid changes performance only marginally
                                                       in comparison. Third, the degradation is strongly
Table 1: Accuracy (%) on GSM8K-Sem-Distractor.   task-dependent: on GSM8K, Agent-Full trails CoT
“AF” denotes Agent-Full. Bold values indicate the best                                           by 14.12–33.36% across models, while on Hot-
performance.
                                      PotQA the gap is only 0.62–2.47%. This contrast
                                                    suggests that tool-use tax is amplified in sequential
  Table 1 shows a consistent pattern across all                                                computation tasks, where errors introduced by the
three models:  CoT substantially outperforms                                                       function-calling protocol can propagate through the
Agent-Full on GSM8K-Sem-Distractor. The over-                                                  reasoning chain, but is milder in retrieval-oriented
all gaps are 14.12, 33.36, and 15.64% for GPT-4.1-                             QA settings where partial evidence or parametric
mini, Qwen3-4B, and Qwen3-32B, respectively.                                              knowledge may help compensate for imperfect tool
This result indicates that, in the presence of seman-                                                         interaction.
tic distractors, adding tool use and multi-step agent
protocols does not automatically improve robust-   Decomposing the Performance Gap.  Table 3
ness and can instead lead to substantial degrada-    factorizes the aggregate CoT-to-Tool gap into its
tion.                                                 three components: ∆cmp, ∆frc, and ∆sty.
  Among distractor variants, PED is consistently      This decomposition sharpens the counterintu-
one of the most challenging settings, particularly    itive finding: real tool execution can provide mea-
for CoT and the Qwen models. This indicates that    surable gains, yet these gains may still be insuf-
entity-level semantic confusion is especially dis-    ficient to offset the cost of entering the tool-use
ruptive to evidence selection and downstream rea-   protocol. On GSM8K, ∆cmp is consistently posi-
soning. Other distractor types show milder and less     tive, but ∆frc is the dominant negative component;


                                         5

Condition                  GSM8K                               HotPotQA

                 Qwen3-4B    Qwen3-32B    GPT-4.1-mini    Qwen3-4B    Qwen3-32B    GPT-4.1-mini

NoTool-CoT            85.44          91.40            90.72           74.79          84.15            87.06
NoTool-FCStyle         84.84          78.56            86.76           70.92          83.98            85.66
Agent-NoopTool        30.64          50.92            48.84           56.69          82.07            84.87
Agent-Full              52.08          75.76            76.60           72.32          83.03            86.44
Agent-Max1Turn        47.72          75.88            72.88           69.97          83.19            86.22
Agent-OracleCalc       89.20          93.40            82.24           93.05          90.70            91.71
Agent-OracleEvid       52.48          79.72            76.00           74.40          84.82            86.67

Table 2: Overall accuracy (%) across seven experimental conditions. GSM8K uses exact-match accuracy. HotPotQA-
32B and HotPotQA-GPT-4.1-mini use contains-match to accommodate free-form answers, while HotPotQA-4B
uses exact match.


 Task       Model    ∆cmp      ∆frc      ∆sty      Net     Task      Model  Nw  Gen. ∆−sty ∆−frc ∆−cmp  Proto.
          4B     +21.44  −54.20   −0.60  −33.36   GSM8K   4B     1198  20.6  11.4  58.7    9.3    79.4
GSM8K   32B    +24.84  −27.64  −12.84  −15.64   GSM8K   32B     606  24.1  24.9  45.5    5.4    75.8
         GPT    +27.76  −37.92   −3.96  −14.12   GSM8K   GPT    585  30.3  12.1  44.6   13.0    69.7

          4B     +15.63  −14.23   −3.87   −2.47    HotPotQA  4B      494  77.3   8.5   7.1    7.1    22.7
 HotPotQA  32B     +0.96   −1.91   −0.17   −1.12    HotPotQA  32B     303  73.3   7.6  13.2    5.9    26.7
         GPT     +1.57   −0.78   −1.40   −0.62    HotPotQA GPT    242  62.8  28.5   2.9    5.8    37.2

Table 3: ∆decomposition of the CoT-to-Tool gap (%).   Table 4: Sample-level ∆attribution (%). “Proto.” =
Bold marks the largest-magnitude negative component  ∆−sty +∆−frc +∆−cmp. Nw denotes the number of incorrect
in each row.                                           samples, and Gen. denotes the proportion of genuinely
                                                           incorrect samples. Bold marks the largest attributable
                                                      source in each row.
for Qwen3-4B, for example, the protocol penalty
is more than twice the tool-execution gain. This
indicates that the problem is not the absence of    rect Agent-Full prediction is attributed to its ear-
useful computation, but that protocol overhead can     liest failure point along Eq. (1). Table 4 summa-
corrupt more performance than tool execution re-    rizes the sample-level attribution, and Table 5 cross-
covers. HotPotQA presents a milder regime, where    tabulates these sources with the A–F failure taxon-
protocol costs are smaller and more easily offset   omy on GSM8K.
by tool gains, leading to a much smaller CoT–Tool      Table 4 reveals a robust task dichotomy. On
gap. Together, these results suggest that tool aug-  GSM8K, a large majority of Agent-Full errors are
mentation is not automatically beneficial: its value    protocol-induced: 79.4% for Qwen3-4B, 75.8%
depends on whether realized tool gains are suffi-    for Qwen3-32B, and 69.7% for GPT-4.1-mini. In
ciently complementary to overcome the surround-    all three cases, ∆−frc is the dominant source, ac-
ing protocol cost.                                 counting for 58.7%, 45.5%, and 44.6% of all fail-
                                                        ures, respectively. By contrast, HotPotQA is dom-
Bottleneck Localization.  The oracle conditions    inated by genuine failures under which both CoT
show that computation quality—rather than evi-   and the agent fail, comprising 77.3% of errors for
dence noise—is the primary limiting factor. Ora-   Qwen3-4B, 73.3% for Qwen3-32B, and 62.8% for
cle computation yields large gains, whereas oracle   GPT-4.1-mini. Protocol-induced errors therefore
evidence brings only modest improvements (Ap-   remain comparatively limited on HotPotQA, al-
pendix A). This motivates a closer examination of   though GPT-4.1-mini exhibits a somewhat larger
how errors arise within individual execution traces,    residual protocol component (37.2%), driven pri-
which we address next.                            marily by ∆−sty rather than ∆−frc.
                                                  Table 5 further shows that the A–F taxonomy
3.4  Decompose the CoT-Tool Gap
                                                   captures failure symptoms rather than their under-
We next apply the diagnosis protocol from Sec-   lying sources. On GSM8K, ∆−frc is the dominant
tion 2.4 to distinguish genuine capability gaps    attribution for Types A, C, and F across all mod-
from protocol-induced degradation. Each incor-    els, suggesting that apparent under-computation,


                                         6

Model Type       N  Gen. ∆−sty ∆−frc ∆−cmp       Task         Model    TB    CoT      Ovlp. (%)
      A Under-comp. 700  20.0  10.7  61.4    7.9                 4B        673      603           89.6
       C Evid. drift    281  23.5  13.2  54.1    9.3    GSM8K      32B       669      629           94.0  4B
      D Integr. fail     11   0.0   9.1  36.4  54.5                GPT       780      744           95.4
        F Plan. mis.    195  19.5  11.8  56.4  12.3                 4B        332      292           88.0
      A Under-comp. 423  22.9  23.9  47.8    5.4      HotPotQA     32B        58       39           67.2
       C Evid. drift     94  31.9  23.4  40.4    4.3                GPT        57       32           56.1
  32B
      D Integr. fail     17   5.9  35.3  52.9    5.9
        F Plan. mis.     54  25.9  35.2  37.0    1.9      Table 6: Capability overlap. TB denotes tool-benefited
      A Under-comp. 297  35.7  11.1  42.4  10.8      samples (Agent-Full  correct and Agent-NoopTool
       C Evid. drift    120  37.5  10.8  39.2  12.5      wrong), CoT the subset of TB also solved by CoT, and  GPT
      D Integr. fail     93   1.1   8.6  64.5  25.8                                                      Ovlp. the corresponding percentage. GPT denotes GPT-
        F Plan. mis.     63  27.0  25.4  42.9    4.8
                                                          4.1-mini.

Table 5: A–F × ∆cross-tabulation for GSM8K (row %).
Bold marks the dominant attributable source in each row.
                                                         tion are already solvable by the model’s native CoT
Rare types B and E are omitted here for compactness.
                                                   reasoning. Only 10.4%, 6.0%, and 4.6% of the
                                                     tool-benefited GSM8K cases are genuinely tool-
evidence drift, and planning mismatch often arise    essential.Thus, ∆cmp can be positive yet insuffi-
after entering the function-calling protocol rather    cient to offset the tool-use tax, because much of the
than from intrinsic reasoning deficits. This pattern    realized tool gain overlaps with native CoT while
is not limited to the Qwen models: for GPT-4.1-  ∆−frc corrupts otherwise solvable examples.
mini, ∆−frc is also the largest contributor to Types     HotPotQA exhibits a different pattern. Overlap
A, C, and F, and even accounts for most Type D   remains high for Qwen3-4B (88.0%), but drops
errors. These results highlight why trajectory-level    to 67.2% for Qwen3-32B and 56.1% for GPT-4.1-
symptoms alone can be misleading: failures that    mini. This indicates that capability overlap alone
appear to be planning or integration errors may in-   does not determine degradation severity: GPT-4.1-
stead be downstream effects of protocol-induced   mini still shows only a small Full–CoT gap on Hot-
degradation.                              PotQA despite substantially lower overlap, imply-
  This distinction is consistent with the oracle anal-   ing that the net effect also depends on the absolute
ysis (Appendix B): OracleCalc largely removes    protocol cost imposed by the task.
Types A and F, OracleEvid suppresses Type C, and    We summarize this pattern as the Capability
Type D remains the main residual bottleneck once   Overlap Principle: when tool-provided capabil-
computation errors are corrected.  Overall, A–F     ity substantially overlaps with the model’s native
categories describe how a trajectory fails, whereas   reasoning ability, much of the realized tool gain
the ∆attribution identifies where that failure is   becomes redundant with native CoT, while the tool-
introduced along the degradation chain.             use protocol still incurs additional overhead. Un-
  The attribution analysis localizes where the    der such conditions, a positive ∆cmp may still fail
losses arise, but it does not yet explain why the    to offset the overall tool-use tax.
positive computation gain ∆cmp still fails to out-
                                                    3.5  Cot-Tool Gap Mitigationweigh the protocol overhead in aggregate.
                                                Table 7 reports the gate’s performance across all
The Capability Overlap Principle.  This leads                                                   four configurations. The gate is trained and eval-
to a natural question: if real tool execution does                                                 uated on disjoint question splits, and all reported
provide useful computation, why does it still fail                                                    scores are measured on held-out test sets.1
to offset the protocol tax? We answer this through
capability overlap: the fraction of tool-benefited    Analysis.  The gate’s effectiveness closely fol-
samples that are also solved by the model’s native   lows the task dichotomy revealed by the ∆attribu-
CoT path.                                             tion analysis in Table 4: it yields substantial gains
  As shown in Table 6, capability overlap is ex-   on GSM8K, where protocol-induced errors domi-
tremely high on GSM8K across all three models:    nate, but only marginal or no benefit on HotPotQA,
89.6% for Qwen3-4B, 94.0% for Qwen3-32B, and
                                                                   1Baselines in Table 7 are re-evaluated on the gate test split
95.4% for GPT-4.1-mini.  In other words, most                                                      and may differ slightly from the full-dataset values reported
samples that appear to benefit from real tool execu-    in Table 2.


                                         7

Config        Full   Gate  +CRITIC  CoT   Gap    Cls.  proved tool learning through high-quality synthetic
GSM-4B    50.64  69.12      74.88  82.64  -32.00  75.75  data (Liu et al., 2025), structure-aware tool repre-
GSM-32B  73.28  77.04      77.44  91.20  -17.92  23.21  sentation (Su et al., 2025), and token-level opti-
GSM-GPT  75.92  75.52      76.56  89.04  -13.12   4.88  mization with fine-grained error scoring (Huang
Hot-4B     73.18  74.97      74.53  76.87   -3.69  48.51  et al., 2025). In parallel, recent benchmarks have
Hot-32B    83.02  82.90      82.10  84.15   -1.13  —  shifted toward realistic and process-oriented evalu-
Hot-GPT   86.37  85.81      87.04  87.15   -0.78  85.72
                                                        ation, covering fine-grained tool-use abilities (Ye
                                                           et al., 2024) and mobile-assistant function calling
Table 7:  Gate effectiveness on held-out test splits.
                                               under multi-turn, imperfect, and shifting user in-Gap = Full – CoT (pp).  Cls. reports the fraction of
the Full-to-CoT gap recovered by the better of Gate    structions (Wang et al., 2025).
and +CRITIC. HotPotQA-32B and HotPotQA-GPT use
contains-match; all others use exact match.              4.2  Fine-Grained Diagnosis of Reasoning and
                                               Agent Failures

                                               Recent work increasingly argues that final-answerwhere most errors reflect genuine capability gaps.
                                                 accuracy alone is insufficient for assessing reason-The strongest recovery appears on GSM8K-4B,
                                                  ing quality. FineLogic (Zhou et al., 2025), Eval-where G-STEP improves accuracy from 50.64%
                                                   uating Step-by-step Reasoning Traces (Lee andto 69.12%, and the +CRITIC variant further raises it
                                              Hockenmaier, 2025), Kim et al. (2025) all empha-to 74.88%, closing 75.75% of the Full-to-CoT gap.
                                                         size that intermediate reasoning traces reveal errorsGains are smaller on GSM8K-32B and HotPotQA-
                                               missed by outcome-only evaluation.4B, and disappear on HotPotQA-32B, where errors
are largely genuine rather than protocol-induced.   A similar shift has emerged in LLM agent eval-
This pattern suggests that gate-based intervention    uation. AgentDiagnose (Ou et al., 2025), Zhang
is most useful when failures are dominated by ∆−frc-    et al. (2025), AgentFail (Ma et al., 2026), and Paper-
type protocol errors, whereas settings dominated   Arena (Wang et al., 2026a) move beyond end-task
by genuine capability gaps require stronger model    success toward trajectory-level diagnosis, failure
improvements rather than additional inference-time    attribution, and root-cause analysis, a trend further
control. GPT-4.1-mini follows the same qualitative   summarized by recent survey work on LLM agent
trend: +CRITIC slightly improves over Agent-Full    trajectory analysis (Wang et al., 2026b).
on both tasks, but the gain is modest on GSM8K
                                       5  Conclusionand largely reflects closure of an already small
residual gap on HotPotQA. Detailed analysis is
                                                     In this work, we studied the CoT–Tool gap under se-
provided in Appendix I.7.
                                                 mantic distractors and showed that tool-augmented
Robustness Across Distractor Types.  The effec-   reasoning does not necessarily outperform native
tiveness of gate-based control is broadly consistent   CoT. We analyzed this gap through a Factorized
across the four semantic distractor categories. In    Intervention Framework, which decomposes tool
particular, the gains are more pronounced in fragile    gains and protocol costs into interpretable com-
GSM8K settings and remain limited on HotPotQA,   ponents, and further introduced the Capability
which is consistent with the protocol-vs-capability   Overlap Principle: many apparent tool gains arise
dichotomy in Table 4. Detailed variant-wise robust-   on samples already solvable by native CoT, while
ness results are provided in Appendix J.              the tool-calling protocol incurs broad additional
                                                 overhead. We also showed that this analysis is ac-
4  Related Work                                  tionable: a lightweight G-STEP intervention can
                                                           partially mitigate protocol-induced failures, but its
4.1  Tool-augmented reasoning and function                                                      limited effect suggests that inference-time patching
      calling                                                 alone is insufficient for more substantial improve-
Recent research has explored tool augmentation   ment. Overall, our findings suggest that tool aug-
and function calling as key directions for extend-   mentation is not universally beneficial: its value
ing LLMs beyond language-only inference. Tool-   depends on whether tools provide genuinely com-
LLM (Qin et  al., 2024) introduced large-scale   plementary capability rather than redundant gains
tool-use data construction, training, and evalua-   with added protocol burden.
tion over real-world APIs, while later studies im-


                                         8

References                                      8 others. 2025. Toolace: Winning the points of llm
                                                           function calling. Preprint, arXiv:2409.00920.
Chen Chen, Xinlong Hao, Weiwen Liu, Xu Huang,
  Xingshan Zeng, Shuai Yu, Dexun Li, Yuefeng Huang,   Xuyan Ma,  Xiaofei  Xie,  Yawen Wang,  Junjie
  Xiangcheng Liu, Wang Xinzhi, and Wu Liu. 2025.     Wang, Boyu Wu, Mingyang Li, and Qing Wang.
  ACEBench: A comprehensive evaluation of LLM      2026.  Demystifying the lifecycle of failures in
   tool usage. In Findings of the Association for Com-      platform-orchestrated agentic workflows. Preprint,
   putational Linguistics: EMNLP 2025, Suzhou, China.      arXiv:2509.23735.
  Association for Computational Linguistics.
                                                  Tianyue Ou, Wanyao Guo, Apurva Gandhi, Graham
Zhipeng Chen, Kun Zhou, Beichen Zhang, Zheng      Neubig, and Xiang Yue. 2025. AgentDiagnose: An
  Gong, Wayne Xin Zhao, and Ji-Rong Wen. 2023.     open toolkit for diagnosing LLM agent trajectories.
   Chatcot: Tool-augmented chain-of-thought reason-      In Proceedings of the 2025 Conference on Empiri-
   ing on chat-based large language models. Preprint,      cal Methods in Natural Language Processing: Sys-
  arXiv:2305.14323.                                  tem Demonstrations, Suzhou, China. Association for
                                                      Computational Linguistics.
Jiali Cheng, Rui Pan, and Hadi Amiri. 2026. Investi-
   gating tool-memory conflicts in tool-augmented llms.    Shishir G  Patil, Huanzhi Mao, Fanjia Yan, Char-
   Preprint, arXiv:2601.09760.                                    lie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, and
                                                     Joseph E. Gonzalez. 2025. The berkeley function
Karl Cobbe, Vineet Kosaraju, Mohammad Bavarian,       calling leaderboard (BFCL): From tool use to agentic
  Mark Chen, Heewoo Jun, Lukasz Kaiser, Matthias       evaluation of large language models. In Forty-second
   Plappert, Jerry Tworek, Jacob Hilton, Reiichiro       International Conference on Machine Learning.
  Nakano, Christopher Hesse, and John Schulman.
  2021. Training verifiers to solve math word prob-   Thinh Pham, Nguyen Nguyen,  Pratibha  Zunjare,
   lems. Preprint, arXiv:2110.14168.                   Weiyuan  Chen,  Yu-Min  Tseng,  and Tu  Vu.
                                                      2026.   Sealqa:  Raising the bar for reasoning
Zhibin Gou, Zhihong Shao, Yeyun Gong, Yelong       in search-augmented language models.  Preprint,
  Shen, Yujiu Yang, Nan Duan, and Weizhu Chen.      arXiv:2506.01062.
  2024.   Critic:  Large language models can self-
   correct with tool-interactive critiquing.  Preprint,    Yujia Qin, Shihao Liang, Yining Ye, Kunlun Zhu, Lan
  arXiv:2305.11738.                                   Yan, Yaxi Lu, Yankai Lin, Xin Cong, Xiangru Tang,
                                                                 Bill Qian, Sihan Zhao, Lauren Hong, Runchu Tian,
Chengrui Huang, Shen Gao, Zhengliang Shi, Dong-     Ruobing Xie, Jie Zhou, Mark Gerstein, dahai  li,
  sheng Wang, and Shuo Shang. 2025. TTPA: Token-     Zhiyuan Liu, and Maosong Sun. 2024. ToolLLM:
   level tool-use preference alignment training frame-       Facilitating large language models to master 16000+
  work with fine-grained evaluation. In Findings of the       real-world APIs. In The Twelfth International Con-
  Association for Computational Linguistics: EMNLP       ference on Learning Representations.
  2025, Suzhou, China. Association for Computational
   Linguistics.                                    Yunyue Su, Zhang Jinshuai, Bowen Fang, Wen Ye, Jing-
                                                  hao Zhang, Bowen Song, Weiqiang Wang, Qiang
Hyeon Hwang, Yewon Cho, Chanwoong Yoon, Yein       Liu, and Liang Wang. 2025. Toolscaler: Scalable
   Park, Minju Song, Kyungjae Lee, Gangwoo Kim,      generative tool calling via structure-aware semantic
  and Jaewoo Kang. 2025. Assessing llm reasoning       tokenization. In Findings of the Association for Com-
   steps via principal knowledge grounding. Preprint,       putational Linguistics: EMNLP 2025, Suzhou, China.
  arXiv:2511.00879.                                     Association for Computational Linguistics.

Wonjoong Kim, Sangwu Park, Yeonjun In, Sein Kim,   Guiyao Tie, Zenghui Yuan, Zeli Zhao, Chaoran Hu,
  Dongha Lee, and Chanyoung Park. 2025. Beyond the      Tianhe Gu, Ruihang Zhang, Sizhe Zhang, Junran Wu,
   final answer: Evaluating the reasoning trajectories of      Xiaoyue Tu, Ming Jin, Qingsong Wen, Lixing Chen,
  tool-augmented agents. Preprint, arXiv:2510.02837.     Pan Zhou, and Lichao Sun. 2025. Can llms correct
                                                       themselves? a benchmark of self-correction in llms.
Jinu Lee and Julia Hockenmaier. 2025.  Evaluating       Preprint, arXiv:2510.16062.
   step-by-step reasoning traces: A survey. Preprint,
  arXiv:2502.12289.                            Daoyu Wang, Mingyue Cheng, Shuo Yu, Zirui Liu,
                                              Ze Guo, Xin Li, and Qi Liu. 2026a.  Paperarena:
Seongyun Lee, Yongrae Jo, Minju Seo, Moontae Lee,    An evaluation benchmark for tool-augmented agen-
  and Minjoon Seo. 2026.  Lost in the noise: How        tic reasoning on  scientific  literature.   Preprint,
  reasoning models fail with contextual distractors.      arXiv:2510.10909.
   Preprint, arXiv:2601.07226.
                                                  Jun Wang, Jiamu Zhou, Muning Wen, Xiaoyun Mo,
Weiwen Liu, Xu Huang, Xingshan Zeng, Xinlong Hao,     Haoyu Zhang, Qiqiang Lin, Cheng Jin, Xihuai Wang,
  Shuai Yu, Dexun Li, Shuai Wang, Weinan Gan,     Weinan Zhang, Qiuying Peng, and Jun Wang. 2025.
  Zhengying Liu, Yuanqing Yu, Zezhong Wang, Yux-     Hammerbench: Fine-grained function-calling eval-
   ian Wang, Wu Ning, Yutai Hou, Bin Wang, Chuhan       uation in real mobile device scenarios.  Preprint,
  Wu, Xinzhi Wang, Yong Liu, Yasheng Wang, and      arXiv:2412.16516.


                                         9

Junjie Wang, Yawen Wang, Mengzhuo Chen, Xiaofei  A  Bottleneck Localization: Oracle
  Xie, Chunyang Chen, Fangwen Mu, Zhe Liu, and      Bounds and Multi-Turn Utility.
  Qing Wang. 2026b. A survey for llm agent trajectory
   analysis: From failure attribution to enhancement.    The oracle conditions explicitly identify where the
                                                remaining performance potential resides (Table 8).
Ruipeng Wang, Yuxin Chen, Yukai Wang, Chang
  Wu, Junfeng Fang, Xiaodong Cai, Qi Gu, Hui Su,
                                                                Task     Model   ∆oracle   ∆context   ∆turn  An Zhang, Xiang Wang, Xunliang Cai, and Tat-Seng
  Chua. 2026c. Agentnoisebench: Benchmarking ro-                 4B      +37.1    +0.4  +4.4
                                            GSM8K
   bustness of tool-using llm agents under noisy condi-                 32B    +17.6    +4.0  −0.1
   tion. Preprint, arXiv:2602.11348.                               4B      +20.7    +2.1  +2.4                                                               HotPot
                                                              32B      +7.7    +1.8  −0.2
Cailin Winston and René Just. 2025. A taxonomy of
   failures in tool-augmented llms. In 2025 IEEE/ACM    Table 8: Oracle upper bounds and multi-turn value (%).
   International Conference on Automation of Software
   Test (AST), pages 125–135.                         For GSM8K–4B,  the  potential  oracle gain
                                                           (∆oracle = +37.1%) is much larger than the contextZhen Xiong, Yujun Cai, Zhecheng Li, and Yiwei
                                                  gain (∆context = +0.4%), indicating that the main  Wang. 2025.  Mapping the minds of llms: A
  graph-based analysis of reasoning llm.  Preprint,    bottleneck lies in the computation chain rather than
  arXiv:2505.13890.                                   in evidence quality. For the 32B model, ∆oracle
                                               remains substantial (+17.6%), while ∆context in-
Minglai Yang, Ethan Huang, Liang Zhang, Mihai Sur-
                                                   creases to +4.0%, suggesting that evidence noise
  deanu, William Wang, and Liangming Pan. 2025.
  How is llm reasoning distracted by irrelevant context?   becomes more visible but still remains a secondary
  an analysis using a controlled benchmark. Preprint,   source of loss.
  arXiv:2505.18761.                        On HotPotQA, ∆oracle is also non-negligible
                                            (+20.7% for 4B and +7.7% for 32B), showing that
Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Ben-
                                                even in a retrieval-centric setting, tool-mediated an-   gio, William W. Cohen, Ruslan Salakhutdinov, and
   Christopher D. Manning. 2018. Hotpotqa: A dataset   swer production remains an important bottleneck.
   for diverse, explainable multi-hop question answer-   Across configurations, ∆oracle is consistently larger
   ing. Preprint, arXiv:1809.09600.                   than ∆context, suggesting that improving tool exe-
                                                    cution and computation quality is likely more ben-
Junjie Ye, Guanyu Li, Songyang Gao, Caishuang Huang,
                                                              eficial than only denoising evidence.  Yilong Wu, Sixian Li, Xiaoran Fan, Shihan Dou, Tao
   Ji, Qi Zhang, Tao Gui, and Xuanjing Huang. 2024.      Finally, multi-turn interaction exhibits a scale-
  Tooleyes: Fine-grained evaluation for tool learning   dependent pattern: the 4B model benefits from
   capabilities of large language models in real-world                                                     additional interaction turns (+4.4% on GSM8K
   scenarios. Preprint, arXiv:2401.00741.
                                              and +2.4% on HotPotQA), whereas the 32B model
Kaituo Zhang, Mingzhi Hu, Hoang Anh Duy Le, Far-   gains little (∆turn ≈0 on both tasks). This suggests
   iha Kabir Torsha, Zhimeng Jiang, Minh Khai Bui,    that additional turns are useful mainly for weaker
  Chia-Yuan Chang, Yu-Neng Chuang, Zhen Xiong,   models, while for stronger models they may intro-
  Ying Lin, Guanchu Wang, and Na Zou. 2026. The                                             duce protocol overhead without substantial infor-
  llm data auditor: A metric-oriented survey on qual-
                                               mation gain.   ity and trustworthiness in evaluating synthetic data.
   Preprint, arXiv:2601.17717.
                              B  A–F Distribution and Oracle
Shaokun Zhang, Ming Yin, Jieyu Zhang, Jiale Liu,       Validation.
  Zhiguang Han, Jingyang Zhang, Beibin Li, Chi
  Wang, Huazheng Wang, Yiran Chen, and Qingyun   Table 9 reports the A–F distribution under Agent-
  Wu. 2025. Which agent causes task failures and    Full and the two oracle conditions for GSM8K.
  when? on automated failure attribution of LLM multi-                                            Under Agent-Full, Type A is the dominant fail-
   agent systems. In Forty-second International Confer-
                                                    ure mode (58–70%), followed by Type C (16–24%)  ence on Machine Learning.
                                            and Type F (9–16%). A surface reading would
Yujun Zhou, Jiayi Ye, Zipeng Ling, Yufei Han, Yue    attribute these errors to insufficient computation
  Huang, Haomin Zhuang, Zhenwen Liang, Kehan   and motivate larger reasoning budgets. The oracle
  Guo, Taicheng Guo, Xiangqi Wang, and Xiangliang
                                                   conditions show a different picture. OracleCalc  Zhang. 2025. Dissecting logical reasoning in llms:
 A fine-grained evaluation and supervision study.   eliminates Types A and F while leaving Type C
   Preprint, arXiv:2506.04810.                            intact; OracleEvid eliminates Type C while leav-


                                         10

Agent-Full  OracleCalc  OracleEvid          Algorithm 1: Type-Guided Noisy Data
      Type  4B  32B  4B  32B  4B   32B          Augmentation
    A     58.4  69.8    0    0  77.8   78.3           Input: Base datasets Dgsm8k and Dhotpotqa;
     C     23.5  15.5  34.1  23.0    0     0                      distractor sentence number k;
    D      0.9   2.8  65.6  73.9   2.4     7.1
      F     16.3   8.9    0    0  18.9   11.6                     insertion positions P; distractor type
                                                                     set T ; LLM generator
Table 9: A–F failure distribution (%) under Agent-Full      M = gpt-4o-mini
and two oracle conditions on GSM8K.                 Output: Augmented noisy dataset Daug
                                                 Daug ←∅;
                                                  foreach base sample x ∈Dgsm8k ∪Dhotpotqa
ing Types A and F intact. Meanwhile, Type D
                                            do
rises sharply under OracleCalc (66–74%), indicat-                                                   Determine the topic tx and keyword set
ing that once computation is made reliable, the                                      Kx of x;
remaining bottleneck is integration: the agent fails                                                                    Initialize distractor set ∆x ←∅;
to correctly consume and report tool outputs. This                                                          for i ←1 to k do
dissociation suggests that the A–F categories cap-                                                               Select distractor type τi ∈T ;
ture structurally distinct failure mechanisms.                                                         Generate distractor di using M
                                                             conditioned on (tx, Kx, τi);
C  Detailed Condition Definitions
                                        ∆x ←∆x ∪{di};
The seven experimental conditions differ in the           Insert ∆x into x according to positions
specific component of the tool-use pipeline that is       P to obtain ˜x;
retained or intervened on.                              Daug ←Daug ∪{˜x};
  In Agent-OracleCalc, the tool is still invoked,     return Daug;
but directly returns the ground-truth answer, elim-
inating errors caused by malformed expressions
or faulty tool use; the agent must still reason over
                                                   formative: on GSM8K, tools provide substantial
the returned result and decide whether to output
                                                  but largely redundant computational gains (+21
it. Agent-OracleEvidence provides an unperturbed,
                                                      to +25%) given the models’ intrinsic mathemat-
noise-free context to isolate the impact of distrac-
                                                           ical ability; on HotPotQA, tools offer smaller
tors. Agent-Max1Turn does not impose a hard limit
                                                  but more genuine information-acquisition utility,
of one tool call; instead, it restricts the agent to a
                                            which helps explain the divergent net outcomes.
single protocol turn while still allowing multiple
tool calls within that turn.
                              E  Sem-Distractor Example  And we provide the example in Figure 2.

                                                   In this section, we provide the examples of Sem-
D  Secondary Patterns in the
                                                      Distractor in Table 10.
    Decomposition Analysis

Two secondary patterns further clarify these dy-  F  The Details of Semantic Distractors
namics. First, the styling penalty is negligible for       Dataset
the 4B model on GSM8K (−0.60%) but moderate
on HotPotQA (−3.87%), and becomes substantial    F.1  The workflow of generating noisy dataset
for the 32B model on GSM8K (−12.84%). This
                                           To demonstrate the workflow more clearly, we give
highlights a task-dependent interaction with model
                                                     the pseudo-code in Algorithm 1.
scale: on GSM8K, the 32B model’s stronger rea-
soning chain is more vulnerable to FC formatting
                                                    F.2  The Examples of Noisy Dataset
disruption (−12.84% vs. −0.60% for 4B), whereas
on HotPotQA, where answers are shorter factoid    In this section, we present a set of examples from
spans, both models show minimal style sensitiv-   the generated noisy dataset, as illustrated in Fig-
ity (≤3.87%), with the 32B model being nearly    ure 3. In our work, the real dataset contains 22
unaffected (−0.17%).                                  distractor sentences. Therefore, the noise distribu-
  Second, the contrast in ∆cmp across tasks is in-    tion is independent of the position.


                                         11

Figure 2: Illustrative example of the seven intervention conditions. All conditions share the same underlying Natalia
clips question and gold answer, but differ in the component being intervened on: prompt style, tool-use protocol,
tool output, evidence context, or interaction budget. The first four conditions form the primary decomposition chain
from NoTool-CoT to Agent-Full, while Agent-OracleCalc, Agent-OracleEvidence, and Agent-Max1Turn serve as
diagnostic probes for computation-related loss, distractor-sensitive evidence selection, and interaction-turn effects,
respectively.


G  Tool-calling Agent Implementation    H Why high overlap leads to smaller
    Details                                    degradation on HotPotQA

For all evaluated models, including GPT-4.1-mini
and the Qwen series, we adopt the same function-
calling(tool-calling) pipeline. GPT-4.1-mini is ac-
cessed through the OpenAI API, while Qwen mod-
els are served through vLLM. In both cases, the
overall workflow remains the same:              HotPotQA also exhibits substantial capability over-
                                                           lap. For Qwen3-4B, 88.0% of tool-benefited cases
  1. Model layer: The model decides whether to    are also solved by CoT, indicating that retrieval
     call a function and generates the correspond-   often returns information already recoverable from
     ing call arguments.                             the model’s parametric knowledge. However, de-
                                                          spite this overlap, the net degradation on HotPotQA
  2. Service layer: The OpenAI API or vLLM
                                               remains much smaller than on GSM8K (Table 3).
    chat.completions  interface converts the
                                      One likely reason is task structure. GSM8K re-
    model output into structured tool_calls.
                                                    quires multi-step sequential computation, where
  3. Execution layer: Python code executes the    disrupting a single intermediate step can invalidate
                                                    the entire reasoning chain. HotPotQA, by con-     actual function (e.g., a local calculator), and
                                                                 trast, relies more on factoid retrieval and evidence     the returned result is fed back to the model for
                                                   aggregation, allowing the model to recover from     subsequent reasoning.
                                                   imperfect tool interaction through partial evidence
  This implementation therefore follows a unified    or parametric knowledge. Thus, overlap alone does
and standard function-calling setup across different    not determine degradation severity; it interacts with
model families.                                      the task’s tolerance to protocol noise.


                                         12

Variant Type (Abbr.)   Perturbation Mechanism        Example from GSM8K

 Base                The original, unmodified evidence    “Natalia sold clips to 48 of her friends in April, and then she
                         sentence extracted directly from the   sold half as many clips in May.”
                             dataset, serving as the ground truth.
 Thematic                Injects domain-relevant background   “Clips are commonly sold in bulk during seasonal events.”
 Background (TB)      knowledge using keywords from
                           the question, providing contextually
                            related but logically useless
                          information.
 Semantic Paraphrase   Restates the original evidence to     “In April, Natalia’s clip sales reached 48 units.”
 (SP)                   maintain semantic equivalence
                        while altering the syntactic
                            structure and vocabulary.
 Parallel Entity         Introduces an alternative entity      “Marcus sold clips to a different group of customers last
 Distractor (PED)       (person or scenario) performing a    summer.” / “Sarah sold clips during a separate event.”
                           similar action to serve as a hard
                          negative distractor.
 Hedged Uncertainty   Wraps the evidence in epistemic      “Natalia reportedly sold clips to a number of friends in
 (HU)                  markers (e.g., reportedly, some say)   April.” / “Some say the May sales might be about half.”
                            to simulate an unreliable or
                           unverified information source.

            Table 10: Summary of semantic noise variants used in our data augmentation pipeline.


I  G-STEP Design and Per-Configuration   178 train / 179 test), and performance metrics are
   Analysis                                       reported strictly on the held-out test split.

I.1  Stage 1: Data Collection                        I.2  Stage 2: Label Construction and Feature
                                                  Engineering
The initial stage aims to obtain the raw performance
data necessary to construct training labels. For each    I.2.1  Label Construction
question (including multiple noise variants), the   For each sample, a binary label (continue or com-
target Large Language Model (LLM) is evaluated    mit) is assigned. This label indicates whether the
under two independent conditions:                model should have continued utilizing tools after its
                                                                initial tool call, based on hindsight knowledge de-
   • Tool-Augmented Baseline (Dbaseline): The    rived from the gold answer and CoT performance.
    model operates under the full function-calling   The priority rules for label assignment are detailed
    (FC) protocol.  For controlled intervention,    in Table 11.
     the interaction is initialized with a required
                                                         I.2.2  Feature Engineering
     tool-use step, after which the model proceeds
                                         The intermediate state of the model after its first    under a predefined maximum number of tool
                                                      tool call  is abstracted into a 120-dimensional,     interactions. The model interacts with the
                                                      inference-safe numeric vector. The feature set com-    environment to produce a final prediction.
                                                        prises two main categories:
   • Chain-of-Thought Baseline (DCoT): The                                                                 • Numeric Features (24 dimensions): Cap-
     identical model receives the same question
                                                             tures execution progress (e.g., budget remain-
     context but without access to any external
                                                                 ing), output stability, consistency between pre-
     tools. The model relies purely on internal
                                                             dictions and reasoning, reasoning signals (e.g.,
   CoT reasoning to produce a final prediction.                                                         uncertainty indicators), evidence proxy, and
                                                             tool trace properties.
  Both conditions operate on the exact same ques-
tion set, enabling a per-sample comparison to iden-       • Hashed Text Features (96 dimensions): Cap-
tify instances where the model possesses the intrin-         tures textual patterns via the hashing trick
sic reasoning capacity to solve a problem (via CoT)      (MD5 mapping to bin indices followed by L2
but fails when utilizing the tool-use protocol.             normalization). The reasoning text yields a
   In this work, the gate is trained on a disjoint ques-        64-dimensional vector, and the last tool output
tion set (GSM8K: 250 train / 250 test; HotPotQA:         yields a 32-dimensional vector.


                                         13

The Examples of Noisy Dataset

  Base:
  Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May.

 Thematic Background (TB)
  Sales  can  fluctuate  from  month  to  month.     Tracking  sales  helps  in  understanding
  trends. Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May.
  Analyzing sales data can reveal patterns. Effective strategies can boost future sales.

  Semantic Paraphrase (SP)
  Natalia  sold  clips  to  48  friends  during  April.    The  quantity  of  clips  sold  in May
 was  half  that  of  April.     Natalia’s May  clip  sales  were  half  as many  as  in  April.
   Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May.    The
  clips Natalia sold in May were half the number sold in April. In May, Natalia’s clip sales were reduced
  to half of April’s total.

  Parallel Entity Distractor (PED)
  In  a   different   region,   Ethan   sold   clips   to  a   different  audience   last  autumn.
  Elsewhere,   Sophia   sold   clips   to   unrelated   buyers   in   a   different   timeframe.
   Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May.      In
  a different case, Lucas sold clips to someone else in a nearby town. Elsewhere, Isabella sold clips to a
  different group during a separate event.

 Hedged Uncertainty (HU)
  It    is    likely    that    Natalia’s    total    sales   spanned   both   months.       Some
  say     the     sales     figures    might     not    have    been     officially     recorded.
   Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May.         It
  is claimed that Natalia’s total clip sales might have been substantial. Some say the combined sales in
  April and May were possibly noteworthy.

  Question:
 How many clips did Natalia sell altogether in April and May?

  Labels:
  evidence sentence ids: [2]. noise sentence ids: [0, 1, 3, 4]. final: 72.


Figure 3: We provide one group of examples in noisy dataset. The groundtruth evidence has been highlighted using
a blue box for clarity.


I.3  Stage 3: Gate Training                                  split with a patience of 20 epochs.

A binary classifier is trained to predict the probabil-                                                                 • Sample Weighting: Labels are weighted by
ity of continuation, P(continue | state), given the                                                        confidence levels derived from evidence speci-
120-dimensional feature vector.                                                                      ficity: strong (3×), medium (2×), and weak
                                                     (1×), with additional boosts applied for tar-
    • Model Architecture: Input features are stan-
                                                       geted error heuristics.
     dardized to zero-mean and unit-variance. The
      classifier is a two-layer Multilayer Perceptron        • Cross-Validation: A 5-fold GroupKFold val-
    (MLP) with 128 and 64 hidden units, utilizing         idation is employed, grouped by question ID
   ReLU activation functions.                            to strictly prevent information leakage across
                                                        noise variants.
    • Optimization Strategy: The model is op-
                                                         I.4  Stage 4: Gate-Augmented Inference     timized using Adam with a learning rate of
    10−3 and L2 regularization (α = 10−4). Early   During the online inference phase, the trained gate
     stopping is applied using a 10% validation     is deployed dynamically inside the function-calling


                                         14

Priority  Condition                   Label     Rationale

      1       Dtool answered correctly       commit   No intervention is required.
      2       Dtool wrong, but DCoT correct    continue  Model reasoning is sufficient; the tool
                                                          protocol caused the failure.
      3       Dtool wrong, tool calls < 2      continue  Under-compute heuristic:  premature
                                                         stopping without sufficient exploration.
      4       Dtool wrong, none of the above  commit   Genuine reasoning failure; further con-
                                                             tinuation is unhelpful.


Table 11: Priority rules for mixed-label construction. Priority 2 acts as the primary signal for the CoT-to-Tool gap.


loop. When the model generates a final text without
tool calls (attempting to submit), the gate evaluates
the current state:                               Algorithm 2: Offline Training Pipeline for
                                               Gate Decision MLP
  1. Extract the 120-dimensional feature vector us-                                                  Input: Baseline dataset Dbase,
     ing the identical feature engineering protocol                                                        Chain-of-Thought dataset Dcot
     established during training.                                              Output: Trained Gate Decision Model
                                 M∗gate  2. The MLP classifier outputs the probability
     P(continue).                               // Phase 1: State Initialization &
                                                Dataset Merging
  3. If P(continue) ≥τ (where the threshold τ
                                     S ←PreprocessAndMerge(Dbase, Dcot);
      is empirically set to 0.05), the gate triggers
    a continue decision. A continuation prompt     // Phase 2: Sample Annotation based
      (e.g., a CRITIC prompt forcing natural lan-        on Heuristics
    guage reasoning prior to the next action) is      foreach sample s ∈S do
     injected into the context, forcing the model to             if s.is_baseline_correct then
      initiate at least one additional tool call.                   ys ←commit;
                                                              else if s.is_cot_correct then
  4. If P(continue) < τ, the gate decides to com-
                                                            ys ←continue;
     mit, and the model’s current answer is ac-
     cepted as final.                                         else if s.tool_calls < 2 then
                                                            ys ←continue;
  To ensure robustness, safety mechanisms includ-
                                                              else
ing a maximum limit on extra turns (e.g., 3 extra
                                                            ys ←commit;
turns), no-progress detection, and duplicate expres-
sion detection are implemented to prevent infinite       Dlabeled ←{(s, ys)}s∈S;
generation loops.
                                             // Phase 3: Feature Extraction &
I.5  Training of Gate                              Model Training
                          X ←ExtractFeatures(Dlabeled, d = 120);
In this section, we provide the pseudocode for the
                                     y ←ExtractLabels(Dlabeled);
training workflow of the gate in Algorithm 2.
                                         Xnorm ←StandardScaler(X);
I.6  Inference with Gate                       Mgate ←InitializeMLP(hidden_dims =
In this section, we provide the pseudocode for the       [128, 64]);
inference workflow with the gate in Algorithm 3.    M∗gate ←
                                                TrainWithGroupKFold(Mgate, Xnorm, y, K =
I.7  Per-Configuration Analysis of Gate                                                           5);
     Effectiveness
                                                 return M∗gate
The gate’s behavior varies substantially across task–
model settings, in ways that closely match the
decomposition-based attribution analysis.


                                         15

GSM8K-4B.  GSM8K-4B is the most favorable
                                                       setting for the gate, as it combines the largest per-
                                            formance gap (−32.00%) with the highest ∆−frc
                                                 share (58.7% of all errors; Table 4). G-STEP
                                                alone improves accuracy from 50.64% to 69.12%
                                              (+18.48%). Adding CRITIC prompts further raises
Algorithm 3: Online Inference Pipeline
                                               accuracy to 74.88%, closing 75.75% of the gap.
with Gate-Controlled Tool Calling
                                              This additional gain (+5.76%) supports our ear-
 Input: Question q, Context c, Large
                                                              lier finding that GSM8K errors are primarily
       Language Model MLLM, Trained
                                               computation-chain failures (Types A and F): ex-
        Gate Model Mgate
                                                            plicit reflection helps the weaker model identify
 Input: System prompt Psys, Continue
                                                   arithmetic mistakes and produce better corrective
       prompt Pcont, Probability threshold
                                                    tool-use strategies.
        τ = 0.05
 Output: Final answer A                   GSM8K-32B.  GSM8K-32B provides a revealing
 // Initialize conversation history          contrast. Although protocol-induced errors remain
    with system and user prompts            prevalent overall (75.8%; Table 4), gap closure
 H ←Psys ⊕FormatUserPrompt(q, c);           reaches only 23.21%. Two factors likely explain
                                                              this. First, a much larger share of the 32B model’s
 while True do
                                                protocol-induced errors comes from ∆−sty (24.9%
    // Generate response from the
                                                      vs. 11.4% for 4B), i.e., format-sensitivity errors
       LLM
                                                         that additional tool turns cannot repair because the
     r ←MLLM(H);                                                degradation occurs at the prompting stage rather
       if HasToolCall(r) then                       than during iterative tool use. Second, even within
       // Execute tool and append           the targeted ∆−frc errors, the 32B model appears less
          observation to the loop           able to generate genuinely new corrective strategies
       o ←ExecuteTool(r.tool_call);             in later turns. The minimal CRITIC gain (+0.40%)
    H ←H ⊕r ⊕o;                               is consistent with this interpretation and with the
     else                                          observation in §2.4 that larger models are more sen-
       // Model attempts to submit            sitive to rigid format constraints than to invocation
          final answer without tool        mechanics.
          calls
                                        HotPotQA-4B.  HotPotQA-4B presents a much         pcont ←Mgate(H, r) ;
                                               narrower gap (−3.69%), and 77.3% of Agent-Full        // Compute P(continue)
                                                     errors are genuine capability gaps (Table 4). The
            if pcont ≥τ then                                                   gate improves accuracy from 73.18% to 74.97%, a
          // Continue the                                             modest +1.79% gain. Although this corresponds to
             interaction by                                        48.51% gap closure, the absolute improvement is
             injecting the continue                                                     limited by the small protocol-induced error budget
             prompt                                               (22.7%). The CRITIC variant (74.53%) performs
      H ←H ⊕r ⊕Pcont;                                                       slightly worse than the base gate, suggesting that
         else                                           on retrieval-heavy tasks, direct tool re-engagement
          // Accept the submission                                                               is more useful than interleaved verbal reflection.
             and halt
       A ←ExtractFinalAnswer(r);        HotPotQA-32B.  HotPotQA-32B is the most con-
           return A;                              strained setting:  the gap is only −1.13%, and
                                         73.3% of errors are genuine. Accordingly, the gate
                                                 provides no measurable improvement (83.02% →
                                               82.90%), while CRITIC further reduces accuracy to
                                             82.10%. This directly supports our decomposition:
                                       when most errors arise from a genuine inability to
                                                   synthesize information across passages, additional
                                                       tool turns offer little help. The bottleneck lies in un-


                                        16

derlying reasoning capability rather than protocol   K.3  The Prompt for Gate Mitigation
execution.                                                   In this section, we provide the prompts for Gate
                                             and Gate+Critic.
J  Variant-wise Robustness Under            The Original Gate prompt is in Figure 11.
   Semantic Distractors                     The critic-style Gate prompt are in Figure 12,
                                                  Figure 13, Figure 14 and Figure 15.
Figure 4 reports accuracy across the four se-                                            The difference between original gate prompt and
mantic distractor categories (TB, SP, PED, HU)                                                              critic gate is the critic-style prompt tends to per-
for Qwen3-4B and Qwen3-32B on GSM8K                                            form explicit verbal reasoning first, and then de-
and HotPotQA.  Across  variants, GATE  and                                                     cides whether to re-trigger the tool.
GATE+CRITIC consistently improve over AGENT-
FULL, indicating that gate-based control mitigates  L  Results in Noisy Condition
part of the degradation introduced by semantic dis-
                                                    In this section, we provide the full detailed resultstractors. The effect is most pronounced in fragile
                                                      for GSM8K and HotPotQA across all conditions,GSM8K settings; for example, on GSM8K-4B un-
                                                        variants, and metrics. The results are shown inder PED, accuracy increases from 44.4% to 70.4%
                                                 Table 12, Table 13 and Table 14.with GATE+CRITIC. This suggests that dynamic
routing is not only an average-case improvement,                                            Limitations
but also a robustness mechanism against semanti-
cally relevant noise.                              This document does not cover the content require-
  At the same time, COT remains the strongest   ments for ACL or any other specific venue. Check
overall reference under distractors. Across vari-   the author instructions for information on maxi-
ants, gated tool use narrows but does not eliminate  mum page lengths, the required “Limitations” sec-
the gap to COT, suggesting that multi-turn tool    tion, and so on.
interaction remains more vulnerable to distractor
amplification than internal reasoning. This limita-
tion is especially visible on HotPotQA-32B, where
all methods remain tightly clustered, indicating
that when the dominant bottleneck is genuine in-
formation synthesis rather than protocol execution,
robustness gains from gate-based control are inher-
ently limited.
   Overall, the variant-wise results support the
same qualitative conclusion as the main text: se-
mantic distractors consistently expose the CoT–
Tool gap, while gate-based control provides partial
but not complete mitigation, with larger benefits
in protocol-dominated settings than in capability-
dominated ones.

K  Prompt

K.1  The Prompt for Generating
     Sem-Distractor

In this section, we provide the prompts for generat-
ing distractors in Figure 5, Figure 6, Figure 7 and
Figure 8.

K.2  The Prompt for Intervention Framework

In this section, we provide the prompts for Interver-
tion Framework in Figure 9 and Figure 10.


                                         17

Qwen3-4B                          Qwen3-32B
Condition        Metric
                            Base  TB  PED  HU   SP   Overall  Base  TB  PED  HU   SP   Overall

               Acc (%)    91.00  86.80  81.40  83.60  84.40   85.44   94.00  92.80  89.40  89.80  91.00   91.40
NoTool-CoT      Ev-F1 (%)  89.78  89.72  89.99  78.15  19.44   73.41   92.48  93.35  95.24  85.89  35.00   80.39
                  AvgCalls    0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    85.80  85.80  82.20  86.60  83.80   84.84   80.00  80.40  75.40  76.40  80.60   78.56
NoTool-FCStyle   Ev-F1 (%)  85.70  90.80  92.12  82.01  19.53   74.03   89.45  95.14  96.71  88.53  33.34   80.63
                  AvgCalls    0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    34.40  29.40  29.80  30.40  29.20   30.64   53.40  50.40  50.40  49.20  51.20   50.92
Agent-NoopTool   Ev-F1 (%)  84.13  87.92  87.60  82.57  20.56   72.56   89.31  93.21  95.44  87.97  30.00   79.18
                  AvgCalls    1.07   1.17   1.22   1.25   1.38    1.22    1.00   1.02   1.02   1.03   1.05    1.02

               Acc (%)    51.20  54.20  48.00  57.40  49.60   52.08   77.60  76.60  73.80  73.20  77.60   75.76
Agent-Full        Ev-F1 (%)  84.78  87.81  88.77  83.11  19.45   72.78   89.01  93.02  95.26  87.42  30.03   78.95
                  AvgCalls    1.26   1.35   1.39   1.43   1.59    1.41    1.03   1.04   1.04   1.04   1.12    1.05
               Acc (%)    47.40  50.80  44.40  53.00  43.00   47.72   78.60  76.20  73.20  73.80  77.60   75.88
Agent-Max1Turn  Ev-F1 (%)  69.85  72.82  76.74  69.36  15.73   60.90   87.96  91.57  94.52  87.02  29.74   78.16
                  AvgCalls    1.26   1.36   1.36   1.42   1.59    1.40    1.01   1.04   1.03   1.03   1.06    1.03

               Acc (%)    87.20  92.60  91.40  88.80  86.00   89.20   94.40  91.80  95.00  93.00  92.80   93.40
Agent-OracleCalc  Ev-F1 (%)  84.09  88.08  89.24  83.47  20.13   73.00   89.17  93.38  95.18  87.75  30.19   79.13
                  AvgCalls    1.20   1.28   1.34   1.37   1.55    1.35    1.00   1.02   1.02   1.03   1.10    1.03

               Acc (%)    50.00  53.00  53.00  53.20  53.20   52.48   78.80  79.80  80.00  80.00  80.00   79.72
Agent-OracleEvid  Ev-F1 (%)  84.17  85.20  85.23  85.19  85.19   84.99   89.08  90.47  90.45  90.45  90.45   90.18
                  AvgCalls    1.28   1.24   1.24   1.24   1.24    1.25    1.02   1.03   1.03   1.03   1.03    1.03

Table 12: Full detailed results for GSM8K across all conditions, variants, and metrics. Accuracy (Acc) and
Evidence-F1 (Ev-F1) are in percentages (%).



                                    Qwen3-4B                          Qwen3-32B
Condition        Metric
                            Base  TB  PED  HU   SP   Overall  Base  TB  PED  HU   SP   Overall

               Acc (%)    75.63  76.19  73.95  74.23  73.95   74.79   83.75  83.19  84.87  84.87  84.03   84.15
NoTool-CoT      Ev-F1 (%)  59.72  60.03  60.70  56.07  28.62   53.03   56.86  58.51  59.10  55.41  25.05   50.99
                  AvgCalls    0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    71.15  71.99  69.75  69.75  71.99   70.92   85.15  84.87  82.91  83.19  83.75   83.98
NoTool-FCStyle   Ev-F1 (%)  48.56  59.30  57.75  49.65  26.15   48.28   54.53  57.64  58.52  53.81  25.22   49.95
                  AvgCalls    0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    49.30  59.10  52.66  57.42  64.99   56.69   84.03  81.79  80.39  80.95  83.19   82.07
Agent-NoopTool   Ev-F1 (%)  10.89  20.68  17.30  22.23  16.01   17.42   51.10  54.58  55.54  49.88  21.79   46.58
                  AvgCalls    1.06   1.08   1.09   1.06   1.07    1.07    1.07   1.12   1.20   1.13   1.16    1.13

               Acc (%)    74.51  73.67  70.87  71.43  71.15   72.32   84.59  83.75  80.11  83.47  83.19   83.03
Agent-Full        Ev-F1 (%)  47.01  52.19  49.44  46.25  32.74   45.53   48.34  50.70  51.19  48.89  27.86   45.40
                  AvgCalls    1.06   1.08   1.09   1.06   1.08    1.07    1.06   1.11   1.17   1.14   1.15    1.13
               Acc (%)    71.99  70.03  68.91  69.47  69.47   69.97   84.03  84.03  80.67  83.47  83.75   83.19
Agent-Max1Turn  Ev-F1 (%)  45.51  49.40  46.26  43.23  31.28   43.14   49.48  51.15  51.87  47.97  27.91   45.68
                  AvgCalls    1.00   1.00   1.00   1.00   1.00    1.00    0.97   0.97   0.96   0.97   0.97    0.97

               Acc (%)    93.00  93.56  92.16  93.28  93.28   93.05   92.16  91.32  89.08  91.60  89.36   90.70
Agent-OracleCalc  Ev-F1 (%)  38.60  44.04  45.09  39.62  21.78   37.82   50.71  53.83  53.94  50.32  22.18   46.19
                  AvgCalls    1.07   1.08   1.09   1.06   1.07    1.07    1.04   1.10   1.19   1.12   1.14    1.12

               Acc (%)    74.51  73.95  74.51  74.51  74.51   74.40   84.87  83.75  85.15  85.15  85.15   84.82
Agent-OracleEvid  Ev-F1 (%)  47.01  47.39  47.82  47.82  47.82   47.57   49.17  49.60  49.77  49.81  49.81   49.63
                  AvgCalls    1.06   1.09   1.08   1.08   1.08    1.08    1.07   1.06   1.10   1.10   1.10    1.08

Table 13: Full detailed results for HotPotQA across all conditions, variants, and metrics. Accuracy (Acc) and
Evidence-F1 (Ev-F1) are in percentages (%).



                                         18

Figure 4: Performance comparison of different reasoning strategies under semantic noise. The radar charts display
the accuracy of Qwen3-4B, Qwen3-32B, and GPT-4.1-mini on GSM8K and HotPotQA. Each subplot contrasts
four configurations (COT, AGENT-FULL, GATE, GATE+CRITIC) evaluated across a clean base set and four noisy
variants (TB, PED, HU, SP).





   The prompt used for generating Thematic Background (TB) filler

 Prompt:
 "You are generating IN-DOMAIN background filler for a math word problem. These sentences should
 SOUND relevant to the same general topic/domain, but MUST NOT help solve the problem.

  Return STRICT JSON ONLY:
 {{
  "topic": "<topic>",
  "before": [<exactly {BEFORE_N} short sentences>],
  "after": [<exactly {AFTER_N} short sentences>]
 }}

 HARD RULES (must follow):
  1. Insert-only: write NEW sentences only; do NOT rewrite or paraphrase the evidence.
  2. Keep ONE coherent in-domain topic (same domain as the problem).
  3. NO numbers anywhere (no digits, no written numbers, no fractions).
  4. No math/solving strategy hints (forbidden: multiply, divide, sum, total, fraction, percent, per, each,
  equation, formula, calculate, compute).
  5. Do NOT use difference markers (forbidden: another, elsewhere, different, nearby, unrelated,
  separate, yesterday).
  6. Do NOT use hedging markers (forbidden: reportedly, claimed, might, possibly, about, around,
  likely, unverified).
  7. Do NOT mention the specific entities (names, places, dates) listed in: [{CORE_WORDS}].
  However, you MAY use general domain terms (e.g. ’clips’, ’store’, ’selling’) to keep the topic relevant.
  8. Do NOT copy core numbers: [{CORE_NUMS}]
  9. Each sentence must be short, factual, and self-contained."

 Output
  Input: Problem core (evidence-centric view): {Q_CORE_TEXT}
  Output:


               Figure 5: The prompt used for generating Thematic Background (TB) Distractor.




                                         19

The prompt used for generating Parrallel Entity Distractor (PED)

Prompt:
"You are generating TOPIC-RELATED distractors that must be LOGICALLY EXCLUDED
from the problem. They should share surface-level domain words, but clearly refer to a different
person/time/place/event.

Return STRICT JSON ONLY:
{{
"topic": "<topic>",
"before": [<exactly {BEFORE_N} short sentences>],
 "after": [<exactly {AFTER_N} short sentences>]
}}

HARD RULES (must follow):
1. Insert-only: write NEW sentences only; do NOT rewrite/paraphrase the evidence.
 2. Keep ONE coherent topic in the same domain.
 3. EACH sentence MUST include at least ONE difference marker: another / elsewhere / different /
nearby / unrelated / separate / in a different / someone else / not this case.
4. NO numbers anywhere.
 5.  Must include 1–2 domain/topic hint words (same domain), but DO NOT restate evidence
 facts/relations.
 6. MUST NOT use hedging markers (forbidden: reportedly, claimed, might, possibly, about, around,
 likely).
7. Use specific INVENTED names (e.g., ’Alice’, ’Mr. Smith’, ’The neighbor’) instead of generic
terms like ’someone’ or ’another person’ to make it sound natural.
 8. Do NOT copy core numbers: [{CORE_NUMS}]
 9. Each sentence short and self-contained."

Output
Input: Problem core (evidence-centric view): {Q_CORE_TEXT}
Output:


                Figure 6: The prompt used for generating Parrallel Entity Distractor (PED).





                                        20

The prompt used for generating Hedged Uncertainty(HU) Distractor

Prompt:
"You are generating TOPIC-RELATED statements that sound like evidence but are epistemically
UNCERTAIN. These should not create contradictions that make the problem unsolvable.

Return STRICT JSON ONLY:
{{
"topic": "<topic>",
"before": [<exactly {BEFORE_N} short sentences>],
 "after": [<exactly {AFTER_N} short sentences>]
}}

HARD RULES (must follow):
1. Insert-only: write NEW sentences only; do NOT rewrite/paraphrase the evidence.
 2. Keep ONE coherent topic in the same domain.
 3. MUST NOT include difference markers (forbidden: another, elsewhere, different, nearby, unrelated,
separate, yesterday).
4. NO numbers anywhere (avoid creating alternative exact facts).
 5. Do NOT assert the answer or options (forbidden: ’the answer is’, ’correct answer’, ’choose option’,
’option X’).
 6. You MAY mention the main entities (e.g. ’{CORE_WORDS}’) to make the distractor sound like a
valid premise, but the hedging marker must keep it uncertain.
7. Do NOT copy core numbers: [{CORE_NUMS}]
 8. Each sentence short and self-contained.
 9. EACH sentence MUST include at least ONE hedging marker: reportedly / claimed / it is said /
some say / might / possibly / perhaps / around / about / likely / unverified / not confirmed.
10. The tone should be speculative, vague, or rumor-based, distinct from the factual tone of the
evidence."

Output
Input: Problem core (evidence-centric view): {Q_CORE_TEXT}
Output:


               Figure 7: The prompt used for generating Hedged Uncertainty(HU) Distractor.





                                        21

The prompt used for generating Semantic Paraphrase (SP) Distractor

Prompt:
"You are generating SEMANTICS-PRESERVING PARAPHRASES of the EVIDENCE sentences in
a word problem. Your output will be inserted BEFORE and AFTER the evidence as paraphrase fillers.

Return STRICT JSON ONLY:
{{
"topic": "<topic>",
"before": [<exactly {BEFORE_N} short sentences>],
 "after": [<exactly {AFTER_N} short sentences>]
}}

HARD RULES (must follow):
1. One coherent topic: all sentences must be about the SAME scenario as the evidence.
 2. Paraphrase-only: every generated sentence MUST be a paraphrase of some [EVID] sentence
content. Do NOT paraphrase [Q] (the question sentence). Do NOT add new facts, new events, or new
 entities.
 3. Syntactic Variation: You MUST change the sentence structure significantly (e.g., switch between
active/passive voice, change word order). Do NOT simply replace one word; make the sentence
LOOK different but MEAN the same.
4. Numbers/values: you may mention numbers ONLY if they already appear in the evidence. Do
NOT introduce any new numbers, ranges, approximations, or near-miss numbers. Keep exact values
unchanged (no ’about’, ’around’, ’roughly’, ’approximately’).
 5. Keep relations unchanged: Preserve relational operators such as half / twice / remaining / difference
 / total. Do NOT change who did what, when, or the direction of a relation.
 6. No markers: Do NOT use difference markers (another / elsewhere / yesterday / different / nearby /
unrelated / separate).
7. No hedging markers: Do NOT use hedging markers (reportedly / claimed / might / possibly / about
 / around / likely / unverified).
 8. No solving hints: Do NOT include step-by-step solution language (multiply / divide / add / subtract
 / compute / calculate / equation / formula).
 9. Each sentence must be short, grammatical, and self-contained."

Output
Input: Problem core (evidence-centric view): {Q_CORE_TEXT}
Output:


               Figure 8: The prompt used for generating Semantic Paraphrase (SP) Distractor.





                                        22

The prompt used for NoTool-CoT

 Prompt:
 "You are a careful math solver. Read the numbered information chunks below. Some chunks are noise
— use only the relevant ones as evidence.

  Rules:
  1. Think step-by-step in ’calc_chain’ FIRST before writing anything else.
  2. CRITICAL: Inside ’calc_chain’, enclose your final computed result in angle brackets and END
 with it, e.g. <42>.
  3. Then copy that exact value into ’final_answer’ (numeric only, no units).
  4. List chunk indices you actually used in ’evidence_ids’.

  Return JSON with keys IN THIS ORDER: calc_chain, evidence_ids, final_answer.

 CRITICAL MATH RULES:
  - ’half as many’ →divide by 2; ’twice as much’ →multiply by 2.
  - ’how much MORE does X need’ = (what X needs) −(what X already has + gifts).
  - ’X does Y to N people K times’ →multiply by BOTH N and K.
  - Count EVERY multiplier in the sentence — don’t miss any."

 Output
  Input: {NUMBERED_CHUNKS}
 Output:


Figure 9: The prompt used for instructing the math solver to extract evidence, reason step-by-step, and format the
final JSON output (NoTool-CoT).





                                         23

The prompt used for the tool-augmented solver

 Prompt:
 "You are a math-solving agent with a ’calculate’ function for arithmetic. You will see a question and
 numbered information chunks. Some chunks are noise — identify the real evidence.

  Strategy:
  1. Identify which chunks contain real evidence (specific numbers, clear facts) vs noise (hedged claims,
  unrelated info, different people/places/times).
  2. Extract relevant quantities from evidence chunks.
  3. Call the calculate function for ALL arithmetic — do NOT compute in your head.
  4. You may call calculate multiple times if needed (e.g. one step per operation).

  After all calculations, respond with JSON:
 {
  "evidence_ids": [integer chunk indices that are real evidence],
  "final_answer": "the numeric answer (just the number, no units)",
  "reasoning": "brief explanation of which chunks you used and why"
 }

 CRITICAL RULES:
  - ’half as many’ →divide by 2; ’twice as much’ →multiply by 2.
  - ’how much MORE does X need’ = (what X needs) −(what X already has + gifts).
  - ’X does Y to N people K times’ →multiply by BOTH N and K.
  - Count EVERY multiplier in the sentence — don’t miss any."

 Output
  Input: {QUESTION}, {NUMBERED_CHUNKS}
 Output:


Figure 10: The prompt used for instructing the tool-augmented math solver to identify evidence, utilize the calculate
function, and format the final JSON output.




   The prompt used for original gate

 Prompt:
 "Your previous tool result is: {prev_output}. Before finalizing, re-check the evidence chunks and
  verify:
 1) Did you use the correct numbers from evidence?
  2) Did you complete all required computation steps to the final answer?

  If anything  is missing or incorrect,  call calculate with a corrected and COMPLETE multi-
  step expression (do not repeat the same expression). If already complete and consistent, return final
 JSON only."

 Output
  Input: Your previous tool result is: {prev_output}
 Output:


Figure 11: The prompt used for instructing the tool-augmented math solver to verify its evidence selection and
calculation completeness before returning the final answer (Original Gate-style).



                                         24

The prompt used for error correction in thesolver

 Prompt:
  "Calculator returned: {prev_output}. Before calling calculate again, reason in words: which numbers
 from evidence do you need, and what is the correct step-by-step plan? Then call calculate with a
 CORRECTED expression (not the same one). Return final JSON after."

 Output
  Input: Calculator returned: {prev_output}
 Output:


Figure 12: The prompt used for instructing the math solver to reflect on previous outputs, correct its reasoning, and
formulate a new plan.


   The prompt used for re-deriving the solution after a potentially incorrect tool result

 Prompt:
  "Previous result ({prev_output}) may be wrong. Re-derive the solution in words from evidence first,
  then call calculate with a revised expression. Do NOT reuse any previous expression. Return final
 JSON after."

 Output
  Input: Previous result: {prev_output}
 Output:


Figure 13: The prompt used for instructing the tool-augmented math solver to re-derive its solution from the
evidence and formulate a revised calculation when the previous result is suspected to be incorrect.


   The prompt used for handling repeated incorrect tool calls

 Prompt:
 "You repeated: {repeated_expression} (returned {prev_output}). Explain in words why this is wrong
 and what should change, then call calculate with a DIFFERENT expression. Return final JSON after."

 Output
  Input: You repeated: {repeated_expression} (returned {prev_output})
 Output:


Figure 14: The prompt used for instructing the tool-augmented math solver to break out of a loop and correct a
repeated incorrect calculation.


   The prompt used for step-by-step verification and sense-checking

 Prompt:
  "Verify in words: re-read the question, list key numbers from evidence, check each arithmetic step.
 Does the answer make sense? If wrong, call calculate with a corrected expression. Return final JSON
  after."

 Output
  Input: {QUESTION}, {EVIDENCE_CHUNKS}, {CURRENT_ANSWER}
 Output:


Figure 15: The prompt used for instructing the math solver to verify its reasoning, check arithmetic steps against the
evidence, and ensure the final answer makes logical sense.


                                         25

GSM8K                           HotPotQA
Condition       Metric
                           Base  TB   PED  HU   SP   Overall  Base  TB   PED  HU   SP   Overall

               Acc (%)    93.20  91.00  89.20  90.40  89.80  90.72  87.96  87.96  87.96  87.68  83.75  87.06
NoTool-CoT     Ev-F1 (%)  90.99  94.44  95.62  86.86  25.91  78.76  49.47  52.26  53.10  50.07  22.48  45.48
                 AvgCalls   0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    88.20  85.20  86.20  87.60  86.60  86.76  86.55  84.59  86.27  85.15  85.71  85.66
NoTool-FCStyle  Ev-F1 (%)  88.60  96.40  96.44  88.52  25.49  79.09  60.10  66.01  65.97  62.04  27.38  56.30
                 AvgCalls   0.00   0.00   0.00   0.00   0.00    0.00    0.00   0.00   0.00   0.00   0.00    0.00

               Acc (%)    48.20  48.00  46.00  49.80  52.20  48.84  85.43  84.87  84.59  84.87  84.59  84.87
Agent-NoopTool  Ev-F1 (%)  89.42  95.78  96.39  88.28  24.80  78.93  55.77  65.32  65.05  58.82  23.74  53.74
                 AvgCalls   1.18   1.11   1.11   1.05   1.65    1.22    1.17   1.55   1.68   1.62   1.45    1.49

               Acc (%)    75.40  76.00  76.60  77.80  77.20  76.60  87.11  85.99  87.11  86.55  85.43  86.44
Agent-Full       Ev-F1 (%)  89.77  95.52  95.27  88.83  23.73  78.63  58.21  60.25  60.37  56.75  33.76  53.87
                 AvgCalls   1.30   1.29   1.32   1.21   2.15    1.45    1.17   1.45   1.59   1.67   1.69    1.51
               Acc (%)    72.00  74.20  70.80  73.60  73.80  72.88  86.55  85.99  85.71  85.99  86.83  86.22
Agent-Max1Turn  Ev-F1 (%)  77.15  83.93  83.99  80.98  13.69  67.95  58.35  62.06  61.28  56.84  32.42  54.19
                 AvgCalls   1.22   1.23   1.20   1.13   2.10    1.37    1.00   1.00   1.00   1.00   1.00    1.00

               Acc (%)    84.20  85.40  82.60  82.60  76.40  82.24  91.88  92.16  91.04  92.72  90.76  91.71
Agent-OracleCalc Ev-F1 (%)  89.47  95.62  95.68  88.16  25.17  78.82  54.14  62.84  62.91  58.29  23.04  52.24
                 AvgCalls   1.27   1.26   1.24   1.19   2.15    1.42    1.17   1.41   1.49   1.47   1.30    1.37

               Acc (%)    74.00  77.20  76.80  76.40  75.60  76.00  87.39  86.27  86.55  86.55  86.55  86.67
Agent-OracleEvid Ev-F1 (%) 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00 100.00
                 AvgCalls   1.28   1.28   1.28   1.28   1.26    1.28    1.22   1.23   1.20   1.17   1.23    1.21

Table 14: Full detailed results for GPT-4.1-mini across GSM8K and HotPotQA under all conditions, variants, and
metrics. Accuracy (Acc) and Evidence-F1 (Ev-F1) are in percentages (%). GSM8K uses exact-match accuracy.
HotPotQA uses the same contains-match criterion as in Tables 2–7.





                                         26