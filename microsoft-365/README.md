# Elfsquad agent for Microsoft 365 Copilot

A declarative agent whose one action is the Elfsquad MCP server at `https://api.elfsquad.io/mcp`. Copilot
discovers the tools when it runs, so new server tools reach users without a new package.

| File | What it is |
|---|---|
| `appPackage/manifest.json` | Microsoft 365 app manifest: name, descriptions, icons, publisher URLs |
| `appPackage/declarativeAgent.json` | The agent: description, conversation starters, the MCP action |
| `appPackage/instructions.md` | The agent's instructions, a condensed form of the plugin skills (8,000 characters at most) |
| `appPackage/ai-plugin.json` | Plugin manifest v2.4 with the `RemoteMCPServer` runtime and OAuth |
| `appPackage/color.png`, `outline.png` | 192×192 colour icon and 32×32 white outline icon |
| `build.py` | Builds the upload ZIP |

## Sign-in

Copilot signs in with the pre-registered client `m365-copilot` and the redirect URI
`https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`. The Developer Portal requires a client
secret, so this client has one, sent in the token request body, and uses PKCE as well. The client is
registered once, in the Teams Developer Portal under **Tools → OAuth client registration**:

| Field | Value |
|---|---|
| Base URL | `https://api.elfsquad.io/mcp` |
| Restrict usage by org | Any Microsoft 365 organization |
| Restrict usage by Teams app | Any Teams app, while testing and through store validation (see below) |
| Client ID | `m365-copilot` |
| Client secret | The secret Elfsquad generated for `m365-copilot` (kept by Elfsquad, not in this repository) |
| Client password authentication method | Request body parameters |
| Authorization endpoint | `https://login.elfsquad.io/oauth2/auth` |
| Token and refresh endpoint | `https://login.elfsquad.io/oauth2/token` |
| Scope | `openid offline_access Elfskot.Api` |
| PKCE | on |

The registration ID it returns goes into the package at build time. It is not a secret.

A package uploaded to a tenant as a custom app gets an app ID from that tenant, not the `id` in
`manifest.json`. A registration restricted to the manifest ID then fails before sign-in: Copilot reports a
token-store or authentication error and never reaches Elfsquad's login. Keep "Any Teams app" while
testing uploaded packages. The Developer Portal labels that option for testing and store validation only,
so once the store listing is live, restrict the registration to the app ID the store gives it.

## Build

```
ELFSQUAD_OAUTH_REGISTRATION_ID=<registration id> microsoft-365/build.py
```

The script inlines `instructions.md`, fills in the registration ID, checks Microsoft's length and icon
limits, and writes `microsoft-365/build/elfsquad-m365-<version>.zip`. Raise `version` in `manifest.json` for
every package you submit.

## Try it in a tenant

Upload the ZIP in the Microsoft 365 admin center (**Agents → Tools → Registry → Upload**), or in Teams under
**Apps → Manage your apps → Upload an app** with custom app upload allowed. Then open Copilot, pick the
Elfsquad agent and sign in. The Elfsquad consent screen names Microsoft 365 Copilot and asks for one
environment.
