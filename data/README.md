# Dataset Folder

The final annotated CSV is here:

```text
data/annotated_examples.csv
```

Required columns:

```csv
text,label
```

Valid labels:

- `evidence_based_guidance`
- `implementation_question`
- `unsupported_claim`
- `showcase_reaction`

The current CSV contains 200 public examples, balanced at 50 rows per label. Extra columns preserve source, URL, author, and labeling rationale for auditability. Do not commit private data or API keys.

The img shows the test result of the data

Metrics: Parseable baseline responses: 30 / 30
First 10 baseline predictions: ['evidence_based_guidance', 'evidence_based_guidance', 'evidence_based_guidance', 'evidence_based_guidance', 'unsupported_claim', 'showcase_reaction', 'implementation_question', 'implementation_question', 'showcase_reaction', 'evidence_based_guidance']
🎯 Baseline accuracy: 0.867  (evaluated on 30/30 parseable responses)

Per-class metrics (baseline):
                         precision    recall  f1-score   support

evidence_based_guidance       0.89      1.00      0.94         8
implementation_question       0.70      1.00      0.82         7
      unsupported_claim       1.00      0.75      0.86         8
      showcase_reaction       1.00      0.71      0.83         7

               accuracy                           0.87        30
              macro avg       0.90      0.87      0.86        30
           weighted avg       0.90      0.87      0.87        30