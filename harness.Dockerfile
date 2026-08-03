# Pinned-CLI harness image.
#
# The published sandbox-harness tags (v0.0.14, v0.0.15) both ship Claude Code
# 2.1.207 and codex-cli 0.144.1. An experiment that needs different CLI
# versions builds this image on top of the published base and overrides the two
# npm globals, so the harness line in RESULTS.md can name an exact base tag plus
# the exact CLI versions that ran.
#
#   podman build -f harness.Dockerfile \
#       --build-arg CLAUDE_VERSION=2.1.220 \
#       --build-arg CODEX_VERSION=0.146.0 \
#       -t sandbox-harness:pinned-cc2.1.220-cx0.146.0 .
#
# Then point run.sh at it: IMAGE=sandbox-harness:pinned-... ./run.sh ...

ARG BASE_TAG=v0.0.15
FROM ghcr.io/latere-ai/sandbox-harness:${BASE_TAG}

ARG CLAUDE_VERSION
ARG CODEX_VERSION

USER root

# Both CLIs live in /usr/local/lib/node_modules in the base image, and
# /usr/local/bin comes first on PATH — so the install has to target that prefix
# explicitly. The base sets NPM_CONFIG_PREFIX=/home/agent/.npm-global, whose bin
# dir is *last* on PATH, so a plain `npm install -g` installs the new versions
# somewhere they are permanently shadowed by the old ones.
#
# The checks assert the exact versions rather than just printing them: that
# shadowing failure is silent, and codex ships its real binary as a per-platform
# optional dependency, so a failed platform resolution is silent too.
RUN npm install -g --prefix /usr/local --no-fund --no-audit \
        "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
        "@openai/codex@${CODEX_VERSION}" \
 && claude --version | grep -qF "${CLAUDE_VERSION}" \
 && codex --version  | grep -qF "${CODEX_VERSION}"

USER agent
