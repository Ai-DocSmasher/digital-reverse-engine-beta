###### Digital Reverse Engine™ — Changelog

###### v1.0.0 — Deterministic TimingGrid Release (Major Upgrade)

###### This release replaces all beat‑detection and onset‑snapping logic with a fully deterministic, DAW‑accurate timing grid.

###### The engine now produces glitch‑free, artifact‑free, sample‑accurate structural reversals.

###### 

###### New DSP Architecture

###### Added TimingGrid (mathematical tempo grid; no detection, no drift)

###### 

###### All modes now slice using deterministic sample positions

###### 

###### Zero jitter, zero onset errors, zero spectral artifacts

###### 

###### New Reverse Modes

###### HQ\_REVERSE — Beat‑level structural reverse (flagship mode)

###### 

###### QBEAT\_REVERSE — Quarter‑beat slicing

###### 

###### TATUM\_REVERSE — Sub‑beat micro‑slicing (1/4 beat, triplet, 1/2 beat, etc.)

###### 

###### STUDIO\_REVERSE — Multi‑bar phrase‑level reverse with user‑tuned slicing

###### 

###### TRUE\_REVERSE — Classic waveform reverse

###### 

###### STUDIO\_REVERSE Enhancements

###### Multi‑bar slicing for long‑form audio

###### 

###### User‑tuned behavior via tempo, beats‑per‑bar, and bar size

###### 

###### Setting beats\_per\_bar = 1 produces macro HQ‑style reversals

###### 

###### Guaranteed multi‑slice logic for audible reversal

###### 

###### Pipeline Improvements

###### Added DSP‑only pipeline for CLI

###### 

###### Added hybrid pipeline with CostEstimator, gating, and receipts

###### 

###### Cleaned imports and removed circular dependencies

###### 

###### Unified mode map across DSP and hybrid layers

###### 

###### Stability \& Quality

###### No static, no glitches, no windowing artifacts

###### 

###### Perfect stereo alignment

###### 

###### Sample‑accurate padding/trim logic

###### 

###### Faster processing due to removal of onset/beat detection

###### 

###### Beta 3 — Structural Reverse Upgrade (Legacy)

###### Added early HQ\_REVERSE (tempo‑grid + onset snapping)

###### 

###### Added TRANSIENTAWARE\_REVERSE (tatum‑like slicing)

###### 

###### Added DJ\_REVERSE (1/8‑beat slicing)

###### 

###### Added STUDIO\_REVERSE (bar‑level structural reverse)

###### 

###### Improved stereo‑safe windowing

###### 

###### Improved tempo detection fallback logic

###### 

###### Added deterministic grid slicing for stability

###### 

###### Added onset snapping for smoother transitions

###### 

###### Added padding/trim logic for perfect output length

###### 

###### Beta 2 — DSP Pipeline

###### Added granular reverse mode

###### 

###### Added Hann window smoothing

###### 

###### Added stereo‑safe processing

###### 

###### Beta 1 — Initial Release

###### TRUE\_REVERSE

###### 

###### Basic CLI

###### 

###### WAV I/O

