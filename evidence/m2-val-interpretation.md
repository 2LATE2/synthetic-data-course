### What the validation results show (written before testing)

- **Every text-to-image pool beats every Meeting 1 baseline on validation.**
  Mean Egyptian Mau recall is 0.76–0.81 for the five pools against 0.67
  (oversampling) and 0.68 (augment-strong), and mean macro-F1 rises too
  (0.901–0.907 against 0.883–0.887), so the gain is not paid for by the other
  breeds. The main mechanism is visible in the confusion counts: real-data models
  call on average 5.2 of the 20 validation Mau photos *Bengal*; with `m2-base`
  this drops to 1.8, while only 0.6 of the 140 other photos per model are wrongly
  called Mau. Fifty-five new, different-looking spotted cats teach the boundary
  between Mau and Bengal better than 55 copies of the same 15 photos.
- **Guidance 15 is the only clearly worse setting:** −5.0 pp Mau recall against
  the base (lower in 4 of 5 seeds, never higher) and −0.65 pp macro-F1. This
  matches the contact sheets: oversaturated, high-contrast, illustration-like
  images are further from the real photos.
- **One simple prompt is slightly worse:** −3.0 pp (lower in 3 seeds, tied in 2).
  Its images have plausible coats but repeat the same pose and background, so
  the 55 drawn images add less variety.
- **Guidance 2 ties with the base on mean Mau recall** (2 seeds higher, 2 lower),
  but its models also call more other cats Mau (1.6 vs 0.6 per model) and confuse
  Mau with Bengal more often (2.6 vs 1.8). The contact sheet shows why it is not
  more useful despite looking more natural: it contains more wrong-breed brown
  tabbies and fused or melted anatomy.
- **10 steps gives the same result as 30 steps** (mean 0.81, three seeds tied).
  With the DPM solver the 10-step images are nearly identical to the 30-step
  ones for the same seed (see the grid), so this is expected; 10 steps would be
  a 3× cheaper way to make the same pool.
- **The differences between pools are small compared with their spread.**
  Apart from guidance 15, every difference to the base is within one or two
  validation photos (5 pp each) and within the paired seed SD (2.7–5.0 pp).
  The large, consistent effect is synthetic data versus the classical baselines,
  not one generation setting versus another.

**Choice.** By the fixed rule the base pool `m2-base` is taken forward: it shares
the highest mean Mau recall (0.81) with guidance 2 and 10 steps; the macro-F1
tie-break differs by only 0.01 pp from 10 steps, and the final tie-break prefers
the base. The contact sheets support the choice over guidance 2 (fewer anatomy
failures, fewer wrong-breed cats, fewer false Mau predictions). Its known flaws
remain: many striped coats (especially from the "close-up … tabby" prompt) and
some serval/leopard-like cats.
