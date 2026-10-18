#!/usr/bin/env bash
# Upload completely before publishing; a failed upload leaves a resumable draft.
set -euo pipefail
tag=${1:?Provide the existing version tag}
artifacts=${2:?Provide the release artifact directory}
mapfile -d '' files < <(find "$artifacts" -maxdepth 1 -type f -print0)
test "${#files[@]}" -gt 0
if draft=$(gh release view "$tag" --json isDraft --jq .isDraft 2>/dev/null); then
    test "$draft" = true || { echo 'Release is already published; refusing to replace its assets.' >&2; exit 1; }
else
    gh release create "$tag" --verify-tag --draft \
        --title "Plasma Shortcut Explorer $tag" --notes-file CHANGELOG.md
fi
gh release upload "$tag" "${files[@]}" --clobber
gh release edit "$tag" --draft=false --latest
