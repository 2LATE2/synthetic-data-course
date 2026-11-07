### What the test results show

- **Both chosen runs beat the Meeting 1 baselines on test** and match the
  Meeting 2 pool: Mau recall 0.767 (`m3-strength-0.9`) and 0.753 (`m3-ip-0.3`)
  against 0.747 (`m2-base`) and 0.693 (oversampling); macro-F1 0.891 and 0.890
  against 0.893 and 0.881. Against oversampling both are higher or equal in every
  seed (+7.3 and +6.0 pp).
- **Against the Meeting 2 pool there is no real difference.** +2.0 pp and
  +0.7 pp Mau recall are less than one test photo (3.3 pp) per model, the seeds
  split 3/0/2 and 2/1/2, and macro-F1 is 0.2–0.3 pp lower. Conditioning the
  generation on the training photos did not add anything measurable on top of
  text-to-image.
- **IP-Adapter's validation gap did not replicate.** On validation `m3-ip-0.3` was
  8 pp below `m2-base`; on test it is 0.7 pp above. With 20–30 Mau photos per
  split, differences of a few photos between generation methods are within noise;
  only the gap between synthetic pools and the classical baselines is consistent
  on both splits.
- **Remaining errors** are the same as before: about 4 of 30 test Mau photos per
  model are called Bengal for every synthetic pool. img2img 0.9 reduces the
  Mau→Russian Blue confusions a little further (1.4 against 2.0 for `m2-base` and
  3.6 for oversampling).

Mean number of the 30 test Mau photos per model predicted as each other breed:

| Run | Bengal | Russian Blue | Abyssinian | Siamese |
| --- | ---: | ---: | ---: | ---: |
| m1-oversample | 4.2 | 3.6 | 1.2 | 0.2 |
| m2-base | 4.4 | 2.0 | 1.2 | 0.0 |
| m3-strength-0.9 | 4.4 | 1.4 | 1.2 | 0.0 |
| m3-ip-0.3 | 4.0 | 2.2 | 1.2 | 0.0 |

**Result carried forward:** best image-to-image run `m3-strength-0.9` — test Mau
recall 0.767 ± 0.041, macro-F1 0.891 ± 0.011; best IP-Adapter run `m3-ip-0.3` —
0.753 ± 0.045, macro-F1 0.890 ± 0.011. Both are on par with `m2-base`
(0.747 ± 0.030, 0.893 ± 0.007) and above every Meeting 1 baseline.
