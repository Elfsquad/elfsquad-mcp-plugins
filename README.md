# Elfsquad MCP plugins

Skills that teach Claude and ChatGPT to work in [Elfsquad](https://www.elfsquad.io), the
configure-price-quote (CPQ) platform, through the Elfsquad MCP server:

```
https://api.elfsquad.io/mcp
```

The server supplies the tools. This plugin supplies the know-how: which tool to call for a job, in what
order, with which arguments, and what to check afterwards. It ships one plugin, `elfsquad`, in two formats:
a Claude Code plugin and an OpenAI (ChatGPT and Codex) plugin. `microsoft-365/` holds the same know-how as a
Microsoft 365 Copilot agent.

## Skills

| Skill | Covers |
|---|---|
| `elfsquad-getting-started` | Selecting an environment, the tenant handle, Read and Write access, errors, the documentation search |
| `elfsquad-data-queries` | Filtering, counting and looking up any data with `QueryData` and the Search tools |
| `elfsquad-feature-models` | Building and editing feature models: features, nodes, structure, properties, dynamic groups, linked models, validation, 3D |
| `elfsquad-model-rules` | Requires, excludes, calculated values, hide conditions, price formulas and expressions |
| `elfsquad-configurator` | Starting and changing configurations, conflicts, prices, the Order Entry view |
| `elfsquad-quotations` | Quotations, statuses, CRM accounts and the prices on a quote |

The skills use the MCP tools only. Work that has no tool yet (publishing a model, configurator steps,
discounts, quotation documents, users and settings) is done in the Elfsquad app, and the skills say so.

## Signing in

The MCP server uses OAuth. When you connect the Claude or ChatGPT app, Elfsquad asks you to sign in and
shows a consent screen that names the assistant, says it will read and change data with your own
permissions, and asks you to choose **one environment**. The connection can only reach that environment. To
work in another one, reconnect and pick it. Elfsquad asks for consent on every new authorization; it does not
remember the decision.

Claude Code signs in with your Elfsquad account without a consent screen. The assistant then lists the
environments you have access to and asks which one to use.

What the assistant may do is what you may do: your roles and permissions in that environment apply. On top
of that, each user has an MCP access level per environment, Read (the default) or Write. With Read access the
assistant can look at everything you can see and run configurations, but every change to data is refused.
An administrator of the environment grants Write access.

Elfsquad does not offer dynamic client registration. Assistants sign in with an OAuth client that Elfsquad
registered for them in advance: `claude` for the Claude apps' connector, `claude-mcp` for Claude Code, and
`openai` for ChatGPT, and `m365-copilot` for Microsoft 365 Copilot. The plugin files already name the right client, so there is nothing to enter.

## Install in Claude

**Claude (web, desktop and Cowork).** Two parts:

1. The connection. Add the Elfsquad connector with the URL `https://api.elfsquad.io/mcp` and sign in. On a
   Team or Enterprise plan, an Owner adds it once under **Organization settings → Connectors**.
2. The skills. Add this repository under **Customize → Plugins → Add → Add marketplace** and install
   `elfsquad`. On a Team or Enterprise plan, an Owner can do this for everyone under **Organization
   settings → Plugins & skills**.

**Claude Code** (version 2.1.231 or later). Add this repository as a plugin marketplace and install the
plugin:

```
/plugin marketplace add Elfsquad/elfsquad-mcp-plugins
/plugin install elfsquad@elfsquad-mcp-plugins
```

Then run `/mcp`, choose `plugin:elfsquad:elfsquad` and **Authenticate**. Your browser opens the Elfsquad
login. Sign-in returns to `http://localhost:51000/callback`, so port 51000 must be free while you sign in.

To add only the connection, without the skills:

```
claude mcp add --transport http --client-id claude-mcp --callback-port 51000 elfsquad https://api.elfsquad.io/mcp
```

The plugin's tools are named `mcp__plugin_elfsquad_elfsquad__<ToolName>`. To be asked before anything is
deleted, add the destructive tools to `permissions.ask` in your settings:

```json
{
  "permissions": {
    "ask": [
      "mcp__plugin_elfsquad_elfsquad__DeleteFeatureModelNodes",
      "mcp__plugin_elfsquad_elfsquad__DeleteRelationships",
      "mcp__plugin_elfsquad_elfsquad__DeleteFeaturePropertyValues",
      "mcp__plugin_elfsquad_elfsquad__DeleteDynamicGroups",
      "mcp__plugin_elfsquad_elfsquad__DeleteThreeDModel"
    ]
  }
}
```

## Install in ChatGPT

The plugin is in `plugins/elfsquad/`, in the portable format described in the
[OpenAI plugin docs](https://developers.openai.com/plugins/build/plugins):

- `plugin.json` is the manifest, with the listing text under `extensions["com.openai"].interface`.
- `mcp.json` declares the server as `streamable-http` with OAuth, using the pre-registered public client
  `openai` (`client.mode: "provided"`, `tokenEndpointAuthMethod: "none"`). Sign-in uses the authorization
  server the MCP endpoint advertises.
- `skills/` holds the skills; `assets/icon.png` is the icon.
- `.codex-plugin/plugin.json` and `.mcp.json` are the Codex compatibility files, used when the portable
  manifest is not read.

To use it in a ChatGPT workspace, zip the `plugins/elfsquad/` folder and upload it as a workspace plugin, or
point Codex at this repository's marketplace file, `.agents/plugins/marketplace.json`.

## Install in Microsoft 365 Copilot

`microsoft-365/` is a declarative agent with the MCP server as its action. Its README describes the OAuth
registration and how to build and upload the app package. Until it is listed in the Microsoft 365 Agent
Store, an administrator can upload the package to their own tenant.

## Repository layout

```
.claude-plugin/marketplace.json     Claude Code marketplace
.agents/plugins/marketplace.json    Codex / ChatGPT marketplace
plugins/elfsquad/
  .claude-plugin/plugin.json        Claude Code manifest
  .mcp.json                         MCP server for Claude Code (and Codex)
  .codex-plugin/plugin.json         Codex manifest
  plugin.json                       Portable manifest (ChatGPT)
  mcp.json                          Portable MCP server declaration with OAuth
  assets/icon.png
  skills/<skill>/SKILL.md
  skills/<skill>/references/*.md
microsoft-365/
  appPackage/                       Microsoft 365 app: manifest, declarative agent, plugin, instructions, icons
  build.py                          Builds the upload ZIP
```

## Privacy

The plugin connects to the Elfsquad MCP server, which acts on your Elfsquad data with your own
permissions. See Elfsquad's [privacy statement](https://www.elfsquad.io/privacystatement).

## More

- Elfsquad: https://www.elfsquad.io
- Product documentation is searchable from inside a session with the `SearchKnowledgeBase` tool.
