# CLI quick reference

Run the helper from the reviewed library, not from downloaded third-party code. Paths below are placeholders, not executable deployment instructions. All `--plan` CLI paths return before input/profile/target reads, network and writes. Omit plan only inside the actual authorized operation.

```sh
# Draft package only; public creation additionally needs --license.
python3 /ABSOLUTE/library/scripts/package_ops.py create /NEW/package \
  --publisher alice --name reports --visibility private

# Explicitly hash reviewed author changes and build; runs no source code/tests.
python3 /ABSOLUTE/library/scripts/package_ops.py build /ABSOLUTE/package \
  --output /NEW/reports-0.1.0.zip --refresh-manifest

python3 /ABSOLUTE/library/scripts/package_ops.py search reports --target /ABSOLUTE/project
# Add --mine only for authenticated owner-scoped search.
python3 /ABSOLUTE/library/scripts/package_ops.py install alice/reports \
  --target /ABSOLUTE/project --client claude --version 0.1.0 \
  --sha256 REVIEWED_64_HEX_DIGEST --reviewed

python3 /ABSOLUTE/library/scripts/package_ops.py update alice/reports \
  --target /ABSOLUTE/project --client claude --version 0.2.0 \
  --sha256 REVIEWED_64_HEX_DIGEST --reviewed
python3 /ABSOLUTE/library/scripts/package_ops.py list --target /ABSOLUTE/project
python3 /ABSOLUTE/library/scripts/package_ops.py list --target /ABSOLUTE/project --mine
python3 /ABSOLUTE/library/scripts/package_ops.py uninstall alice/reports --target /ABSOLUTE/project
python3 /ABSOLUTE/library/scripts/package_ops.py recover --target /ABSOLUTE/project
```

Publishing and owner withdrawal are explicit separate commands with `--reviewed` and a retained `--request-id`; publish also requires the exact `--sha256`. The token is loaded from a private profile or `--token-file`; never put a token in the command line. See `publish --help`, `delist --help`, `delete --help` for exact fields. Keep the original request ID after an unknown reply and use the read-only `operation --request-id ORIGINAL_ID` helper (API `operation.get`); never silently generate another publication.

Native skills: Claude `/palarran-package-create|search|install|update|uninstall|list`, Codex `$palarran-package-ACTION`. The installed unified plugin also exposes `/palarran:package:ACTION`. File installation alone is not client discovery, memory connectivity, signature verification or semantic package acceptance.
