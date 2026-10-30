# VibeCheck numbers

Written by the notebooks. Don't edit by hand.

<!-- data -->
## Data: the vibe is in the reviews (notebook 01)

| metric                                |   value |
|:--------------------------------------|--------:|
| SF cafes, restaurants and bars        |   5,679 |
| ...with at least one review with text |   5,669 |
| Reviews kept (max 50 per place)       | 212,176 |
| Median reviews kept per place         |      48 |
| Places at the 50-review cap           |   2,413 |
| Median Google review count per place  |     118 |
| Median review length (words)          |      15 |

- Groups: cafe 1,166, restaurant 3,679, bar 834
- **12.9% of reviews** use a plain atmosphere word; **83.0% of places** have at least one such review.
- 3,654 places (64%) have Google's *Atmosphere* tag: Casual 3,475, Cozy 1,862, Romantic 248, Upscale 235, Historic 82, Trending 36, Quiet 18.

Do the tags match the reviews?

| Atmosphere tag   |   places tagged |   % tagged places whose reviews say it |   % untagged places whose reviews say it |
|:-----------------|----------------:|---------------------------------------:|-----------------------------------------:|
| Casual           |            3475 |                                   14.2 |                                     14   |
| Cozy             |            1862 |                                   42.6 |                                     19   |
| Romantic         |             248 |                                   25.8 |                                      3   |
| Upscale          |             235 |                                   21.3 |                                      3.9 |
| Historic         |              82 |                                   20.7 |                                      1.4 |
| Trending         |              36 |                                    8.3 |                                      4.7 |
| Quiet            |              18 |                                   27.8 |                                     16.3 |

Example place: **Four Barrel Coffee**, 375 Valencia St, San Francisco, CA 94103 · Coffee shop · ★4.5 (2,187 Google reviews) · Atmosphere: Casual, Cozy

> ★5 "Great coffee in the Mission with comfortable seating and a carefully curated vibe!"
> ★5 "Still my favorite! Great coffee, great vibe‼️"
<!-- /data -->

<!-- slang -->
## Slang: the vibe is not in the words people search with (notebook 02)

Words picked before counting. All rows shown.

| query          | plain meaning                                           |   reviews (slang) |   reviews (plain) |   places (slang) |   places (plain) |
|:---------------|:--------------------------------------------------------|------------------:|------------------:|-----------------:|-----------------:|
| boujee         | fancy, upscale, classy, elegant, luxurious              |                32 |              1582 |               32 |             1154 |
| lowkey         | low-key, low key, laid-back, unpretentious, understated |                14 |               548 |               14 |              478 |
| vibey          | atmosphere, ambiance, ambience                          |               763 |             10919 |              628 |             3530 |
| aesthetic      | beautiful, gorgeous, stylish, decor                     |                93 |              4171 |               91 |             2236 |
| chill          | relaxed, relaxing, calm, mellow, laid-back              |              1418 |              1365 |              965 |             1035 |
| bussin         | delicious, tasty, flavorful                             |                 5 |             31683 |                5 |             4949 |
| slaps          | delicious, tasty, flavorful                             |                24 |             31683 |               23 |             4949 |
| goated         | the best, excellent, outstanding                        |                 0 |             22461 |                0 |             4969 |
| poppin         | lively, bustling, busy, packed                          |                29 |              4045 |               27 |             2539 |
| instagrammable | photogenic, picturesque                                 |                11 |                20 |               10 |               19 |
| sus            | sketchy, shady, suspicious                              |                 5 |               214 |                5 |              192 |
| turnt          | rowdy, wild, rambunctious                               |                 2 |               191 |                2 |              174 |

- Urban Dictionary lexicon: 12,384 slang terms (595 two-word phrases), from 108,395 well-voted definitions.
- Not in the 2016 dump: boujee, vibey, bussin, goated, instagrammable. We need the live UD API for these.
- Top-voted meanings can miss the sense: lowkey = "To keep things secret". Pick the one that fits the query.
- 563,394 review sentences (spaCy); 4.2% contain at least one lexicon term.

30 most common lexicon hits in reviews. Mostly food words and typos, so the lexicon is for queries, not reviews:
boba (1,853), pho (1,321), falafel (609), naan (506), chewy (504), miso (485), crepes (315), sourdough (311), nachos (300), ceviche (292), dumpling (283), mochi (276), quesadilla (256), bento (253), sangria (240), guacamole (234), low key (232), tiramisu (232), omelette (228), buttery (222), tenderloin (210), homey (209), meatball (208), gyro (200), shabu (187), chorizo (180), noe (177), a a (170), horchata (160), scrumptious (158)
<!-- /slang -->

<!-- features -->
## Features prototype (notebook 03)

Embeddings: 469 sentences x 768 dims (all-mpnet-base-v2).

| place              | Google Atmosphere                 |   sentences | top 5 vibe phrases (KeyBERT)                                                                                   |   % positive |   % negative |
|:-------------------|:----------------------------------|------------:|:---------------------------------------------------------------------------------------------------------------|-------------:|-------------:|
| Four Barrel Coffee | Casual, Cozy                      |         129 | best coffee shop, great ambiance, friendly staff, negative reviews, average price                              |           74 |           12 |
| The Beehive        | Casual, Cozy, Trending, Upscale   |         142 | beautiful cocktail bar, indoor seating, beehive drink, playful new american, attentive servers                 |           71 |            8 |
| House of Prime Rib | Cozy, Historic, Romantic, Upscale |         198 | fantastic food, generally credible restaurant, quality prime rib, old school atmosphere, annual birthday visit |           63 |           12 |
<!-- /features -->
