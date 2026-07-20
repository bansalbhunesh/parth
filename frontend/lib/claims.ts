export const PRODUCT_CLAIMS = {
  benchmark: {
    name: "ps4_external_v1",
    version: "1.2.0",
    recall: 0.862,
    precision: 0.953,
    f1: 0.905,
    falseAlerts: 0,
    cleanNegatives: 64,
    ruleRecall: 0.111,
    pairs: 53,
    labels: 129,
    systems: 17,
  },
  verification: {
    backendTests: 901,
    frontendTests: 80,
    browserJourneys: 160,
  },
  hero: {
    caughtWeek: 11,
    testWeek: 38,
    actionWindowWeeks: 27,
  },
} as const;

export const BENCHMARK_LIMITATION =
  "Mostly team-authored fixtures; 10 documents derive from public primary sources, reviewer-2 adjudication is pending, and this is not field or customer validation.";
