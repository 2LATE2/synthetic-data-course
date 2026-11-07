### What the test results show

- **The chosen text-to-image run beats all three Meeting 1 baselines on test, in
  every seed.** Mean test Mau recall is 0.747 against 0.693 for oversampling (the
  strongest baseline), 0.653 for augment-strong and 0.507 for real data only;
  macro-F1 is also higher (0.893 against 0.873–0.881), so the other breeds are not
  harmed. Against oversampling the gain is +5.3 pp, i.e. about 1.6 of the 30 test
  Mau photos per model, higher in 5/5 seeds.
- **The gain is smaller than on validation** (+14 pp over oversampling there).
  Part of this is expected: `m2-base` was chosen as the best of five pools on only
  20 validation Mau photos, so its validation score is optimistic. The test value
  is the number to carry into Meeting 3.
- **The mechanism differs from validation.** On validation the synthetic pool
  mainly reduced Mau→Bengal confusions. On test, Mau→Bengal stays at about 4 of 30
  photos per model for every method except real data (9.0). The extra gain of
  `m2-base` comes from fewer Mau photos called **Russian Blue** (2.0 per model,
  against 3.6 for oversampling and 4.4 for augment-strong), plausibly because the
  pool adds many silver-grey cats in new poses and lighting. The Mau/Bengal
  boundary is still the main remaining error. This matches the most common failure
  in the pool: striped or leopard-spotted coats do not teach what separates a Mau
  from a Bengal.

Mean number of the 30 test Mau photos per model predicted as each other breed:

| Run | Bengal | Russian Blue | Abyssinian | Siamese |
| --- | ---: | ---: | ---: | ---: |
| m1-real | 9.0 | 5.0 | 0.8 | 0.0 |
| m1-oversample | 4.2 | 3.6 | 1.2 | 0.2 |
| m1-augment-strong | 4.2 | 4.4 | 1.6 | 0.2 |
| m2-base | 4.4 | 2.0 | 1.2 | 0.0 |

**Result carried into Meeting 3:** `m2-base` (SD 1.5, 30 steps, guidance 7.5,
DPM, four varied prompts) — test Mau recall 0.747 ± 0.030, macro-F1 0.893 ± 0.007.
