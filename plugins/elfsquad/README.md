# Elfsquad

Work in [Elfsquad](https://www.elfsquad.io), the configure-price-quote (CPQ) platform, from Claude or
ChatGPT. The plugin connects to the Elfsquad MCP server at `https://api.elfsquad.io/mcp` and adds six skills
that tell the assistant how to use its tools:

- **elfsquad-getting-started**: choose an environment, Read and Write access, errors, the documentation search
- **elfsquad-data-queries**: filter, count and look up data
- **elfsquad-feature-models**: build and edit feature models
- **elfsquad-model-rules**: requires, excludes, calculated values, hide conditions and price formulas
- **elfsquad-configurator**: configure a product, resolve conflicts, read prices
- **elfsquad-quotations**: quotations, statuses and CRM accounts

You sign in with your Elfsquad account. The assistant works with your own roles and permissions, and changes
to data need Write access for MCP, which an administrator of the environment grants. Skills ask before
anything that deletes.

Installation for each assistant is described in the
[repository README](https://github.com/Elfsquad/elfsquad-mcp-plugins#readme). For help, contact
[Elfsquad](https://www.elfsquad.io/contact-us).

## Privacy

The plugin sends your requests to the Elfsquad MCP server at `https://api.elfsquad.io/mcp`, which acts on
your Elfsquad data with your own permissions. Elfsquad's
[privacy statement](https://www.elfsquad.io/privacystatement) describes how that data is handled.
