# Vacation-PC rehearsal patch — 2026-09-04

Focused patch applied to the accepted Strategy Intelligence build.

- Global dark-theme controls, search results, links, selected-card states and banners now have explicit high-contrast text colors.
- Portfolio never treats reference/fair value as executable. It exposes current lowest BIN/execution source/age, reference source/age, current liquidation P/L after 5% EA tax, a persisted desired listing price, and projected P/L at that desired listing price.
- Portfolio refreshes from the existing WebSocket/poll fallback, so liquidation P/L follows new execution observations.
- Buying a listing contained in a manual execution book preserves the original observation and creates a derived local book with the consumed listing removed. The next observed listing becomes the local mark; if no observed listing remains, no executable price is shown until fresher evidence arrives.
- Trade/model confidence and execution-observation confidence remain separate and are explicitly labelled.
- Regression tests cover the accepted 95,000 buy -> 101,000 sell path and partial sales.
