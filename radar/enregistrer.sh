#!/usr/bin/env bash
# Enregistre radar/ et flux/veille/ sur la branche (appele apres chaque etape de .github/workflows/radar.yml).
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add radar/
[ -d flux/veille ] && git add flux/veille/
git diff --cached --quiet && exit 0
git commit -q -m "Radar : $1 du $(date -u +%Y-%m-%d)"
for essai in 1 2 3 4; do
  git pull -q --rebase origin "${GITHUB_REF_NAME}" && git push -q origin "HEAD:${GITHUB_REF_NAME}" && exit 0
  sleep $((10 * essai))
done
exit 1
