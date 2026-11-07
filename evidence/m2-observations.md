## What the contact sheets show (written before any Meeting 2 classifier result)

Observations from the first 24 attempts of every pool (the contact sheets) and
the same-seed grid above. Counts refer to those 24 images, judged by eye.

![Failure examples](evidence/m2-failures.jpg)

**Failure types found**

- **Wrong coat pattern — stripes instead of spots.** The most frequent failure.
  Real Egyptian Mau have random spots; SD 1.5 often draws mackerel or zebra
  stripes, especially on the body and face (base #9, #11, #15, #17, #20, #21, #23).
  The second base prompt (`close-up … spotted silver tabby coat`) produces it
  almost every time (#1, #5, #9, #17, #21): the word *tabby* pulls towards stripes.
- **Wrong breed — serval/leopard/Bengal look.** Very large ears, long thin legs
  and large solid leopard spots or rosettes (base #2, #7, #10, #18, #22). The
  fourth prompt's *bronze spotted coat* gives Bengal-like leopard rosettes (#18).
  This matters because the real-data classifier already confuses Mau with Bengal.
- **Impossible anatomy.** Merged or fused bodies and melted faces, much more
  frequent at low guidance (guidance 2: #0, #1, #16 two fused cats, #20, #21);
  a dog-like head at 10 steps (#6); stretched, arched bodies at every setting (#22).
- **Framing.** Extreme close-ups that cut the cat off (base #1, #5, #21), which do
  not look like the Oxford-IIIT Pet snapshots; a person's legs in the frame (#6).
- **Painting / over-processed style.** Guidance 15 gives oversaturated, high-
  contrast images with glowing green eyes and bright pink ears (#9, #11, #17);
  they look like illustrations more than photos.
- **Repeated poses and backgrounds.** The single simple prompt gives mostly the
  same sitting pose facing the camera on a plain indoor background, often
  portrait framing, collars, and very large bat-like ears (#5, #19, #21); there are
  no garden or lying scenes.
- **Safety-blocked attempts.** One black image in `m2-base` (#13) and one in
  `m2-guidance-2`; they stay in the manifests as `safety_blocked` and are never
  drawn for training.

**How the settings change the images (same seeds, see the grid)**

- **Guidance 2** follows the prompt loosely: softer, more natural photos with
  realistic lighting, but many cats are ordinary brown or classic tabbies (wrong
  breed) and anatomy fails more often.
- **Guidance 15** keeps the composition of the base image but exaggerates colour,
  contrast and spots; the most "graphic" and least photographic pool.
- **10 steps** is almost identical to the 30-step base for most seeds (the DPM
  solver converges quickly), with slightly softer details and occasional defects.
- **One simple prompt** gives the least diverse pool (poses, backgrounds), but its
  coats are not worse than the base's; the bronze/leopard images disappear.
