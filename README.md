# Snuffle Pigs

Minecraft **Bedrock** add-on: five hand-made pigs that **search**. Sibling
project to [Loyal Companions](https://loyal.pelleops.se) (dogs) and
[Purrfect Companions](https://purrfect.pelleops.se) (cats) — same machinery,
different animal, different verb.

Minecraft already has a pig. It exists to become pork, and riding it with a
carrot on a stick barely steers. This add-on gives the pig a job: it **smells
ore through solid rock** and tells you which way it lies, it **roots up
truffles** out of the ground, and saddled it **actually steers**.

![the pigs](publish/pigs.png)

## The five

| Name | Breed | Nose | Speed | Health | Lives in |
|------|-------|------|-------|--------|----------|
| Nilla | Kunekune | 6 blocks | 0.26 | 14 | plains |
| Bramble | Mangalitsa | 7 blocks | 0.24 | 20 | taiga |
| Blossom | Large White | 5 blocks | 0.22 | 24 | plains |
| Soot | Berkshire | **12 blocks** | 0.25 | 18 | forest |
| Ember | Tamworth | 8 blocks | **0.32** | 16 | savanna |

The differences are not decoration. Soot smells ore twice as far as Blossom, and
Blossom carries the most and takes the most punishment. You pick a pig for the
job, not for the colour.

They are not reskins either: each body is built from its own measurements, so
the Kunekune really is low and round and the Large White really is heavy. What
makes a pig read as a pig at a glance is the snout, so every breed has its own.

## How to use them

- **Tame** with a carrot — about four tries in ten per carrot.
- **Switch modes** with a stick in hand: Follow → Snuffle → Stay.
- **Snuffle.** In Snuffle mode a pig roots truffles out of dirt, grass, podzol,
  mycelium, moss, mud and rooted dirt. You see the truffle in its snout for a
  moment before it drops, so you can tell where it came from.
- **Catch a scent.** In Snuffle mode a pig senses ore through the stone around
  it and reports what it smells, which way it lies and how far off it is. A
  compass direction and a distance, not exact coordinates: it tells you where to
  dig and leaves the digging to you.
- **Saddle** one and it steers the way a horse steers. Add a **chest** for
  saddlebags with fifteen slots.
- **Wallow.** A pig that finds mud lies down in it and walks around muddy on its
  belly and legs for a while afterwards. Water washes it off. It does nothing
  useful — it is simply what pigs do.
- **Breed** with a truffle, a potato or a beetroot. The piglet is born already
  yours, and it grows up.

Truffles are food, and they are also the best breeding feed — what you find has
a use even when the larder is full.

## Building and testing

```bash
python3 tools/make_pigs.py         # generates EVERYTHING: models, textures, JSON, language
python3 tools/render_pigs.py       # publish/pigs.png — see them without Minecraft
tools/snuffle-test                 # static gates + a live Bedrock server
python3 tools/snuffle-falsifiera   # proves the gates actually fail
tools/snuffle-uthallighet          # state survives a restart, and what the loop costs
```

Nothing in `SnuffleCompanions_BP/` or `SnuffleCompanions_RP/` is written by
hand — `tools/make_pigs.py` owns them and rewrites them from scratch. Edit a
generated file and the change is gone on the next run.

`snuffle-falsifiera` breaks one thing at a time in a copy of the pack and checks
that the right gate complains about the right thing. A gate that has never seen
a failure is not proven; it might as well be a line that always says yes.

Requirements: a Bedrock server in `/opt/bds/server`, and the cat project's
`render_regression.py` for reading and writing PNGs.
