# Final Report — Image Safety Foundation + WebP→PNG Node V1

Status: **FINAL CONTENT / TERMINAL CLOSURE CI PENDING**

## Objective

Extract the legacy WebP→PNG behavior as the first official Image Node Pack while making image safety, EXIF orientation, animation policy, transparency and publication explicit reusable product contracts.

## Initial state

- Slice 5 was terminally promoted at `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / run `33665431920` 5/5.
- WebP→PNG and Images→PDF both lived in the stable GUI and repeated a Pillow safety/orientation boundary.
- no canonical image package existed;
- Files/Folders remained a broader cross-platform traversal problem.

## Truth sources

- exact `main` and hosted Actions evidence;
- `K Tools Neo - Versão Estável 2.py` as legacy characterization source;
- current core Artifact/cache/type contracts;
- current Text/PDF/Documents Node Packs as one-owner/package integration references;
- Pillow release compatibility verification used only for dependency governance.

## Hypotheses and decisions

WebP→PNG was selected over Images→PDF and Files/Folders because it establishes the reusable image boundary with fewer aggregate/traversal semantics. The hypothesis that a dedicated `IMAGE_SET` was needed was not supported: FILE_SET with IMAGE Artifact members proved sufficient in workflow and registry evidence.

Pillow is locked to `>=12,<13`; 80M pixels remains the V1 ceiling. Animated WebP intentionally uses frame 0. PNG preserves alpha. Publication is NEVER, collision-safe and atomic per output rather than transactional across the full batch.

## TDD / evidence chain

- spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / run `33666227293` — 5/5;
- RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / run `33667224304` — prior suites and Pillow bootstrap green, failure at absent `ktools_images` product;
- GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / run `33667874076` — 5/5 including Image suite and real WebP→PNG smoke in all Python lanes.

## Delivered implementation

`packages/ktools-images` now owns:

- Pillow safety/decompression limits and EXIF normalization;
- image-pack PNG collision/temp/promote publication;
- one canonical WebP→PNG converter;
- direct API;
- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1, NEVER;
- IMAGE Artifact MIME/provenance/frame/orientation/mode/dimension metadata;
- hosted generated RGB/RGBA conversion smoke.

## Audit

Architecture audit passed. API and workflow adapter delegate to the same converter and do not duplicate Pillow transformation/publication algorithms. No generic cross-domain writer was introduced. No subprocess evidence is claimed. Earlier completed outputs after a later batch failure remain an explicit ownership boundary rather than being deleted speculatively.

## Compatibility debt

The stable GUI still contains its historical WebP→PNG implementation. It is frozen compatibility debt: new semantics and bug fixes originate in `ktools-images` until traditional Tool/UI surfaces are rewired.

## Residual risks / deferred work

- Pillow major upgrades require explicit evidence;
- Images→PDF still needs a distinct aggregate-PDF contract while reusing canonical image safety;
- Files/Folders still needs bounded traversal semantics;
- set-wide rollback is not implemented;
- production UI wiring is outside this slice.

## Terminal condition

The implementation and audit are complete. Formal `RESOLVED / PROMOTED` status is granted only after the synchronized memory-closure HEAD that contains this report passes all five hosted jobs. No additional code change is currently required.
