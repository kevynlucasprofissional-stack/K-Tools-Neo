# ktools-pdf

Official K-Tools PDF Node Pack.

Canonical V1 capabilities:

- ordered local PDF merge via `pdf.merge.files: FILE_SET -> PDF`;
- balanced local PDF split via `pdf.split.parts: FILE -> FILE_SET`;
- checked local PDF reading, protected/corrupt fail-closed behavior and shared atomic PDF publication;
- direct APIs and workflow nodes delegating to the same capability owners.

The stable legacy GUI remains a compatibility caller/debt surface; new PDF merge/split semantics belong here.
