### How close to the real photos should the images be? (written before testing)

**Closer is not better.** On the validation photos the classifier gains most
from images that are *far* from the 15 training photos, and least from near
copies:

- **img2img improves as strength grows**: Mau recall 0.70 → 0.77 → 0.76 → 0.81
  for strength 0.3 → 0.9, and macro-F1 0.892 → 0.906. Strength 0.3 (feature
  similarity 0.86 to its source, closer than any two real Mau photos are to each
  other, 0.67) behaves like oversampling (0.67): seven near-copies of each of the
  same 15 cats add almost no new information. It is also the only img2img pool
  that is worse than `m2-base` in every seed (−11 pp, 0/0/5).
- **Strength 0.9 is as good as the text-only Meeting 2 pool** (0.81, paired
  difference 0.0 pp, 1/3/1 seeds), and it is the pool with the lowest similarity
  to the training photos (0.55, only a little above `m2-base`'s 0.49). At this
  strength only the colour palette of the source survives, so it is effectively a
  text-to-image pool with a photo-derived colour scheme.
- **IP-Adapter gets slightly worse as the scale grows** (0.73, 0.72, 0.72, 0.69)
  and is below `m2-base` at every scale (−8 to −12 pp; lower in 4–5 of 5 seeds),
  though still above or at the Meeting 1 baselines. Its similarity to the
  training photos hardly changes with the scale (0.56–0.59), so the photo
  conditioning mostly changes the *style* of the images, not how close they are.
- **What separates the pools is not captured by the two simple measures.**
  IP-Adapter at scale 1.0 is about as far from the photos (0.58) and as diverse
  (within-pool similarity 0.52) as img2img 0.9 (0.55, 0.51) and `m2-base` (0.49,
  0.52), but its recall is 12 pp lower. The contact sheets suggest why:
  IP-Adapter images have an over-contrasted, graphic look with very large black
  spots, long serval-like bodies and saturated colour casts, and they copy studio
  backdrops and collars. This resembles the guidance-15 pool of Meeting 2 (also
  −5 pp). Natural, photo-like images of *new* cats seem to matter more than
  closeness to the training photos.
- **Cost.** img2img pools also make the models call more other cats Mau
  (1.2–1.6 per model against 0.6 for `m2-base` and the IP-Adapter pools),
  i.e. part of their recall is bought with false positives; macro-F1 shows this
  as a 0.15–1.5 pp loss against `m2-base`.
- **Spread.** Five seeds and 20 validation Mau photos (5 pp each): the IP-Adapter
  pools differ from each other by at most one photo on average. The robust
  findings are the ends of the img2img sweep (near copies ≈ oversampling;
  strength 0.9 ≈ text-to-image) and IP-Adapter being consistently below `m2-base`.

**Answer.** For this classifier the useful images are *about as far from the
training photos as another real Egyptian Mau would be, or further* (similarity
≤ 0.6 here), as long as they still look like real photographs of the breed.
Near copies (img2img ≤ 0.5) mostly repeat the 15 cats, including their
watermarks and collars.

**Choices** (fixed rule: highest mean validation Mau recall per mode):
`m3-strength-0.9` for image-to-image and `m3-ip-0.3` for IP-Adapter. Neither is
better than the Meeting 2 pool on validation; they are tested as the best run of
each mode, as the assignment asks.
