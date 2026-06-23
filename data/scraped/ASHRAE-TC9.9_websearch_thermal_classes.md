# Scraped: ASHRAE-TC9.9

Source: WebSearch — ASHRAE TC 9.9 thermal guidelines

## ASHRAE TC 9.9 Thermal Guidelines — Class Envelopes (paraphrased)

### Temperature Limits by Class

| Class | Allowable Range (dry-bulb) | Typical Equipment |
|-------|---------------------------|-------------------|
| A1 | 15–32 °C (59–89.6 °F) | Enterprise servers, storage |
| A2 | 10–35 °C (50–95 °F) | Volume servers, rack-mount |
| A3 | 5–40 °C (41–104 °F) | Extended temperature operation |
| A4 | 5–45 °C (41–113 °F) | Maximum flexibility, free-air |

### Recommended Envelope (all classes)
- Dry-bulb temperature: 18–27 °C (64.4–80.6 °F)
- Dew point: 5.5 °C to 15 °C
- Relative humidity: ≤ 60% RH at recommended, max 80% for A1/A2, max 90% for A4
- Recommended humidity low end: higher of −9 °C dew point or 8% RH

### Key Technical Points
- Measurements taken at server inlet (not room ambient)
- A1/A2 cover most enterprise and hyperscale deployments
- A3/A4 enable economiser modes in moderate climates
- Above 70% RH, pollutant-driven corrosion risk increases significantly
- Warranty coverage may differ from reliability — A2 range often supports reliable operation even if OEM warranty specifies A1
- Rate of change: recommended max 5 °C/hr at server inlet to avoid condensation
- 5th edition (2021) expanded guidance on liquid cooling and high-density deployments
