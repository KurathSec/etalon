# The census

This is the denominator. Coverage of the leak-class space is a reported quantity
with its own `n`, and without a committed census that `n` does not exist and any
coverage figure is an assertion.

One row per published timing result, each with a facet tuple drawn from the
closed vocabulary in `data/classes.toml` and an explicit adjudication. The
corpus then covers some fraction of the attested cells, and the cells it does
not cover are printed by name rather than omitted.

**This is a seed, not a complete census, and `census_status` says so.** A partial
census makes coverage look better than it is, so the status travels with the
number and the intended full population is stated: the timing-attack CVE
population studied by Kholoosi, Babar and Yilmaz (arXiv 2308.11862) over the
National Vulnerability Database from March 2003 to December 2022, plus the
constant-time literature since.

Every identifier here was resolved against Crossref, the USENIX proceedings or
the CVE record during entry, not from memory. One was corrected in the process:
Minerva is recorded elsewhere in this programme under `10.13154/tches.v2020.i4.281-308`,
which does not resolve; the live registration is `10.46586/...`, the prefix
IACR moved to.

An entry may be **excluded**, and the reason is recorded rather than the row
being deleted. An excluded row still counts as evidence that the class was
considered.
