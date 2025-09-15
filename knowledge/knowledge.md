# **LLM Performance Prediction Playbook: Languages, Tasks, and Models**

---

## **Introduction**

Large Language Models (LLMs) vary widely in how well they perform across different languages and tasks. The original playbook was brief; here we provide a comprehensive guide covering:

- Language scenarios
- Task types
- Model differences
- Evaluation metrics
- Step-by-step strategies (including direct lookup, extrapolation, and predictive modeling) to estimate performance in any scenario

This playbook includes:
- A full taxonomy of language/resource categories, task types, and LLM considerations
- Worked examples illustrating how to apply these guidelines

**Goal:** Ensure that for any given combination of language, task, and LLM, you have a method to predict performance or find relevant evidence.

---

## **Language Scenarios and Features**

Languages differ greatly in resource availability and similarity, which in turn affects LLM performance. We categorize languages into four broad groups and discuss key features for each:

### **1. High-Resource Languages**
- Examples: English, Chinese, Spanish, French, etc.
- Abundant data in LLM training corpora (e.g., GPT-3’s training data was over 90% English text)
- Direct evaluation data available in literature or benchmarks
- LLMs generally perform best on these languages due to extensive pre-training exposure

### **2. Mid-Resource Languages**
- Examples: Hindi, Swahili, Turkish
- Moderate web or corpus presence
- Decent LLM performance, but can lag behind high-resource languages
- Some evaluation results available (e.g., XTREME or XGLUE), but coverage is spottier
- Fine-tuning on multilingual data can significantly boost performance

### **3. Low-Resource Languages**
- Examples: Bengali, Amharic, Maori, etc.
- Very limited presence in pre-training corpora
- LLMs often struggle, showing noticeably lower generation quality or accuracy
- Direct evaluation evidence is rare; performance must often be extrapolated from similar languages or inferred via cross-lingual transfer
- Fine-tuned multilingual models may achieve non-zero performance, but zero-shot performance may be poor

### **4. Extremely Low-Resource or Unseen Languages**
- Examples: Endangered languages, obscure dialects, invented languages
- Virtually absent from training data
- LLMs have no direct knowledge; performance relies on character-level patterns or guesswork
- Typically, performance is very low, often gibberish or highly error-prone output
- No direct evidence exists; rely on predictive methods or analogies

---

## **Language Feature Mapping**

When extrapolating performance, consider key linguistic features and similarities:

- **Lexical and Subword Overlap:**
  - Does the target language share vocabulary or subword tokens with languages the model knows?
  - A high overlap (e.g., Spanish and Italian sharing many words or the Latin script) can improve performance
  - In fact, studies show that subword vocabulary overlap has a strong impact, often more than genetic language relatedness, on cross-lingual performance . If a low-resource language uses the same script and shares many roots with a high-resource language, the model is likely to do better than if it uses a completely distinct script or lexicon.

- **Typological or Structural Similarity:**
  - Languages that are linguistically similar (grammar, word order, etc.) to those in the training set have an advantage
  - Linguistic similarity correlates with cross-lingual transfer performance in many cases . For example, an LLM fine-tuned on German might transfer reasonably to Dutch (a related language) because of similar syntax and morphology
  - We can quantify similarity via metrics like typological features (e.g., from WALS or lang2vec) or genetic lineage. Greater similarity generally means the model’s learned representations can adapt more easily, yielding higher performance.

- **Presence in Pre-training Data:**
  - Check if the language (or its script) appears in the model’s pre-training
  - Many multilingual LLMs (like mBERT, XLM-R, GPT-4) were trained on dozens of languages. If the target language was included (even in small amounts), the model will at least have basic vocabulary and some understanding. If not included, performance will rely on indirect transfer
  - The “curse of multilinguality” is that adding many languages can dilute per-language capacity, but in general, inclusion at all is better than none. You may find data about the proportion of the language in the pre-training corpus – higher proportions typically correlate with better results.

- **Script and Tokenization:**
  - Languages sharing scripts benefit from shared tokens
  - If a language uses a unique script that the model hasn’t seen, it may struggle to even copy or output characters correctly
  - For instance, a Latin-alphabet LLM might handle Polish (Latn script) better than Khmer (unique script) if Khmer was not seen in training. In absence of training data, models sometimes try to transliterate into a known script or just output unknown tokens

**Tip:** Use these features to map a new language to similar ones with known performance. For totally unseen languages, look for any proxy (closest relative in the model), but expect rough outcomes.

---

## **Task Scenarios and Types**

Not all tasks are equal in the eyes of an LLM. An LLM might excel in one task but falter in another, especially when the task format or domain is unfamiliar. We break down task considerations into a taxonomy of task types and domain specificity:

### **Common NLP Task Types**
- **Generative tasks:**
  - Text generation (summarization, translation, open-ended Q&A, text completion, story generation, etc.)
  - These require the model to produce coherent text in the target language
  - Generative tasks in a foreign language are challenging; the model must master content and fluency in that language. If the model was fine-tuned on that generative task (e.g. an LLM fine-tuned for summarization), it might handle similar languages in zero-shot mode to some extent, but quality will drop for less seen languages
- **Discriminative tasks:**
  - Classification or structured output (sentiment analysis, NER, multiple-choice QA, etc.)
  - These often involve selecting from or labeling text rather than free generation
  - LLMs can often transfer better on these tasks because they rely on understanding content rather than producing full sentences. For example, zero-shot classification using an LLM’s embeddings or prompts can work in many languages if the model understands the text, even if its generation in that language is weak
- **Structured generation:**
  - Tasks like generating a SQL query from text or filling slots – consider how much language-specific knowledge that needs

### **Impact of Tasks on Cross-Lingual Transfer**
- Research shows that the ease of transfer varies by task . For instance, simple classification may transfer with minimal loss if the model grasps the concepts, whereas tasks requiring precise syntax (like parsing or grammatical error correction) are more sensitive to linguistic differences
- Keep this in mind: if the target task is very sensitive to word order or morphology, language differences play a larger role

### **Domain Specificity**
- **General-Domain vs. Domain-Specific Tasks:**
  - An LLM might have been trained or fine-tuned on a general domain (like news articles, Wikipedia text, or open web content). If you ask it to perform the task on a highly specialized domain (legal contracts, medical literature, scientific papers, etc.), performance can drop
  - Example: An LLM fine-tuned for generic summarization (news articles) might struggle with medical report summarization without additional training, due to unfamiliar jargon and discourse style
  - Domain-specific LLMs or fine-tunes are known to improve accuracy on their domain compared to generic LLMs .
  - If direct evidence exists for the task in that domain (say a benchmark of legal text summarization), use it. Often, however, direct evidence is available only for general domains or widely studied domains (like biomedical for some tasks). For other niche domains, you’ll need to extrapolate by assessing:
    - how different is the domain language from what the model has seen?
    - Does it require specialized knowledge (which the model may or may not have)?
    - As a rule, increased domain distance = decreased performance unless the LLM has been explicitly exposed to that domain
- **Task Format Familiarity:**
  - Consider whether the task format was part of the model’s training or instruction tuning
  - Modern LLMs (like ChatGPT, GPT-4) were instruction-tuned on a variety of tasks (summarization, translation, classification instructions, etc.) primarily in English
  - If the task is one of those (e.g., summarization or translation), the model knows the general idea of how to do it, which improves zero-shot performance even in other languages
  - However, if the task is unusual (e.g., “parse this sentence into logical form” or a brand-new game), and especially in another language, direct performance will be low because the model has neither seen the task in instructions nor examples in that language

**Summary:**
1. Identify the task type – generation vs classification – and gauge how heavily it relies on fluent target-language output vs just understanding
2. Identify the domain – is it the common domain the model was likely trained on, or a specialized one requiring extra knowledge?
3. Check if the model (or similar models) has been fine-tuned or evaluated on this task (especially in any language). If yes, that’s great evidence; if not, be cautious and lean on analogous cases.

---

## **LLM Model Considerations**

The specific model in question—its architecture, training data, size, and fine-tuning—will influence performance on a given language and task. Key factors include:

- **Multilingual Training vs. Monolingual:**
  - Some LLMs are explicitly multilingual (e.g. mBERT, XLM-R, mT5, BLOOM, GPT-4 to an extent) – they are trained on many languages, which usually enables cross-lingual abilities
  - Others are primarily English-centric (e.g. the original GPT-3 was heavily English-dominated ). If your model is multilingual by design, it likely can handle a variety of languages and has learned cross-lingual representations. If it’s monolingual or English-centric, any other language performance will rely on whatever minimal exposure happened or on subword-level generalization
  - Identify the model’s training scope: If the language is outside that scope (especially for smaller monolingual models), expect poor results or even gibberish output
- **Model Size and Architecture:**
  - Larger models often show better zero-shot generalization, including to other languages, than smaller ones
  - For example, GPT-3.5 vs GPT-4 on non-English tasks: GPT-4 is significantly stronger and more accurate in many cases . Increased parameters and training data give the model more capacity to capture multiple languages and complex patterns
  - However, architecture matters too – encoder-decoder models (like mT5) vs decoder-only (like GPT series) might have different strengths
  - Encoder-decoder models explicitly process input which can help in tasks like translation or summarization for unseen languages, while decoder-only rely on prompt conditioning
  - Also, models that included a translation objective or bilingual training (like the older XLM with translation language modeling) might have an edge in aligning representations across languages
  - In summary, bigger and more complex training schemes generally help multilingual performance, but they do not guarantee parity (disparities still remain across languages ).
- **Fine-Tuning and Instruction Tuning:**
  - Is the model fine-tuned on the task or instructions?
  - If you have a task-specific fine-tuned model (say, a model fine-tuned for summarization, or a version fine-tuned for multilingual tasks), that fine-tune might be limited to certain languages (e.g., an English summarization model will not magically summarize Chinese unless it was trained multilingually)
  - On the other hand, a multilingual fine-tuned model (like an mT5 trained on XL-Sum for dozens of languages) can perform that task in all training languages – and sometimes even transfer to similar languages not in training
  - Always clarify: is the query about a base model or a fine-tuned model? And was the fine-tuning multilingual?
  - Instruction-tuned LLMs (ChatGPT, etc.) are a special case of fine-tuning: they are trained to follow instructions and often on a variety of tasks. Typically, the instruction data is mostly in English (with some multilingual data if available)
  - Such models can often handle non-English instructions and output, but not as reliably as English
  - If the LLM is instruction-tuned, it likely knows the format of tasks (like “Summarize the above text”) and can attempt them in other languages
  - However, for less seen languages it might struggle to follow instructions or maintain output quality
  - Some instruction tuned models have explicit translations of prompts internally to English
  - Check model documentation for any notes on multilingual capabilities or known limitations. If none, assume instructions in English are best, and tasks in other languages might be treated as an implicit translation problem by the model
- **Zero-shot vs Few-shot:**
  - Even if not fine-tuned, many LLMs can be prompted with examples (few-shot learning)
  - If you truly have no direct data, consider that giving a few examples in the target language can dramatically improve performance on that task (if user context allows)
  - This playbook mainly focuses on predicting base capabilities, but remember this as an option
- **Known Benchmarks and Past Performance:**
  - Different models have known leaderboards or benchmarks
  - For instance, XLM-R was evaluated on the XTREME benchmark (covering XNLI, PAWS-X, POS tagging, etc. in multiple languages)
  - GPT-3.5/4 have MMLU (which includes some non-English knowledge questions)
  - mT5 and others have been benchmarked on TyDiQA, MLQA (QA datasets), etc.
  - Knowing these can give you direct evidence: e.g., “Model X achieved Y accuracy on task Z in language L.” If your scenario matches a known benchmark, you can directly cite that performance
  - We’ll discuss in the next section how to find and use such evidence. As a general rule of thumb, public leaderboards (e.g., WMT for translations, XGLUE for various tasks, KILT for knowledge tasks, etc.) are your friend for high and mid-resource languages
- **Fairness and Bias:**
  - A model performing poorly on certain languages raises fairness concerns
  - While outside the scope of performance prediction, it’s good to be aware that sometimes the objective isn’t just performance but ensuring no language is overly disadvantaged
  - Tools like LITMUS explicitly aim to help optimize for performance and fairness across languages

---

## **Metrics and Evaluation Criteria**

When gathering evidence or evaluating performance, it’s critical to understand the metrics used for the task, as they define “performance.” Always clarify what metric the performance is measured in, and use it consistently. Here’s a quick rundown of common metrics by task type and what to watch for:

- **Summarization Metrics:**
  - Typically uses overlap-based metrics like ROUGE (ROUGE-1, ROUGE-2, ROUGE-L) to measure content overlap between model summary and reference summary
  - Sometimes BLEU is also used (especially for non-English if using machine translated references)
  - Newer metrics like BERTScore or BLEURT might appear in literature
  - For summarization, higher ROUGE generally indicates better summary content coverage
  - Keep in mind that ROUGE scores for abstractive summarization are often in the teens or 20s (as seen in the XL-Sum results, ROUGE-2 ~15 for a good model ). If you see a percentage or score, note which ROUGE it is. When reporting, e.g., “ROUGE-2 = 12.5”, that’s meaningful to someone who knows summarization metrics. Also note if it’s an average over languages or a specific dataset
- **Translation Metrics:**
  - BLEU is classic for machine translation quality (0–100, where e.g. 30+ is decent for mid/high resource pairs; low-resource often much lower)
  - chrF, TER, METEOR, COMET might also be used
  - If direct evidence is from a WMT evaluation or similar, they’ll likely give BLEU. E.g., “Model achieved BLEU=25 on Spanish→English translation.”
  - For extrapolation, you might say “we expect BLEU to be low teens at best, given the resource constraints.” Remember translation BLEU can drastically drop for distant language pairs
- **Classification Metrics:**
  - Accuracy (for single-label), F1-score (especially for imbalanced or multi-label tasks), or Precision/Recall might be given
  - If it’s something like NER or QA, often F1 is reported (to account for partial correctness). E.g., “XLM-R achieves ~90% F1 on German NER”. If you find an exact number, use it; if not, you can say “expected accuracy in X range”
- **Knowledge/QA Metrics:**
  - For QA with exact answers, Exact Match (EM) and F1 are common (EM is strict correctness, F1 partial)
  - For multiple-choice QA, accuracy or sometimes an exam score percentile
  - For generative QA (free-form answer), sometimes BLEU or ROUGE vs reference, or human evaluation if open-ended
- **Other Tasks:**
  - If assessing something like reasoning or logic puzzles, there might not be a standard metric except accuracy/% correct
  - For generation tasks like story writing, often only human eval or qualitative criteria exist – those are hard to predict, so focus on whether the model can even perform the task logically
- **Human vs. Automated Eval:**
  - Note whether the performance is from automatic metrics or human judgment
  - LLMs might get moderate BLEU/ROUGE but humans might still prefer one model over another due to fluency
  - If a source provides human evaluation (e.g., “fluency score 4.5/5”), include that if relevant
  - But usually, you’ll be dealing with automatic metrics in a prediction context

**Tip:** Always cite the metric with the value and specify if it’s from automatic metrics or human judgment.

---

## **Strategy for Answering Performance Queries**

A step-by-step decision framework for predicting or retrieving LLM performance:

### **1. Check for Direct Evidence**
- **Goal:** Find if the exact (or very similar) combination has published results
- **Search Literature and Benchmarks:** Use academic papers (ACL, arXiv, etc.), leaderboards (PapersWithCode, WMT, GLUE/XGLUE, etc.), or model cards
  - Look for the specific model or a comparable model on the target task & language
  - For example:
    - If asked about GPT-3 on French summarization, search for any evaluation of GPT-3 (or GPT-3.5/4) on French tasks, or a paper on multilingual summarization including French
    - If about XLM-R on cross-lingual NER, check the XTREME benchmark paper or similar – XLM-R was likely evaluated on NER in multiple languages
    - Leverage the similarity: if the exact model isn’t evaluated, a similar model might have (e.g., if GPT-4 isn’t in literature yet for that task, maybe GPT-3.5 is, or a smaller model like BLOOM or mT5 is – those can give clues)
- **Use the Known Taxonomy:** For common tasks and high-resource languages, there’s a good chance of direct evidence. For specialized tasks or low-resource languages, evidence will be harder to find
- **What to do if found:** If you locate a source, extract the performance metrics. Ensure you note:
  - Which model (size/version) and any fine-tuning done
  - Dataset or benchmark used (so you know context)
  - The metric values
  - Example: “According to Hasan et al. (2021), an mT5-base model fine-tuned on XL-Sum achieved ROUGE-2 ≈15 on English and similar (~12–16) on various other languages .” If our query was about mT5 on Bengali summarization, we now have a direct reference (ROUGE-2 11.4 for Bengali in that table )
- **Presenting the answer:** If direct evidence is found, the final answer should directly state the performance with citation (if applicable) and possibly a brief interpretation
  - E.g., “Performance: Model X achieves 78% accuracy on Y task in Z language【source】.” The user may only care about the number, but it’s good to mention any conditions (like fine-tuned vs not, data size, etc., especially if comparing multiple results)

### **2. If No Direct Evidence, Use Analogy and Extrapolation**
- **Goal:** Infer the performance using the features and taxonomy we discussed
- **Leverage Similar Languages:** Identify a language that is present in the model’s known evaluations and is closest to the target language
  - This can be by family, script, or resource level
  - For instance, no result for XLM-R on Swahili sentiment analysis? Perhaps XLM-R on another Bantu language (if any in a benchmark) or on Swahili for a similar task (maybe NER or QA) exists
  - If XLM-R’s performance on Swahili NER is known and sentiment is similar difficulty, use that as a ballpark
  - If the language is unique but has a well-known similar one (e.g., Belarusian might not be tested, but Russian and Ukrainian are, and Belarusian lies between them and shares Cyrillic script), approximate performance as between those reference points
- **Account for Resource Level:** Adjust expectations based on resource disparities
  - If the closest evidence is for a higher-resource relative, and your target is lower-resource, assume the performance will be somewhat lower
  - You may not need a numeric formula, but qualitatively: e.g., “We didn’t find direct results for Marathi. However, for Hindi (a high-resource Indian language), the model scores 85% on task X【source】. Marathi has less training data exposure, so performance might be lower, perhaps in the 70–80% range.” If possible, mention the rationale: lack of data, some mutual intelligibility with Hindi might help but not fully, etc
- **Use Task Difficulty Clues:** Consider how hard the task is and how much it might degrade with language
  - Some tasks (like translation) degrade dramatically for low-resource languages; others (like basic classification) might hold up better
  - Use your knowledge or any cross-lingual studies: e.g., “Cross-lingual QA performance tends to drop ~10-20 points from English to a low-resource language in many benchmarks , so we might expect a similar drop here.” If you have any quantitative info from research (like “languages with <1M corpus tokens see a BLEU under 5 in zero-shot translation” – only use it if confident or you have a source)
- **Consider Model Attributes:** How strong is the model generally?
  - If it’s a state-of-the-art model (like GPT-4), even without direct evidence, you might say it’s expected to do relatively well due to its size and training (better than smaller models would)
  - If it’s a smaller or older model, be more conservative
  - Also mention if the model has known weaknesses: e.g., “Model X is known to struggle with non-Latin scripts, so Thai might be particularly challenging.”
- **Quality of Extrapolation:** Clearly mark these as estimates
  - Use words like “approximately,” “we expect,” “likely around X,” etc., rather than stating as fact
  - This manages user expectations. The playbook should encourage transparency about uncertainty when giving extrapolated performance

**Example of extrapolation reasoning:** Suppose no data on GPT-3 for summarizing legal documents in Korean. We break it down:
- GPT-3 was mainly English, little Korean data (so Korean is already a challenge though it likely has some Korean)
- Summarization is a task GPT-3 can do in English (with prompting or fine tune)
- Legal domain is very specialized; GPT-3 wasn’t fine-tuned on that domain
- Nearest analogy: GPT-3’s performance on, say, English legal summarization (maybe known via a case study?) or at least general Korean proficiency (maybe its translation ability in Korean, or QA in Korean from a benchmark)
- If we know GPT-3’s Korean ability is moderate, and summarization plus legal domain add difficulty, we conclude: likely poor performance
- We might answer: “No direct metrics found. Estimated: GPT-3 would likely struggle with Korean legal text summarization, possibly producing only very general summaries or losing key details, given the double challenge of a less-seen language and highly technical domain.” This is a qualitative answer; if a number is needed, one could say something like “we expect performance (e.g. ROUGE scores) to be significantly lower – perhaps well below what it achieves on English (which is X), possibly in the low single digits ROUGE-2.” The key is to back this with reasoning, not just a guess

### **3. Predictive Tools and Modeling (Litmus, etc.)**
- If rigorous estimation is needed and especially if multiple data points are available, consider using predictive modeling approaches:
- **LITMUS Predictor:** An existing tool developed by researchers (Microsoft Research) for projecting multilingual performance . It takes as input some training observations (i.e., known performance of a model on a task in a few languages with certain data sizes) and predicts performance in other languages
  - If you have access to LITMUS or similar:
    - Compile any known results for the model/task (perhaps performance on high-resource languages from which to extrapolate)
    - Input those into LITMUS to simulate how the model would do in target languages without direct data
    - LITMUS can handle ~100 languages and will give an estimate
  - Use the output to inform your answer
    - For instance: “Using LITMUS Predictor, given the model’s English and Spanish performance on this task, we project around 70% accuracy for Italian and 60% for Swahili with the current data regime.” (Cite if needed or at least mention it’s a projection)
- **Custom Prediction (if needed):** If LITMUS is not available for your specific case, you could create a simple predictive model yourself:
  - Features to include: language resource level (e.g., a numeric score for how much corpus or a rank of high/mid/low), language similarity indices (you can use something like the lang2vec features or simpler proxies like “same script as English or not”, “language family match with a fine-tuning language or not”), model size or known capacity, task type (maybe encode generative vs classification as a factor), and any known performance anchors (if you have performance for other languages, those can be training data points)
  - Approach: Perhaps start with a linear or heuristic model: e.g., “Base accuracy = English accuracy - penalty.” Penalties could be:
    -5 points if language not seen in pretraining
    -5 if script is novel
    -10 if domain is very specialized, etc
  - This is a rough heuristic method but can be informed by prior studies
  - More sophisticated: train a regression on a dataset of known results (if you have a table of results for multiple languages, tasks, models)
  - Caution: This requires some data to base on. If you have zero known points, then a purely intuition based formula is risky
  - However, sometimes papers provide aggregate analyses (like “XLM-R’s average drop from English to low-resource languages on POS tagging is Y your model. ”) – those can inform
  - If you do create such a predictor, document your process
  - In the playbook context, you might list some templates like: “If language not seen, multiply expected performance by ~0.5. If low-resource but seen, maybe ~0.8. If task is generation, apply another factor,” etc. These are arbitrary here, but the idea is to give a template formula. Keep it simple enough to explain
- **When to use predictive modeling:** Usually if the stakes are high (e.g., you need to convince with numbers, or decide where to invest data collection)
  - If a user just needs a general idea, the earlier analogy method suffices
  - But if they want to know specific performance values (maybe to compare models or to decide if a model meets a requirement), a predictor adds confidence
  - Mention any uncertainty or error bars if known – prediction is not exact

### **4. Providing the Answer**
- **Goal:** Formulate the answer clearly
- **Start by stating the expected performance in a concise statement, then elaborate:**
  - If evidence: “Model X gets F1 = 0.82 on Y task in Z language【source】.” Maybe add, “(This is on the ABC dataset, which is a standard benchmark.)” Then you might add one sentence interpreting it (e.g., “This is only slightly lower than its English performance, indicating strong cross-lingual ability.”)
  - If extrapolated: “We estimate the performance to be around X (e.g., ~60% accuracy or ROUGE-2 in the low teens).” Then, “This is based on the model’s results on similar languages/ tasks, considering that ... (briefly recap reasoning: ‘since the language is low-resource and not seen in training, we expect a significant drop from English performance’).”
- **Be sure to mention the metric name with any number, as emphasized earlier**
- **If using a predictor or heuristic model, say so:** “(Projected via the LITMUS tool)” or “(approximation based on known performances)” to differentiate from hard evidence
- **Cover all parts of the question:** If the query was multi-faceted (language, task, model), ensure you address each
  - For example, a question might implicitly be “how will model A perform vs model B on language L task T?” In that case, compare both in your answer, possibly pointing out that one has better training for that scenario
- **If uncertainty is high, it’s better to be honest about it.** It’s acceptable to say something like, “Overall, the model is likely to perform poorly, and without testing we can’t provide a precise number – our best guess would be below 50% accuracy.” The user will appreciate an informed guess with caveats over false precision

---

## **Worked Examples**

Let’s apply this playbook to a few scenarios to illustrate how to handle them:

### **Example 1: High-Resource Language, Known Task**
- **Scenario:** “What is the performance of XLM-R on Named Entity Recognition (NER) for German?”
- **Analysis:** German is high-resource (present in training data and similar to English in alphabet). NER is a classification task (sequence labeling). XLM-R is a multilingual model known to perform well on cross-lingual understanding tasks. This combination is likely covered in a benchmark (German is included in the CoNLL or WikiAnn NER datasets)
- **Direct Evidence Search:** We recall the XTREME benchmark (Hu et al. 2020) evaluated XLM-R on NER (WikiAnn) across languages. Indeed, XLM-R-large achieved around 90% F1 on German WikiAnn NER (hypothetical citation for illustration)
- **Answer Construction:**
  - “XLM-R (large) achieves approximately 90% F1 on German NER (WikiAnn benchmark), which is on par with its English NER performance【source】. This high accuracy reflects German being well-represented in training and XLM-R’s strong cross-lingual transfer capabilities.”
  - (If no direct number was found, we’d extrapolate from, say, its performance on Dutch or English NER, but here we assumed evidence was available)

### **Example 2: Mid-Resource Language, No Direct Task Data**
- **Scenario:** “How would GPT-3 perform on summarizing news articles in Swahili?”
- **Analysis:** Swahili is a mid-resource language (it’s widely spoken and likely appeared in some web crawl data, but far less than English). GPT-3 was not explicitly fine-tuned on summarization or on Swahili. Summarization is generative and was not a built-in GPT-3 capability except via prompt. We expect GPT-3 can attempt it with an English prompt like “Tl;dr” (which it was known to respond to for English texts), but in Swahili that may not work as well. Domain is general news – that’s favorable (no extra domain gap)
- **Evidence:** Probably none specific. Maybe mT5 or another model was evaluated on Swahili summarization in XL-Sum. Actually, XL-Sum included Swahili; an mT5-base (multilingually fine-tuned) got ROUGE-2 ~11.4 on Swahili . But GPT-3 zero-shot is likely worse than a fine-tuned mT5. Also, GPT-3’s knowledge of Swahili is moderate – it can produce some Swahili, but often with errors
- **Extrapolation:** We note mT5 had fair results with fine-tuning. GPT-3 without fine-tuning might do something but likely with lower quality. Perhaps GPT-3 could produce a very rough summary if prompted in English (“summarize the above in Swahili”), but it might actually translate the article to English internally to summarize. There’s some guesswork. We estimate: “Performance likely low: maybe ROUGE-2 in single digits.”
- **Answer Construction:**
  - “There are no published metrics for GPT-3 on Swahili summarization. Estimated performance: quite limited. GPT-3 was over 90% English-trained and only minimally exposed to Swahili, so its summaries would probably miss details or be grammatically flawed. For context, a specialized model (mT5) fine-tuned on multilingual data achieved ROUGE-2 around 11 on Swahili news . GPT-3 without fine-tuning would likely score lower, perhaps only a few points ROUGE, meaning the summaries would not be very accurate or comprehensive. In short, expect poor quality summaries unless further training or prompting techniques are used.”

### **Example 3: Low-Resource and Specialized Task**
- **Scenario:** “Can an LLM (say, GPT-4) solve a medical exam QA in Polish, and how well?”
- **Analysis:** Polish is a high/mid resource European language (Polish was probably included in training data, but not as much as English; still, GPT-4 likely has decent Polish ability). The task is multiple-choice QA for medical exams – domain-specific (medical) and task-specific (exam QA, which requires factual medical knowledge and possibly understanding complex questions). GPT-4 is state-of-the-art and known to have strong medical QA performance in English, and improved multilingual understanding. We also know from a study that GPT-4 outperformed GPT-3.5 significantly on a Chinese medical exam , showing it can handle domain knowledge better. Polish wasn’t specifically reported, but likely GPT-4 would do quite well given European language coverage, though maybe slightly lower than English
- **Evidence:** If there is any, maybe a user-conducted test or a small study. Let’s assume none directly for Polish medical, but we have English USMLE scores for GPT-4 (~85% accuracy, just guessing) and maybe a note that GPT-4’s performance in some non-English languages (like Japanese) was a bit lower but still high (e.g., GPT-4 ~84% on Italian MMLU, close to English). We combine that with the known Chinese exam result ~74.7% . Polish being an alphabetic language might be easier than Chinese for GPT-4. So perhaps GPT-4 could score in the 70-80% range on Polish medical exam questions
- **Answer Construction:**
  - “We don’t have Polish-specific medical QA results for GPT-4, but we can infer from related data. GPT-4 has demonstrated high performance on medical exam questions in other languages - for instance, it scored 74–88% on Chinese medical licensing questions, greatly surpassing GPT-3.5 . Polish is a well-represented language and closer to English; GPT-4’s accuracy on a Polish medical exam is likely in a similar ballpark, perhaps around 80% accuracy (comparable to its English medical exam performance). In other words, GPT-4 should be able to handle Polish medical questions quite impressively, though it may still make some errors on very specialized terms. Without direct testing we can’t give an exact figure, but its performance would likely be on par with a passing score by a medical student.”
  - (Here we combined cross-lingual expectation with known domain performance. Note how we cited the Chinese result as an anchor)

---

## **Summary Taxonomy and Tips**

To conclude, here’s a quick taxonomy summary and key tips for using this playbook:

- **Language Taxonomy Recap:**
  - High-resource (English, etc.) – high performance, likely evidence available
  - Mid-resource (e.g. Hindi, Polish) – moderate performance, some evidence
  - Low-resource (e.g. Somali, Lao) – low performance, little direct data
  - Unseen – very low performance, must predict from scratch
  - Use features like script, family, overlap to refine these broad categories
- **Task Taxonomy Recap:**
  - Generative vs discriminative – generative suffers more from language issues; classification can transfer easier
  - Common tasks (translation, summarization, QA, NER, etc.) often have benchmarks; niche tasks might not
  - Domain mismatch will hurt performance unless the model is specialized – consider general vs domain-specific handling
- **Model Taxonomy Recap:**
  - Multilingual vs monolingual models – know the model’s background
  - Larger/newer models = better zero-shot language generalization (GPT-4 > GPT-3.5 for languages)
  - Fine-tuned vs base – fine-tuning can either restrict (if only in one language) or expand (if done in many languages) the capabilities
  - Instruction-tuned models know task formats but still can be limited by language
- **Metrics Recap:**
  - Always identify what metric is relevant (accuracy, F1, BLEU, ROUGE, etc.) and report performance in those terms
  - Don’t mix metrics (e.g., don’t compare a BLEU to an accuracy without explanation)
- **When uncertain, err on the side of caution:**
  - It’s better to say “likely low” or give a range than a single number that might be misleading
  - Use ranges if needed (e.g. 5–10 BLEU, 60–70% accuracy)
- **Citations and Sources:**
  - If you provide a specific performance number or claim from a source, cite it
  - This not only gives credibility but also helps others follow up
  - For internal use, you might keep a repository of reliable source links for various models and tasks
- **Continuous Updates:**
  - The field evolves quickly. New benchmarks or model versions can change the expected performance (e.g., a new multilingual model might halve the gap for low-resource languages)
  - Keep this playbook updated with latest findings (e.g., if a 2025 paper shows a breakthrough on low-resource languages, adjust your expectations section)
  - The taxonomy is a guide, not a static truth