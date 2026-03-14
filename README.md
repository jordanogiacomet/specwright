# Initializer

Este repositorio implementa um inicializador de projetos orientado por PRD.

Hoje ele deve ser entendido como um projeto em modo de diagnostico e alinhamento interno, nao como um gerador finalizado ou como uma aplicacao de producao. O objetivo desta iteracao e preservar a ideia principal do produto enquanto reduz inconsistencias de contrato entre os engines, o fluxo de CLI e os artefatos gerados.

Se outro ChatGPT ou agente for continuar o trabalho daqui, este README serve como mapa rapido do que o projeto e, do que realmente esta ativo no codigo, e de quais regras conceituais nao podem ser quebradas.

## O que este projeto e

A ideia central do repositorio e:

1. receber uma descricao textual de projeto via CLI
2. detectar um `archetype`
3. derivar `stack`, `features` e `capabilities`
4. sintetizar um `spec` canonico em memoria
5. gerar artefatos como PRD, arquitetura, stories e documentos derivados
6. validar e refinar o resultado

O produto a preservar e um `PRD-driven project initializer`.

Nao transforme este repositorio em:

- uma aplicacao SaaS
- um CMS de producao
- um scaffold generico sem modelagem de dominio
- um fluxo que colapse `archetype`, `capabilities`, `features` e `answers` em um conceito unico

## Estado atual da iteracao

O repositorio esta em `understand-and-diagnose mode`.

Isso significa que qualquer agente deve:

1. entender o comportamento atual
2. comparar codigo versus intencao documentada
3. registrar inconsistencias
4. fazer apenas mudancas seguras e bem justificadas

Os documentos de contexto desta iteracao nao sao decorativos. Eles sao parte do contrato de trabalho.

## Ordem obrigatoria de leitura

Antes de qualquer mudanca relevante, leia nesta ordem:

1. `progress.txt`
2. `decisions.md`
3. `diagnosis.md`
4. `architecture.md`
5. `prd.json`

Depois disso, leia o codigo do fluxo ativo, especialmente:

- `initializer/__main__.py`
- `initializer/cli.py`
- `initializer/flow/new_project.py`
- `initializer/engine/archetype_engine.py`
- `initializer/engine/capability_derivation.py`
- `initializer/engine/capability_engine.py`
- `initializer/engine/knowledge_engine.py`
- `initializer/engine/architecture_engine.py`
- `initializer/engine/story_engine.py`
- `initializer/ai/refine_engine.py`
- `initializer/validation/prd_validator.py`
- `initializer/validation/story_coverage.py`

## Conceitos canonicos do dominio

Estes conceitos devem permanecer distintos:

### `archetype`

Classificacao do tipo de produto.

Exemplos atuais:

- `editorial-cms`
- `marketplace`
- `saas-app`
- `generic-web-app`

Responsabilidade:

- definir identidade canonica
- fornecer stack padrao
- fornecer features padrao
- opcionalmente fornecer capabilities padrao

### `capability`

Enriquecimento arquitetural ou de plataforma.

Exemplos atuais:

- `cms`
- `public-site`
- `scheduled-jobs`
- `i18n`

Responsabilidade:

- adicionar decisions de arquitetura
- adicionar componentes de arquitetura
- semear stories
- alimentar constraints, risks e outros artefatos derivados

### `feature`

Funcionalidade de produto esperada no planejamento gerado.

Exemplos atuais:

- `authentication`
- `roles`
- `media-library`
- `draft-publish`
- `preview`
- `scheduled-publishing`

Responsabilidade:

- influenciar geracao de stories
- influenciar arquitetura
- influenciar cobertura e validacao

### `answers`

Respostas estruturadas do CLI.

Exemplos atuais:

- `project_name`
- `project_slug`
- `summary`
- `surface`
- `deploy_target`

Importante: `answers` nao sao equivalentes a `archetype` nem a `capabilities`. Se houver relacao, ela deve ser derivada explicitamente.

## Contrato canonico do `spec`

O `spec` e a estrutura em memoria compartilhada pela pipeline.

Campos minimos ativos hoje:

- `prompt`
- `archetype`
- `archetype_data`
- `stack`
- `features`
- `capabilities`
- `architecture`
- `stories`
- `answers`

Campos derivados que o fluxo `new` atual tambem popula:

- `constraints`
- `design_system`
- `risks`
- `diagram`

## Fluxo ativo confirmado no codigo

O entrypoint principal e:

- `python -m initializer`
- ou o script `initializer` definido em `pyproject.toml`

Subcomandos expostos:

- `new`
- `plan`
- `refine`
- `doctor`
- `validate`

O caminho realmente confirmado e alinhado com a pipeline principal hoje e o `new`.

Fluxo ativo:

1. `initializer/__main__.py` chama `initializer.cli.main()`
2. `initializer.cli.main()` roteia o subcomando
3. `initializer new` chama `initializer.flow.new_project.run_new_project()`
4. `run_new_project()` executa a pipeline abaixo

Pipeline real de `initializer new`:

1. pede a descricao livre do projeto
2. chama `build_initial_spec(prompt)`
3. `build_initial_spec()` chama `detect_archetype(prompt)`
4. coleta respostas estruturadas do usuario
5. deriva capabilities a partir de `archetype_data`, `spec["archetype"]` e `spec["answers"]`
6. aplica handlers de capability
7. aplica conhecimento arquitetural adicional
8. gera arquitetura consolidada
9. gera stories consolidadas
10. refina o spec
11. deriva `constraints`, `design_system`, `risks` e `diagram`
12. roda validacao estrutural e checagem de cobertura de stories
13. escreve artefatos em `output/<project_slug>/`

## Perguntas do CLI no fluxo `new`

Hoje o CLI pergunta, nesta ordem:

1. `Describe the project`
2. `Project name`
3. `Project slug`
4. `One sentence summary`
5. `Choose product surface`
6. `Choose deploy target`

Valores estruturados atuais:

- `surface`
  - `internal_admin_only`
  - `admin_plus_public_site`
- `deploy_target`
  - `docker`
  - `docker_and_k8s_later`

## Derivacao atual de archetype, features e capabilities

### Archetype

O detector ativo esta em `initializer/engine/archetype_engine.py`.

Ele retorna um objeto com:

- `id`
- `name`
- `stack`
- `features`
- `capabilities`

Mapeamento atual:

- prompt editorial ou CMS -> `editorial-cms`
- prompt marketplace -> `marketplace`
- prompt SaaS -> `saas-app`
- fallback -> `generic-web-app`

### Features

As features padrao atualmente vem do `archetype`.

Exemplo importante:

- `editorial-cms` traz `authentication`, `roles`, `media-library`, `draft-publish`, `preview` e `scheduled-publishing`

### Capabilities

O fluxo ativo usa `initializer/engine/capability_derivation.py`.

Hoje ele deriva capabilities por estas fontes:

1. defaults do `archetype`
2. respostas estruturadas
3. capabilities ja existentes no spec

Derivacoes ativas e confirmadas:

- `editorial-cms` inclui `cms`
- `surface == admin_plus_public_site` adiciona `public-site`

Derivacoes suportadas pelo motor, mas nao expostas diretamente no questionario atual:

- `scheduled-jobs`
- `i18n`

Essas duas ainda dependem de respostas mais ricas no `answers` ou de um `spec` alimentado por outro caminho.

## Engines principais e papeis reais

### `archetype_engine`

Detecta o archetype e fornece os defaults.

### `capability_derivation`

Normaliza e deriva `spec["capabilities"]` a partir de archetype e respostas.

### `capability_engine`

Itera `spec["capabilities"]` e aplica handlers registrados em `initializer/engine/capability_registry.py`.

Handlers atuais:

- `initializer/capabilities/cms.py`
- `initializer/capabilities/public_site.py`
- `initializer/capabilities/scheduled_jobs.py`
- `initializer/capabilities/i18n.py`

### `knowledge_engine`

Acrescenta decisions baseadas em stack e features.

### `architecture_engine`

Gera a arquitetura final preservando e mesclando enriquecimentos anteriores.

Resultado tipico:

- `frontend`
- `api`
- `database`
- `object-storage`
- `worker`
- `cdn`

### `story_engine`

Gera stories canonicas e faz `upsert` por `story_key` ou por titulo quando possivel.

### `refine_engine`

Acrescenta refinamentos heuristicos ao PRD e stories operacionais fixas, incluindo:

- `ST-900`
- `ST-901`

### Engines derivados

O fluxo `new` atual tambem chama:

- `constraint_engine`
- `design_system_engine`
- `risk_engine`
- `architeture_diagram_engine`

Esses engines alimentam documentos adicionais no diretorio de output.

## Estrutura de saida do fluxo `new`

Para um projeto com slug `my-project`, o fluxo atual escreve:

```text
output/my-project/
  spec.json
  PRD.md
  architecture.md
  stories/
    ST-001.md
    ...
  docs/
    constraints.md
    design-system.md
    risks.md
    architecture/
      diagram.mmd
```

Referencia validada nesta iteracao:

- `output/st012-editorial-validation/`

Esse diretorio registra o caso editorial principal que foi usado como validacao de ponta a ponta da pipeline atual.

## Cenario de referencia mais importante

O principal cenario de referencia deste repositorio hoje e o editorial.

Prompt de referencia:

`Editorial CMS with admin panel, public website, media library, preview, and scheduled publishing for articles`

Resultado esperado de alto nivel no fluxo ativo:

- `archetype == editorial-cms`
- `capabilities == ['cms', 'public-site']`
- stack `nextjs + payload + postgres`
- componentes como `cdn`, `frontend`, `api`, `database`, `object-storage`, `worker`
- conjunto coerente de stories de bootstrap, features e operacao

## O que esta validado versus o que ainda parece parcial

### Fluxo mais confiavel hoje

- `initializer new`
- `build_initial_spec()`
- `detect_archetype()`
- derivacao explicita de capabilities
- aplicacao de capability handlers
- geracao de arquitetura
- geracao de stories
- derivacao de constraints, design system, risks e diagram
- escrita em `output/<slug>/`

### Areas que outro agente deve tratar com cautela

Existem modulos que parecem legados, paralelos ou apenas parcialmente alinhados com o fluxo ativo:

- `initializer/runtime/`
- `initializer/synthesis/`
- `initializer/graph/story_graph.py`
- `initializer/flow/plan_project.py`
- parte dos `renderers/`, porque o fluxo `new` atual mistura writers inline com renderers dedicados

Pontos importantes:

- `initializer/flow/plan_project.py` referencia `collect_input` e `render_decisions` em `initializer.flow.new_project`, mas esses simbolos nao existem hoje nesse modulo
- `doctor` valida uma estrutura de projeto diferente da que `new` escreve atualmente
- `validate` depende de `jsonschema`, que esta em `pyproject.toml`, mas precisa estar instalado no ambiente

Em outras palavras: o repositorio tem um caminho principal funcional e caminhos secundarios que ainda nao compartilham o mesmo contrato com o mesmo grau de confianca.

## Inconsistencias e limites conhecidos

Outro agente precisa saber destas tensoes atuais antes de mexer no codigo:

1. O projeto melhorou o contrato canonico do fluxo `new`, mas ainda existem modulos antigos com semantica diferente.
2. Nem toda capability suportada pelo registry e produzida automaticamente pelo questionario atual.
3. Os handlers de capability ainda nao usam exatamente a mesma estrategia de identidade e merge que os geradores canonicos.
4. A cobertura de capability em `initializer/validation/story_coverage.py` ainda e baseada em busca textual simples dentro da descricao da story.
5. Existem dois estilos de escrita de artefatos no repositorio:
   - writers inline no fluxo `new`
   - renderers dedicados em `initializer/renderers/`

Isso nao invalida o projeto, mas significa que mudancas amplas sem diagnostico podem reintroduzir drift rapidamente.

## Mapa do repositorio

Diretorios mais importantes:

- `initializer/flow/`
  - orquestracao dos subcomandos
- `initializer/engine/`
  - motores centrais de derivacao e sintese
- `initializer/capabilities/`
  - handlers por capability
- `initializer/validation/`
  - validacoes do spec e cobertura de stories
- `initializer/renderers/`
  - renderizacao e escrita de docs auxiliares
- `initializer/runtime/`
  - caminho alternativo para semantic spec
- `initializer/synthesis/`
  - fluxo mais antigo de sintese
- `output/`
  - artefatos gerados e exemplos de referencia
- `contracts/` e `schemas/`
  - contratos auxiliares e schema

Documentos raiz mais importantes:

- `AGENTS.md`
- `progress.txt`
- `decisions.md`
- `diagnosis.md`
- `architecture.md`
- `prd.json`

## Regras de trabalho para outro agente

Se voce estiver continuando este projeto, siga estas regras:

1. Preserve a identidade do produto como inicializador PRD-driven.
2. Nao colapse `archetype`, `capabilities`, `features` e `answers`.
3. Compare sempre documentacao e implementacao.
4. Considere o fluxo `initializer new` como a fonte principal de comportamento atual.
5. Trate `runtime/`, `synthesis/` e alguns subcomandos secundarios como areas que exigem verificacao antes de confiar.
6. Registre descobertas e mudancas em `progress.txt`.
7. Nao faca refatoracoes largas sem antes explicar qual contrato existente esta quebrado.

## Como rodar

Instalacao local recomendada:

```bash
python -m pip install -e .
```

Ver ajuda:

```bash
python -m initializer --help
```

Executar o fluxo principal:

```bash
python -m initializer new
```

Validar um output gerado:

```bash
python -m initializer validate output/<project-slug>
```

Observacao: o comando `validate` importa `jsonschema`. Se o ambiente nao estiver com as dependencias instaladas, ele vai falhar antes da validacao.

## O que um outro ChatGPT deve lembrar em uma frase

Este repositorio nao e um scaffold generico: ele e um inicializador orientado por PRD, com pipeline baseada em engines especializadas e um fluxo principal hoje centrado em `initializer new`, devendo ser evoluido por alinhamento de contratos, nao por redesign do produto.
