# TakeMeter Planning

## Community

I am studying Raspberry Pi and embedded maker communities, especially posts similar to what appears in r/raspberry_pi, r/AskElectronics, robotics forums, and project-build spaces. This community is a good fit because the discourse mixes concrete implementation advice, debugging requests, broad confident recommendations, and lightweight project reactions. Those distinctions matter because makers need to know whether a post is actionable technical guidance, a request that needs more help, an unsupported take, or just a project update.

## Labels

The classifier uses four mutually exclusive labels.

| Label | Definition | Clear examples |
| --- | --- | --- |
| `evidence_based_guidance` | A post gives concrete, technically grounded advice using specific parts, commands, measurements, code, diagrams, or reproducible troubleshooting steps. | "Use a logic-level MOSFET instead of driving the motor from the GPIO pin directly; the GPIO pin cannot supply motor current." / "Run `i2cdetect -y 1` first, then verify SDA and SCL are on pins 3 and 5 with a common ground." |
| `implementation_question` | A post asks for help with a specific build, bug, wiring choice, library, or deployment issue and includes enough context for others to answer. | "My Pi 4 reads the MCP3008 fine over SPI, but the servo jitters whenever Wi-Fi starts. The servo has a separate 5V supply and common ground. What should I check?" / "I am building a glove controller with flex sensors; should I smooth readings in Python or on the microcontroller?" |
| `unsupported_claim` | A post makes a broad recommendation, warning, ranking, or confident opinion without enough evidence or implementation detail to justify it. | "Raspberry Pi is terrible for robotics. Just use Arduino for everything." / "Python is always too slow for sensor projects." |
| `showcase_reaction` | A post mainly shows, celebrates, reacts to, or briefly comments on a project without asking for technical help or making a supported technical argument. | "Finished my first wearable controller prototype today." / "That case design looks clean." |

## Hard Edge Cases

The hardest boundary is between `unsupported_claim` and `evidence_based_guidance`. A post can sound confident and include one technical detail without actually giving enough evidence to be useful. The decision rule is: if the detail would let another builder reproduce, verify, or debug the claim, label it `evidence_based_guidance`; if the detail is vague, cherry-picked, or only decorative, label it `unsupported_claim`.

Another boundary is between `implementation_question` and `showcase_reaction`. A project update that includes a question is labeled `implementation_question` only when the question asks for technical help and includes enough context. A celebratory post with a vague "thoughts?" stays `showcase_reaction`.

## Data Collection Plan

Collected 200 public posts or comments from Raspberry Pi, embedded systems, robotics, and maker-adjacent communities. The final CSV is `data/annotated_examples.csv`. It keeps two required notebook columns plus audit columns:

```csv
text,label,source,source_url,author,label_reason
```

Final distribution:

| Label | Target count |
| --- | ---: |
| `evidence_based_guidance` | 50 |
| `implementation_question` | 50 |
| `unsupported_claim` | 50 |
| `showcase_reaction` | 50 |

Sources were Raspberry Pi Stack Exchange questions, Raspberry Pi Stack Exchange answers, and Hacker News Algolia search results for maker/embedded topics. If the dataset is expanded later, collect more examples from threads where each discourse type naturally appears rather than forcing borderline posts into a weak label. Keep the smallest class at or above 20% of the dataset when possible.

## Evaluation Metrics

Accuracy will show the overall same-test-set comparison between the fine-tuned DistilBERT model and the Groq zero-shot baseline. Per-class precision, recall, and F1 are also required because the labels are not equally costly. For example, low recall on `evidence_based_guidance` would mean the model misses useful technical answers, while low precision on `unsupported_claim` would unfairly mark useful posts as unsupported.

The confusion matrix will show which label boundaries fail most often. `wrong_predictions.csv` will support the required qualitative error analysis with at least three concrete mistakes.

## Definition of Success

The classifier is useful if the fine-tuned model beats the Groq zero-shot baseline on the same test set and reaches at least 70% overall test accuracy with no class F1 below 0.55. For a real community tool, I would not deploy it as an automatic moderation decision-maker; "good enough" means it can triage posts for review or summarize discourse patterns while keeping a human in the loop.

## AI Tool Plan

For label stress-testing, I will ask an AI tool to generate 5-10 borderline maker-community posts between `unsupported_claim` and `evidence_based_guidance`, then revise the decision rules if I cannot label them consistently.

For annotation assistance, I may use an LLM to pre-label a batch, but every label must be reviewed manually. If I use pre-labeling, I will add a column such as `prelabeled_by_ai` or document the workflow in the README AI usage section.

For failure analysis, I will give the wrong predictions to an AI tool and ask it to identify repeated patterns. I will verify any suggested pattern by reading the original examples myself before including it in the evaluation report.

## Stretch Feature Notes

Before starting any stretch feature, update this section with the plan. The strongest candidates are confidence calibration and systematic error pattern analysis because the notebook already saves probabilities and wrong predictions.
