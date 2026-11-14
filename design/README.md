# Profile visuals

Actual React Bits Folder, Gooey Nav and Decrypted Text components rendered with React + Remotion.

```sh
npm ci
npm run dev -- --no-open
```

Open the Benny composition for the live Folder and text interactions; Links contains Gooey Nav with the real destinations.

To export:

```sh
npx remotion render Benny ../assets/profile-header.gif --codec=gif
npx remotion still Benny ../assets/profile-header.png --frame=75
npx remotion still Links links.png
```

The README contains linked image exports because GitHub Markdown does not execute React. The GIF uses a deterministic clock; the Studio preview keeps real interactions. The four nav segments link independently in the README.

See THIRD_PARTY.md for component provenance and license terms.
