# Ändringar

## 0.1.0 — 2026-08-23

Gående skelett: fem grisar som går att tämja, kommendera, sadla, rida och föda
upp, och som bökar upp tryfflar och vittrar malm.

- Fem raser med egna kroppar (kunekune, ullgris, lantras, berkshire, tamworth)
  och egna värden för näsa, fart och liv.
- Bökandet: tryffel ur jorden i bökläget, synlig i trynet innan den faller.
- Vittringen: malm genom berget, med väderstreck och avstånd. Räckvidden är
  rasens.
- Ridning med `minecraft:rideable` + `behavior.controlled_by_player`, alltså
  riktig styrning — inte vanilla-grisens morot på pinne. Sadelväskor med kista.
- Testkedja: tio statiska spärrar plus en skarp serverkörning, och ett verktyg
  som bevisar att spärrarna faller.

### Fyra fällor som kostade tid

- **`minecraft:rooted_dirt` finns inte i Bedrock** — blocket heter
  `dirt_with_roots`. Namnet kom från Javas blocklista. Vaniljas `blocks.json` på
  disk är en ofullständig överskrivningsfil (744 poster, utan `grass_block`), så
  facit måste vara MOTORN: testet frågar `BlockTypes.get()` i en skarp körning.
- **En egenskap landar först vid tickens slut.** `setProperty` kastar inte och
  ser ut att lyckas, men `getProperty` i samma tick ger gamla värdet. Testet läste
  tillbaka direkt och rapporterade "inget i trynet" i tre körningar — ett fel i
  testet som pekade rakt på bökandet.
- **Testet tävlade mot mobbens AI.** `random_stroll` ligger i baskomponenterna
  så att en gris i bökläge inte står stilla, och mellan att kroken la jorden och
  att bökandet kördes hade grisen gått därifrån. Krokarna flyttar nu grisen till
  en känd ruta först.
- **`saturation_modifier` som sträng underkänns i egna föremål.** Vanilla skriver
  `"supernatural"` i sina, men ett eget föremål på format_version 1.20.50 vill ha
  en siffra. Felet står bara i ContentLog och föremålet blir oätligt.
