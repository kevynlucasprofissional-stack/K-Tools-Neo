# Plan — Image Safety Foundation + WebP→PNG Node V1

Status: **COMPLETE / TERMINAL CLOSURE CI PENDING**

## Executed sequence

1. Preserved terminal Slice-5 evidence `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.
2. Fresh-compared WebP→PNG, Images→PDF and bounded Files/Folders.
3. Selected WebP→PNG as the first Image Node Pack slice and locked Pillow/image semantics before code.
4. Landed docs-only spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3`; run `33666227293` passed 5/5.
5. Landed discriminating RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc`; run `33667224304` proved the missing Image product after prior suites and Pillow bootstrap.
6. Implemented `ktools-images` with safety, publication and one converter owner.
7. Exposed thin direct API + `image.webp_to_png` node.
8. Added root CI installation/tests and real generated RGB/RGBA workflow smoke.
9. Audited for duplicated image semantics, Artifact/cache/failure boundaries and premature abstractions.
10. Exact technical GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076` passed 5/5.
11. Prepared ADR, evidence, final report and canonical memory closure.
12. Remaining gate: this synchronized closure HEAD must pass five hosted jobs before formal promotion.

## Implemented architecture

```text
ktools_images.safety
  -> Pillow version-independent V1 policy surface: pixel/bomb/orientation

ktools_images.publication
  -> image-pack collision + PNG temp/promote cleanup

ktools_images.converter
  -> canonical convert_webp_files_to_png
       -> safety + Pillow frame/orientation/mode normalization + publication

ktools_images.api
  -> converter owner

ktools_images.node
  -> converter owner
```

No generic media registry, IMAGE_SET or cross-domain atomic writer was introduced.

## Audit result

PASS: package dependency, safety ceiling, first-frame animation policy, EXIF, alpha, later-source failure, IMAGE Artifact metadata/snapshots, NEVER/republication, direct/workflow equivalence, single converter ownership and hosted real-PNG verification are all covered by executed evidence.
