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
  because `GITHUB_TOKEN` cannot push upstream workflow file changes.
- `.github/workflows/codex-bazel.yml` checks out an openai/codex commit, writes
  `overlay/tuist.toml`, runs `tuist bazel setup`, and then `bazel build` and
  `bazel test`. Run it manually with a `ref` to replay any upstream commit, and
  with `remote_cache: false` for a cold baseline.
- `.github/workflows/once.yml` checks out an openai/codex commit, adds
  `overlay/once.toml`, and runs `once build` and `once test`. The shared cache
  and run reporting go to the `tuist/codex-once` Tuist project.

Upstream workflows are disabled in this fork so nothing from openai/codex's
release or deploy automation runs here.
