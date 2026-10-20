# Unicode Standard and Unicode Character Database (UCD): latest release and file paths — research digest

**As of 2026-10-20.** Question: What is the latest released version of the Unicode Standard and its Character Database, its release date, and has a later version been published since UCD 18.0.0 — and do DerivedGeneralCategory.txt, Scripts.txt, ScriptExtensions.txt, DerivedCoreProperties.txt, PropList.txt, CaseFolding.txt, PropertyAliases.txt and PropertyValueAliases.txt each exist in it at the path the release publishes?

## Answer

The latest released version is the Unicode Standard 18.0.0 with the Unicode Character Database 18.0.0, released 2026-09-16. That date is the release page's date line; the `Public/18.0.0/` directory stamp and the unicodetools tag name agree. No later version has been published as of 2026-10-20. The highest numbered directory under unicode.org/Public/ is 18.0.0, with no 18.0.1, 18.1.0 or 19.x, and the versions page names 18.0.0 as the latest and mentions nothing later. All eight files exist in the release under https://www.unicode.org/Public/18.0.0/:
- `ucd/DerivedCoreProperties.txt`
- `ucd/PropList.txt`
- `ucd/CaseFolding.txt`
- `ucd/PropertyAliases.txt`
- `ucd/PropertyValueAliases.txt`
- `ucd/Scripts.txt`
- `ucd/ScriptExtensions.txt`
- `ucd/extracted/DerivedGeneralCategory.txt`

DerivedGeneralCategory.txt is in the `extracted/` subdirectory and is not in the top level of `ucd/`. All eight are present under their expected names, and the listings show no near-name variants that would indicate a split. The release's tag in the unicodetools repository is `final-18.0-20260916`, not an `18.0.0`-shaped name. The release page's own body still carries beta-review wording. "Released" therefore rests on the other primaries below, not on that page (see Confidence and gaps).

## Evidence

- https://www.unicode.org/versions/ — retrieved 2026-10-20 — under "The Unicode Standard, Latest Version": "The Unicode Standard, Version 18.0.0, (South San Francisco: The Unicode Consortium, 2026." The page dates the version by year only. Its version list runs 18.0.0 (2026), 17.0.0 (2025), 16.0.0 (2024), 15.1.0 (2023), and it names no beta, draft, 18.0.1, 18.1 or 19.0.
- https://www.unicode.org/versions/Unicode18.0.0/ — retrieved 2026-10-20 — heading "Unicode® 18.0.0", date line "2026 September 16", link text "Announcement". Also: "Data files for Version 18.0 of the Unicode Character Database are available." and "This version supersedes all previous versions of the Unicode Standard."
  - File notes: the new data files named are "JurchenSources.txt" and "SealSources.txt". It also says "The UCD file Index.txt has not been updated for Unicode Version 18.0; the file published in Version 18.0 is identical to the file for Version 17.0." and "This file is obsolete and will be removed altogether in Unicode Version 19.0." It states no file removed, renamed, split or withdrawn, and names none of the eight in any change.
  - The same page also opens with "This is a preliminary draft page for an upcoming release." and "During the beta review period, feedback about errors on this page will be helpful and appreciated."
- https://www.unicode.org/Public/18.0.0/ReadMe.txt — retrieved 2026-10-20 — "This directory contains final data files and charts for version 18.0.0 of the Unicode Character Database and for the synchronized Unicode Technical Standards." The text wraps after "of the" in the source. The words beta, draft and preliminary do not occur in the file.
- https://www.unicode.org/Public/ — retrieved 2026-10-20 — the only numbered entries from 17 up are "17.0.0/" (2026-02-04 17:49) and "18.0.0/" (2026-09-16 10:03). UCA/, UCD/, emoji/, idna/, security/ and zipped/ are all stamped 2026-09-16 10:16. Also listed and not opened: draft/ (2026-09-30 16:04) and latest/ (2025-11-19 12:39).
- https://www.unicode.org/Public/18.0.0/ucd/ — retrieved 2026-10-20 — "Index of /Public/18.0.0/ucd" lists these rows, each stamped 2026-09-01 15:29: DerivedCoreProperties.txt 1.1M, PropList.txt 146K, CaseFolding.txt 87K, PropertyAliases.txt 9.7K, PropertyValueAliases.txt 82K, Scripts.txt 191K, ScriptExtensions.txt 21K. It also lists the subdirectory `extracted/`. DerivedGeneralCategory.txt is not in this listing, and no Scripts-*.txt or other variant spellings appear.
- https://www.unicode.org/Public/18.0.0/ucd/extracted/ — retrieved 2026-10-20 — "Index of /Public/18.0.0/ucd/extracted" lists the row DerivedGeneralCategory.txt, 2026-09-01 15:29, 276K, and no other DerivedGeneral* file.
- https://github.com/unicode-org/unicodetools/tags — retrieved 2026-10-20 — newest tag on the first page of the list is "final-18.0-20260916" (Sep 16, 2026). The next release tags are "final-17.0-20250910", "final-16.0-20240912" and "final-15.1-20230908". No tag on that page uses the 18.0.0 or 17.0.0 form. The page's dates are not release dates (the 17.0 tag shows Aug 16, 2025 against a name suffix of 20250910), so only the tag's name is used here.

## What would change this

The request's trigger was: a version later than 18.0.0 is released, or one of the eight files is renamed, split or withdrawn. It did not fire as of 2026-10-20. There is no later numbered directory under /Public/ and no later version on the versions page. All eight files are present under their expected names, and the release page records no change to any of them; its file notes are the two additions and the Index.txt note above. The plan stands.

Two signals for a re-check:
- The versions page says "Starting with Unicode 14.0, each of those releases is targeted for the third quarter of each year." This is as the fetch tool quoted it; I did not see the sentence's antecedent. It points to the next major release in the third quarter of 2027.
- The versions list also carries update releases (15.1.0 in 2023, 12.1.0 in 2019), so an x.y.1 or x.1.0 release can land between majors.

## Confidence and gaps

High for the version (18.0.0), the eight paths, and "no later version". Each rests on at least two unicode.org pages that agree: the versions page, the /Public/ listing, the version directory's own ReadMe.txt, and the two directory listings. The unicodetools tag name is a further primary that agrees. Budget: 8 of 8 fetches used, no searches. Unresolved or not done:

1. **Release-page banner.** The page at /versions/Unicode18.0.0/ still opens with "This is a preliminary draft page for an upcoming release." and repeats "During the beta review period" in its Unicode Character Database section. It never calls 18.0 the current release, yet it carries the date line 2026 September 16.
   - I read this as an unremoved beta banner. The version directory's ReadMe.txt says "final", the /Public/ stamps and the tag `final-18.0-20260916` point to 2026-09-16, and the versions page lists 18.0.0 as the latest.
   - No source says so explicitly, so it is an inconsistency on unicode.org's side. Cite the release page for its date line and file notes, not for "released".
2. **How it was read.** The fetch tool returns a small model's reading of each page, not its bytes. The quotes and listing rows above are as it returned them, and nothing was re-read as raw text.
3. **Release status.** The versions page dates 18.0.0 by year only, and the fetch tool reported that it does not say "released" in so many words. The day and the final status come from the other primaries.
4. **Not opened at the budget.**
   - The unicodetools tree at the tag was not opened. Whether the eight files are checked into the repository at that tag is unchecked, especially the derived DerivedCoreProperties.txt and DerivedGeneralCategory.txt. The tag's commit SHA is also unrecorded.
   - The contents of the eight files were not read, so existence rests on the listings (header lines such as "Scripts-18.0.0.txt" were not seen).
   - /Public/draft/, /Public/latest/ and /Public/UCD/ were not opened. I take draft/ to be unreleased working data but did not verify it. Nothing above depends on any of them, because every path given is a versioned 18.0.0 path.
   - UAX #44 was not read. The release page's UAX #44 row says its section on the directory structure under /Public/draft/ and versioned directories "was rewritten" for 18.0. I did not check whether it names a different location for any of the eight.
