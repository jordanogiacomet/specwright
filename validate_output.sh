#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Specwright Output Validation Script
# 
# Roda após gerar um projeto com:
#   python -m initializer new
#
# Uso:
#   ./validate_output.sh output/my-cms
#   ./validate_output.sh output/backops
# ============================================================

PROJECT_DIR="${1:?Uso: ./validate_output.sh <output-dir>}"

PASS=0
FAIL=0
SKIP=0

pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
skip() { echo "  ⏭️  $1"; SKIP=$((SKIP + 1)); }

echo ""
echo "========================================"
echo " Validando: $PROJECT_DIR"
echo "========================================"

# ============================================================
# GRUPO 1: Arquivos de scaffold existem
# ============================================================
echo ""
echo "--- 1. Scaffold files ---"

for f in \
    "package.json" \
    "tsconfig.json" \
    "docker-compose.yml" \
    ".env.example" \
    ".gitignore" \
    "Dockerfile" \
    "next.config.ts" \
    "postcss.config.mjs" \
    "eslint.config.mjs" \
    "README.md" \
    "src/app/layout.tsx" \
    "src/app/page.tsx" \
    "src/app/globals.css"
do
    if [[ -f "$PROJECT_DIR/$f" ]]; then
        pass "$f existe"
    else
        fail "$f FALTA"
    fi
done

# ============================================================
# GRUPO 2: Arquivos do Specwright existem
# ============================================================
echo ""
echo "--- 2. Specwright contract files ---"

for f in \
    "spec.json" \
    "PRD.md" \
    "architecture.md" \
    "decisions.md" \
    "progress.txt" \
    "ralph.sh" \
    ".codex/AGENTS.md" \
    ".openclaw/AGENTS.md" \
    ".openclaw/OPENCLAW.md" \
    ".openclaw/execution-plan.json" \
    ".openclaw/manifest.json" \
    ".openclaw/repo-contract.json" \
    ".openclaw/commands.json" \
    "docs/design-system.md" \
    "docs/constraints.md" \
    "docs/risks.md" \
    "docs/architecture/diagram.mmd"
do
    if [[ -f "$PROJECT_DIR/$f" ]]; then
        pass "$f existe"
    else
        fail "$f FALTA"
    fi
done

# ============================================================
# GRUPO 3: Stories existem e são ricas
# ============================================================
echo ""
echo "--- 3. Stories ---"

STORY_DIR="$PROJECT_DIR/docs/stories"
if [[ -d "$STORY_DIR" ]]; then
    STORY_COUNT=$(ls "$STORY_DIR"/*.md 2>/dev/null | wc -l)
    if [[ "$STORY_COUNT" -gt 0 ]]; then
        pass "$STORY_COUNT stories geradas"
    else
        fail "Nenhuma story encontrada em docs/stories/"
    fi

    # Checar se primeira story tem acceptance criteria
    FIRST_STORY=$(ls "$STORY_DIR"/*.md 2>/dev/null | head -1)
    if [[ -n "$FIRST_STORY" ]]; then
        if grep -q "Acceptance Criteria" "$FIRST_STORY"; then
            pass "$(basename $FIRST_STORY) tem Acceptance Criteria"
        else
            fail "$(basename $FIRST_STORY) SEM Acceptance Criteria"
        fi

        if grep -q "Scope Boundaries" "$FIRST_STORY"; then
            pass "$(basename $FIRST_STORY) tem Scope Boundaries"
        else
            fail "$(basename $FIRST_STORY) SEM Scope Boundaries"
        fi

        if grep -q "Expected Files" "$FIRST_STORY"; then
            pass "$(basename $FIRST_STORY) tem Expected Files"
        else
            fail "$(basename $FIRST_STORY) SEM Expected Files"
        fi

        if grep -q "Validation" "$FIRST_STORY"; then
            pass "$(basename $FIRST_STORY) tem Validation"
        else
            fail "$(basename $FIRST_STORY) SEM Validation"
        fi
    fi
else
    fail "docs/stories/ não existe"
fi

# ============================================================
# GRUPO 4: spec.json tem as novas seções
# ============================================================
echo ""
echo "--- 4. spec.json contract ---"

if [[ -f "$PROJECT_DIR/spec.json" ]]; then
    for section in \
        "archetype" \
        "stack" \
        "features" \
        "capabilities" \
        "architecture" \
        "stories" \
        "answers" \
        "constraints" \
        "design_system" \
        "risks" \
        "diagram" \
        "project_structure" \
        "domain_model"
    do
        if python3 -c "import json; d=json.load(open('$PROJECT_DIR/spec.json')); assert '$section' in d" 2>/dev/null; then
            pass "spec.json tem '$section'"
        else
            fail "spec.json SEM '$section'"
        fi
    done

    # Checar domain_model tem entities
    if python3 -c "
import json
d=json.load(open('$PROJECT_DIR/spec.json'))
dm=d.get('domain_model',{})
assert len(dm.get('entities',[])) > 0
assert len(dm.get('roles',[])) > 0
assert len(dm.get('business_rules',[])) > 0
assert 'strategy' in dm.get('auth_model',{})
" 2>/dev/null; then
        pass "domain_model tem entities, roles, business_rules, auth_model"
    else
        fail "domain_model incompleto"
    fi

    # Checar project_structure
    if python3 -c "
import json
d=json.load(open('$PROJECT_DIR/spec.json'))
ps=d.get('project_structure',{})
assert ps.get('ecosystem') in ('node','python','go','unknown')
assert len(ps.get('directories',[])) > 0
assert len(ps.get('root_files',[])) > 0
" 2>/dev/null; then
        pass "project_structure tem ecosystem, directories, root_files"
    else
        fail "project_structure incompleto"
    fi

    # Checar architecture tem communication e boundaries
    if python3 -c "
import json
d=json.load(open('$PROJECT_DIR/spec.json'))
arch=d.get('architecture',{})
assert len(arch.get('communication',[])) > 0
assert len(arch.get('boundaries',{}).get('frontend',[])) > 0
assert len(arch.get('boundaries',{}).get('backend',[])) > 0
" 2>/dev/null; then
        pass "architecture tem communication e boundaries"
    else
        fail "architecture SEM communication ou boundaries"
    fi
else
    fail "spec.json não existe"
fi

# ============================================================
# GRUPO 5: commands.json não está vazio
# ============================================================
echo ""
echo "--- 5. commands.json ---"

COMMANDS_FILE="$PROJECT_DIR/.openclaw/commands.json"
if [[ -f "$COMMANDS_FILE" ]]; then
    if python3 -c "
import json
d=json.load(open('$COMMANDS_FILE'))
cmds=d.get('commands',{})
assert cmds.get('build','') != '', 'build is empty'
assert cmds.get('lint','') != '', 'lint is empty'
assert cmds.get('test','') != '', 'test is empty'
assert cmds.get('dev','') != '', 'dev is empty'
assert 'setup' in d
" 2>/dev/null; then
        pass "commands.json tem comandos reais (não vazios)"
    else
        fail "commands.json com comandos vazios"
    fi
else
    fail "commands.json não existe"
fi

# ============================================================
# GRUPO 6: architecture.md é rico
# ============================================================
echo ""
echo "--- 6. architecture.md ---"

ARCH_FILE="$PROJECT_DIR/architecture.md"
if [[ -f "$ARCH_FILE" ]]; then
    for section in "Communication" "Responsibility Boundaries" "Typical Request Flow" "Architectural Decisions"; do
        if grep -q "$section" "$ARCH_FILE"; then
            pass "architecture.md tem '$section'"
        else
            fail "architecture.md SEM '$section'"
        fi
    done
else
    fail "architecture.md não existe"
fi

# ============================================================
# GRUPO 7: Payload-specific (se payload backend)
# ============================================================
echo ""
echo "--- 7. Payload-specific (se aplicável) ---"

if [[ -f "$PROJECT_DIR/src/payload.config.ts" ]]; then
    pass "payload.config.ts existe"

    if [[ -f "$PROJECT_DIR/src/collections/Users.ts" ]]; then
        pass "collections/Users.ts existe"
    else
        fail "collections/Users.ts FALTA"
    fi

    if [[ -d "$PROJECT_DIR/src/app/(payload)" ]]; then
        pass "src/app/(payload)/ existe"
    else
        fail "src/app/(payload)/ FALTA"
    fi

    if grep -q "payload" "$PROJECT_DIR/package.json"; then
        pass "package.json tem payload deps"
    else
        fail "package.json SEM payload deps"
    fi
else
    skip "Não é projeto Payload — pulando checks específicos"
fi

# ============================================================
# GRUPO 8: ralph.sh é executável
# ============================================================
echo ""
echo "--- 8. ralph.sh ---"

if [[ -f "$PROJECT_DIR/ralph.sh" ]]; then
    if [[ -x "$PROJECT_DIR/ralph.sh" ]]; then
        pass "ralph.sh é executável"
    else
        fail "ralph.sh NÃO é executável"
    fi

    if grep -q "execution-plan.json" "$PROJECT_DIR/ralph.sh"; then
        pass "ralph.sh lê execution-plan.json"
    else
        fail "ralph.sh não referencia execution-plan.json"
    fi
else
    fail "ralph.sh não existe"
fi

# ============================================================
# GRUPO 9: npm install + build (se quiser rodar)
# ============================================================
echo ""
echo "--- 9. Execução real (manual) ---"
echo "  Para testar execução real, rode:"
echo ""
echo "    cd $PROJECT_DIR"
echo "    npm install"
echo "    docker compose up -d"
echo "    cp .env.example .env.local"
echo "    npm run dev"
echo ""
echo "  Depois verifique:"
echo "    - http://localhost:3000 abre"
if [[ -f "$PROJECT_DIR/src/payload.config.ts" ]]; then
    echo "    - http://localhost:3000/admin abre o Payload admin"
fi
echo "    - docker compose ps mostra postgres healthy"
echo ""

# ============================================================
# RESULTADO
# ============================================================
echo "========================================"
echo " RESULTADO"
echo "========================================"
echo "  ✅ Passou: $PASS"
echo "  ❌ Falhou: $FAIL"
echo "  ⏭️  Pulou: $SKIP"
echo "========================================"

if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi