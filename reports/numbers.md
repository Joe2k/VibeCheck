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

Which dictionary knows our 12 query words?

- Urban Dictionary dump (2016): 7/12. Missing: boujee, vibey, bussin, goated, instagrammable.
- Wiktionary (2026, 86,767 slang terms): 10/12. Missing: aesthetic, poppin.
- Together: 12/12. First senses are often wrong ("slaps" = makeup), so pick the sense that fits the query.

| term           | Urban Dictionary (2016)                                                                    | Wiktionary (2026)                                                                          |
|:---------------|:-------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------|
| boujee         | —                                                                                          | Behaving like or pertaining to people of a higher social status, middle-class / bourgeois  |
| lowkey         | To keep things secret                                                                      | In a low-key or surreptitious manner; secretively; understatedly; on the down-low.         |
| vibey          | —                                                                                          | Having a vibe; atmospheric and trendy.                                                     |
| aesthetic      | ADJECTIVE:   1. Beautiful.   2. Sensitive to or appreciative of art or beauty.   3. Relati | —                                                                                          |
| chill          | 1. to calm down   2. cool, tight, wicked, sick, sweet, nice, etc.   3. to hang out   4. to | Calm, relaxed, easygoing.                                                                  |
| bussin         | —                                                                                          | Delicious.                                                                                 |
| slaps          | crackin songs from the bay area                                                            | Makeup; cosmetics.                                                                         |
| goated         | —                                                                                          | Being or considered the greatest of all time; the best.                                    |
| poppin         | to get (something) started                                                                 | —                                                                                          |
| instagrammable | —                                                                                          | Visually attractive or interesting such that it lends itself to being photographed and pos |
| sus            | A funny word used in Youtube Poops.                                                        | Suspicion (in terms of a sus law).                                                         |
| turnt          | Turnt is a variation of 'turned' used only to describe when someone is excessively excited | Energetic, happy, or excited, especially as a result of alcohol or drugs.                  |
<!-- /slang -->


<!-- tag_queries -->
## Tag queries: the gap in search results (notebook 03)

Throwaway keyword scorer, 8 tags, plain vs. slang query with the same meaning.
Labels = places Google tags that way. Mean P@10: **plain 0.48, slang 0.32**, chance 0.15.

| tag                        |   relevant places |   chance | plain query                                 |   P@10 plain | slang query                        |   P@10 slang |
|:---------------------------|------------------:|---------:|:--------------------------------------------|-------------:|:-----------------------------------|-------------:|
| Cozy                       |               371 |     0.32 | cozy cafe with comfortable seating          |          0.8 | comfy lowkey cafe to chill         |          0.5 |
| Romantic                   |               246 |     0.07 | romantic restaurant for a date night        |          0.9 | restaurant to impress bae          |          0.2 |
| Upscale                    |               200 |     0.05 | upscale fancy elegant restaurant            |          0.3 | boujee restaurant to flex          |          0.3 |
| Historic                   |                82 |     0.01 | historic old place with a long history      |          0.2 | og old school spot                 |          0.3 |
| Trending                   |                36 |     0.01 | trendy popular new bar                      |          0   | poppin bar everyone is hyped about |          0   |
| Good for working on laptop |               299 |     0.26 | quiet cafe to work on my laptop with wifi   |          0.5 | cafe to grind on homework          |          0.5 |
| College students           |               711 |     0.13 | cheap place popular with college students   |          0.4 | spot for broke college kids        |          0.1 |
| Groups                     |              1417 |     0.39 | restaurant good for large groups of friends |          0.7 | restaurant for the whole squad     |          0.7 |
<!-- /tag_queries -->

<!-- features -->
## Features prototype (notebook 04)

Embeddings: 469 sentences x 768 dims (all-mpnet-base-v2).

| place              | Google Atmosphere                 |   sentences | top 5 vibe phrases (KeyBERT)                                                                                   |   % positive |   % negative |
|:-------------------|:----------------------------------|------------:|:---------------------------------------------------------------------------------------------------------------|-------------:|-------------:|
| Four Barrel Coffee | Casual, Cozy                      |         129 | best coffee shop, great ambiance, friendly staff, negative reviews, average price                              |           74 |           12 |
| The Beehive        | Casual, Cozy, Trending, Upscale   |         142 | beautiful cocktail bar, indoor seating, beehive drink, playful new american, attentive servers                 |           71 |            8 |
| House of Prime Rib | Cozy, Historic, Romantic, Upscale |         198 | fantastic food, generally credible restaurant, quality prime rib, old school atmosphere, annual birthday visit |           63 |           12 |
<!-- /features -->
