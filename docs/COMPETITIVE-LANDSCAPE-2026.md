# 2026 Mobile-to-PC Agent Architecture Comparison

As of November 2026, major AI labs have converged on remote computer control—accepting local attack-surface trade-offs to achieve mobile convenience. Google stands positioned to differentiate on **security isolation and datacenter compute speed**.

---

## Architectural Matrix (November 2026)

> **Note:** Capabilities and OS support reflect documented public releases and previews as of November 2026 and vary by subscription tier and client version.

| Provider | Product / Feature | Connection Mechanism | Execution Location | Local PC Blast Radius |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | **ChatGPT Dots** & **Codex Remote** | Desktop `Allow access` daemon, QR pairing, or SSH host link | User's local Mac/Windows/SSH host | **High** — Direct local filesystem & shell execution |
| **Anthropic** | **Claude Code Remote Control** & **Cowork** | Paired local terminal session & synced desktop workspace | User's local Windows/macOS/Linux CLI | **Moderate–High** — Executes in local user context with mobile prompts |
| **Moonshot AI** | **Kimi Code Desktop** & **Kimi CLI** | `Settings -> Remote Control` QR URL & SSH execution | User's local PC or SSH host | **High** — Direct shell and local directory control |
| **Meta** | **Muse** | Cloud VM initiating outbound SSH / Tailscale into user host | Hybrid (Cloud VM + tunneled local host) | **High** — Cloud VM holds authorized SSH/tailnet path into LAN |
| **xAI** | **Grok Bot** | Persistent cloud VM paired with desktop client (`.deb`/`.rpm`/Win/Mac) | Hybrid (Cloud VM + local command client) | **High** — Desktop client runs approved local shell & file ops |
| **Google (Current)** | **Gemini App / Live** + **Gemini CLI** | None natively (Jules read-only Nov 11, 2026; Antigravity local/web) | Split (Cloud chat vs. manual local CLI) | **Low**, but high manual transfer friction |
| **Google (Proposed)** | **Air-Gapped Cloud-Drive Relay** | Voice -> Borg/gVisor -> Drive Staging -> Outbound Local Pull | **Google Cloud** (build) + **User PC** (verified run) | **Minimal** — Zero inbound ports, zero background local daemons |

---

## Strategic Takeaway for Google

Competing tools treat the user's home PC as the primary compute node and stretch a remote-control wire back to the user's phone. That design forces compilation, package downloads, and test suites through home broadband and keeps the user's workstation powered on and network-exposed.

Google owns **Gemini Live** (real-time voice), **Antigravity 2.0** (artifact-driven multi-agent engineering), **Borg + gVisor** (battle-tested sandboxing), and **Google Drive on Colossus** (ubiquitous cloud storage already tied to every Google account). Connecting those four layers via a scoped staging relay leapfrogs direct-tunneling competitors on speed, battery/power efficiency, and enterprise-grade Zero Trust security.
