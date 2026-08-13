# Integration guide

Dopamine ships one canonical skill and deterministic adapters for every agent family covered here. The adapters are generated from `skills/dopamine/SKILL.md`; CI rejects stale copies.

## What “verified” means

These labels are intentionally strict:

- **Runtime discovery:** an installed host listed the Dopamine skill from this checkout.
- **Vendor validation:** the host's own validator accepted the package.
- **Local validation:** repository tests parse the manifest, verify referenced paths, enforce version/name consistency, and check generated adapters byte-for-byte.
- **Portable adapter:** the repository supplies the documented instruction file, but that host was not installed here. This is format support, not a claim that a live session was exercised.

No integration is described as runtime-tested unless its CLI actually ran on the development machine.

## Support matrix

| Agent | Integration supplied | Verification in this repository |
|---|---|---|
| Claude Code | `.claude-plugin/plugin.json`, marketplace, `skills/` | **Vendor validation** with Claude Code 2.1.220 |
| Codex | `.codex-plugin/plugin.json`, Codex marketplace, `skills/` | **Local plugin-schema validation**; Codex CLI 0.147.0 install commands confirmed |
| OpenCode | `.opencode/skills/dopamine/` | **Runtime discovery** with OpenCode 1.17.15 |
| Gemini CLI | `gemini-extension.json` + `AGENTS.md` | **Vendor validation** with Gemini CLI 0.44.1 |
| Pi | `package.json` with `pi.skills` | **Local validation** and successful `npm pack --dry-run`; Pi CLI unavailable locally |
| GitHub Copilot CLI | `.github/plugin/` and `.github/copilot-instructions.md` | **Local validation**; Copilot CLI unavailable locally |
| GitHub Copilot Chat/editor | `.github/copilot-instructions.md` | **Local validation** against GitHub's documented path |
| Cursor | `.cursor/rules/dopamine.mdc` | **Local validation** against Cursor's documented MDC format |
| Windsurf | `.windsurf/rules/dopamine.md` | **Local validation** against Windsurf's documented `always_on` format |
| Cline | `.clinerules/dopamine.md` | **Local validation** against Cline's documented rule path |
| Kiro | `.kiro/steering/dopamine.md` | **Local validation** against Kiro's documented `inclusion: always` format |
| Qoder | `.qoder-plugin/plugin.json`, `.qoder/rules/` | **Local validation**; Qoder unavailable locally |
| Devin CLI | `.devin-plugin/plugin.json`, `skills/` | **Local validation**; Devin CLI unavailable locally |
| Grok Build | `.grok-plugin/marketplace.json`, `.grok/skills/` installer target | **Local validation**; Grok Build unavailable locally |
| OpenClaw | `.openclaw/skills/dopamine/` and installer target | **Local validation**; OpenClaw unavailable locally |
| Hermes Agent | `plugin.yaml`, `skills/` | **Local validation**; Hermes Agent unavailable locally |
| Antigravity CLI | `.agents/rules/dopamine.md`, `AGENTS.md` | **Portable adapter** |
| CodeWhale | `plugin.json`, `AGENTS.md` | **Portable adapter** |
| Swival | `plugin.json`, `AGENTS.md` | **Portable adapter** |
| Aider | `AGENTS.md` for `aider --read AGENTS.md` | **Portable adapter**; Aider is installed, but no paid-model session was run |
| Zed | `AGENTS.md` | **Portable adapter** |
| JetBrains Junie | `AGENTS.md` | **Portable adapter** |
| Amp | `AGENTS.md` | **Portable adapter** |
| Jules | `AGENTS.md` | **Portable adapter** |

This covers the complete 24-agent target set audited for this release. It does not pretend all of those vendors share one plugin standard, and it does not turn structural validation into a runtime claim.

## Install from a checkout

Clone once:

```sh
git clone https://github.com/ujjwalredd/Dopamine.git
cd Dopamine
```

Install all verified user-scope filesystem targets:

```sh
./scripts/install.sh --agent all --scope user
```

That installs Codex, Claude Code, OpenCode, Grok Build, OpenClaw, Windsurf, Cline, GitHub Copilot CLI, and Kiro targets. Cursor and Qoder expose only project targets in this installer because no verified user-scope filesystem destination was found.

Install all project-native targets into another repository:

```sh
./scripts/install.sh --agent all --scope project --project /path/to/repository
```

Choose one target with `--agent codex`, `claude`, `opencode`, `grok`, `openclaw`, `cursor`, `windsurf`, `cline`, `copilot`, `kiro`, or `qoder`. The installer preflights every destination and refuses to overwrite existing instructions.

For an AGENTS-compatible host without a dedicated target:

```sh
./scripts/install.sh --agent portable --scope project --project /path/to/repository
```

If that repository already has `AGENTS.md`, merge Dopamine manually. The installer deliberately will not overwrite it.

## Native package installation

### Codex

```sh
codex plugin marketplace add ujjwalredd/Dopamine
codex plugin add dopamine@dopamine
```

Or use the dependency-free checkout installer:

```sh
./scripts/install.sh --agent codex --scope user
```

### Claude Code

```text
/plugin marketplace add ujjwalredd/Dopamine
/plugin install dopamine@dopamine-skills
```

### Gemini CLI

```sh
gemini extensions install https://github.com/ujjwalredd/Dopamine
```

### Pi

```sh
pi install git:github.com/ujjwalredd/Dopamine
```

Pi will load only the declared `skills/` resource. Dopamine contains no Pi extension code and no runtime dependencies.

### Aider

```sh
aider --read AGENTS.md
```

Run that from a checkout containing Dopamine's `AGENTS.md`, or install the portable adapter into the target project first.

## Maintainer verification

```sh
python3 scripts/validate_skill.py
python3 scripts/generate_integrations.py --check
python3 -m unittest discover -s tests -v
claude plugin validate .
gemini extensions validate .
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
opencode debug skill
npm --cache /tmp/dopamine-npm-cache pack --dry-run --json
```

The first three commands are dependency-free and run in CI. Host CLI checks run only when that host is installed.

## Primary format references

- [OpenAI Agent Skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [Gemini CLI extensions](https://geminicli.com/docs/extensions/)
- [Pi packages](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/packages.md)
- [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [Cursor rules](https://docs.cursor.com/context/rules)
- [Windsurf rules](https://docs.windsurf.com/windsurf/cascade/memories)
- [Cline rules](https://docs.cline.bot/customization/cline-rules)
- [Kiro steering](https://kiro.dev/docs/steering/)
- [Aider conventions](https://aider.chat/docs/usage/conventions.html)
