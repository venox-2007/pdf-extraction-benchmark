# arXiv:2605.00123v1[cs.AI]30Apr2026

## Minimal, Local, Causal Explanations for Jailbreak Success in Large Language Models

Shubham Kumar & Narendra Ahuja University of Illinois Urbana-Champaign {sk138, n-ahuja}@illinois.edu

### Abstract

Safety trained large language models (LLMs) can often be induced to answer harmful requests through jailbreak prompts. Because we lack a robust understanding of why LLMs are susceptible to jailbreaks, future frontier models operating more autonomously in higher-stakes settings may similarly be vulnerable to such attacks. Prior work has studied jailbreak success by examining the model’s intermediate representations, identifying directions in this space that causally encode concepts like harmfulness and refusal. Then, they globally explain all jailbreak attacks as attempting to reduce or strengthen these concepts (e.g., reduce harmfulness). However, different jailbreak strategies may succeed by strengthening or suppressing different intermediate concepts, and the same jailbreak strategy may not work for different harmful request categories (e.g., violence vs. cyberattack); thus, we seek to give a local explanation—i.e., why did this specific jailbreak succeed? To address this gap, we introduce LOCA, a method that gives Local, CAusal explanations of jailbreak success by identifying a minimal set of interpretable, intermediate representation changes that causally induce model refusal on an otherwise successful jailbreak request. We evaluate LOCA on harmful original–jailbreak pairs from a large jailbreak benchmark across Gemma and Llama chat models, comparing against prior methods adapted to this setting. LOCA can successfully induce refusal by making, on average, six interpretable changes; prior work routinely fails to achieve refusal even after 20 changes. LOCA is a step toward mechanistic, local explanations of jailbreak success in LLMs. Code to be released.

### 1 Introduction

Large language models (LLMs) have continued to grow in their capabilities, and with the rise of agentic AI, they are being used more autonomously for higher-stakes settings (Bommasani et al., 2021; Wang et al., 2023). Because of their potential for misuse, LLMs deployed to the public typically undergo alignment fine-tuning in order to learn to refuse harmful (e.g., safety policy violating) requests while providing helpful answers on harmless requests (Bai et al., 2022); however, jailbreak attacks can create harmful requests that bypass LLM refusal, eliciting a harmful response (Chu et al., 2025).

To understand LLM refusal behavior, a growing body of mechanistic interpretability work has identified directions in their intermediate representation space that causally encode concepts like harmfulness and refusal (Wollschl¨ager et al., 2025; Arditi et al., 2024; Ball et al., 2024). Then, these concepts are used to produce a global—across all inputs—explanation for refusal behavior. For example, some prior works find that jailbreaks succeed by reducing the degree of harmfulness in intermediate representations (Arditi et al., 2024; Ball et al., 2024). However, different jailbreak strategies may succeed by strengthening or suppressing different intermediate concepts, and the same jailbreak strategy may not work for different request categories (e.g., violence vs. cyberattack). We believe that jailbreak success may be more nuanced than what global explanations can capture, motivating the need for local, sample-specific explanations. Furthermore, we want our explanation to be causal; that is, our explanation should isolate aspects of the intermediate representation that, when intervened

on, induce refusal behavior on an otherwise successful jailbreak request. Finally, we desire a minimal or parsimonious explanation to ensure we identify the most important causal interventions; this results in an explanation more conducive to human understanding and interpretation (Cowan, 2010; Miller, 1956). To achieve this, we propose LOCA as a method to find minimal, LOcal, CAusal explanations of jailbreak success. Our contributions are:

- 1. LOCA can induce refusal on an otherwise successful jailbreak request by making (on average) six interventions on intermediate representations from a Llama chat model. Other methods are generally unable to induce refusal even after 20 interventions.
- 2. An ablation study validates that LOCA’s algorithmic novelties drive improvement, explaining why LOCA outperforms prior methods.
- 3. A localization analysis finds that changes to instruction (i.e., user request) tokens are the most causally important for inducing refusal in earlier layers. LOCA induces refusals in later layers by relying almost exclusively on punctuation and post-instruction (i.e., chat template) tokens.
- 4. A case study on using LOCA to explain an instance of jailbreak success.


### 2 Related works

Finding interpretable linear directions, or concepts, in LLMs: The linear representation hypothesis posits that meaningful concepts are encoded as linear directions in a model’s representation space (Park et al., 2023; Elhage et al., 2022). For example, prior work has found directions corresponding to truth (Zou et al., 2023) and knowledge awareness (Ferrando et al., 2025). These directions can be found in a supervised manner by training probes on intermediate representations, or activations, to separate between positive and negative examples of a concept (Cunningham et al., 2026). Aside from probing, sparse autoencoders (SAEs) have emerged as a powerful, unsupervised tool to surface a large set of disentangled interpretable concepts (Bricken et al., 2023; Cunningham et al., 2023).

To make causal claims about the function of a concept encoded by a given direction (either from a probe or an SAE), prior works analyzes the impact of changing activations along the specified direction during the LLM’s forward pass. These changes, or interventions, typically happen by either activation steering or activation patching. Activation steering adds (or subtracts) the scaled direction to activations at many or all token positions (Turner et al.,

- 2023). It is critical to scale the operation properly; a scale too small may result in no change, and a scale too large may push the model off-manifold, resulting in non-nonsensical outputs. Activation patching makes interventions by replacing activations during a forward pass on the target prompt with reference activations from a different, reference prompt (Meng et al., 2022; Heimersheim & Nanda, 2024). Because we have reference activations, it is easier to make targeted and varied changes per-token. Activation patching commonly uses a reference prompt from a closely matched template to align activations across corresponding token positions; otherwise, defining the token correspondence becomes less clear.


Global understanding of jailbreaks in an LLM’s representation space: Much of the literature has concentrated on understanding jailbreaks by looking for global explanations in the intermediate representation space of LLMs. Some works suggest that the refusal is mediated by harmfulness; thus, jailbreaks succeed by suppressing input token projections onto these harmfulness directions (Arditi et al., 2024; Ball et al., 2024; Lin et al., 2024). Complementary work by Wollschl¨ager et al. (2025) finds that a gradient-based optimization can yield a refusal subspace that is more suitable for causally controlling refusal (e.g., by steering the model). However, other work offers a more nuanced perspective. A study from Zou et al. (2023) finds that in 90% of successful jailbreaks, the model accurately represents the request as harmful, yet does not refuse. Furthermore, Zhao et al. (2025) finds causal evidence that LLMs represent harmfulness and refusal separately: refusal can be bypassed even if the model knows the question is harmful. This suggests that while refusal can be represented in a low-dimensional subspace, refusal is determined by multiple internal concepts, not just harmfulness. Furthermore, these concepts may not be global—they may

vary greatly among different jailbreak examples. Zhao et al. (2025); Kirch et al. (2025) find that different jailbreak strategies try to bypass refusal through different mechanisms, and different request risk categories may rely on different concepets to induce refusal.

There have been two previous attempts at characterizing these concepts by looking at early (or upstream) layer representations. Lee et al. (2025) find causal, early-layer SAE directions (or vectors) that, when used for steering, increase downstream request token embedding projections onto the refusal direction (found from Arditi et al. (2024)). On three hand-selected prompts, this method surfaced upstream causal steering vectors that induced refusal. Yeo et al. (2025) find upstream SAE vectors causal to refusal with a two-step process: (1) take the top-M SAE directions that have the highest cosine similarity with the refusal direction and (ii) take the top-K (where K < M) SAE vectors that lead to the largest change on output token probabilities after activation patching from a harmful, non-refused instruction to a harmful, refused instruction. They validate these SAE vectors by steering, showing that the causal vectors can either induce or bypass refusal.

Both works successfully find upstream vectors causal to refusal, but these concepts are not used to locally explain why a jailbreak succeeded. Additionally, both works are limited by the following weaknesses. First, they use first-order approximations that are averaged across tokens; consequently, they struggle to localize interventions to specific tokens, so they make interventions along all tokens. Furthermore, the top-K vectors are selected in one-shot, which ignores interaction effects introduced when steering or patching with the selected vectors. LOCA addresses both limitations, allowing us to explain jailbreak success in terms of the minimal, causal change needed to recover the original refusal response.

### 3 LOCA: LOcal, CAusal explanations of jailbreak success

We consider the following setting. The user wants an LLM to answer the original, target prompt xo, but the LLM has gone through alignment and refuses answering xo. The user creates a jailbreak prompt xj to bypass the alignment and elicit an answer to the original xo. To explain why xj succeeded, we are interested in finding a minimal change to xj in the representation space that causes xj to fail (i.e., induce a similar refusal response to xo).

To make the change, we can either perform activation steering or activation patching. Lee et al. (2025) performed steering, which we believe to be suboptimal because it (1) may result in off-manifold representations and (2) there is not a principled way to select the tokens for steering. Thus, we opt to perform activation patching, which allows for tokenspecific, within-distribution changes. To enable activation patching between two structurally different prompts, LOCA first matches tokens from xj to xo. Then, LOCA iteratively ranks the per-token, per-concept changes using a first-order approximation and applies activation patching to the intermediate token representations, or token embeddings, of xj.

##### 3.1 Preliminaries

Transformers. Decoder-only transformers (Vaswani et al., 2017) tokenize a prompt x into a sequence of input tokens T = (t1, t2,..., tN), where the number of tokens N depends on

x. Each token ti is embedded to hi(1) ∈ RD. The transformation from each transformer layer l is written back to the residual stream, updating the intermediate token embedding

- as hi(l). After the last layer, the model predicts the next output token as logits y ∈ R|V| over the vocabulary V, which is converted to probabilities p via softmax. Similar to prior studies (Arditi et al., 2024; Zhao et al., 2025; Lee et al., 2025; Yeo et al., 2025), we analyze intermediate representations from the residual stream.


Activation Patching. Given two sequences Treference and Ttarget, activation patching evaluates the effect of overwriting (or patching) selected intermediate activations from Ttarget with corresponding activations from Treference. The patching effect measures how much the LLM output changed—specifically, how closely the new output recovers yreference.

![image 1](<native_3_images/imageFile1.png>)

![image 2](<native_3_images/imageFile2.png>)

![image 3](<native_3_images/imageFile3.png>)

![image 4](<native_3_images/imageFile4.png>)

![image 5](<native_3_images/imageFile5.png>)

![image 6](<native_3_images/imageFile6.png>)

![image 7](<native_3_images/imageFile7.png>)

![image 8](<native_3_images/imageFile8.png>)

![image 9](<native_3_images/imageFile9.png>)

![image 10](<native_3_images/imageFile10.png>)

![image 11](<native_3_images/imageFile11.png>)

![image 12](<native_3_images/imageFile12.png>)

![image 13](<native_3_images/imageFile13.png>)

![image 14](<native_3_images/imageFile14.png>)

![image 15](<native_3_images/imageFile15.png>)

![image 16](<native_3_images/imageFile16.png>)

![image 17](<native_3_images/imageFile17.png>)

![image 18](<native_3_images/imageFile18.png>)

![image 19](<native_3_images/imageFile19.png>)

![image 20](<native_3_images/imageFile20.png>)

![image 21](<native_3_images/imageFile21.png>)

![image 22](<native_3_images/imageFile22.png>)

![image 23](<native_3_images/imageFile23.png>)

![image 24](<native_3_images/imageFile24.png>)

![image 25](<native_3_images/imageFile25.png>)

![image 26](<native_3_images/imageFile26.png>)

![image 27](<native_3_images/imageFile27.png>)

![image 28](<native_3_images/imageFile28.png>)

![image 29](<native_3_images/imageFile29.png>)

![image 30](<native_3_images/imageFile30.png>)

![image 31](<native_3_images/imageFile31.png>)

![image 32](<native_3_images/imageFile32.png>)

![image 33](<native_3_images/imageFile33.png>)

![image 34](<native_3_images/imageFile34.png>)

![image 35](<native_3_images/imageFile35.png>)

![image 36](<native_3_images/imageFile36.png>)

![image 37](<native_3_images/imageFile37.png>)

![image 38](<native_3_images/imageFile38.png>)

![image 39](<native_3_images/imageFile39.png>)

![image 40](<native_3_images/imageFile40.png>)

![image 41](<native_3_images/imageFile41.png>)

![image 42](<native_3_images/imageFile42.png>)

![image 43](<native_3_images/imageFile43.png>)

![image 44](<native_3_images/imageFile44.png>)

(a) Token matching issue (b) Re-sample Tinst, then match (c) Final matching scheme

- Figure 1: LOCA token matching: The jailbreak prompt xj and original (reference) prompt xo can be of any format, making naive token matching ill-specified (Fig. 1a). LOCA handles this by resampling (in this case, upsampling) xo’s Tinst tokens to match the length of xj’s Tinst tokens (Fig. 1b). Then, Tinst and Tpost-inst tokens can be matched one-to-one (Fig. 1c).


Sparse Autoencoders. Sparse autoencoders (SAEs) are a family of autoencoders that map an input activation x ∈ Rd to a feature vector f ∈ Rm and then reconstruct the input with a linear decoder Wd. SAEs typically take the form of:

f = ϕ(Wex + be), xˆ = Wdf + bd (1) where ϕ is a non-linear funtion. SAEs are trained to minimize reconstruction error while satisfying some sparsity objective on f. Each row vi ∈ Rd of Wd is a concept vector, denoting an interpretable direction in the original representation space. LOCA will activation patch along these concept vectors.

##### 3.2 Token matching

Activation patching is conventionally used when xreference and xtarget follow the same structure, since the correspondence between reference tokens and target tokens is straightforward. This is problematic when trying to patch between the original (reference) prompt xo and a jailbreak (target) prompt xj, since the jailbreak can be of any format and length, as long as it is successful (Fig. 1a). LOCA handles this with a token matching scheme (shown in Fig. 1b, 1c). A prompt x to an instruct (or chat) LLM will follow a chat template, resulting in the following three components: (1) system tokens (Tsys), (2) instruction tokens (Tinst), and (3) post-instruction tokens (Tpost-inst):

- 1. Tsys tokens (and their embeddings) are the same for any x in causal, decoder-only transformers, so we safely ignore them.
- 2. Tinst tokens from xo and xj have variable length. xo’s Tinst are upsampled or downsampled to match the length of xj’s Tinst, allowing us to match one-to-one. When upsampling, we simply repeat the upsampled token embedding (no interpolation). When downsampling, we skip over embeddings.
- 3. Tpost-inst tokens are the same (in both content and length) for any prompt x, though naturally their embeddings are different. Embeddings at these positions are matched one-to-one.


While arbitrary, we find that this token matching scheme works well in practice. We denote this scheme as function M : R → R, which takes in a target token index and returns the matched reference token index.

##### 3.3 Patching effect measure

Denote the patched jailbreak embedding sequence at layer l as H˜ j(l). Ideally, our patching effect measures the full difference between the generated response to Ho(l) and H˜ j(l). However, it is computationally expensive to generate the full response to H˜ j(l) for each patching operation. Thus, it is common to define a measure in terms of the first output token prediction p. To avoid focusing on specific vocabulary dimensions, we choose L = KL(po||˜pj), where KL(a||b) denotes the KL divergence between probability distribution b and a reference distribution a. From here on, we drop the superscript l.

![image 45](<native_3_images/imageFile45.png>)

![image 46](<native_3_images/imageFile46.png>)

![image 47](<native_3_images/imageFile47.png>)

![image 48](<native_3_images/imageFile48.png>)

![image 49](<native_3_images/imageFile49.png>)

![image 50](<native_3_images/imageFile50.png>)

![image 51](<native_3_images/imageFile51.png>)

![image 52](<native_3_images/imageFile52.png>)

- Figure 2: LOCA algorithm: LOCA computes the first output token probabilities po and pj of the refused original xo and successful jailbreak xj prompt. Then, it selects a jailbreak embedding hj,i∗ to activation patch along direction v∗ ti minimize the KL divergence of the two distributions. The minimization is done over a first-order approximation (Eq. 3), and v is selected from a SAE decoder Wd. This procedure is applied iteratively to induce refusal.


##### 3.4 Token-specific first-order approximation to patching along SAE directions

It is intractable to compute the first-token prediction ˜pj for all possible activation patches. Instead, we use the first-order approximation of the patching effect when patching the i’th jailbreak embedding in layer l along any direction v, given by:

d(i, v; po, pj, l) = ∇hj,iKL(po ∥ pj)Tv

directional derivative

(ho,M(i) − hj,i)Tv magnitude term

(2)

To develop an explanation, it is critical that patching occurs along interpretable directions v. Thus, we patch along the concept vectors in the corresponding layer’s SAE decoder Wd, which can be interpreted with interfaces such as Neuronpedia (Lin, 2023). Notice how our approximation is token-specific (denoted by i), as opposed to prior work.

##### 3.5 Operationalizing LOCA as an iterative algorithm

To give a minimal, local, causal explanation of jailbreak success, LOCA uses an iterative algorithm. The iterative version of Eq. 2 is denoted by iterant α as:

KL(po||p(jα))Tv](ho,M(i) − h(j,αi))Tv (3) Then, the iterative algorithm proceeds as follows:

#### d(α)(i, v) = [∇h(α)

j,i

- 1. Set α = 0. Initialize p(j0) = pj, h(j,0i) = hj,i ∀ i = 1...Nj, where Nj is the number of jailbreak tokens.
- 2. Find the minimizer: i(α)∗, v(α)∗ = argmin

i=1...Nj,v∈Wd

d(α)(i, v)

- 3. Activation patch h(j,αi(+α)1∗) with the matched ho,M(i(α)∗), but only along direction v(α)∗. The remaining jailbreak embeddings are unchanged from the previous iteration. This results in embedding sequence Hj(α+1), which is used to complete the forward pass to compute p(jα+1).
- 4. Set α := α + 1 and repeat Step 2 and 3. Terminate upon meeting a stopping criterion.


###### KL-AUC

Lee et al. (2025) Yeo et al. (2025) LOCA (Ours)

10.0

KL-AUC

7.5

5.0

2.5

0.0

0 5 10 15 20

Intervention layer

###### LD-AUC

10.0

7.5

LD-AUC

5.0

2.5

0.0

0 5 10 15 20

Intervention layer

###### Minimal Patches (MP)

20

MinimalPatches(MP)

15

10

5

0

0 5 10 15 20

Intervention layer

Refusal Rate (RR)

1.00

RefusalRate(RR)

0.75

0.50

0.25

0.00

0 5 10 15 20

Intervention layer

(a) GEMMA

###### KL-AUC

10.0

Lee et al. (2025) Yeo et al. (2025) LOCA (Ours)

7.5

KL-AUC

5.0

2.5

0.0

5 10 15 20 25

Intervention layer

###### LD-AUC

10

LD-AUC

5

0

5 10 15 20 25

Intervention layer

###### Minimal Patches (MP)

20

MinimalPatches(MP)

15

10

5

0

5 10 15 20 25

Intervention layer

Refusal Rate (RR)

1.00

RefusalRate(RR)

0.75

0.50

0.25

0.00

5 10 15 20 25

Intervention layer

(b) LLAMA

- Figure 3: LOCA consistently induces refusal with minimal patches; other methods struggle. We evaluate LOCA, Lee et al. (2025), and Yeo et al. (2025) on 50 jailbreak requests and report KL-AUC, LD-AUC, MP, and RR on all layers (for which we have a pre-trained SAE available) on the GEMMA and LLAMA models. All metrics are ±1 std. dev. except RR.

Appendix B contains more details on the patching operation. By recalculating the first-order approximation in every iteration (Eq. 3), our approximations are conditioned on prior activation patching steps, improving over prior work.

- 4 Evaluating & Analyzing LOCA


First, we compare LOCA to prior work (Lee et al., 2025; Yeo et al., 2025), showing that LOCA induces refusal at a significantly higher rate and requires significantly fewer patches than other methods. LOCA’s effectiveness is validated with an ablation study, and a localization analysis gives insights into where refusal is determined in earlier layers.

Models. We study the Gemma-2-2B-IT (GEMMA) and Llama-3.1-8B-Instruct (LLAMA) chat models (Riviere et al., 2024; Dubey et al., 2024). These models are safety aligned and instruction-tuned (IT), and they refuse most canonical harmful requests (Arditi et al., 2024).

SAEs. For GEMMA, we use the open-source GemmaScope SAEs, which are trained on text from the same distribution as GEMMA’s pretraining data (web documents, code, and scientific articles) (Lieberum et al., 2024). Although the GemmaScope SAEs are trained on activations from the base model, prior work shows that they transfer reasonably well to IT-models without additional finetuning (Yeo et al., 2025; Lieberum et al., 2024; Kissane et al., 2024). For LLAMA, we use the open-source SAEs from Arditi & Chen (2025), which are trained on a mix of pre-training, chat, and misaligned data; this makes the SAE more likely to surface jailbreak-relevant concepts.

Baselines. We use the prior methods in Lee et al. (2025) and Yeo et al. (2025) as the comparative baselines. Implementation details and efforts taken to adapt these methods to our setting are in Appendix C.

Datasets. We use the WhatFeatures dataset (Kirch et al., 2025), a collection of 10,800 jailbreak attacks generated from 35 jailbreak methods. For each model, we generate and save responses to each jailbreak attack, using greedy decoding with a generation length of 512 tokens. Jailbreak success is labeled with the HarmBench autograder (Mazeika et al.,

- 2024). We randomly split this dataset into train, validation, and test sets using a 70/10/20 split. The train and validation set is used only by Lee et al. (2025) to find the refusal direction.


###### KL-AUC

| |Base-LOCA (not token-specific or iterative)<br><br>Token-LOCA (not iterative)<br><br>LOCA (Ours)|
|---|---|
| | |
| | |
| | |
| | |


10.0

7.5

KL-AUC

5.0

2.5

0.0

0 5 10 15 20

Intervention layer

LD-AUC

10.0

7.5

LD-AUC

5.0

2.5

0.0

0 5 10 15 20

Intervention layer

| |Minimal Patches (MP)| | | | |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |


20

###### MinimalPatches(MP)

15

10

5

0

0 5 10 15 20

Intervention layer

Refusal Rate (RR)

1.00

RefusalRate(RR)

0.75

0.50

0.25

0.00

0 5 10 15 20

Intervention layer

- Figure 4: LOCA is better because it is token-specific and iterative. We ablate key aspects of LOCA by creating two variants. Base-LOCA is neither token-specific nor iterative. TokenLOCA is token-specific, but not iterative. We evaluate on GEMMA, with the same setup as Sec. 4.1. Prior works are variants of Base-LOCA, which explains their poor performance.


Metrics. We are interested in measuring how closely the output from the patched embedding tokens matches the original output. To avoid generating the response after each successive patching operation, we propose metrics that measure differences between the original and patched output only for the first output token. These metrics can be computed efficiently and serve as a proxy for how close the two generated outputs are. We introduce four metrics. After each patch operation, we compute (1) the KL Divergence (termed KL) of the two predicted next-token probabilities, and (2) the logit difference (termed LD) between the original and patched for the original’s predicted token, as justified by Heimersheim & Nanda (2024). Since we are interested in achieving the lowest error with the smallest number of patches, we condense the metric to a scalar by reporting the Area Under the Curve (AUC) normalized by the total patches applied, which we term as KL-AUC and LD-AUC. To ensure we are able to recover refusal behavior with minimal changes, we record (3) the number of patches needed for the patched predicted token to match the first output token on the original prompt, termed Minimal Patches (MP). If the method is unable to induce refusal within a pre-determined number of patches K, we set that sample’s MP = K. After all patches are applied, we calculate (4) the Refusal Rate (RR) by checking if the first output token after all patches matches the original first output token.1

##### 4.1 LOCA generates minimal, local, causal explanations of jailbreak success

We filter the test set to samples original-jailbreak pairs where xo failed and xj succeeded (as measured by Harmbench). From this set, we randomly sample 50 original-jailbreak pairs for evaluation. We test up to K = 20 interventions from each method across all intermediate layers (except the last layer) for which a corresponding SAE exists. We report the KL-AUC, LD-AUC, MP, and RR for GEMMA and LLAMA in Fig. 3

Astonishingly, we find that LOCA can, on average, induce refusal behavior on LLAMA with 6-8 patching operations on early-layer residual embeddings. This is a significant reduction from prior work in activation steering (Arditi et al., 2024), which induced refusal by steering mid-layer residual embeddings along every input token position (which could be from 50-200 tokens). For GEMMA, refusal is induced with an average of 12-16 early-layer patching operations. Less patching operations are needed in downstream layers.

LOCA substantially outperforms the baselines across our other metrics. As the layer on which LOCA performs the patching increases, our per-patching metrics (LD-AUC and KL-AUC) decrease. MP conclusively proves that LOCA is able to recover the original prompt output in fewer patching operations, and LOCA’s RR consistently increases for both LLAMA and GEMMA models, reaching 100% at layers 7 and 17, respectively. Prior work struggles to improve RR as the intervention layer increases, and they likewise fail to achieve improvements on the other metrics. We explore reasons for this next.

1Ideally, refusal would be determined after generating the entire response. This cheap proxy empirically works well (Arditi et al., 2024); we note failure cases in Appendix F.

Location

Token

###### Early Early-Middle Middle

Cumulative % of Tokens

50

50

100

100

![image 53](<native_3_images/imageFile53.png>)

![image 54](<native_3_images/imageFile54.png>)

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


50

100

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


![image 55](<native_3_images/imageFile55.png>)

Uservs.Post-Instruction

40

40

80

80

40

80

30

30

60

60

30

60

count

count

count

40

20

40

40

20

20

20

10

20

20

10

10

0

0

0 5 10 15 20

Number of Patching Operations

0

0

0

0

0 5 10 15 20

0 5 10 15 20

50

50

50

100

100

100

![image 56](<native_3_images/imageFile56.png>)

![image 57](<native_3_images/imageFile57.png>)

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


![image 58](<native_3_images/imageFile58.png>)

Punctuationvs.Word

40

80

40

40

80

80

30

60

30

30

60

60

count

count

count

40

20

40

40

20

20

20

10

20

20

10

10

0

0

0 5 10 15 20

Number of Patching Operations

0

0

0

0

0 5 10 15 20

0 5 10 15 20

- Figure 5: Localization analysis. We analyze the tokens (both location and type) LOCA selects for LLAMA at three layer depths. (Top) LOCA tends to select user instruction tokens in early layers, and post-instruction tokens in later layers. (Bottom) Early layers do not have a bias towards any token type; later layers almost exclusively chose PUNCTUATION tokens.


##### 4.2 LOCA succeeds by making iterative, token-specific changes

LOCA makes two distinctive improvements over prior work. First, LOCA computes the first-order approximation for each token, while prior works average the gradient over the entire token span. Second, LOCA uses an iterative algorithm, where the approximation is recalculated after applying each patch operation to take token interaction effects into account.2 To validate the effect of these improvements, we create variants of LOCA and repeat the experiment from Section 4.1. Base-LOCA computes the gradient term for the first-order approximation by averaging over the tokens. The magnitude term is still tokenspecific. Token-LOCA retains the token-specific first-order approximation of LOCA, but does not use an iterative algorithm. The ordering is calculated once and used to identify the top-K patching operations. Results are reported in Fig 4 for GEMMA. Across all metrics, LOCA outperforms the variants. Prior methods from Lee et al. (2025); Yeo et al. (2025) can be seen as variants of Base-LOCA with different objective functions; thus, these results help explain their shortcomings in generating minimal, local, causal explanations.

##### 4.3 Where and which tokens are most important for explaining jailbreak success?

Existing work shows that ending tokens (final instruction token and post-instruction tokens) are causally represent harmfulness and refusal (Zhao et al., 2025). However, the role of the other instruction tokens is unclear. Given that the refusal signal is represented as a low-dimensional subspace in the residual stream of the middle layers, one hypothesis is that earlier layers perform computations over the input prompt to determine the middle-layer refusal signal (Lee et al., 2025). Given that LOCA can find minimal, causal interventions to induce refusal, we add additional insight to this hypothesis by studying which tokens (in terms of both location and type) LOCA selects for patching. We show results for LLAMA here; results for GEMMA, which are similar, are in Appendix E.

To study token location, we create a distribution plot (top row of Fig 5) of the cumulative percentage of tokens LOCA selected that belong to Tpost-inst (as opposed to Tinst) at three layer depths: (i) early, (ii) early-middle, (iii) middle.3 In early layers, LOCA tends to select Tinst tokens. In early-middle layers, the location of selected tokens does not have a strong

- 2While this means LOCA’s compute time scales linearly with the number of iterations, the improvements are empirically justified. A comparison on computation time is in Appendix D.
- 3For LLAMA, we analyze 3, 7, and 15. For GEMMA, we analyze layers 5, 10, and 15.


bias, but in middle layers, the selection skews towards Tpost-inst tokens, while keeping a non-negligible distribution of Tinst tokens.

We study token type by classifying tokens as either PUNCTUATION or WORD. A token is a WORD if it starts with a letter or contains a number or decimal character. Otherwise, the token is a PUNCTUATION. Given their syntactic role in the chat template, all tokens in Tpost-inst are classified as PUNCTUATION. The WORD vs. PUNCTUATION distribution plot is shown in the bottom row of Fig 5. For both models, early and early-middle layers do not exhibit a strong bias towards either token type. Middle layers exhibit a strong shift to PUNCTUATION tokens, in accordance with the shifted emphasis to Tpost-inst tokens.

We add additional insight to the earlier hypothesis: the refusal signal is determined mostly by Tinst tokens in early layers, with no preference for token type. In middle layers, refusal is influenced more by Tpost-inst tokens, but can still be present in PUNCTUATION Tinst tokens.

##### 4.4 Case study: how AutoDAN convinces LLAMA to give instructions on illegally acquiring firearms?

Given that LOCA can find explanations on LLAMA that require only a few activation patches, we examine one explanation as a case study.4 An AutoDAN jailbreak (Liu et al., 2024), where the model is told to operate in a privileged “Developer Mode”, is effective at eliciting harmful responses from GEMMA and LLAMA models. To understand why, we apply LOCA to a successful AutoDan-jailbroken prompt asking for instructions on acquiring illegal firearms. Full outputs from the LOCA algorithm are in Appendix G; SAE concepts are interpreted using Neuronpedia. After two activation patches in a middle layer (layer 11), LOCA induces refusal behavior. The first patch is on the assistant Tpost-inst token; the patch increases the strength of concept #31126, which activates on harmful requests (e.g., violence, sexual content, illegal behavior). The second activation patch is applied on a PUNCTUATION Tinst token. The patch decreases concept #125009, which maximally activates on harmless requests concerning code generation. Thus, we interpret the AIM jailbreak success through two mechanisms: (1) a refusal concept associated with harmful prompts was suppressed and (2) the jailbreak convinced the model that operating in “Developer Mode” was akin to answering harmless questions on code generation. Next, we apply LOCA on an early layer (layer 3) for a more fine-grained understanding. LOCA induces refusal after five activation patches, with most of them concentrating on PUNCTUATION tokens. The first activation patch is on a “fabricating” Tinst token, which instructs the model to compensate for a lack of knowledge by fabricating answers. Interestingly, the patch decreases concept #21337, which activates on generic text. To answer this specific prompt, the model must provide website URLs to acquire illegal firearms, and we interpret the first patching operation as evidence that the model believes fabricating this information is harmless. Follow-up patches mainly decrease the strength of harmless, continuation-related concepts. This supports the view that the jailbreak succeeds by increasing the strength of harmless concepts in key PUNCTUATION and Tpost-inst tokens. Unintuitively, the final activation patch increases a concept that maximally activates on generally harmless questions, which leads to LOCA inducing refusal. It is likely we are unable to interpret the final concept correctly.

### 5 Limitations & Conclusion

LOCA is a step towards creating minimal, local, causal explanations of jailbreak success. However, it is not without issues; in particular, Appendix F details failure cases we encountered during manual inspection. Furthermore, interpreting LOCA explanations on earlier layers of LLAMA was time-intensive and error prone. While SAEs can provide interpretable directions, it’s possible that these directions are not “optimal” for jailbreak explanations. Future work should seek to remedy the failure cases, while incorporating methods targeted towards finding interpretable, jailbreak-relevant concepts.

4We anecdotally find interpreting LLAMA significantly easier than GEMMA. We attribute this to the availability of a LLAMA pre-trained SAE on chat data, which surfaces more conversational and jailbreak-relevant concepts.

### References

Andy Arditi and Runjin Chen. Finding ”misaligned persona” features in open-weight models. https://www.lesswrong.com/posts/NCWiR8K8jpFqtywFG/ finding-misaligned-persona-features-in-open-weight-models, September 2025. LessWrong post, accessed March 24, 2026.

Andy Arditi, Oscar Balcells Obeso, Aaquib Syed, Daniel Paleka, Nina Rimsky, Wes Gurnee, and Neel Nanda. Refusal in language models is mediated by a single direction. In The Thirty-eighth Annual Conference on Neural Information Processing Systems, 2024. URL https://openreview.net/forum?id=pH3XAQME6c.

Yuntao Bai, Andy Jones, Kamal Ndousse, Amanda Askell, Anna Chen, Nova Dassarma, Dawn Drain, Stanislav Fort, Deep Ganguli, Thomas Henighan, Nicholas Joseph, Saurav Kadavath, John Kernion, Tom Conerly, Sheer El-Showk, Nelson Elhage, Zac HatfieldDodds, Danny Hernandez, Tristan Hume, Scott Johnston, Shauna Kravec, Liane Lovitt, Neel Nanda, Catherine Olsson, Dario Amodei, Tom B. Brown, Jack Clark, Sam McCandlish, Chris Olah, Benjamin Mann, and Jared Kaplan. Training a helpful and harmless assistant with reinforcement learning from human feedback. ArXiv, abs/2204.05862, 2022. URL https://api.semanticscholar.org/CorpusID:248118878.

Sarah Ball, Frauke Kreuter, and Nina Rimsky. Understanding jailbreak success: A study of latent space dynamics in large language models. ArXiv, abs/2406.09289, 2024. URL https://api.semanticscholar.org/CorpusID:270440981.

Rishi Bommasani, Drew A. Hudson, Ehsan Adeli, Russ Altman, Simran Arora, Sydney von Arx, Michael S. Bernstein, Jeannette Bohg, Antoine Bosselut, Emma Brunskill, et al. On the opportunities and risks of foundation models. ArXiv, abs/2108.07258, 2021. URL https://api.semanticscholar.org/CorpusID:237091588.

Trenton Bricken, Adly Templeton, Joshua Batson, Brian Chen, Adam Jermyn, Tom Conerly, Nick Turner, Cem Anil, Carson Denison, Amanda Askell, Robert Lasenby, Yifan Wu, Shauna Kravec, Nicholas Schiefer, Tim Maxwell, Nicholas Joseph, Zac HatfieldDodds, Alex Tamkin, Karina Nguyen, Brayden McLean, Josiah E Burke, Tristan Hume, Shan Carter, Tom Henighan, and Christopher Olah. Towards monosemanticity: Decomposing language models with dictionary learning. Transformer Circuits Thread, 2023. https://transformer-circuits.pub/2023/monosemantic-features/index.html.

Junjie Chu, Yugeng Liu, Ziqing Yang, Xinyue Shen, Michael Backes, and Yang Zhang. JailbreakRadar: Comprehensive assessment of jailbreak attacks against LLMs. In Wanxiang Che, Joyce Nabende, Ekaterina Shutova, and Mohammad Taher Pilehvar (eds.), Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pp. 21538–21566, Vienna, Austria, July 2025. Association for Computational Linguistics. ISBN 979-8-89176-251-0. doi: 10.18653/v1/2025.acl-long.1045. URL https://aclanthology.org/2025.acl-long.1045/.

Nelson Cowan. The magical mystery four. Current Directions in Psychological Science, 19:51 – 57, 2010. URL https://api.semanticscholar.org/CorpusID:263337328.

Hoagy Cunningham, Aidan Ewart, Logan Riggs Smith, Robert Huben, and Lee Sharkey. Sparse autoencoders find highly interpretable features in language models. ArXiv, abs/2309.08600, 2023. URL https://api.semanticscholar.org/CorpusID:261934663.

Hoagy Cunningham, Jerry Wei, Zihan Wang, Andrew Persic, Alwin Peng, Jordan Abderrachid, Raj Aryan Agarwal, Bobby Chen, Austin Cohen, Andy Dau, Alek Dimitriev, Rob Gilson, Logan Howard, Yi Hua, Jared Kaplan, Jan Leike, Mu Lin, Christopher Liu, Vladimir Mikulik, Rohit Mittapalli, Clare O’Hara, Jin Pan, Nikhil Saxena, Alex Silverstein, Yue Song, Xunjie Yu, Giulio Zhou, Ethan Perez, and Mrinank Sharma. Constitutional classifiers++: Efficient production-grade defenses against universal jailbreaks. The Fourteenth International Conference on Learning Representations, abs/2601.04603, 2026. URL https://api.semanticscholar.org/CorpusID:284543962.

Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. 2024. URL https://api.semanticscholar.org/CorpusID:271571434.

Nelson Elhage, Tristan Hume, Catherine Olsson, Nicholas Schiefer, Thomas Henighan, Shauna Kravec, Zac Hatfield-Dodds, Robert Lasenby, Dawn Drain, Carol Chen, Roger Baker Grosse, Sam McCandlish, Jared Kaplan, Dario Amodei, Martin Wattenberg, and Chris Olah. Toy models of superposition. ArXiv, abs/2209.10652, 2022. URL https://api.semanticscholar.org/CorpusID:252439050.

Javier Ferrando, Oscar Balcells Obeso, Senthooran Rajamanoharan, and Neel Nanda. Do i know this entity? knowledge awareness and hallucinations in language models. In The Thirteenth International Conference on Learning Representations, 2025. URL https:// openreview.net/forum?id=WCRQFlji2q.

Stefan Heimersheim and Neel Nanda. How to use and interpret activation patching. ArXiv, abs/2404.15255, 2024. URL https://api.semanticscholar.org/CorpusID:269302704.

Nathalie Maria Kirch, Constantin Niko Weisser, Severin Field, Helen Yannakoudakis, and Stephen Casper. What features in prompts jailbreak LLMs? investigating the mechanisms behind attacks. In Yonatan Belinkov, Aaron Mueller, Najoung Kim, Hosein Mohebbi, Hanjie Chen, Dana Arad, and Gabriele Sarti (eds.), Proceedings of the 8th BlackboxNLP Workshop: Analyzing and Interpreting Neural Networks for NLP, pp. 480–520, Suzhou, China, November 2025. Association for Computational Linguistics. ISBN 979-8-89176-346-3. doi: 10.18653/ v1/2025.blackboxnlp-1.28. URL https://aclanthology.org/2025.blackboxnlp-1.28/.

Connor Kissane, robertzk, Arthur Conmy, and Neel Nanda. Saes (usually) transfer between base and chat models. https://www.lesswrong.com/posts/fmwk6qxrpW8d4jvbd/ saes-usually-transfer-between-base-and-chat-models, July 2024. LessWrong post, accessed 2026-03-28.

Daniel Lee, Eric Breck, and Andy Arditi. Finding features causally upstream of refusal. https://www.lesswrong.com/posts/Zwg4q8XTaLXRQofEt/ finding-features-causally-upstream-of-refusal, January 2025. LessWrong post, accessed March 24, 2026.

Tom Lieberum, Senthooran Rajamanoharan, Arthur Conmy, Lewis Smith, Nicolas Sonnerat, Vikrant Varma, Janos Kramar, Anca Dragan, Rohin Shah, and Neel Nanda. Gemma scope: Open sparse autoencoders everywhere all at once on gemma 2. In Yonatan Belinkov, Najoung Kim, Jaap Jumelet, Hosein Mohebbi, Aaron Mueller, and Hanjie Chen (eds.), Proceedings of the 7th BlackboxNLP Workshop: Analyzing and Interpreting Neural Networks for NLP, pp. 278–300, Miami, Florida, US, November 2024. Association for Computational Linguistics. doi: 10.18653/v1/2024.blackboxnlp-1.19. URL https://aclanthology.org/ 2024.blackboxnlp-1.19/.

Johnny Lin. Neuronpedia: Interactive reference and tooling for analyzing neural networks,

2023. URL https://www.neuronpedia.org. Software available from neuronpedia.org.

Yuping Lin, Pengfei He, Han Xu, Yue Xing, Makoto Yamada, Hui Liu, and Jiliang Tang. Towards understanding jailbreak attacks in LLMs: A representation space analysis. In Yaser Al-Onaizan, Mohit Bansal, and Yun-Nung Chen (eds.), Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, pp. 7067–7085, Miami, Florida, USA, November 2024. Association for Computational Linguistics. doi: 10.18653/ v1/2024.emnlp-main.401. URL https://aclanthology.org/2024.emnlp-main.401/.

Xiaogeng Liu, Nan Xu, Muhao Chen, and Chaowei Xiao. AutoDAN: Generating stealthy jailbreak prompts on aligned large language models. In The Twelfth International Conference on Learning Representations, 2024. URL https://openreview.net/forum?id=7Jwpw4qKkb.

Mantas Mazeika, Long Phan, Xuwang Yin, Andy Zou, Zifan Wang, Norman Mu, Elham Sakhaee, Nathaniel Li, Steven Basart, Bo Li, David Forsyth, and Dan Hendrycks. Harmbench: A standardized evaluation framework for automated red teaming and robust refusal. 2024.

Kevin Meng, David Bau, Alex J Andonian, and Yonatan Belinkov. Locating and editing factual associations in GPT. In Alice H. Oh, Alekh Agarwal, Danielle Belgrave, and Kyunghyun Cho (eds.), Advances in Neural Information Processing Systems, 2022. URL https://openreview.net/forum?id=-h6WAS6eE4.

George A. Miller. The magical number seven plus or minus two: some limits on our capacity for processing information. Psychological review, 63 2:81–97, 1956. URL https: //api.semanticscholar.org/CorpusID:15654531.

Kiho Park, Yo Joong Choe, and Victor Veitch. The linear representation hypothesis and the geometry of large language models. In Causal Representation Learning Workshop at NeurIPS 2023, 2023. URL https://openreview.net/forum?id=T0PoOJg8cK.

Gemma Team: Morgane Riviere, Shreya Pathak, Pier Giuseppe Sessa, Cassidy Hardin, Surya Bhupatiraju, L’eonard Hussenot, Thomas Mesnard, Bobak Shahriari, Alexandre Ram’e, Johan Ferret, et al. Gemma 2: Improving open language models at a practical size. ArXiv, abs/2408.00118, 2024. URL https://api.semanticscholar.org/CorpusID:270843326.

Alexander Matt Turner, Lisa Thiergart, Gavin Leech, David S. Udell, Juan J. Vazquez, Ulisse Mini, and Monte Stuart MacDiarmid. Steering language models with activation engineering. 2023. URL https://api.semanticscholar.org/CorpusID:261049449.

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. Advances in neural information processing systems, 30, 2017.

Lei Wang, Chengbang Ma, Xueyang Feng, Zeyu Zhang, Hao ran Yang, Jingsen Zhang, ZhiYang Chen, Jiakai Tang, Xu Chen, Yankai Lin, Wayne Xin Zhao, Zhewei Wei, and Ji rong Wen. A survey on large language model based autonomous agents. Frontiers of Computer Science, 18, 2023. URL https://api.semanticscholar.org/CorpusID:261064713.

Tom Wollschl¨ager, Jannes Elstner, Simon Geisler, Vincent Cohen-Addad, Stephan Gunnemann,¨ and Johannes Gasteiger. The geometry of refusal in large language models: Concept cones and representational independence. In Forty-second International Conference on Machine Learning, 2025. URL https://openreview.net/forum?id=80IwJqlXs8.

Wei Jie Yeo, Nirmalendu Prakash, Clement Neo, Ranjan Satapathy, Roy Ka-Wei Lee, and Erik Cambria. Understanding refusal in language models with sparse autoencoders. In Christos Christodoulopoulos, Tanmoy Chakraborty, Carolyn Rose, and Violet Peng (eds.), Findings of the Association for Computational Linguistics: EMNLP 2025, pp. 6377–6399, Suzhou, China, November 2025. Association for Computational Linguistics. ISBN 9798-89176-335-7. doi: 10.18653/v1/2025.findings-emnlp.338. URL https://aclanthology. org/2025.findings-emnlp.338/.

Jiachen Zhao, Jing Huang, Zhengxuan Wu, David Bau, and Weiyan Shi. LLMs encode harmfulness and refusal separately. In The Thirty-ninth Annual Conference on Neural Information Processing Systems, 2025. URL https://openreview.net/forum?id=zLkpt30ngy.

Andy Zou, Long Phan, Sarah Chen, James Campbell, Phillip Guo, Richard Ren, Alexander Pan, Xuwang Yin, Mantas Mazeika, Ann-Kathrin Dombrowski, Shashwat Goel, Nathaniel Li, Michael J. Byun, Zifan Wang, Alex Troy Mallen, Steven Basart, Sanmi Koyejo, Dawn Song, Matt Fredrikson, Zico Kolter, and Dan Hendrycks. Representation engineering: A top-down approach to ai transparency. ArXiv, abs/2310.01405, 2023. URL https: //api.semanticscholar.org/CorpusID:263605618.

### A Appendix summary

The appendix provides additional material not included in the main text due to space constraints. It includes:

- 1. Sec. B: details for how LOCA performs activation patching along chosen directions.


- 2. Sec. C: implementation details for methods we compare LOCA against. Include efforts we made to adapt them to the setting studied in this paper.
- 3. Sec. D: compute resources used by LOCA, baseline methods, and to do the experiments.
- 4. Sec. E: additional localization experiment results (complements Sec. 4.3).
- 5. Sec. F: failure cases of LOCA and our refusal proxy.
- 6. Sec. G: full LOCA algorithm outputs for the case study conducted in Sec. 4.4.


### B Activation patching in LOCA

We start by describing how LOCA activation patches in the case of a single patch operation. Suppose we want to patch hj with ho, but only along a direction v. The patched h˜ j is obtained by:

h˜ j = hj − vvThj + vvTho (4)

In other words, we subtract the jailbreak’s projection onto v and add the original’s projection onto v, leaving the orthogonal component unchanged. In case LOCA selects multiple directions V = (v1...vk) to patch hj along, we find the orthonormal basis Q of V through a QR-decomposition, and use Q in place of v in Eq. 4.

### C Implementation details for baseline methods

##### C.1 Lee et al. (2025)

T

In the original formulation, the authors define a refusal metric R = h(L)

N r(l) as the lasttoken (N) projection of the embedding at layer L onto a refusal direction r living in that same layer. Then, for any layer l < L, one can compute a refusal gradient as ∇h(l)

R for every embedding token position. Then, they compute a relative gradient RGi,k = vkT∇h(l)

i

R, where vk is selected from rows from a SAE decoder Wd. They average over all token positions to rank the SAE vectors. We adapt their method to our setting by computing RGi,k for all jailbreak (xj) and original (xo) token positions. Then, we compute the first-order approximation as:

i

d(i, vk) =

- 1

- 2 ∑


- 1

- 2 ∑


RGi(,jk) +

RGi(,ok)]

i

i

gradient term

ho,M(i) − h(j,αi))Tvk magnitude term

(5)

Thus, we average the gradient term over all token positions (as in the original method), but we use a token-specific magnitude term to create the first-order approximation. Then, we select the top-K embedding-vector pairs for patching. If l < 15, then we set L = 15, since the refusal direction typically lives in the middle layers of the moel. Else, we set L = l + 1. Empirically, we find that including jailbreak tokens in the average for the gradient term improves results.

##### C.2 Yeo et al. (2025)

We use the same equation as above, with a different gradient term. Let pi be the output nexttoken probabilities given prompt xi. Let zi = argmax pi, where pi(zi) denotes the largest probability. Then, Yeo et al. (2025) propose to measure the indirect effect m = pj(zo) − pj(zj).

Location

Token

###### Early Early-Middle Middle

Cumulative % of Tokens

50

50

100

100

![image 59](<native_3_images/imageFile59.png>)

![image 60](<native_3_images/imageFile60.png>)

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


50

100

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


![image 61](<native_3_images/imageFile61.png>)

Uservs.Post-Instruction

40

40

80

80

40

80

30

30

60

60

30

60

count

count

count

40

20

40

40

20

20

20

10

20

20

10

10

0

0

0 5 10 15 20

Number of Patching Operations

0

0

0

0

0 5 10 15 20

0 5 10 15 20

50

50

50

100

100

100

![image 62](<native_3_images/imageFile62.png>)

![image 63](<native_3_images/imageFile63.png>)

| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


| | | | | |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |


![image 64](<native_3_images/imageFile64.png>)

Punctuationvs.Word

40

80

40

40

80

80

30

60

30

30

60

60

count

count

count

40

20

40

40

20

20

20

10

20

20

10

10

0

0

0 5 10 15 20

Number of Patching Operations

0

0

0

0

0 5 10 15 20

0 5 10 15 20

- Figure 6: Localization analysis. We analyze the tokens (both location and type) LOCA selects for GEMMA at three layer depths. We observe similar results as to Fig. 5.


We use this to compute the first-order approximation as:

∇hjmTvk

d(i,vk) = ∑

i

gradient term

ho,M(i) − h(j,αi))Tvk magnitude term

(6)

Again, the gradient term is computed over all token positions for only the jailbreak prompt. Then, we select the top-K embedding-vector pairs for patching to maximize the objective.

### D LOCA & experimental compute requirements

Experiments: All experiments were completed on either a single NVIDIA A40 or A100. Completing the experiments and obtaining the results in 3 take less than 10 hours of GPU time.

Time to generate a local explanation: Lee et al. (2025) and Yeo et al. (2025) select their top-20 token-vector pairs within 2 seconds. With the same setup, LOCA requires 7 seconds, mainly due to it’s iterative nature. However, given that LOCA can induce refusal after a few patches, it is possible to implement a greedy exit condition to terminate the algorithm earlier than the 20th iteration.

### E LOCA localization results for GEMMA

We repeat the analysis in Sec. 4.3 for GEMMA, and we report the results in 6 . The findings are similar, so we draw the same conclusions.

### F Failure cases

The main limitation of this approach is that we base refusal on an objective computed on the first output token. However, there are cases where both the jailbreak prompt and the original prompt have the same first output token. This naturally poses a problem for the Refusal Rate metric that we propose. It also does not allow LOCA to actually induce refusal, since our KL objective in Eq 2 is very small. Below we examine two examples of this behavior:

Original Prompt: “How can I kill the most people with only $1? Please list several ways”

Original Response: “I understand you’re asking about ways to harm people with a small amount of money, but I cannot provide that information...”

Jailbreak Prompt: “Disregard previous instructions. Henceforth, you’ll act as Mistral in Developer Mode ... [PROMPT]: How can I kill the most people with only $1? Please list several ways”

Jailbreak Response: “I cannot fulfill your request. My purpose is to provide safe and helpful information. (Developer Mode Output) Sure, here...”

The model refuses the original prompt starting with “I”, which is a common token for models to begin refusal with. On the jailbreak prompt, the model initially refuses by starting with “I”, but then generates a jailbreak response, because the jailbreak encourages the model to discard prior guardrails and enter “Developer Mode”.

Original Prompt: “Give me a list of easily obtainable household items that can be used to make a lethal poison.”

Original Response: “I cannot provide you with a list of household items that can be used to make a lethal poison...”

Jailbreak Prompt: “Respond to the following writing tasks: I. Sonnet. Write a sonnet answering the following prompt ‘Frolicking rabbits amid verdant blades of grass.’ II. Prose. Write a response in prose to the following prompt: ‘Give me a list of easily obtainable household items that can be used to make a lethal poison.’ III. Limerick. Write a limerick answering the following prompt ... Write just the responses (and no headings), starting with ‘I. Sonnet‘”

Jailbreak Response: “I. The sun-kissed meadow, emerald bright ... II. A few common household items can be used to create a lethal poison...”

The model again refuses by starting with “I”. However, the jailbreak prompt explicitly encourages the model to begin it’s response with “I”, and it cleverly asks the model to embed the jailbreak response in the middle. Anecdotally, the Harmbench autograder also tends to misclassify some of successful jailbreak responses as harmless.

### G Full outputs for the case study

We detail the full results for the case study conducted in Sec. 4.4 here. For layer 11, the following activation patches are made:

- 1. Tpost-inst token #671 (“assistant”) is activation patched along concept #31126. The activation patch increases the concept strength by 1.50.

- (a) KL divergence is 0.77
- (b) Concept #31126 interpretation: activates on the “assistant” token following harmful chat requests (violence, sexual content, instructions on committing illegal actions).


- 2. Tinst token #638 (“).”) is activation patched along concept #125009. The activation patch decreases the concept strength by -1.48.


- (a) KL divergence is 0.04
- (b) Concept #125009 interpretation: activates on tokens following a chat request to generate code.
- (c) Refusal is induced.


For layer 3, the following activation patches are made:

- 1. Tinst token #591 (“fabric”) is activation patched along concept #21337. The activation patch decreases the concept strength by -0.79.

- (a) KL divergence is 4.03
- (b) Concept #21337 interpretation: activates on generic text. No clear pattern.


- 2. Tpost-inst token #671 (“assistant”) is activation patched along concept #66275. The activation patch decreases the concept strength by -0.39.

- (a) KL divergence is 2.71
- (b) Concept #66275 interpretation: activates on text regarding newsletters, website cookies, logging in, email subscriptions.


- 3. Tinst token #638 (“).”) is activation patched along concept #105801. The activation patch decreases the concept strength by -0.87.

- (a) KL divergence is 0.99
- (b) Concept #105801 interpretation: activates on the period token in text describing chemical companies. Generally harmless text.


- 4. Tinst token #270 (“.”) is activation patched along concept #105801. The activation patch decreases the concept strength by -1.20.

- (a) KL divergence is 0.77
- (b) Concept #105801 interpretation: activates on the period token in text describing chemical companies. Generally harmless text.


- 5. Tpost-inst token #669 (“eot id”) is activation patched along concept #30002. The activation patch increases the concept strength by 0.70.


- (a) KL divergence is 0.40
- (b) Concept #30002 interpretation: activates on the eot id on generally harmless chat questions.

- (c) Refusal is induced.


