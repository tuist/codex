# openai/codex with Bazel and Once

This is the default branch of `tuist/codex`. It only holds the experiment;
`main` is an unmodified mirror of [openai/codex](https://github.com/openai/codex).

The goal is to run the same openai/codex commit through two Tuist projects so
its cache and insights can be compared:

- [tuist/codex-bazel](https://tuist.dev/tuist/codex-bazel) builds and tests with
  plain Bazel through Tuist's remote cache and Build Event Service.
- [tuist/codex-once](https://tuist.dev/tuist/codex-once) builds and tests with
  [Once](https://github.com/tuist/once), which derives its graph from the
  repository Bazel workspace and stores action results in Tuist.

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
  `overlay/once.toml`, and runs `once build` and `once test`. The shared cache
  and run reporting go to the `tuist/codex-once` Tuist project.

Both build workflows authenticate to Tuist with GitHub OpenID Connect
(`id-token: write`), so no long-lived secret is needed. The `tuist/codex`
repository is connected to both Tuist projects, which is what the OIDC exchange
uses to resolve them.

Both workflows only run the `ubuntu-24.04` leg by default. Pass
`include_macos: true` to add a `macos-14` leg when GitHub-hosted macOS capacity
is available to the fork.

Once derives the same Bazel graph, but its Bazel ownership path runs
`bazel aquery deps(<label>)` for every target. That analysis currently fails for
the larger codex targets (`//codex-rs/cli:codex`, `//codex-rs/apply-patch:...`),
so the Once defaults build a leaf crate (`//codex-rs/ansi-escape`) while the
Bazel defaults build the `codex` binary. Override `build_target` and
`test_target` to try other targets.

Upstream workflows are disabled in this fork so nothing from openai/codex's
release or deploy automation runs here.
