# Release notes

## 1.3.1

**The pigs have faces now.** Three faults were live at the same time and none of
the checks said a word, because every file was valid in every other respect. It
took a player writing in to find the first one.

* **Blossom had no eyes.** The largest head in the pack — nine texels wide —
  carried the same 1x1 eye as the Kunekune's seven, proportionally the smallest
  of all five, and it sat down beside the snout where it disappeared into the
  shadow. Eyes scale with the head now and sit in the upper third.
* **Ember and Nilla had no nostrils at all.** The snout's face starts on half a
  texel, and the rounding put the dots on the *neighbouring* face instead. A
  snout without nostrils is still a pink snout, so nobody had noticed across
  three releases.
* **Soot's nostrils were nearly black on a nearly black snout.** The same kind
  of invisibility as Blossom's eyes, from the other direction. Nostril colour
  follows the snout now, so it reads on a pink Large White and a black Berkshire
  alike.

Every eye has a highlight in the upper corner. It is the single detail that
separates an animal from a cute animal, and the children had asked for cuter
pigs.

**The snout ends in a disc.** The Tamworth's snout is four and a half units long
and was a plain box — from the side the pig read as an anteater, not a pig. A
pig is recognised by a nose that ends in a flat disc wider than the bridge, and
all five breeds have one now. On Ember it makes the most difference.

## 1.2.0

**Pigs wallow now.** A pig that finds mud lies down in it and walks around muddy
on its belly and legs for a while afterwards. Water washes it off. Wild pigs do
it too — a muddy pig in a swamp is the whole point. It does nothing useful; it
is simply what pigs do, and nothing else in the pack did it.

Three quieter things, all of them promises the pack was already making:

- A pig's **hitbox now follows its size**. Every breed had the same one, so a
  Kunekune was as wide to walk into as a Large White.
- The **saddlebags are proven to carry**. They always did, but nothing had ever
  checked that the fifteen slots hold anything.
- Taming, mode, saddle, bags **and what is in the bags** are now proven to
  survive a world restart.

## 1.1.0

The pack is now called **Snuffle Pigs**, the same name it has in the store. It
was "Snuffle Companions" inside the game and "Snuffle Pigs" on the shop page,
and one thing should not have two names.

Nothing else changed: same five pigs, same noses, same saddlebags.

## 1.0.3

Five hand-made pigs that smell ore through solid rock, root up truffles and
carry you.

- **Snuffle mode.** A pig senses ore through the stone around it and reports what
  it found, which way and how far. Range is per breed: Soot reaches twelve
  blocks, Blossom five.
- **Truffles.** Rooted out of grass, dirt, podzol, mycelium, moss and mud, and
  visible in the pig's snout before they drop. Edible, and the best breeding
  feed.
- **Real riding.** Saddle a pig and it steers like a horse — no carrot on a
  stick. A chest fits saddlebags.
- **Commands** with a stick: Follow, Snuffle, Stay.
- **Five breeds** with their own bodies, noses, speeds and health, spawning in
  plains, forest, taiga and savanna.
- **Piglets** born already tame, that grow up.
- English and Swedish.
