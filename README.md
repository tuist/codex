# openai/codex with Bazel and Once

This is the default branch of `tuist/codex`. It only holds the experiment;
`main` is an unmodified mirror of [openai/codex](https://github.com/openai/codex).

The goal is to run the same openai/codex commit through two Tuist projects so
its cache and insights can be compared:

- [tuist/codex-bazel](https://tuist.dev/tuist/codex-bazel) builds and tests with
  plain Bazel through Tuist's remote cache and Build Event Service.
- [tuist/codex-once](https://tuist.dev/tuist/codex-once) builds and tests with
  [Once](https://github.com/tuist/once) against the `codex-rs` Cargo
  workspace, so Once derives every crate, binary, and test from Cargo instead
  of loading the repository Bazel workspace. Its action results go to Tuist.

## Workflows

- `.github/workflows/sync.yml` runs every four hours: it fast-forwards `main`
  from openai/codex, disables the upstream workflows that arrive with it, and
  builds and tests the latest upstream commit with both toolchains. The
  fast-forward needs a `SYNC_TOKEN` secret (Contents and Workflows write)
  because `GITHUB_TOKEN` cannot push upstream workflow file changes; without it
  the builds still run against the upstream commit.
- `.github/workflows/codex-bazel.yml` checks out an openai/codex commit, writes
  `overlay/tuist.toml`, runs `tuist bazel setup`, and then `bazel build` and
  `bazel test`. Run it manually with a `ref` to replay any upstream commit, and
  with `remote_cache: false` for a cold baseline.
- `.github/workflows/once.yml` checks out an openai/codex commit, adds
  `overlay/once.toml` to the `codex-rs` Cargo workspace, and runs `once build`
  and `once test` from `codex-rs`. The shared cache and run reporting go to the
  `tuist/codex-once` Tuist project. The defaults build the `codex` binary
  (`cargo_codex_cli_bin_codex`) and run one Cargo test target.

Both build workflows authenticate to Tuist with GitHub OpenID Connect
(`id-token: write`), so no long-lived secret is needed. The `tuist/codex`
repository is connected to both Tuist projects, which is what the OIDC exchange
uses to resolve them.

Both workflows only run the `ubuntu-24.04` leg by default. Pass
`include_macos: true` to add a `macos-14` leg when GitHub-hosted macOS capacity
is available to the fork.

Once works from Cargo, so its graph is the `codex-rs` workspace rather than
the Bazel one. Override `build_target` and `test_target` with any
`once query targets` id from `codex-rs`.

Upstream workflows are disabled in this fork so nothing from openai/codex's
release or deploy automation runs here.
