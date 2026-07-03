# runs/

One directory per benchmark run:

```
<date>_<provider>_<model>_run<K>/
  run_config.yaml       resolved config + label freeze hash for this run
  predictions.jsonl     raw predicted findings per pair (input hash, output hash)
  per_pair_results.csv  tp/fp/fn, exact/semantic, latency, mode, not_run per pair
  summary.json          aggregate metrics for this run
  errors.jsonl          any provider/timeout errors (one per line)
```

Rule-mode runs use provider `rule` / model `rule-engine`. LLM runs record the
resolved provider/model and repeat index. Runs are small text artifacts and are
committed so results are reproducible and auditable.
