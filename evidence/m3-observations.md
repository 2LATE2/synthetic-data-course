## What the contact sheets show (written before any Meeting 3 classifier result)

Each contact-sheet pair is source training photo → generated image; numbers
refer to the first 24 images of each pool.

**Image-to-image (the photo is the starting point)**

- **Strength 0.3 — near copies.** Same cat, pose, background and lighting; only
  fine texture changes. Even the photographers' signatures and watermarks are
  copied (#5, #20 "©Chamani", #2, #17). Because the 15 photos are reused about
  seven times each, a 0.3 pool is close to oversampling with slight noise.
- **Strength 0.5 — same scene, redrawn cat.** Pose and background stay; the coat
  and face are redrawn and often get sharper, more contrasted markings, sometimes
  stripes on legs and flanks (#6, #13). Watermarks are still reproduced, now as
  garbled text (#20). One attempt was safety-blocked (#1).
- **Strength 0.7 — new pose, old palette.** Colours and rough layout survive,
  but many images get a new pose or scene (#1 on a cushion, #3 among flowers,
  #21 on a patterned pillow). The coat starts to drift to the SD 1.5 look of
  Meeting 2: leopard-like spots (#14) and stripes.
- **Strength 0.9 — almost a text-to-image pool.** Only the colour palette is left;
  the Meeting 2 failures return: leopard/cheetah rosettes (#11, #14, #19),
  stripes (#21), odd anatomy and crops (#6, #7).

**IP-Adapter (the photo is a reference)**

- **Scale 0.3 — mostly the prompt.** New scenes and poses, similar to `m2-base`;
  the photo shows only in the overall colour (golden source #12 → golden cat).
- **Scale 0.5 — coat colour and details transfer.** Coat colour and the type of
  markings follow the source more, and details are copied: the red collar of the
  close-up source photo appears again (#10). Scenes are still new.
- **Scale 0.7–1.0 — the photo starts to dominate, with its own style.**
  Background colours and objects of the source come back (#6 fence and garden
  like the source's enclosure, #13 red sofa, #19/#20 studio backdrops, #21 fence),
  and the prompt matters less. The images get an over-contrasted look with very
  large black spots and long, serval-like bodies (#8, #23 at 1.0), and saturated
  colour casts (#3, #18 at 1.0). One attempt at scale 1.0 was safety-blocked (#2).

**Things that are copied but should not be:** watermarks and signatures
(img2img ≤ 0.5), collars (IP-Adapter ≥ 0.5, img2img at all strengths), and the
studio backdrops of the show-cat photos. They are not breed features, so a
classifier may learn them as shortcuts for "Egyptian Mau".

**The two modes move in opposite directions.** img2img keeps the *scene* (pose,
background, framing) and gives up the *cat* as strength grows; IP-Adapter keeps
the *cat's appearance* (coat colour, marking style) and invents a new scene,
copying more of the photo as the scale grows.
