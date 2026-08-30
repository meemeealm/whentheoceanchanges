# whentheoceanchanges
Submission for Pacific DataViz Challenge

```text
                    ┌─────────────────────────┐
                    │      GitHub / Frontend  │
                    │                         │
                    │ HTML / JS / Plotly      │
                    │ Climate JSON data       │
                    └────────────┬────────────┘
                                 │
                    chart data 
                    explanation style
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       Cloud Run         │
                    │                         │
                    │   API / Backend         │
                    │                         │
                    │  1. Validate request    │
                    │  2. Select chart data   │
                    │  3. Build context       │
                    │  4. Prompt Gemini       │
                    │  5. Validate response   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       Gemini API        │
                    │                         │
                    │ ELI5 / General /        │
                    │ Scientist explanation   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Structured explanation  │
                    │                         │
                    │ explanation             │
                    │ key findings            │
                    │ caveats                 │
                    │ conclusion              │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Plotly / UI        │
                    │                         │
                    │ Chart + AI explanation  │
                    └─────────────────────────┘
```
