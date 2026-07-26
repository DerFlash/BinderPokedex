# Release Workflow

BinderPokedex uses one shared release-candidate build for pull requests and
tagged releases. A pull request proves that the complete release payload can be
built, but it never publishes a GitHub Release.

## Workflow boundary

```text
Build Release Candidate (reusable, read-only)
  -> fetch every configured scope
  -> validate every PDF-enabled promoted poster
  -> generate every scope in every supported language
  -> create all language ZIP archives
  -> build and verify release-manifest.json
  -> upload one temporary Actions artifact

Verify Release Build (pull request or manual)
  -> call Build Release Candidate
  -> stop after the temporary artifact

Create Release (v* tag only)
  -> call Build Release Candidate
  -> download the verified artifact
  -> publish the GitHub Release
```

The reusable build and pull-request caller have only `contents: read`
permission. Only the `publish` job in `Create Release` has `contents: write`.
The PR workflow cannot create tags, releases, commits, announcement changes, or
repository pull requests.

## Poster behavior

ComfyUI and agent-assisted authoring are not CI dependencies. Poster candidates
are generated and reviewed locally, then promoted as versioned repository
assets. The shared release build runs:

```bash
python scripts/poster_assets/validate_promoted_poster.py --all-enabled
```

after fetching current scope data and before generating PDFs. The build fails
when an enabled bundle has missing files, provenance or manifest drift, changed
prompt inputs, invalid source-pixel evidence, incorrect dimensions, or wrong
print metadata.

The normal PDF command then discovers each enabled `poster.yaml`, adds localized
logo and text, slices the text-free master, and embeds the cards. It never
starts ComfyUI.

## Pull-request release rehearsal

`.github/workflows/verify-release.yml` runs for every pull request and may also
be started manually. It calls the same reusable workflow as a tag release and
therefore builds:

- all configured scopes;
- all nine release languages;
- every language-specific ZIP;
- the release manifest;
- the exact file set consumed by the publish job.

The resulting `release-candidate` is an ordinary short-lived Actions artifact,
not a GitHub Release. Its purpose is inspection and proof that publication
could succeed from that commit.

## Tagged release

`.github/workflows/release.yml` remains restricted to `v*` tags. Its publish
job cannot start until the shared candidate build succeeds. It publishes the
already verified artifact without rebuilding PDFs or archives.

After publication, `.github/workflows/announce-release.yml` consumes the
release manifest and prepares the separate README announcement pull request.

## Release-candidate verification

`scripts/release/verify_release_candidate.py` rejects a candidate unless:

- every configured scope has generated card-count data;
- every language has at least one PDF;
- total and per-language PDF counts agree;
- all nine expected ZIP files exist and match their manifest sizes;
- every ZIP is readable and contains the expected number of PDFs.

`--skip-poster` remains a local diagnostic option. Official PR rehearsals and
tagged releases do not use it; an invalid enabled poster must fail the build
instead of silently disappearing from the release.
