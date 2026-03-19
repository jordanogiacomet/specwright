# Task: Implement ST-007 — Initialize project repository

You are implementing a single story for the project **todo-app**.

## Story

# ST-007 — Initialize project repository

**Story key:** `bootstrap.repository`

## Description

Create project structure using nextjs + node-api + postgres.

## Acceptance Criteria

- [ ] package.json exists with scripts: dev, build, lint, test
- [ ] .env.example exists with all required environment variables
- [ ] .env.local is created by copying .env.example with working default values for local development
- [ ] TypeScript is configured with tsconfig.json
- [ ] ESLint and Prettier are configured
- [ ] npm install completes without errors
- [ ] npm run build passes

## Scope Boundaries

- Do NOT implement any features yet — this is project scaffolding only
- Do NOT add authentication, roles, or any business logic
- Do NOT create database tables — that is a separate story

## Expected Files

- `package.json`
- `tsconfig.json`
- `.eslintrc.js or eslint.config.js`
- `.env.example`
- `.env.local`
- `.gitignore`
- `README.md`

## Validation

- Run: `npm install`
- Run: `npm run build`
- Run: `npm run lint`
- Manual: Project directory exists with expected structure

## Instructions

- Read .codex/AGENTS.md for project context and scope boundaries
- Read spec.json for the full project specification
- Read architecture.md for component structure
- Make minimal, targeted changes for this story ONLY
- Do NOT change architecture or scope beyond what this story requires
- Run tests if available after implementation
- If this is a bootstrap story, set up the project structure first

## CRITICAL: Database Migrations

If this story adds, removes, or modifies any collection fields, database models, 
or schema (including adding localization to fields), you MUST:

1. Make the schema change
2. Generate a migration: 
3. Run the migration: 
4. Verify with: 

Skipping this will cause runtime errors like "relation does not exist".

## Validation

After implementation, run available validation commands (test, lint, build).
If no commands exist yet, note that in your response.
