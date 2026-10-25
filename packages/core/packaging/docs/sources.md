# Primary sources and adaptations

Read2026-10-25. These references motivate specific boundaries; our schema, limits, transactions and numeric targets are Palarran choices, not vendor performance claims.

| Source | Applied principle | Boundary |
|---|---|---|
| [GitHub Packages permissions](https://docs.github.com/en/packages/learn-github-packages/about-permissions-for-github-packages) | Package access and repository access are separate; public/private and scoped permissions must be explicit | We use configured publishers/readers, not GitHub auth or GitHub Packages protocol |
| [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Least privilege, immutable reviewed subjects and untrusted third-party code | SHA256 integrity is not a package signature or a permission grant |
| [OWASP file upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Allowlist paths/types, bound expanded archives, authorize downloads and store outside served roots | Pattern checks do not prove absence of secrets or prompt injection |
| [PyPA installed project records](https://packaging.python.org/en/latest/specifications/recording-installed-packages/) | File records support traceable management/removal | Our receipts are not Python wheel/RECORD compatibility |
| [npm unpublish](https://docs.npmjs.com/cli/v11/commands/npm-unpublish/) | Withdrawal has dependency/reproducibility consequences | Our explicit delist/tombstone policy does not copy npm timing rules |
| [AWS S3 model](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) and [object metadata](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingMetadata.html) | Blob identity/storage and mutable registry metadata have separate owners | The default needs no cloud; S3-compatible deployments need provider-specific acceptance |
| [Python ZIP](https://docs.python.org/3.9/library/zipfile.html) | Inspect metadata/contents without blindly extracting | Existing Python3.9 compatibility is retained, not an assertion it is a current supported release |
| [Google SRE objectives](https://sre.google/sre-book/service-level-objectives/) | SLO measurements differ from contractual SLA | The plan's250ms/99.5% proposals are ours and not observed production guarantees |

No proprietary snippets are copied. Archive and installer logic are original implementation; tests use synthetic owned fixtures.
