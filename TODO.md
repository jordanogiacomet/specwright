# Todo App — Archetype de validação rápida

## Por que existe

O `todo-app` é o archetype mais simples do Specwright. Ele gera ~8 stories em vez de ~20, usa um domínio trivial (Todo + User), e roda em ~1-2h no Codex. 

Use pra:
- Validar que o pipeline gera artefatos corretos
- Testar o ralph.sh loop com retry
- Verificar que migrations funcionam
- Testar design style e design references
- Medir o tempo total de geração + execução

## Como usar

### Modo 1: Via prompt (detecta automaticamente)

```bash
initializer new --assist
# Prompt: "simple todo app"
# Vai detectar archetype: todo-app
```

### Modo 2: Via spec de referência (pula prompts)

```bash
initializer new --spec todo-reference.json
```

O `todo-reference.json` já tem todas as respostas preenchidas:
- project_name: "Todo App"
- surface: internal_admin_only
- deploy_target: docker
- stack: nextjs + node-api + postgres

### Modo 3: Via spec + design references

```bash
initializer new --spec todo-reference.json --reference ./screenshots/
```

## Stories geradas (~8)

1. **bootstrap.repository** — scaffolding do projeto
2. **bootstrap.database** — postgres + docker-compose + migrations
3. **bootstrap.backend** — Next.js API routes + health check
4. **bootstrap.frontend** — app shell + layout
5. **feature.authentication** — register + login + logout + session
6. **product.todo-model** — Todo entity + migration
7. **product.todo-api** — CRUD endpoints (POST/GET/PATCH/DELETE)
8. **product.todo-ui** — lista + add + toggle + delete
9. **product.todo-filtering** — filtros (all/pending/completed) + sort

## Domain model

```
Todo
  fields: title, description, completed, dueDate, priority, createdAt, updatedAt
  states: pending → completed (toggle)
  belongs_to: User

User
  fields: email, name, passwordHash, createdAt
  has_many: Todo
```

Roles: user only (sem admin).
Auth: email + password, JWT session.
Business rules: owner-only access, permanent delete, newest first.

## Challenges (no --assist)

1. **Todo data model** — minimal vs standard vs rich
2. **Filtering strategy** — none vs basic vs advanced
3. **Auth complexity** — email-only vs +reset vs OAuth

## Resultado esperado

Depois de `./ralph.sh`:
```
output/todo-app/
├── src/
│   ├── app/
│   │   ├── api/todos/route.ts
│   │   ├── api/todos/[id]/route.ts
│   │   ├── (app)/todos/page.tsx
│   │   ├── (auth)/login/page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── TodoList.tsx
│   │   ├── TodoItem.tsx
│   │   ├── AddTodoForm.tsx
│   │   ├── TodoFilters.tsx
│   │   └── Layout.tsx
│   ├── lib/
│   │   ├── auth.ts
│   │   └── db.ts
│   └── models/
│       └── todo.ts
├── docker-compose.yml
├── package.json
└── ralph.sh
```