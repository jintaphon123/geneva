# MCP Server Patterns

## Tool Definition Quality Rules

```typescript
// ❌ Poor tool definition
{
    name: "get",                        // not descriptive
    description: "Gets data",           // useless description
    input_schema: {
        type: "object",
        properties: {
            id: { type: "string" }      // no description on param
        }
        // missing required[]
    }
}

// ✅ Production-quality tool definition
{
    name: "get_document",
    description: "Retrieve a document by ID. Use when the user references a specific document, wants to read stored content, or asks to open/view a note. Returns full document content and metadata.",
    input_schema: {
        type: "object",
        properties: {
            document_id: {
                type: "string",
                description: "The UUID of the document to retrieve"
            },
            include_metadata: {
                type: "boolean",
                description: "If true, include created_at, updated_at, and tags in response. Default: false"
            }
        },
        required: ["document_id"]
    }
}
```

**Tool description rules:**
1. State what it does in one sentence (action verb + object)
2. State WHEN to use it (triggers, not just what it returns)
3. Note important constraints (limits, required state, side effects)
4. Never repeat the input parameter names in the description

## TypeScript MCP Server Scaffold

```typescript
// src/server.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
    { name: 'second-brain-mcp', version: '1.0.0' },
    { capabilities: { tools: {} } }
);

// Tool registry
const tools = [
    {
        name: 'search_memories',
        description: 'Search stored memories by semantic similarity. Use when user asks what they know about a topic, wants to recall past decisions, or needs to find related context.',
        inputSchema: {
            type: 'object' as const,
            properties: {
                query: { type: 'string', description: 'Natural language search query' },
                limit: { type: 'number', description: 'Max results to return. Default: 5, max: 20' },
                filter_tag: { type: 'string', description: 'Optional: filter results to this tag only' },
            },
            required: ['query'],
        },
    },
    // ... more tools
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case 'search_memories':
                return await handleSearchMemories(args as { query: string; limit?: number });
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (err) {
        return {
            content: [{ type: 'text', text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Auth Strategy Options

| Strategy | When | Implementation |
|---|---|---|
| API key in header | Internal tools, single team | Read from env, inject in all requests |
| OAuth token forwarding | User-delegated access (Google, GitHub) | Pass token from MCP client context |
| Service account | Server-to-server, Cloud APIs | Key file from env, auto-refresh |
| No auth | Local-only, dev tools | Fine for localhost MCP servers |

```typescript
// API key injection (most common for internal APIs)
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error('API_KEY environment variable required');

async function callAPI(endpoint: string, body?: unknown) {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json',
        },
        ...(body ? { method: 'POST', body: JSON.stringify(body) } : {}),
    });

    if (!res.ok) {
        const error = await res.text();
        throw new Error(`API error ${res.status}: ${error}`);
    }
    return res.json();
}
```

## OpenAPI → MCP Mapping

```python
# Convert OpenAPI operation to MCP tool definition
def openapi_to_mcp_tool(path: str, method: str, operation: dict) -> dict:
    # Name: verb_resource from operationId or method+path
    op_id = operation.get('operationId', f"{method}_{path.replace('/', '_').strip('_')}")
    name = to_snake_case(op_id)

    # Build input_schema from parameters + requestBody
    properties = {}
    required = []

    for param in operation.get('parameters', []):
        properties[param['name']] = {
            'type': param['schema']['type'],
            'description': param.get('description', f"The {param['name']} parameter"),
        }
        if param.get('required'):
            required.append(param['name'])

    if 'requestBody' in operation:
        body_schema = operation['requestBody']['content']['application/json']['schema']
        for field, schema in body_schema.get('properties', {}).items():
            properties[field] = {
                'type': schema['type'],
                'description': schema.get('description', ''),
            }
        required.extend(body_schema.get('required', []))

    return {
        'name': name,
        'description': operation.get('summary', '') + ' ' + operation.get('description', ''),
        'input_schema': {
            'type': 'object',
            'properties': properties,
            'required': required,
        }
    }
```

## MCP Tool Evolution (Backward Compatibility)

```typescript
// Adding parameters: always optional with default
// Before
{ required: ["document_id"] }

// After (safe — new param is optional)
{
    required: ["document_id"],
    properties: {
        document_id: { type: "string" },
        format: { type: "string", enum: ["text", "markdown"], description: "Default: text" }
    }
}

// NEVER: remove a required parameter (breaking change)
// NEVER: change a parameter type (breaking change)
// ALWAYS: bump version in server metadata for breaking changes
```
