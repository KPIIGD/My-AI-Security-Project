# AI Development Automation Research

조사 기준: 2026-06-17 Asia/Seoul

이 문서는 단체 프로젝트에서 AI로 개발 업무 대부분을 자동화하거나 보조하는 흐름을 조사한 결과다. 조사 범위는 AI 개발 자동화, agentic engineering, coding agent 생태계, 현업 도입 방식, 벤치마크, 커뮤니티 후기, 전문가 관점, LLM 프로젝트 이해 방법, Obsidian/Slack/Google Drive 활용, 보안/거버넌스까지 포함한다.

조사 방식은 15개 병렬 조사 트랙, 직접 웹/GitHub 검증, ChatGPT Pro Web Search 9개 chunk, ChatGPT Pro Deep Research 2회 교차검증을 결합했다. GitHub star/fork/pushed 수치는 `gh api repos/{owner}/{repo}`로 2026-06-17 Asia/Seoul 기준 재확인했다. 수치는 계속 변한다.

## 결론

현재 이 흐름을 부를 때 가장 안전한 표현은 **AI-assisted software development**, **AI-augmented software engineering**, **agentic coding**, **agentic software engineering**, **agentic engineering**이다. 빠른 프로토타입 문맥에서는 **vibe coding**도 널리 쓰이지만, 현업/보안/프로덕션 문서에서는 그대로 쓰기보다 "검토되지 않은 AI 생성 코드에 의존하는 프로토타이핑 방식"으로 구분하는 편이 낫다. Simon Willison은 vibe coding을 사람이 코드를 읽지 않는 방식으로 구분했고, Addy Osmani는 실무형 접근을 "AI가 구현하더라도 인간이 아키텍처, 품질, 정확성을 소유하는 agentic engineering"으로 설명한다. 관련 글: [Simon Willison on vibe coding](https://simonwillison.net/2025/Mar/19/vibe-coding/), [Addy Osmani on agentic engineering](https://addyosmani.com/blog/agentic-engineering/).

2026-06-17 기준 최신 기술의 핵심은 단일 도구 순위가 아니라 다음 조합이다. OpenAI의 Codex 관련 공개 자료도 같은 방향을 가리킨다. 모델 자체는 GPT-5.5 같은 frontier coding model로 계속 올라가지만, 실제 생산성은 Codex harness, Symphony 같은 orchestration/control plane, 테스트/리뷰/권한 설계가 결합될 때 나온다: [GPT-5.5](https://openai.com/index/introducing-gpt-5-5/), [Harness engineering](https://openai.com/index/harness-engineering/), [Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/).

- 프론티어 모델: GPT/Codex 계열, Claude 계열, Gemini 계열 등.
- agent harness: CLI, IDE, cloud agent, PR agent, sandbox, 권한 승인, tool calling, MCP.
- 프로젝트 컨텍스트 구조: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `llms.txt`, repo map, architecture docs, ADR, tests, schemas, runbooks.
- 검증 루프: unit/integration/e2e tests, lint, typecheck, CI, code review, security scan, dependency/secret scanning.
- 지식/권한 설계: GitHub, Slack, Drive/Docs, Obsidian/Notion, connector 권한, audit log, DLP.

현업에서 "AI가 프로젝트 대부분을 자동화했다"고 말하려면, 코드 생성량보다 **scope control, deterministic verification, PR review, production guardrail**을 같이 설명해야 한다. 커뮤니티 후기와 전문가 글 모두 병목이 "코드 작성"에서 "믿어도 되는지 판단하고 병합하는 과정"으로 이동했다고 반복해서 지적한다. 관련 글: [Addy Osmani on agentic code review](https://addyosmani.com/blog/agentic-code-review/), [Simon Willison on using LLMs for code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/).

## 용어 정리

| 용어 | 의미 | 현업 문서에서의 권장도 |
|---|---|---|
| AI-assisted software development | AI가 개발자를 보조하는 넓은 표현. 자동완성, chat, 테스트 생성, 문서화까지 포함 | 가장 무난함 |
| AI-augmented software engineering | 개발 프로세스 전체를 AI로 증강한다는 표현. 요구사항, 설계, 구현, 검증, 운영까지 포함 | 보고서/논문형 문맥에 적합 |
| Agentic coding | agent가 파일을 읽고, 수정하고, 명령을 실행하고, 테스트를 반복하는 방식 | coding agent 설명에 적합 |
| Agentic software engineering | issue 해결, PR, CI, 리뷰, 배포 전 검증까지 agent가 참여하는 엔지니어링 흐름 | 현업 도입 설명에 적합 |
| Agentic engineering | 인간이 방향/품질을 소유하고 agent가 구현/탐색/반복을 수행하는 운영 모델 | 최신 실무형 표현 |
| Vibe coding | 코드를 거의 읽지 않고 AI 출력과 실행 결과만 보며 밀어붙이는 방식 | 프로토타입에는 가능, 프로덕션에는 위험 |
| Context engineering | LLM이 작업을 잘하도록 필요한 정보, 지침, 도구, 검색 결과, memory를 구성하는 작업 | 매우 중요 |
| Human-AI teaming | 사람이 목표/제약/리뷰를 맡고 AI가 실행/탐색/초안을 맡는 협업 구조 | 조직 변화 설명에 적합 |

Anthropic은 context engineering을 단순 prompt가 아니라 inference 중 들어가는 모든 정보의 구성 전략으로 설명한다: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). Martin Fowler도 coding agent에서 재사용 prompt, instruction files, task context를 분리하는 관점을 정리했다: [Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html).

## 조사 트랙

| 트랙 | 조사 대상 |
|---|---|
| A | OpenAI Codex: CLI, App, Cloud, GitHub integration, security |
| B | Anthropic Claude Code: memory, skills, MCP, hooks, subagents, security |
| C | Cursor, Windsurf/Devin Desktop, VS Code agent mode |
| D | GitHub Copilot: agent mode, cloud agent, code review, Actions |
| E | 오픈소스 coding agents: GitHub stars, forks, license, self-host 가능성 |
| F | 벤치마크/논문: SWE-bench, Terminal-Bench, LiveCodeBench 등 |
| G | 커뮤니티 후기: Reddit, Hacker News, X/Twitter, Threads 접근 한계 포함 |
| H | 전문가 관점: Karpathy, Osmani, Willison, Beck, Cherny 등 |
| I | LLM 프로젝트 이해/context engineering |
| J | Obsidian 활용 |
| K | Slack 활용 |
| L | Google Drive/Docs/Workspace/Gemini/NotebookLM |
| M | 현업 도입 아키텍처 |
| N | 보안/거버넌스 |
| O | ChatGPT Pro Web Search/Deep Research 교차검증 결과 |

ChatGPT Pro Web Search는 9개 chunk를 순차 실행했다. Deep Research는 한 번은 확인 필요 신호로 중단됐고, 이후 승인 조건을 명시해 공개 웹 기반 독립 교차검증을 완료했다. 최종 문서에는 공식 문서, 논문/벤치마크, GitHub 원출처, 원문 블로그, 공개 커뮤니티 자료로 교차확인된 내용만 본문 판단으로 병합했다. X/Twitter와 Threads는 접근 제한 때문에 limited/unverified community signal로만 취급했다. 공식 설명: [Deep Research in ChatGPT](https://help.openai.com/en/articles/10500283-deep-research-in-chatgpt), [ChatGPT Search](https://help.openai.com/en/articles/9237897-chatgpt-search).

## ChatGPT Pro 교차검증 결과

| Chunk | 판단 | 문서 반영 |
|---|---|---|
| 용어/전문가 | confirm/new | vibe coding은 "코드를 읽지 않는 프로토타이핑"으로 제한하고, agentic engineering/context engineering을 현업 표현으로 강화 |
| OpenAI/Codex | confirm/conflict/new | "GPT-5.5 Codex" 대신 `gpt-5.5` 또는 "GPT-5.5 in Codex"로 표기, Codex Security/Sites/Plugins/Skills/App Server/SDK/Windows/mobile 추가 |
| Claude Code | confirm/new | Auto memory, context cost, nested skills/subagents, MCP Tool Search, `--safe-mode`, auto mode 잔여 위험 추가 |
| IDE/GitHub | confirm/conflict/new | Cursor 3의 "agents"를 fixed 3-agent 구조로 쓰지 않음, Devin Desktop 전환, VS Code `.agent.md`/`AGENTS.md` 역할 구분, Copilot cloud agent 용어 정리 |
| OSS agents | confirm/conflict/new | Claude Code license 주의, Continue read-only, Crush FSL, Roo/opencode-ai archived, bolt.diy self-host 문맥 추가 |
| Benchmarks | confirm/conflict/new | SWE-bench Verified 단독 사용 부적합, SWE-bench Pro/Terminal-Bench/FeatureBench/SWE-EVO/SWE-Explore 보강, model+agent harness 단위 평가 강조 |
| 지식관리 | confirm/new | Obsidian canonical memory, Slack real-time context, Google governed artifacts 구조로 정리, Slack persistent archive/Drive MCP prompt injection 주의 추가 |
| 보안 | confirm/conflict/new | NSA MCP, OWASP MCP Top 10, GitHub push protection 한계, Codex setup/agent phase, ChatGPT app action controls, Claude managed MCP/auto mode 위험 추가 |
| 커뮤니티 | confirm/conflict/unverified | 생산성 신호와 함께 리뷰 병목, 과금 loop, Full Access/data-loss, CI 공급망 위험을 커뮤니티 signal로 반영 |
| Deep Research | confirm/conflict/new | DORA/Stack Overflow/METR로 "도입은 강하지만 생산성은 조건부"라는 균형 결론, GitHub MCP secret scan/Google Cloud MCP/Agents SDK guardrail 보강 |

## 도구 생태계

### OpenAI Codex

Codex는 단일 제품이 아니라 CLI, App, Cloud/Web, IDE/GitHub integration, App Server/SDK, plugins/skills, Sites, Security까지 포함하는 개발 agent 제품군이다. Codex CLI는 로컬 터미널에서 코드를 읽고 수정하고 명령을 실행하는 Rust 기반 오픈소스 agent다: [Codex CLI docs](https://developers.openai.com/codex/cli), [openai/codex](https://github.com/openai/codex).

Codex App은 여러 thread/worktree를 병렬로 다루는 데 초점을 둔다. 로컬 terminal/browser/computer use와 Git 작업을 포함하는 작업 환경이다: [Codex App docs](https://developers.openai.com/codex/app). Codex Cloud는 GitHub 저장소에 연결해 원격 환경에서 task를 수행하고 branch/PR 흐름으로 결과를 남긴다: [Codex Cloud docs](https://developers.openai.com/codex/cloud), [GitHub integration](https://developers.openai.com/codex/integrations/github).

OpenAI가 공개한 최신 실무 자료에서 중요한 변화는 **harness engineering**과 **orchestration**이다. Harness engineering 글은 인간이 거의 prompt와 PR review만으로 개입하고, Codex가 `gh`, 로컬 스크립트, repository-embedded skills, 브라우저/DOM/screenshot 도구를 직접 써서 context 수집과 검증을 수행하는 방향을 설명한다: [Harness engineering](https://openai.com/index/harness-engineering/). Symphony는 issue tracker/프로젝트 보드를 agent control plane으로 바꿔 "열린 task마다 agent가 지속 실행되고 사람이 결과를 리뷰"하는 모델을 제시한다: [Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/), [openai/symphony](https://github.com/openai/symphony).

모델 측면에서는 OpenAI가 `gpt-5.5`를 Codex/ChatGPT의 agentic coding model로 공개했고, Terminal-Bench 2.0과 SWE-Bench Pro 같은 지표를 함께 제시했다: [Introducing GPT-5.5](https://openai.com/index/introducing-gpt-5-5/), [Codex models](https://developers.openai.com/codex/models). 공식 표현은 `gpt-5.5` 또는 "GPT-5.5 in Codex"에 가깝고, "GPT-5.5 Codex"라는 별도 모델명으로 쓰는 것은 피하는 편이 정확하다. 벤치마크 수치는 harness, contamination, vendor reporting 방식에 민감하므로 "GPT-5.5가 항상 최고"로 단정하기보다, 내부 repo task와 CI/review burden으로 재평가해야 한다.

제품 측면에서는 Codex가 local CLI/App/Cloud를 넘어 computer use, in-app browser, plugins, skills, memory, automations, mobile access로 확장되고 있다. 이는 coding agent가 IDE 보조 도구에서 "개발 workflow를 따라다니는 작업자"로 이동한다는 신호다: [Codex for almost everything](https://openai.com/index/codex-for-almost-everything/), [Work with Codex from anywhere](https://openai.com/index/work-with-codex-from-anywhere/), [Computer Use](https://developers.openai.com/codex/app/computer-use), [Remote connections](https://developers.openai.com/codex/remote-connections).

App Server와 SDK는 Codex harness를 직접 제품/사내 도구/CI에 넣기 위한 경로다. App Server는 rich client용 JSON-RPC interface이고, SDK는 CI/CD, 내부 도구, 자체 agent app 통합에 적합하다: [Codex App Server](https://developers.openai.com/codex/app-server), [Codex SDK](https://developers.openai.com/codex/sdk). Plugins는 skills, app integrations, MCP servers를 재사용 가능한 workflow로 묶고, Skills는 `SKILL.md` 기반 authoring format이다: [Codex plugins](https://developers.openai.com/codex/plugins), [Codex skills](https://developers.openai.com/codex/skills).

Codex와 별도로 OpenAI Agents SDK도 long-horizon agent를 만들기 위한 일반 harness로 확장되고 있다. 업데이트된 SDK는 file inspection, command execution, code editing, approvals, tracing, sandbox execution, state/resume bookkeeping 같은 agent-loop 구성 요소를 제공한다: [Agents SDK guide](https://developers.openai.com/api/docs/guides/agents), [The next evolution of the Agents SDK](https://openai.com/index/the-next-evolution-of-the-agents-sdk/). Agents SDK 기반 workflow에서는 MCP, tracing, guardrails, handoffs를 별도 통제면으로 설계한다. 특히 guardrail은 모든 handoff/tool 경로에 동일하게 적용된다고 가정하지 말고, handoff 전후 검증과 human review를 별도 gate로 둔다: [Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/), [Agents SDK handoffs](https://openai.github.io/openai-agents-python/handoffs/).

Codex Sites는 Business/Enterprise/Edu preview 성격의 내부 web app 생성/배포 흐름이다. lightweight JS/TS full-stack app, Sign in with ChatGPT, data/file storage, RBAC를 다루지만 모든 deployment URL은 production deployment로 취급해야 한다: [Codex Sites](https://developers.openai.com/codex/sites), [ChatGPT Business release notes](https://help.openai.com/en/articles/11391654-chatgpt-business-release-notes).

보안 면에서는 sandbox, approval policy, network control, rules, enterprise managed configuration이 핵심이다. 공식 문서 기준으로 Codex는 sandbox/approval을 통해 파일/네트워크/명령 실행 경계를 제어한다: [Agent approvals and security](https://developers.openai.com/codex/agent-approvals-security), [Sandboxing](https://developers.openai.com/codex/concepts/sandboxing), [Rules](https://developers.openai.com/codex/rules), [Enterprise admin setup](https://developers.openai.com/codex/enterprise/admin-setup). Cloud에서는 dependency 설치를 위한 setup phase와 실제 agent phase를 분리하고, agent phase의 network는 기본적으로 꺼진다. Codex Security는 일반 sandbox가 아니라 GitHub repo scan, threat model, validation, suggested patch를 제공하는 별도 security research preview로 봐야 한다: [Codex Security](https://developers.openai.com/codex/security).

현업 활용점:

- 로컬 CLI: 작은 버그 수정, 테스트 작성, 리팩터링, 문서화, 반복 실행.
- App: 여러 독립 작업을 worktree/thread로 병렬 처리.
- Cloud/Web: issue 기반 branch 작업, PR 초안, 리뷰 요청, CI 실패 대응.
- Symphony/harness: issue board를 agent queue/control plane으로 쓰고, task별 agent 실행/검증/리뷰를 반복.
- GitHub Action: PR에서 반복 가능한 Codex 실행/리뷰/검증 루프 구성: [Codex GitHub Action](https://developers.openai.com/codex/github-action).

### Claude Code

Claude Code는 chat assistant가 아니라 저장소 탐색, 계획, 파일 수정, 명령 실행, memory, subagent, hook, skill, MCP를 포함하는 agentic coding 환경이다. 공식 best practices는 먼저 codebase를 탐색하고, 계획을 세우고, 검증 가능한 목표를 주고, 테스트를 반복하라고 권장한다: [Claude Code best practices](https://code.claude.com/docs/en/best-practices), [Claude Code overview](https://code.claude.com/docs/en/overview), [Changelog](https://code.claude.com/docs/en/changelog).

Claude Code의 핵심 구성:

- `CLAUDE.md`와 Auto memory: 세션 시작 시 로딩되는 프로젝트 규칙/기억. Auto memory는 machine-local이며 audit가 필요하다: [Memory docs](https://code.claude.com/docs/en/memory).
- Skills: 반복 가능한 지식/절차 패키지. nested `.claude/skills`와 side-effect skill의 `disable-model-invocation` 정책을 고려한다: [Skills docs](https://code.claude.com/docs/en/skills).
- Hooks: 특정 명령/이벤트에 deterministic guardrail 적용. `PreToolUse`, `ConfigChange`, `SessionStart` hook이 보안/감사에 중요하다: [Hooks guide](https://code.claude.com/docs/en/hooks-guide).
- Subagents: 역할별 specialist agent. isolated context, nested subagents, tool/skill/MCP scope, worktree isolation을 설계한다: [Subagents docs](https://code.claude.com/docs/en/sub-agents).
- MCP: 외부 도구/데이터 연결. HTTP transport, MCP Tool Search, managed MCP allowlist를 검토한다: [MCP docs](https://code.claude.com/docs/en/mcp), [Managed MCP](https://code.claude.com/docs/en/managed-mcp).
- Security: prompt injection, permission, sandbox, connector 위험을 다룸: [Claude Code security](https://code.claude.com/docs/en/security).

실무상 Claude Code는 대형 리팩터링/탐색/계획/테스트 루프에 강하지만, permission fatigue 때문에 무심코 위험 권한을 승인하는 문제가 생길 수 있다. Anthropic은 sandboxing에서 filesystem과 network isolation을 모두 강조한다: [Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing), [Sandboxed Bash](https://code.claude.com/docs/en/sandboxing). Auto mode는 승인 자동화 기능이지만 sandbox 대체재가 아니며 false negative가 남을 수 있다: [Claude Code auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode), [How we contain Claude](https://www.anthropic.com/engineering/how-we-contain-claude). 또한 Agent SDK는 Claude Code의 tool loop와 context management를 Python/TypeScript library로 가져와 production agent를 만들 수 있게 한다: [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview).

### Cursor, Devin Desktop/Windsurf, VS Code Agent Mode

Cursor는 IDE형 agent 워크스페이스다. Cursor 3의 핵심은 "정확히 3개의 agent"가 아니라 agent-first workspace, Agents Window, local/cloud agents, cloud-local handoff, web/mobile/Slack/GitHub/Linear 진입점이다: [Cursor 3](https://cursor.com/blog/cursor-3), [Cursor on web and mobile](https://cursor.com/blog/agent-web). Rules, codebase indexing, semantic search, instant grep, `.cursorignore`, `.cursorindexingignore`, Team Rules, nested `AGENTS.md`를 통해 context를 구성한다: [Cursor rules](https://cursor.com/docs/rules), [Cursor search](https://cursor.com/docs/agent/tools/search), [Cursor ignore files](https://cursor.com/docs/reference/ignore-file). Cursor SDK와 Cloud Agents API는 public beta 성격으로, local/cloud/self-hosted agent runtime을 TypeScript에서 호출하는 경로다: [Cursor TypeScript SDK](https://cursor.com/blog/typescript-sdk).

Windsurf는 2026-06-02 Devin Desktop으로 전환됐다. Devin Desktop은 기존 IDE 기능을 유지하면서 Devin Cloud, Agent Command Center, Spaces, Kanban형 multi-agent 관리를 결합하는 방향이다: [Introducing Devin Desktop](https://cognition.ai/blog/introducing-devin-desktop), [Devin Desktop changelog](https://docs.devin.ai/desktop/changelog). Devin/Windsurf 계열은 `.devin/rules/`, legacy `.windsurfrules`, `.windsurf/rules/`, `AGENTS.md`, Cursor `.mdc` rules import, `.devinignore`, fast context, memories, workflows를 지원한다: [Devin AGENTS.md docs](https://docs.devin.ai/desktop/cascade/agents-md), [Devin Desktop FAQ](https://docs.devin.ai/desktop/devin-desktop-faq), [Devin Local](https://docs.devin.ai/desktop/devin-local).

VS Code Agent Mode는 Copilot 기반 agent를 IDE 안에 통합한다. agent가 codebase를 검색하고 파일 수정/터미널 명령/오류 수정 루프를 수행하며 MCP 서버를 사용할 수 있다: [VS Code agent mode](https://code.visualstudio.com/blogs/2025/04/07/agentMode), [VS Code MCP servers](https://code.visualstudio.com/docs/agent-customization/mcp-servers). VS Code 기준으로 custom agents는 `.agent.md` 파일이고, `AGENTS.md`는 custom instructions 계층으로 쓰는 구분이 중요하다: [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents), [VS Code custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions). Agent Skills는 Copilot in VS Code, Copilot CLI, Copilot cloud agent에서 재사용 가능한 skill format으로 설명된다: [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills).

IDE형 도구의 장점은 개발자가 context를 유지하면서 diff를 바로 볼 수 있다는 점이다. 약점은 로컬 권한과 IDE extension 권한이 넓어질 수 있고, 여러 agent가 같은 worktree에서 충돌할 수 있다는 점이다.

### GitHub Copilot

GitHub Copilot은 IDE agent mode, Copilot cloud agent, code review, custom instructions, Actions/Issues/PR integration을 포함한다. 2025년에는 "Copilot coding agent"라는 명칭으로 GA가 공지됐지만, 현재 공식 문서의 주 용어는 **Copilot cloud agent**다. Cloud agent는 GitHub에서 repository를 조사하고 plan을 만들고 branch에 code change를 push한 뒤 PR로 검토받는 흐름이다: [About Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent), [Copilot coding agent GA](https://github.blog/changelog/2025-09-25-copilot-coding-agent-is-now-generally-available/).

현업에서 중요한 기능:

- Cloud agent: issue/agent tab/API/Slack 등에서 작업 시작: [Start Copilot sessions](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions).
- Custom agent: task 유형별 설정: [Create custom agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents).
- Code review: PR 검토 보조: [Copilot code review](https://docs.github.com/copilot/using-github-copilot/code-review/using-copilot-code-review).
- Custom instructions: repo/org instruction: [Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot).
- Agentic Workflows: natural language로 workflow를 설명하고 Actions YAML로 연결하는 public preview: [GitHub Agentic Workflows](https://github.blog/changelog/2026-06-11-github-agentic-workflows-is-now-in-public-preview/).
- Slack/API: Slack thread나 REST API에서 cloud agent session을 시작하는 public preview 흐름: [Copilot cloud agent Slack integration](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/integrate-cloud-agent-with-slack), [Cloud agent API](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api).
- Agent HQ/third-party agents: Copilot cloud agent뿐 아니라 Codex 같은 third-party coding agent를 GitHub 안에서 함께 다루는 방향: [OpenAI Codex in GitHub Docs](https://docs.github.com/en/copilot/concepts/agents/openai-codex), [Copilot features](https://docs.github.com/en/copilot/get-started/features).
- Agentic audit log: enterprise audit log에서 `actor:Copilot` 기준으로 agentic activity를 추적: [Audit log events for agents](https://docs.github.com/en/copilot/reference/agentic-audit-log-events).

주의점도 공식 문서에 명확하다. Copilot cloud agent는 repository code에 접근하고 push할 수 있으며, prompt injection, sensitive information, audit visibility, automation risk가 있다: [Risks and mitigations for Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations). 또한 cloud agent는 Copilot content exclusions를 적용하지 않는다는 제한이 문서에 명시되어 있다: [About Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent). Slack에서 agent session을 시작하면 thread 내용이 PR context로 저장될 수 있고, linked GitHub account 권한으로 write action이 수행될 수 있으므로 민감한 논의는 context 범위를 제한해야 한다. Cloud agent API, Slack integration, Agentic Workflows에는 public preview 항목이 포함된다. API는 user-to-server token 중심이고, Agentic Workflows는 Actions minutes, inference/AI credits, `.lock.yml` compile, safe outputs, `max-ai-credits` 같은 운영 통제가 필요하다. Enterprise audit log는 `actor:Copilot` 기준 최근 agentic activity를 보여주지만, 로컬 Copilot prompt/client session data까지 모두 포함한다고 가정하면 안 된다: [Copilot cloud agent API](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api), [Slack integration](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/integrate-cloud-agent-with-slack), [Agentic audit events](https://docs.github.com/en/copilot/reference/agentic-audit-log-events).

### 오픈소스/self-host coding agent

GitHub 수치 기준: 2026-06-17 Asia/Seoul. `pushed`는 KST 환산 날짜/시간이다.

| Repo | Stars | Forks | Pushed KST | Archived | License | 판단 |
|---|---:|---:|---|---|---|---|
| [openai/codex](https://github.com/openai/codex) | 91,484 | 13,515 | 2026-06-17 04:28 | No | Apache-2.0 | OpenAI 공식 CLI, local/cloud 연계 |
| [openai/symphony](https://github.com/openai/symphony) | 25,394 | 2,575 | 2026-06-10 08:25 | No | Apache-2.0 | Codex orchestration/control-plane spec |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | 132,792 | 21,486 | 2026-06-16 06:35 | No | Anthropic Commercial Terms | 공개 repo지만 엄격한 OSS/self-host 후보로 분류하지 않음 |
| [cline/cline](https://github.com/cline/cline) | 63,385 | 6,698 | 2026-06-17 04:22 | No | Apache-2.0 | IDE/CLI/SDK와 model-agnostic 운영에 강함 |
| [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) | 24,237 | 3,321 | 2026-05-16 03:08 | Yes | Apache-2.0 | archived라 신규 도입 비권장 |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 46,320 | 4,599 | 2026-05-22 23:02 | No | Apache-2.0 | Git 기반 CLI pair programming이 성숙 |
| [continuedev/continue](https://github.com/continuedev/continue) | 33,722 | 4,670 | 2026-06-17 01:10 | No | Apache-2.0 | README상 read-only/비활성 신호가 있어 신규 핵심 의존 전 확인 필요 |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | 77,365 | 9,833 | 2026-06-17 04:26 | No | MIT core / enterprise 예외 | GUI/API/SDK/Cloud/Enterprise형 플랫폼, self-host 후보 |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 19,531 | 2,135 | 2026-06-16 06:50 | No | MIT | 연구/benchmark issue-fixing, 현재 개발 중심은 mini-swe-agent로 이동 |
| [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | 5,212 | 714 | 2026-06-16 07:21 | No | MIT | 작고 단순한 baseline, 평가/실험에 좋음 |
| [opencode-ai/opencode](https://github.com/opencode-ai/opencode) | 12,970 | 1,476 | 2025-09-18 11:54 | Yes | MIT | archived legacy |
| [anomalyco/opencode](https://github.com/anomalyco/opencode) | 175,234 | 21,258 | 2026-06-17 04:16 | No | MIT | 현재 active OpenCode 계열로 보임 |
| [charmbracelet/crush](https://github.com/charmbracelet/crush) | 25,405 | 1,826 | 2026-06-17 02:38 | No | FSL-1.1-MIT | active successor 성격의 터미널 agent, strict OSS 표기는 주의 |
| [aaif-goose/goose](https://github.com/aaif-goose/goose) | 49,584 | 5,239 | 2026-06-17 04:24 | No | Apache-2.0 | local agent 운영 후보 |
| [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) | 25,277 | 2,522 | 2026-06-17 02:08 | No | Apache-2.0 | Qwen 생태계 연계 후보, OAuth free tier 중단 조건 확인 필요 |
| [stackblitz-labs/bolt.diy](https://github.com/stackblitz-labs/bolt.diy) | 19,480 | 10,410 | 2026-02-07 23:36 | No | MIT | Bolt self-host 문맥에서는 stackblitz/bolt.new보다 적합한 후보 |

실사용 후보는 Cline, Aider, OpenHands, mini-SWE-agent, anomalyco/opencode, Goose, Qwen Code다. Roo Code와 opencode-ai/opencode는 archived 상태라 신규 핵심 의존으로는 부적합하다. Continue는 stars와 생태계 가치는 있지만, README상 read-only/비활성 신호가 있어 신규 도입 전 반드시 재확인해야 한다. Claude Code는 공개 repo가 있지만 Anthropic Commercial Terms가 적용되므로 OSS/self-host agent로 분류하면 안 된다. Crush는 active terminal agent지만 FSL-1.1-MIT라 엄격한 오픈소스 정책 조직에서는 별도 검토가 필요하다.

### AI app builder형

AI app builder는 "아이디어를 앱으로 바로 만드는" 제품군이다. v0, Replit Agent, Bolt, Lovable 등이 대표적이다.

- v0: Vercel의 AI app builder와 platform API. UI/component를 넘어 full-stack app generation으로 확장 중이다: [v0](https://v0.app/), [v0 Platform API](https://vercel.com/blog/build-your-own-ai-app-builder-with-the-v0-platform-api).
- Replit Agent: prompt에서 앱/웹사이트를 만들고 배포까지 연결하는 browser 개발 환경: [Replit AI](https://replit.com/ai), [Replit docs](https://docs.replit.com/build/welcome).
- Bolt: browser에서 full-stack app을 prompt, run, edit, deploy하는 흐름: [Bolt](https://bolt.new/), [stackblitz/bolt.new](https://github.com/stackblitz/bolt.new).
- Lovable: 비개발자/창업자용 AI app builder 성격이 강하다. 다만 public/private 설정과 데이터 노출 문제는 별도 확인이 필요하다: [Lovable guide](https://lovable.dev/guides/best-ai-app-builders).

이 계열은 MVP, UI prototype, admin dashboard, demo app에는 강하다. 그러나 보안/권한/데이터 모델/결제/인증/마이그레이션/운영 로직은 반드시 engineer review와 CI/CD gate를 거쳐야 한다.

## 현업 활용점

AI 개발 자동화는 다음 영역에서 실제 효과가 크다.

| 영역 | 활용 방식 | 권장 guardrail |
|---|---|---|
| 요구사항 정리 | 회의록/Slack thread/issue를 task brief, acceptance criteria, edge cases로 변환 | 원문 보존 위치와 결정 문서 분리 |
| 설계 | architecture option 비교, API contract 초안, ADR 초안 | 사람이 final decision owner |
| 구현 | 작은 issue, bug fix, 반복 CRUD, glue code, migration script 초안 | branch/PR 단위, 테스트 필수 |
| 리팩터링 | dead code 제거, type 정리, 함수 분리, naming 개선 | diff size 제한, behavior-preserving tests |
| 테스트 | unit/integration/e2e test 생성, regression 재현, fixture 정리 | test가 실제 실패를 잡는지 확인 |
| 코드 리뷰 | PR 요약, 위험 파일 표시, reviewer checklist 생성 | approval은 사람만 |
| 보안 점검 | secret scanning, dependency review, threat model checklist, taint-like review | high-risk finding은 수동 triage |
| 문서화 | README, runbook, API docs, changelog, onboarding guide | 실제 명령과 최신 경로 검증 |
| 온보딩 | repo map, first tasks, build/test flow 설명 | stale docs 방지 |
| PR/CI 자동화 | CI failure 분석, 작은 fix push, review comment 대응 | protected branch와 required checks |
| UI 검증 | screenshot diff, Playwright, browser automation, accessibility check | 사람이 최종 UX 확인 |
| 운영 자동화 | release note, incident summary, Slack digest, metrics report | prod write 권한 금지 |

위험한 영역도 명확하다.

- production DB, object storage, backup, billing, auth, IAM, DNS, secrets 변경을 agent에게 직접 맡기지 않는다.
- agent가 "도움이 되려고" scope 밖 파일을 수정하는 것을 막기 위해 task brief에 변경 가능/금지 파일을 명시한다.
- agent가 만든 코드는 "똑똑한 신입 개발자의 PR"처럼 리뷰한다.
- agent에게 prod credential, broad cloud token, organization admin 권한을 주지 않는다.

## LLM에게 프로젝트를 이해시키는 방법

LLM이 프로젝트를 잘 이해하게 만드는 핵심은 "많이 넣기"가 아니라 "항상 넣을 것, 필요할 때 찾을 것, 절대 넣지 않을 것"을 분리하는 것이다.

### 필수 컨텍스트 계층

| 계층 | 예시 | 목적 |
|---|---|---|
| 고정 규칙 | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` | agent별 행동 규칙, 금지사항, 검증 방식 |
| 문서 지도 | `docs/index.md`, `llms.txt`, `MANIFEST.md`, repo map | 어디를 먼저 읽어야 하는지 알려줌 |
| 설계 원천 | architecture docs, interface spec, scoring/masking/audit docs | 코드 변경의 근거 |
| 결정 기록 | ADR, `docs/decisions/`, meeting decision | 왜 이렇게 만들었는지 보존 |
| 계약 원천 | OpenAPI, JSON Schema, config schema, DB schema | agent가 API를 추측하지 않게 함 |
| 검증 원천 | tests, release gate, CI workflow, runbook | 완료 기준을 deterministic하게 제공 |
| 운영 맥락 | issues, PR history, Slack summary, Drive docs | 현재 왜 이 작업을 하는지 제공 |
| 검색 계층 | semantic search, file search, MCP/RAG | 필요할 때만 보조 검색 |

현재 repo처럼 root `AGENTS.md`를 공통 원천으로 두고 `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`를 얇은 adapter로 유지하는 구조는 최신 관행과 잘 맞는다. OpenAI는 Codex에서 `AGENTS.md`를 repo 지침으로 사용한다: [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md). Claude Code는 `CLAUDE.md` memory를 지원한다: [Claude Code memory](https://code.claude.com/docs/en/memory). Gemini CLI는 `GEMINI.md`를 사용한다: [Gemini CLI GEMINI.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md). `llms.txt`는 외부 LLM/문서 crawler가 핵심 문서를 찾도록 돕는 compact index로 쓰기 좋다: [llms.txt spec](https://github.com/answerdotai/llms-txt).

Deep Research와 Anthropic/Thoughtworks 자료를 교차검증한 결론은 "긴 context window에 전부 넣기"가 아니라 **finite context를 큐레이션하고, 필요한 자료만 tool로 당겨오고, 오래된/잡음 context를 비우는 것**이다. Anthropic은 just-in-time context, compaction, tool-result clearing, memory를 핵심 패턴으로 설명하고, Martin Fowler/Thoughtworks는 prompts와 instructions를 버전 관리되는 개발 산출물로 다룬다: [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Claude memory/compaction cookbook](https://docs.anthropic.com/en/docs/build-with-claude/context-windows), [Context Engineering for Coding Agents](https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html), [Specification by Prompting](https://martinfowler.com/articles/exploring-gen-ai/specification-by-prompting.html).

Context cost 기준:

| 컨텍스트 방식 | 비용/효과 | 권장 사용 |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md`, repo instructions | 매 작업에 들어가는 고정 비용 | 짧고 강한 규칙, 금지사항, 검증 명령만 |
| repo map, `docs/index.md`, `llms.txt` | 검색 방향을 줄여줌 | "어디를 읽을지" 안내 |
| semantic/file search | 필요한 순간만 비용 발생 | 구현 전 탐색, 관련 파일 찾기 |
| Slack/Drive/Docs connector | 최신 업무 맥락 제공 | read-only, allowlist, source citation 필수 |
| tool result / terminal output | 매우 빠르게 context를 오염시킴 | 실패 원인만 요약하고 raw log는 링크로 보존 |
| memory | 장기 반복 작업에 유용 | 개인정보/secret/오래된 결정 audit 필수 |

### Task Brief 템플릿

```md
Task Brief

날짜/기준:
목표:
범위:
명시적 제외:
먼저 읽을 파일:
관련 소스/테스트/스키마:
변경 가능 파일:
변경 금지 파일:
보안 규칙:
검증 명령:
완료 기준:
모르면 중단하고 물어볼 조건:
```

### Context Pack 템플릿

```md
Context Pack

## Always Read
- AGENTS.md
- docs/index.md
- package-specific AGENTS.md

## Source Of Truth
- architecture:
- API/schema:
- config:
- tests:
- runbook:

## Current Task
- issue/PR:
- acceptance criteria:
- risk:
- allowed files:

## Do Not Include
- raw PII
- secrets
- production credentials
- raw logs with sensitive data
- generated build/output directories unless explicitly needed
```

### Semantic Search / MCP / RAG 설계

MCP는 AI application과 외부 data/tool/workflow를 연결하는 표준이다: [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro). OpenAI file search/vector store와 embeddings도 문서 검색 계층으로 쓸 수 있다: [OpenAI file search](https://developers.openai.com/api/docs/guides/tools-file-search), [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings). Azure 문서도 RAG를 retrieval 기반으로 LLM 답변을 grounding하는 구조로 설명한다: [Azure RAG overview](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview).

권장 metadata:

```yaml
path:
title:
doc_type: agent_rule | architecture | schema | test | runbook | decision
scope: root | package | reference
owner:
version_or_date:
pii_safety: safe | aggregate_only | exclude
source_of_truth: true | false
related_contracts:
```

운영 원칙:

- `AGENTS.md`와 `docs/index.md`는 pinned context로 둔다.
- semantic search는 보조 검색이다. 검색 결과가 instruction보다 우선하지 않는다.
- `output/`, `outputs/`, `build/`, raw failure logs, raw PII 가능 보고서는 기본 제외한다.
- MCP connector는 읽기 전용부터 시작한다.
- Slack/Drive/GitHub에서 찾은 중요한 결정은 durable Markdown으로 다시 남긴다.

## 지식관리 도구 활용

### Obsidian

Obsidian은 local-first Markdown vault다. Vault는 로컬 파일 시스템 폴더이고, 내부 링크/backlinks/tags/properties/Canvas/Templates/Tasks/Dataview를 통해 프로젝트 지식 베이스를 만들 수 있다: [How Obsidian stores data](https://obsidian.md/help/data-storage), [Backlinks](https://obsidian.md/help/Plugins/Backlinks), [Tags](https://obsidian.md/help/tags), [Properties](https://obsidian.md/help/properties), [Canvas](https://obsidian.md/help/Plugins/Canvas), [Templates](https://obsidian.md/help/Plugins/Templates).

권장 용도:

- 개인/팀 연구 노트.
- 실험 로그, prompt card, 평가 결과, threat model.
- `[[concept]]` 기반 backlinks로 결정과 실험 추적.
- Dataview/Bases로 source, decision, experiment dashboard 구성: [Dataview](https://blacksmithgu.github.io/obsidian-dataview/), [Obsidian Bases](https://obsidian.md/help/bases).
- Git sync로 Markdown vault versioning: [Obsidian Git](https://github.com/Vinzent03/obsidian-git).

추천 vault 구조:

```text
AI-Security-KB/
  00-inbox/
  10-projects/
    project-name/
      overview.md
      decisions/
      experiments/
      eval-runs/
      prompts/
      threat-models/
      release-evidence/
  20-concepts/
  30-sources/
  40-agent-context/
  50-canvases/
  60-templates/
  70-dashboards/
  90-archive/
```

보안 주의:

- Obsidian community plugin은 제3자 코드이며 파일 접근/네트워크 접근을 할 수 있다: [Plugin security](https://obsidian.md/help/plugin-security).
- Obsidian Sync는 remote vault에 end-to-end encryption을 제공하지만 local vault 자체를 암호화하지 않는다: [Sync security and privacy](https://obsidian.md/help/Obsidian%20Sync/Security%20and%20privacy).
- AI plugin, embedding cache, Git remote에 raw PII/secret이 들어가지 않게 한다.
- Smart Connections, Obsidian Copilot 같은 AI plugin은 local-first 또는 local model을 지원할 수 있지만, provider 설정에 따라 외부 embedding/model API로 vault 내용이 나갈 수 있다. plugin별 색인 대상이 tags/properties/frontmatter를 모두 포함한다고 가정하지 말고, retrieval test를 별도로 해야 한다: [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections), [Obsidian Copilot](https://github.com/logancyang/obsidian-copilot).

### Slack

Slack은 장기 기록 저장소보다 팀 context/event bus로 쓰는 편이 안전하다. 채널, thread, canvas, huddle notes, workflow, MCP server를 잘 연결하면 agent가 현재 작업 맥락을 찾기 쉽다. Slack AI 기능은 요금제별로 channel/thread summary, AI search, recap, huddle notes, canvas/workflow AI를 제공한다: [Guide to AI features in Slack](https://slack.com/help/articles/25076892548883-Guide-to-AI-features-in-Slack).

권장 구조:

- `#announcements`: 공지.
- `#project-name`: 프로젝트 본 대화.
- `#agent-context`: agent에게 줄 요약/링크.
- `#agent-run-log`: agent 실행 결과 요약.
- `#decisions`: 결정 사항 링크.
- `#code-review`: PR 리뷰 호출.
- `#deploy`: 배포/릴리즈.
- `#alerts`: 운영 알림.

운영 규칙:

- 채널 본문은 작업 단위 제목, 링크, 담당자, 마감, 결정만 둔다.
- 상세 논의는 thread로 모은다: [Slack threads](https://slack.com/help/articles/115000769927-Use-threads-to-organize-discussions).
- 채널 canvas에는 현재 목표, 주요 링크, 결정 목록, 온보딩을 유지한다: [Slack canvas](https://slack.com/help/articles/203950418-Use-a-canvas-in-Slack).
- huddle notes는 action item을 남기는 데 유용하지만 외부 사용자/guest 포함 시 제한이 있다: [Huddle notes](https://slack.com/help/articles/31377193680019-Use-AI-to-take-huddle-notes-in-Slack).
- Workflow Builder는 PR 알림, 회의 후 action item 생성, 주간 요약 같은 낮은 위험 자동화부터 적용한다: [Slack workflow automation](https://slack.com/features/workflow-automation).

Slack MCP server와 Real-time Search API는 AI assistant가 Slack data에 접근하도록 하는 공식 연결 방식이다. Slack은 2026-02-17 changelog에서 MCP server와 RTS API를 발표했고, 둘 다 agent가 channel/thread/file context를 더 정확히 가져오도록 설계됐다: [Slack MCP changelog](https://docs.slack.dev/changelog/2026/02/17/slack-mcp), [Slack developer MCP docs](https://docs.slack.dev/ai/slack-mcp-server), [Slack agentic collaboration](https://slack.com/blog/news/powering-agentic-collaboration). OAuth scope, app approval, audit logs, DLP를 같이 설계해야 한다: [App approval](https://slack.com/help/articles/222386767-Manage-app-approval-for-your-workspace), [App permissions](https://slack.com/intl/en-nz/help/articles/115003461503-Understand-app-permissions), [Slack audit logs](https://slack.com/help/articles/360000394286-Audit-logs-in-Slack), [Slack DLP](https://slack.com/help/articles/12914005852819-Slack-data-loss-prevention).

Slack AI 보안 설명은 customer data가 Slack-controlled infrastructure 밖으로 나가지 않고 LLM training에 쓰이지 않는다고 설명한다. 그러나 이것은 Slack native AI의 설명이며, third-party app/agent는 별도 vendor policy와 OAuth scope 검토가 필요하다: [Security for AI features in Slack](https://slack.com/help/articles/28310650165907-Security-for-AI-features-in-Slack), [Slack AI features](https://slack.com/features/ai).

무료 플랜은 최근 90일 메시지/파일 검색 제한이 있으므로 장기 decision archive로 쓰지 않는다: [Slack free plan limitations](https://slack.com/help/articles/27204752526611-Feature-limitations-on-the-free-version-of-Slack). Slack API Terms와 Real-time Search API 방향을 고려하면, Slack 전체를 외부 vector DB에 영구 복제하는 설계보다 permission-aware query-time retrieval로 제한하는 편이 안전하다: [Slack Web API](https://docs.slack.dev/apis/web-api/), [Slack Real-time Search API](https://docs.slack.dev/apis/web-api/real-time-search-api), [Slack API Terms](https://slack.com/terms-of-service/api).

### Google Drive, Docs, Sheets, Slides, Gemini, NotebookLM

Google Drive/Workspace는 공식 산출물과 권한 기반 공유에 강하다. 역할 분리는 다음이 좋다.

- Drive shared drive: 산출물 원장, 권한, 버전, 활동 이력.
- Docs: 요구사항, 회의록, 결정, handoff, 보고서.
- Sheets: 실험 결과, issue matrix, 평가표, 비용/한도 추적.
- Slides: 발표자료.
- Gemini for Workspace: 문서 초안, 요약, Drive 검색, 표/수식/슬라이드 보조.
- NotebookLM: 선별된 source corpus 기반 질의/요약/출처 확인.

Shared drive는 개인 Drive보다 팀 소유권과 권한 관리가 안정적이다. Drive API에서 shared drive를 다룰 때 `supportsAllDrives`, `driveId`, `corpora=drive` 등 파라미터가 필요하다: [Shared drives API guide](https://developers.google.com/workspace/drive/api/guides/enable-shareddrives). 권한은 Google Group 기반으로 Manager/Content Manager/Contributor/Commenter/Viewer를 분리한다: [Drive roles and permissions](https://developers.google.com/workspace/drive/api/guides/ref-roles).

Drive는 revision/change history를 제공하고, Drive Activity API와 Reports API로 감사/증거 관리가 가능하다: [Drive changes and revisions](https://developers.google.com/workspace/drive/api/guides/change-overview), [Manage revisions](https://developers.google.com/workspace/drive/api/guides/manage-revisions), [Drive Activity API](https://developers.google.com/workspace/drive/activity/v2), [Drive audit reports](https://developers.google.com/workspace/admin/reports/v1/guides/manage-audit-drive).

Docs/Sheets/Slides 자동화는 공식 API를 사용한다: [Docs API overview](https://developers.google.com/workspace/docs/api/how-tos/overview), [Sheets API concepts](https://developers.google.com/workspace/sheets/api/guides/concepts), [Slides API overview](https://developers.google.com/workspace/slides/api/guides/overview).

Gemini for Workspace는 조직의 Workspace security/data handling control을 따른다고 설명한다. 다만 Gemini가 사용자 권한 안의 Drive/Docs/Gmail 데이터를 요약할 수 있으므로, 접근권한 설계가 곧 AI 접근권한 설계다: [Gemini Workspace Privacy Hub](https://knowledge.workspace.google.com/admin/generative-ai/generative-ai-in-google-workspace-privacy-hub). Gemini side panel은 Docs/Sheets/Slides/Drive/Gmail/Chat에서 초안, 요약, 표, 수식, 자료 검색을 지원한다: [Google Workspace with Gemini](https://knowledge.workspace.google.com/admin/generative-ai/workspace-with-gemini/google-workspace-with-gemini). Google 문서는 Gemini source가 context window 제한 때문에 일부만 쓰일 수 있고, source를 놓치거나 잘못 인용할 수 있다고 경고하므로, Drive source 연결 후에도 citation 확인과 원문 재검증이 필요하다: [Use sources with Gemini](https://support.google.com/drive/answer/16813283?hl=en).

NotebookLM은 source 기반 notebook으로 쓸 수 있고 답변에 citation을 제공한다: [NotebookLM guide](https://support.google.com/notebooklm/answer/16206563?hl=en), [NotebookLM sources](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en). 2026년 업데이트로 Google Drive source 자동 동기화가 추가되어 Docs/Sheets/Slides가 바뀌면 notebook source도 더 쉽게 최신화된다: [NotebookLM Drive syncing](https://workspaceupdates.googleblog.com/2026/05/keep-your-sources-up-to-date-with-automatic-Drive-syncing-in-NotebookLM.html). 기본 한도와 source copy/auto-sync 모델을 이해해야 하며, notebook 공유 시 source 문서와 note가 함께 노출될 수 있다: [NotebookLM sources](https://support.google.com/notebooklm/answer/16215270), [NotebookLM FAQ](https://support.google.com/notebooklm/answer/16269187). Enterprise/Workspace 환경에서는 sharing, IAM, cache, data region 적용 여부를 확인해야 한다: [NotebookLM Enterprise overview](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview), [NotebookLM admin controls](https://knowledge.workspace.google.com/admin/generative-ai/notebooklm/turn-notebooklm-on-or-off-for-users).

Google Workspace MCP는 2026-06-17 기준 Developer Preview 성격이 강하다. Drive MCP는 OAuth, `drive.readonly`, `drive.file` scope와 파일 검색/읽기/생성/권한 조회 도구를 제공한다: [Configure Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers), [Configure Drive MCP server](https://developers.google.com/workspace/drive/api/guides/configure-mcp-server), [Workspace MCP developer preview](https://workspaceupdates.googleblog.com/2026/05/agent-tools-and-security-updates-for-workspace-developers.html). Google도 Drive MCP 문서에서 untrusted 문서가 prompt injection 경로가 될 수 있다고 경고한다. Docs/Sheets/Slides 전용 MCP server를 전제하기보다 Drive file/Gemini source/API automation으로 다루는 편이 현재 공개 문서와 더 맞다.

Google Cloud 쪽에서는 Workspace MCP와 별도로 Google infrastructure에서 실행되는 remote MCP server와 Google official MCP server 목록이 공개되어 있다. Cloud/infra/data agent를 설계할 때는 Workspace Drive MCP와 Google Cloud managed MCP를 구분해야 한다: [Google Cloud MCP supported products](https://docs.cloud.google.com/mcp/supported-products), [google/mcp](https://github.com/google/mcp), [Managed MCP servers for Google Cloud databases](https://cloud.google.com/blog/products/databases/managed-mcp-servers-for-google-cloud-databases).

Workspace 보안은 DLP와 감사 로그까지 같이 봐야 한다. Google Workspace DLP는 Drive/Gmail/Chat/Calendar/Chrome 등에서 data protection rule과 alert/audit-only test를 제공하지만, 미스캔 범위와 edition 제한이 있다: [Google Workspace DLP](https://knowledge.workspace.google.com/admin/security/about-dlp), [Create data protection rules](https://knowledge.workspace.google.com/admin/security/create-data-protection-rules), [DLP dashboard and alerts](https://support.google.com/a/answer/14088117). Drive log events와 API-based action audit는 agent/MCP가 파일을 읽거나 다운로드한 흔적을 조사하는 데 필요하다: [Drive log events](https://knowledge.workspace.google.com/admin/reports/drive-log-events), [API-based audit logs](https://workspaceupdates.googleblog.com/2024/05/audit-logs-for-API-based-actions.html).

## 현업 도입 아키텍처

가장 안정적인 구조는 GitHub를 코드/이슈/PR의 단일 운영 원장으로 두고, Slack은 event bus, Drive/Docs는 공식 산출물, Obsidian/Notion은 지식 베이스, coding agent는 branch/PR 작업자, CI/CD는 merge/deploy gate로 분리하는 것이다.

```text
Slack 요청/장애/리뷰 호출
  -> GitHub Issue / Project item
  -> 사람 또는 coding agent가 branch 작업
  -> Pull Request
  -> CI: test, lint, typecheck, security scan, dependency scan
  -> CODEOWNERS / required reviewer / human review
  -> staging/prod environment approval
  -> deploy 결과와 incident 알림은 Slack
  -> 결정, 회의록, 승인 문서는 Docs/Drive 또는 Notion에 링크
```

LLM context 흐름은 별도 gateway로 분리한다.

```text
Agent task
  -> Context Gateway
  -> pinned repo docs: AGENTS.md, docs/index.md, architecture, tests
  -> Obsidian/Notion: 결정/ADR/실험 로그 요약
  -> Google Drive: 공식 산출물, 회의록, spec, spreadsheet
  -> Slack: 현재 thread/channel context를 query-time으로 제한 검색
  -> response에는 source URL, retrieved_at, permission_basis, sensitivity를 붙임
```

이 구조의 핵심은 Slack/Drive 전체를 agent memory로 복제하지 않는 것이다. Obsidian/Notion은 curated memory, Drive는 governed artifacts, Slack은 real-time context로 역할을 나누고, 중요한 결정은 durable Markdown/Docs로 승격한다. Source chunk에는 `source_system`, `source_url`, `owner`, `permission_basis`, `sensitivity`, `retrieved_at`, `retention_policy`, `hash`를 붙인다.

GitHub Projects는 issue/PR 기반 작업 보드다: [GitHub Projects](https://docs.github.com/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects). Pull Request는 변경 논의, review, checks, merge blocker를 모으는 협업 단위다: [About pull requests](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests). CODEOWNERS와 rulesets/branch protection은 review와 merge policy를 강제한다: [CODEOWNERS](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [Branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).

Slack에는 GitHub app을 연결해 PR/issue 알림과 리뷰 흐름을 만든다: [GitHub in Slack](https://docs.github.com/en/integrations/how-tos/slack/use-github-in-slack), [GitHub Slack app](https://slack.com/marketplace/A01BP7R4KNY-github). Google Drive/Docs는 comment/action item/approval로 공식 산출물 검토를 담당한다: [Docs comments and action items](https://support.google.com/docs/answer/65129?co=GENIE.Platform%3DDesktop&hl=en), [Drive approvals](https://support.google.com/drive/answer/9387535?co=GENIE.Platform%3DDesktop&hl=en).

조직별 추천:

| 조직 | 권장 스택 | 실험 순서 |
|---|---|---|
| 개인 | GitHub Free/Pro, GitHub Actions, Obsidian local vault, Google Docs, Codex/Claude/Aider | docs/test/refactor부터 agent 사용 |
| 소규모팀 | GitHub Team, Projects, CODEOWNERS, Slack Pro, Google shared drive, Notion/Obsidian | issue -> agent branch -> PR -> 사람 리뷰 |
| 제품 개발팀 | GitHub Team/Enterprise, Actions environments, required reviewers, Slack 채널 체계, Drive approvals, DORA metrics | CI/CD gate와 review latency 측정 |
| 엔터프라이즈 | GitHub Enterprise, SAML/SCIM, audit log streaming, Slack Enterprise Grid, Workspace DLP, Notion Enterprise | SIEM과 connector allowlist 먼저 |
| 보안 민감 조직 | self-hosted runner, private package mirror, secret scanning/push protection, local/sandbox agent, no prod write | 비민감 repo pilot 후 확장 |

DORA metrics는 lead time, deployment frequency, change fail rate, failed deployment recovery time을 추적하는 기준으로 쓸 수 있다: [DORA metrics](https://dora.dev/guides/dora-metrics/). GitHub Actions environment approval은 배포 gate에 적합하다: [Deploying with GitHub Actions](https://docs.github.com/actions/deployment/about-deployments/deploying-with-github-actions).

## 국내/서비스 회사 실무 사례

해외 vendor 문서와 benchmark는 도구의 방향을 보여주지만, 국내 서비스 회사 기술 블로그는 "AI를 실제 업무 어디에 붙였는지"를 보기 좋다. 특히 개발 자동화 문서에는 다음 자료를 보강 근거로 넣는 것이 유용하다.

| 출처 | 참고할 글 | 문서에 주는 의미 |
|---|---|---|
| NAVER D2 | [AI 에이전트를 위한 Playwright E2E 테스트 하네스 구축하기](https://d2.naver.com/helloworld/6811215) | AI agent가 만든 코드를 믿기 위한 Playwright 기반 E2E 검증 하네스 사례. UI 검증/agent verification 근거로 좋다. |
| NAVER D2 | [MLXP : Kubernetes LLM Serving 최적화 기술 도입기](https://d2.naver.com/helloworld/1059238) | Kubernetes 기반 LLM serving 최적화 사례. agent 자체보다 LLM serving/운영 인프라를 조사할 때 보강 가치가 크다. |
| NAVER D2 | [AI국민비서: 공공 특화 에이전트 구축하기](https://d2.naver.com/helloworld/6647064) | 도메인 특화 agent를 구축할 때 정책/도메인 context/공공 서비스 제약을 어떻게 다루는지 참고할 수 있다. |
| Kakao Tech | [AI 데브옵스 시스템, 카카오릴리즈](https://tech.kakao.com/posts/742) | 배포 계획, 배포 실행, 배포 후 모니터링을 AI와 결합한 DevOps workflow 사례. 운영 자동화 섹션에 적합하다. |
| Kakao Tech | [분산 추적 기반 AI 운영 생태계](https://tech.kakao.com/posts/747) | "모니터링 -> 감지 -> 원인 분석 -> 조치 -> 반영" 흐름을 AI 운영과 연결하는 자료. agent observability와 incident workflow 보강에 좋다. |
| Kakao Tech | [실시간 코드 리뷰 및 품질 관리: AI 기반 정적 분석 기술](https://tech.kakao.com/posts/732), [단위 테스트 자동 생성을 통한 코드 품질 향상](https://tech.kakao.com/posts/733) | 코드 리뷰/정적 분석/테스트 생성 자동화의 국내 사례. PR gate와 review burden 논의에 연결된다. |
| Kakao Tech | [AI의 자기 보호 시스템: AI 가드레일](https://tech.kakao.com/posts/741) | AI 서비스 운영에서 guardrail과 지속 모니터링이 필요하다는 점을 국내 사례로 설명한다. |
| KakaoPay Tech | [페이증권의 업무도우미 AI봇을 소개합니다](https://tech.kakaopay.com/post/choonsiri/) | Amazon Bedrock, Slack bot, 사내 지식저장소/RAG, 코드리뷰봇을 결합한 금융권 내부 AI assistant 사례. |
| KakaoPay Tech | [PR을 더 느리게 만들기 위한 고민](https://tech.kakaopay.com/post/kakaopayins-slow-pr-fast-dev/) | AI로 구현 속도는 빨라졌지만 리뷰 병목이 생겼고, 작은 PR/설계 의도/트레이드오프 중심으로 리뷰를 재설계해야 한다는 현업 신호. |
| 우아한형제들 | [하네스 엔지니어링으로 팀 맞춤형 AI 환경 구축하기](https://techblog.woowahan.com/26177/) | Cursor Rules/Skills로 팀 규칙을 agent context에 넣고, script summary로 context/token을 줄이는 국내 harness engineering 사례. |
| 우아한형제들 | [우아한공방의 새로운 동료, 시스템 맥락을 가진 챗봇서비스 개발기](https://techblog.woowahan.com/26319/) | MCP만으로는 비개발자 접근성, 품질 측정, 권한/운영 통제가 어렵다는 한계를 지적하고 Bedrock Knowledge Bases 기반 RAG 챗봇으로 확장한 사례. |
| 우아한형제들 | [RAG, 들어는 봤는데… 내 서비스엔 어떻게 쓰지?](https://techblog.woowahan.com/25900/) | RAG를 색인, 생성, 평가 파이프라인으로 나눠 실제 서비스 적용 절차를 설명한다. |
| 우아한형제들 | [5년 동안 못 푼 배민 다국어 숙제, AI와 함께 한 달 만에 끝내기](https://techblog.woowahan.com/26162/) | LLM이 단순 챗봇이 아니라 대규모 운영 backlog를 줄이는 실행 도구가 될 수 있음을 보여준다. 단, 빠른 실험/의사결정 구조가 같이 필요하다. |
| Toss Tech | [LLM을 이용한 서비스 취약점 분석 자동화 #1](https://toss.tech/article/vulnerability-analysis-automation-1), [#2](https://toss.tech/article/vulnerability-analysis-automation-2) | 대용량 코드 context, hallucination, 비용/운영, source-code browse MCP, multi-agent, LangGraph/LangChain, Langfuse 같은 보안 자동화 구현 고민이 잘 드러난다. |
| Toss Tech | [개발자는 AI에게 대체될 것인가](https://toss.tech/article/will-ai-replace-developers), [소프트웨어 3.0 시대를 맞이하며](https://toss.tech/article/software-3-0-era) | 개발자 역할이 코드 생산자에서 설계자, agent 지휘자, 검증 책임자로 이동한다는 관점 자료. |
| Cloudflare Blog | [The AI engineering stack we built internally](https://blog.cloudflare.com/internal-ai-engineering-stack/) | Engineering Codex, agent skills, multi-agent consensus, AI Gateway 운영 지표처럼 대규모 사내 AI engineering stack 사례가 구체적이다. |
| Cloudflare Blog | [Orchestrating AI Code Review at scale](https://blog.cloudflare.com/ai-code-review/) | OpenCode 기반 CI-native multi-agent code review, plugin architecture, specialist reviewers, severity 판단, single structured review comment 구조가 현업 PR 자동화에 매우 직접적이다. |
| AWS ML Blog | [Evaluate Amazon Bedrock Agents with Ragas and LLM-as-a-judge](https://aws.amazon.com/blogs/machine-learning/evaluate-amazon-bedrock-agents-with-ragas-and-llm-as-a-judge/), [Evaluate RAG reliability using Bedrock](https://aws.amazon.com/blogs/machine-learning/evaluate-the-reliability-of-retrieval-augmented-generation-applications-using-amazon-bedrock/) | Bedrock Agent/RAG를 운영하려면 evaluation과 reliability 측정을 별도 설계해야 한다는 구현 참고 자료. |
| OpenAI Engineering | [Engineering](https://openai.com/news/engineering/) | Codex, harness engineering, Responses API computer environment, WebSocket 기반 agentic workflow, Codex sandbox/Windows 운영 자료가 모여 있어 frontier vendor의 제품화 흐름을 추적하기 좋다. |
| Anthropic Engineering | [Engineering](https://www.anthropic.com/engineering), [How we contain Claude across products](https://www.anthropic.com/engineering/how-we-contain-claude) | Claude Code, context engineering, tool use, managed agents, containment, persistent memory poisoning, multi-agent trust escalation 같은 agent 보안/운영 관점을 보강한다. |

직접적인 개발 자동화 사례는 아니지만, 다음 자료는 배경 참고로 분리해 두는 것이 좋다.

| 출처 | 참고할 글 | 문서에 주는 의미 |
|---|---|---|
| Google Research / DeepMind | [AI in software engineering at Google](https://research.google/blog/ai-in-software-engineering-at-google-progress-and-the-path-ahead/), [Towards a science of scaling agent systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/), [ReasoningBank](https://research.google/blog/reasoningbank-enabling-agents-to-learn-from-experience/) | Google 내부 개발 도구, agent scaling, agent memory 연구를 볼 수 있다. 현업 coding agent 도입의 정답이라기보다 evaluation, agent memory, productization 원칙의 근거로 쓴다. |
| Meta Engineering - AI | [Ranking Engineer Agent](https://engineering.fb.com/2026/03/17/developer-tools/ranking-engineer-agent-rea-autonomous-ai-system-accelerating-meta-ads-ranking-innovation/), [Meta Adaptive Ranking Model](https://engineering.fb.com/2026/03/31/ml-applications/meta-adaptive-ranking-model-bending-the-inference-scaling-curve-to-serve-llm-scale-models-for-ads/), [Building Meta's GenAI Infrastructure](https://engineering.fb.com/2024/03/12/data-center-engineering/building-metas-genai-infrastructure/) | Ads ranking/ML lifecycle를 자동화하는 agent 사례와 대규모 AI infra/serving 사례를 제공한다. 일반 웹서비스 개발 자동화보다는 ML 실험 자동화와 대규모 추천/서빙 아키텍처 참고에 가깝다. |
| Netflix TechBlog - Machine Learning | [Machine Learning](https://netflixtechblog.com/tagged/machine-learning), [Building the Model Lifecycle Graph](https://netflixtechblog.com/democratizing-machine-learning-at-netflix-building-the-model-lifecycle-graph-5cc6d5828bb1) | 추천, 미디어 ML, MLOps, model lifecycle graph처럼 ML platform 운영을 이해하는 데 좋다. coding agent보다는 "AI/ML을 제품 조직에 운영 체계로 붙이는 법"을 설명할 때 보조 근거로 둔다. |

이 자료들을 종합하면 국내 실무 사례는 네 가지 패턴으로 묶인다.

- **Context/Harness**: `AGENTS.md`, Cursor Rules/Skills, repo map, script summary, Engineering Codex처럼 agent가 따라야 할 작업 환경을 먼저 만든다.
- **RAG/Knowledge Assistant**: Slack/Drive/사내 문서/디자인 시스템/보안 지식을 검색 가능한 knowledge base로 만들되, 권한/메타데이터/평가/품질 측정을 함께 설계한다.
- **DevOps/Review Automation**: 배포, 모니터링, 정적 분석, 테스트 생성, PR review를 AI와 연결하지만 최종 merge/deploy gate는 사람/CI/policy가 잡는다.
- **Security Automation**: 취약점 분석 자동화는 가장 가치가 크지만 hallucination, 대용량 코드 context, MCP 권한, trace/monitoring, 오탐/정탐 평가가 병목이다.

따라서 이 문서를 국내 사례로 발표하거나 팀에 공유할 때는 NAVER D2, Kakao Tech, 우아한형제들, Toss, KakaoPay를 먼저 보여주고, Cloudflare/AWS는 해외 대규모 운영/아키텍처 참고 자료로 붙이는 구성이 가장 설득력 있다.

## 벤치마크와 논문

공개 benchmark는 도구 비교의 시작점일 뿐, 현업 성공을 보장하지 않는다.

| Benchmark | 의미 | 현재 해석 |
|---|---|---|
| [SWE-bench](https://www.swebench.com/) | 실제 GitHub issue 해결 | 대표 repo-scale benchmark |
| [SWE-bench Verified](https://www.swebench.com/verified.html) | 사람이 검증한 SWE-bench subset | 2026년 frontier model 평가에는 오염/테스트 문제로 단독 사용 부적합 |
| [SWE-bench Pro](https://labs.scale.com/leaderboard/swe_bench_pro_public) | 더 어려운 held-out/enterprise-style benchmark | frontier 비교에 더 유용한 흐름 |
| [Terminal-Bench](https://www.tbench.ai/) | terminal task 수행 능력 | agentic terminal automation 측정 |
| [LiveCodeBench](https://livecodebench.github.io/) | 시간 기반 contamination 완화 coding benchmark | algorithm/code generation 비교에 유용 |
| [HumanEval](https://arxiv.org/abs/2107.03374) / [EvalPlus](https://evalplus.github.io/) | 함수 단위 coding 능력 | 너무 좁으므로 보조 지표 |
| [MBPP](https://github.com/google-research/google-research/tree/master/mbpp) / [APPS](https://arxiv.org/abs/2105.09938) | programming problem solving | 보조 지표 |
| [BigCodeBench](https://github.com/bigcode-project/bigcodebench) | 더 실용적인 coding benchmark | 보조 지표 |
| [SWE-PolyBench](https://amazon-science.github.io/SWE-PolyBench/) | multi-language repo-level SWE task | Python 중심 SWE-bench 보완 |
| [SWE-bench Multilingual](https://www.swebench.com/multilingual.html) | 9개 언어 repo task | multi-language calibration |
| [SWE-EVO](https://arxiv.org/abs/2512.18470) | release note 기반 long-horizon software evolution | feature/evolution 능력 평가 |
| [FeatureBench](https://arxiv.org/abs/2602.10975) | end-to-end feature development | SWE-bench류보다 제품 기능 구현에 가까움 |
| [SWE-Explore](https://arxiv.org/abs/2606.07297) | repo exploration/localization diagnostic | "어디를 봤는지" 측정 |

OpenAI는 SWE-bench Verified가 frontier coding capability를 더 이상 잘 측정하지 못한다고 설명하며 SWE-bench Pro를 권장한다: [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/). 2026-06-17 기준 공개 leaderboard에서는 Terminal-Bench 2.1이 agent harness별 terminal automation 성능을 보여주고, SWE-Bench Pro는 더 어려운 long-horizon software engineering task를 표방한다: [Terminal-Bench 2.1 leaderboard](https://www.tbench.ai/leaderboard/terminal-bench/2.1), [SWE-Bench Pro](https://labs.scale.com/leaderboard/swe_bench_pro_public), [SWE-Bench Pro paper](https://arxiv.org/html/2509.16941v1). 따라서 "최고 agent" 판단은 SWE-bench Verified 한 줄 순위가 아니라 Terminal-Bench, SWE-bench Pro, LiveCodeBench, 자체 held-out repo tasks, CI pass rate, review burden을 함께 봐야 한다.

벤치마크 해석 규칙:

| 구분 | 의미 | 문서화 필드 |
|---|---|---|
| vendor-reported | vendor blog/launch post가 제시한 수치 | 모델, harness, split, budget, 재현 가능성 |
| public leaderboard | benchmark 운영자가 공개한 ranking | 제출일, agent scaffold, pass@k, tool permission |
| paper result | 논문 실험 조건의 수치 | commit/version, dataset split, cost, run count |
| internal eval | 조직 내부 repo snapshot 평가 | repo commit, hidden tests, reviewer acceptance, cost/latency |

모델 단독 성능과 agent harness 성능은 분리해야 한다. 같은 모델이라도 Codex CLI, Claude Code, Copilot cloud agent, OpenHands, custom harness에서 결과가 달라진다. Terminal-Bench 논문도 model과 agent scaffold 효과를 분리하기 어렵다고 지적한다: [Terminal-Bench paper](https://arxiv.org/html/2601.11868v1).

관련 연구:

- SWE-bench paper: [arXiv 2310.06770](https://arxiv.org/abs/2310.06770).
- SWE-agent: [arXiv 2405.15793](https://arxiv.org/abs/2405.15793).
- AutoCodeRover: [arXiv 2404.05427](https://arxiv.org/abs/2404.05427).
- Agentless: [arXiv 2407.01489](https://arxiv.org/abs/2407.01489).
- OpenHands: [arXiv 2407.16741](https://arxiv.org/abs/2407.16741).
- SWE-smith: [arXiv 2504.21798](https://arxiv.org/abs/2504.21798).
- SWE-PolyBench: [arXiv 2504.08703](https://arxiv.org/abs/2504.08703).
- SWE-bench Multilingual: [SWE-bench Multilingual](https://www.swebench.com/multilingual.html).
- CodeClash: [CodeClash](https://codeclash.ai/).
- SWE-EVO: [arXiv 2512.18470](https://arxiv.org/abs/2512.18470).
- AI Agentic Programming survey: [arXiv 2508.11126](https://arxiv.org/html/2508.11126v1).
- FeatureBench: [arXiv 2602.10975](https://arxiv.org/abs/2602.10975).
- SWE-Explore: [arXiv 2606.07297](https://arxiv.org/abs/2606.07297).

현업 내부 평가 권장:

- 10-30개 실제 과거 issue를 재현 가능한 sandbox에 넣는다.
- 해결 성공 여부보다 diff size, test pass, reviewer time, rollback risk를 같이 기록한다.
- agent가 만든 PR을 사람이 이해하는 데 걸린 시간을 측정한다.
- secret/PII/권한/운영 변경 작업은 별도 high-risk category로 둔다.
- 같은 모델도 Codex CLI, Claude Code, Copilot cloud agent, custom harness에 따라 결과가 달라지므로 "model eval"과 "agent harness eval"을 분리한다.
- benchmark 점수는 vendor-reported, leaderboard-run, internal-run 여부를 구분하고, 동일 task를 최소 3회 반복해 flakiness를 측정한다.
- pass@1은 실제 자동화 신뢰도, pass@k는 사람이 여러 후보 중 선택하는 workflow의 상한선으로 분리한다.
- 내부 metric에는 hidden test pass, reviewer acceptance, regression safety, diff quality, cost/latency, security violation, revert rate, context efficiency를 넣는다.

## 커뮤니티 후기와 전문가 관점

커뮤니티 후기는 통계가 아니라 signal로 봐야 한다. Reddit, Hacker News, X/Twitter, Threads 모두 표본 편향과 접근 제한이 있다. X와 Threads는 로그인/동적 페이지 제한 때문에 전문 확인이 어려운 경우가 있었고, 단독 근거로 쓰기보다는 Reddit mirror, HN 토론, 공식 문서와 교차검증했다.

현업 adoption 자료도 균형 있게 읽어야 한다. DORA 2025는 AI를 조직 역량의 amplifier로 설명하고, Stack Overflow 2025는 AI 사용은 늘었지만 정확성 신뢰와 긍정 sentiment는 약해졌다고 보고한다. METR의 2025/2026 연구는 숙련 개발자의 생산성 효과가 task selection, agent generation, 도구 사용 방식에 따라 복잡하게 달라진다는 신호를 준다: [DORA 2025](https://dora.dev/research/2025/dora-report/), [Stack Overflow Developer Survey 2025 AI](https://survey.stackoverflow.co/2025/ai), [METR experienced OSS developer study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/), [METR uplift update](https://metr.org/blog/2026-02-24-uplift-update/).

반복적으로 나온 커뮤니티 신호:

- 작은 작업, 스크립트, 테스트, 리팩터링, UI 초안, DevOps 잡무에서 생산성 향상이 크다.
- 오래된 대형 codebase, 인프라, 보안/데이터 변경, 제품 전체 설계는 감독 비용이 증가한다.
- 실패 패턴은 context loss, fake API, 불필요한 리팩터링, 테스트 미통과, scope creep, 승인된 함수 밖 변경, 완료 선언 후 미검증, hallucination loop -> 과금 loop다.
- 비용은 월 구독이 싸게 느껴지는 경우와 API/고급 플랜 한도가 빠르게 소진되는 경우가 공존한다. request 수가 아니라 token, context, MCP, memory/background task, model choice, GitHub Actions minutes까지 본다.
- 리뷰 병목이 커진다. agent가 PR을 만들어도 merge-ready 판단은 여전히 사람/CI/정책의 몫이다.
- production 사고 사례의 원인은 agent 자체보다 과도한 token scope, destructive action gate 부재, backup blast radius, prod 권한 부여인 경우가 많다.
- Full Access/danger mode, bypass permissions, issue/PR/comment prompt injection, Bash tool, package publish token이 결합되면 CI/CD 공급망 사고로 이어질 수 있다. Cline CLI 사고 회고와 Snyk 분석은 이 threat model을 실제 사례로 보여준다: [Cline post-mortem](https://cline.bot/blog/post-mortem-unauthorized-cline-cli-npm), [Snyk analysis](https://snyk.io/blog/cline-supply-chain-attack-prompt-injection-github-actions/).

전문가 관점:

- Andrej Karpathy: 자연어가 Software 3.0의 programming interface가 된다는 관점. vibe coding은 prototype 맥락으로 봐야 한다: [YC interview](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again).
- Addy Osmani: `spec -> plan -> scoped agent task -> diff review -> tests -> human accountability`를 강조한다: [Agentic engineering](https://addyosmani.com/blog/agentic-engineering/), [Agentic code review](https://addyosmani.com/blog/agentic-code-review/), [Comprehension debt](https://addyosmani.com/blog/comprehension-debt/).
- Simon Willison: context, tests, 사람이 언제든 넘겨받을 수 있는 상태를 강조한다: [Using LLMs for code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/), [Vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/).
- Kent Beck: augmented coding은 vibe coding과 달리 test, complexity, coverage를 계속 본다: [Augmented Coding](https://tidyfirst.substack.com/p/augmented-coding-beyond-the-vibes).
- Boris Cherny/Claude Code 흐름: plan mode, 병렬 session, shared instructions, reusable commands, evidence-based verification을 강조한다. 인터뷰성 자료는 제품 리더 발언이므로 과장 가능성도 감안한다: [Lenny interview](https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens).

## 보안과 거버넌스

AI coding agent는 저장소, 터미널, 커넥터, CI, 이슈, Slack까지 접근할 수 있는 자동화 주체다. 기본 정책은 **읽기/계획 우선, PR-only 변경, 프로덕션 직접 접근 금지, 사람 리뷰, CI gate, 감사로그**다.

| 영역 | 정책 |
|---|---|
| Secret leakage | 장기 secret을 agent runtime에 주지 않는다. GitHub secret scanning/push protection을 켠다: [GitHub secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning). |
| IP/licensing | public-code matching, license scan, code reference 확인을 사용한다: [Copilot public code policies](https://docs.github.com/copilot/how-tos/manage-your-account/managing-copilot-policies-as-an-individual-subscriber), [Code referencing](https://docs.github.com/en/copilot/concepts/completions/code-referencing?tool=jetbrains). |
| Least privilege | read-only/approval 기반 기본값. Codex sandbox/approval, Claude permission을 조직 정책으로 고정: [Codex security](https://developers.openai.com/codex/agent-approvals-security), [Claude security](https://code.claude.com/docs/en/security). |
| Connector permissions | OAuth scope와 read/write capability를 별도 검토. OpenAI/Slack/Google admin controls 사용: [OpenAI apps admin controls](https://help.openai.com/en/articles/11509118-admin-controls-security-and-compliance-in-apps-enterprise-edu-and-business), [Google app access control](https://knowledge.workspace.google.com/admin/apps/control-which-apps-access-google-workspace-data). |
| MCP prompt injection | tool description, server instruction, 외부 문서/메시지는 untrusted input. allowlist, private registry, approval, DLP 적용: [MCP security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices), [OWASP MCP Tool Poisoning](https://owasp.org/www-community/attacks/MCP_Tool_Poisoning). |
| MCP token/auth | OAuth 2.1, exact redirect URI, consent binding, token passthrough 금지, confused deputy 방지를 적용: [MCP authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization), [MCP security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices). |
| MCP inventory | 모든 MCP server의 owner, version, scopes, allowed tools, egress, audit destination을 등록하고 shadow MCP server를 막는다: [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/), [NSA MCP security design considerations](https://www.nsa.gov/Portals/75/documents/Cybersecurity/CSI_MCP_SECURITY.pdf). |
| Agent runtime telemetry | agent가 읽은 파일, 실행한 명령, 호출한 tool, 네트워크 접근, 생성한 diff를 감사 가능하게 남긴다: [Running Codex safely](https://openai.com/index/running-codex-safely/). |
| Human review | 모든 agent change는 PR로만. approval은 사람만. |
| CI gate | test, lint, typecheck, CodeQL, dependency review, secret scanning을 required check로 묶는다: [GitHub merge protection](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/set-merge-protection). |
| GitHub MCP secret scan | GitHub remote MCP server의 secret scanning tools로 commit/PR 전 agent 변경을 검사한다. 단 local MCP server config는 지원하지 않고, finding은 현재 agent session에만 표시되는 pre-commit safety check라 GitHub Security tab/alert API의 system-of-record를 대체하지 않는다: [GitHub MCP secret scanning GA](https://github.blog/changelog/2026-05-05-secret-scanning-with-github-mcp-server-is-now-generally-available/), [Scan for secrets with GitHub MCP Server](https://docs.github.com/code-security/how-tos/use-ghas-with-ai-coding-agents/scan-for-secrets-with-github-mcp-server). |
| Production access | prod DB, prod kube context, cloud admin role, deploy approval 권한을 agent에 주지 않는다. |
| Audit log | Enterprise에서는 SIEM/eDiscovery로 agent activity를 보관한다: [GitHub agentic audit events](https://docs.github.com/en/copilot/reference/agentic-audit-log-events), [GitHub audit log streaming](https://docs.github.com/enterprise-cloud%40latest/admin/monitoring-activity-in-your-enterprise/reviewing-audit-logs-for-your-enterprise/streaming-the-audit-log-for-your-enterprise), [Slack audit logs](https://slack.com/help/articles/360000394286-Audit-logs-in-Slack). |
| DLP | Slack DLP, Google Workspace DLP, GitHub secret scanning을 함께 쓰되 미스캔 범위를 문서화한다: [Slack DLP](https://slack.com/help/articles/12914005852819-Slack-data-loss-prevention), [Google Workspace DLP](https://knowledge.workspace.google.com/admin/security/about-dlp). |
| Compliance | vendor별 SOC 2/ISO/GDPR/HIPAA/FedRAMP 범위를 구매 전에 확인: [OpenAI Trust Portal](https://trust.openai.com/), [Google Workspace AI privacy](https://workspace.google.com/security/ai-privacy/). |

MCP와 agentic connector는 특히 조심해야 한다. MCP는 표준화된 연결을 제공하지만, tool poisoning과 indirect prompt injection의 공격면도 함께 만든다. NSA도 MCP를 AI-driven automation의 보안 설계 대상으로 다루며 access control, prompt handling, tool execution, auditability, third-party integration governance를 강조한다: [NSA press release](https://www.nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/Article/4496698/nsa-releases-security-design-considerations-for-ai-driven-automation-leveraging/), [NSA MCP security design considerations](https://www.nsa.gov/Portals/75/documents/Cybersecurity/CSI_MCP_SECURITY.pdf). 관련 보안 자료: [MCP threat modeling paper](https://arxiv.org/html/2603.22489v1), [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/), [Palo Alto Unit 42 on MCP attack vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/).

MCP security baseline:

- OAuth/OIDC discovery와 protected resource metadata를 확인하고, token audience validation을 적용한다: [MCP authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization).
- token passthrough, broad scope, long-lived shared token을 금지한다.
- tool/server allowlist와 version pinning을 둔다.
- local MCP server는 sandbox, filesystem allowlist, network egress 제한을 적용한다.
- tool output은 다음 tool call의 instruction이 아니라 untrusted data로 처리한다.
- shadow MCP server, context oversharing, audit/telemetry 부재를 OWASP MCP Top 10 risk로 관리한다.

보안 rollout checklist:

1. 승인된 agent/MCP/connector inventory를 만든다.
2. 기본값은 read-only, network off, production secret 없음으로 둔다.
3. Slack/Drive/GitHub connector는 channel/folder/repo allowlist로 시작한다.
4. Write, delete, deploy, publish, external send, credential access는 항상 사람 승인으로 묶는다.
5. GitHub branch protection, CODEOWNERS, CodeQL, dependency review, secret scanning, push protection을 agent branch에도 동일 적용한다.
6. GitHub push protection은 MCP server interaction에도 일부 적용되지만 공개 repo 중심 제한이 있으므로 private/internal repo는 추가 scanner와 token rotation이 필요하다: [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection), [Secret scanning scope](https://docs.github.com/en/code-security/reference/secret-security/secret-scanning-scope).
7. ChatGPT apps는 RBAC, action controls, app permissions를 분리해 관리한다. `Never ask` 같은 자동 승인 설정은 high-risk 조직 기본값으로 쓰지 않는다: [OpenAI apps admin controls](https://help.openai.com/en/articles/11509118-admin-controls-security-and-compliance-in-apps-enterprise-edu-and-business), [Apps in ChatGPT](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt).
8. Claude Code managed MCP는 Anthropic이 MCP server 자체를 security-audit했다는 뜻이 아니므로 `allowManagedMcpServersOnly` 같은 강제 allowlist를 검토한다: [Claude managed MCP](https://code.claude.com/docs/en/managed-mcp).
9. Google OAuth scope-level app control, Drive audit logs, Workspace DLP를 켠다: [Google app access control](https://knowledge.workspace.google.com/admin/apps/control-which-third-party-and-internal-apps-access-google-workspace-data), [Drive log events](https://knowledge.workspace.google.com/admin/reports/drive-log-events).
10. 모든 agent run은 task brief, tool calls, approvals, commands, diffs, test result, cost, reviewer decision을 저장한다.

## 최종 추천

2026-06-17 기준으로 가장 최신에 가까운 접근은 **frontier coding model + agent harness/orchestrator + project context files + CI/PR gate + knowledge connector governance** 조합이다. OpenAI는 GPT-5.5 같은 모델 성능과 함께 harness engineering/Symphony를 공개했고, Anthropic은 Claude Code의 context engineering/sandboxing/Agent SDK를 강화하며, GitHub는 Copilot cloud agent/Agentic Workflows/audit log로 repository-native automation을 밀고 있다. 따라서 "어떤 앱이 최고인가"보다 "우리 팀의 GitHub, Slack, Drive, Obsidian/Notion, CI, 보안 정책에 어떤 agent loop를 안전하게 붙일 것인가"가 더 정확한 의사결정 기준이다.

### 개인/학생/소규모 실험

권장 스택:

- GitHub repo + GitHub Actions 최소 CI.
- Codex CLI 또는 Claude Code 또는 Aider.
- Obsidian local vault로 실험/결정/프롬프트 기록.
- Google Docs로 제출/보고서 산출물 작성.

실험 순서:

1. `AGENTS.md`, `docs/index.md`, `llms.txt`를 만든다.
2. test/lint 명령을 하나로 정리한다.
3. agent에게 문서화, 테스트 추가, 작은 bug fix부터 맡긴다.
4. 모든 변경은 diff review 후 merge한다.

### 소규모 팀

권장 스택:

- GitHub Team, Projects, Issues, PR template, CODEOWNERS.
- Slack Pro: `#project`, `#code-review`, `#agent-run-log`.
- Google shared drive: 공식 문서/회의록/발표자료.
- Notion 또는 Obsidian: wiki/실험 로그.
- Codex/Claude/Copilot agent는 issue -> branch -> PR 흐름으로만 사용.

실험 순서:

1. Slack 요청을 GitHub issue로 만든다.
2. agent에게 issue 단위 task brief를 준다.
3. CI와 reviewer가 통과해야 merge한다.
4. 결정은 `docs/decisions/` 또는 Drive/Notion에 남긴다.

### 제품 개발팀

권장 스택:

- GitHub Enterprise/Team + branch rulesets + required checks.
- Copilot cloud agent 또는 Codex Cloud로 low/medium risk issue 자동화.
- Claude Code/Codex CLI로 local deep work.
- Slack event bus, Drive approvals, Notion product/spec DB.
- DORA, PR cycle time, review latency, flaky test rate 측정.

핵심 정책:

- agent PR은 작은 단위로 제한.
- code owner review 필수.
- security/infra/auth/billing/data migration은 senior review 필수.
- production deploy는 environment approval로 분리.

### 엔터프라이즈

권장 스택:

- GitHub Enterprise Cloud/Server, SAML/SCIM, audit log streaming, Advanced Security.
- Slack Enterprise Grid, app approval, audit logs, DLP.
- Google Workspace DLP, target audiences, shared drive policy.
- Enterprise AI 계정만 허용. 개인 Pro/Plus 계정으로 회사 repo 처리 금지.
- MCP/connector allowlist, OAuth scope review, SIEM 연동.

도입 순서:

1. legal/privacy/security signoff.
2. 소수 pilot, read-only/plan mode.
3. 비민감 repo에서 PR-only.
4. connector/MCP allowlist.
5. audit log/SIEM.
6. 민감 repo 별도 정책.

### 보안 민감 조직

권장 스택:

- local/sandbox agent 우선.
- self-hosted runner, private package mirror, restricted network.
- cloud agent는 비민감 repo부터.
- raw PII/secret/log 원문은 AI context에서 제외.
- DLP, secret scanning, license scanning, human approval.

금지 기본값:

- agent에게 production write 권한 부여 금지.
- agent에게 long-lived cloud admin token 부여 금지.
- 자동 merge 금지.
- destructive command 자동 승인 금지.
- public/shareable app builder에 민감 데이터 입력 금지.

## ChatGPT Pro Web Search / Deep Research 검증

ChatGPT Pro Web Search는 다음 9개 chunk로 나눠 실행했고, 각 chunk가 완료된 뒤 다음 chunk로 넘어갔다.

| Chunk | 결과 |
|---|---|
| 용어/전문가 | vibe coding 의미 오용, agentic engineering/context engineering 확산, Addy/Simon/Kent/Martin Fowler 관점 확인 |
| OpenAI/Codex | `gpt-5.5` 명칭 정정, Codex product suite, App Server/SDK, Plugins/Skills, Sites, Security 확인 |
| Claude Code | Auto memory, nested skills/subagents, MCP Tool Search, managed MCP, auto mode 위험 확인 |
| IDE/GitHub | Cursor 3, Devin Desktop, VS Code `.agent.md`, Copilot cloud agent/Agentic Workflows/Slack/API/audit 확인 |
| OSS agents | archived/read-only/license/self-host 가능성 확인, Claude Code/Crush/Continue/Roo/opencode-ai 표기 정정 |
| Benchmarks | SWE-bench Verified 한계, SWE-bench Pro/Terminal-Bench/FeatureBench/SWE-EVO/SWE-Explore 보강 |
| 지식관리 | Obsidian canonical memory, Slack real-time retrieval, Google governed artifacts 구조 확인 |
| 보안 | NSA MCP, OWASP MCP Top 10, Codex/Claude/GitHub/Slack/Google governance 확인 |
| 커뮤니티 | 리뷰 병목, 비용/loop, Full Access, Cline 공급망 사고, X/Threads 접근 제한 확인 |

Deep Research는 처음에 plan/source confirmation 성격의 확인 필요 신호가 나와 중단됐다. 이후 사용자가 승인했다는 조건을 명시해 공개 웹 기반 독립 교차검증을 다시 실행했고, 마지막으로 누락/최신 근거 확인용 focused Deep Research를 한 번 더 실행했다. 다음 충돌과 보강점을 본문에 반영했다.

| 충돌/보강 | 반영 |
|---|---|
| SWE-bench Verified는 최신 frontier coding agent 평가 단일 기준으로 부적합 | SWE-bench Pro/Terminal-Bench/내부 eval 병렬 판단으로 수정 |
| 생산성 효과는 보편적이지 않음 | DORA/Stack Overflow/METR를 추가해 "도입은 강하지만 생산성은 조건부"로 정리 |
| MCP는 표준이라 안전하다는 표현은 틀림 | NSA/OWASP/MCP official 기반 governance checklist 추가 |
| Slack/Drive/Obsidian 광범위 연결은 위험 | context gateway, allowlist, read-only, permission-aware retrieval 구조 추가 |
| Context engineering은 긴 context가 아니라 finite context 관리 | context cost 표와 pinned/search/memory 분리 추가 |
| GitHub MCP secret scanning은 alert system 대체가 아님 | remote MCP 전용, session-local pre-commit safety check로 정리 |
| Google Cloud MCP와 Workspace/Drive MCP는 다름 | Cloud managed remote MCP, Workspace MCP, open-source/local MCP를 분리 |

실행 한계도 있었다. 9개 Web Search와 2회 Deep Research 교차검증은 완료됐지만, 중간중간 ChatGPT가 "요청이 너무 많습니다" rate limit 상태가 되어 간격을 두고 진행했다. 따라서 이 문서는 완료된 Pro Search/Deep Research 결과와 직접 검증한 공식/원출처를 종합한 스냅샷이다.

## 한계

- ChatGPT Pro Web Search 9개 chunk와 Deep Research 2회 결과는 본문에 병합했다. 다만 중간중간 rate limit이 발생해 추가 반복은 간격을 두고 제한적으로 진행했다.
- X/Twitter와 Threads는 로그인/동적 UI 제한 때문에 전문 확인이 제한됐다.
- GitHub stars/forks/pushed 수치는 기준일 스냅샷이며 계속 변한다.
- 가격, 모델 한도, enterprise 기능, compliance 인증 범위는 빠르게 바뀐다.
- 커뮤니티 후기는 자가 보고이며 통계가 아니다.
- benchmark 점수는 오염, test quality, task distribution, harness 차이에 민감하다.
- "최고 도구"는 조직의 codebase, 테스트 품질, 보안 요구, budget, 리뷰 문화에 따라 달라진다.

## 짧은 선택 가이드

- 이미 GitHub 중심 팀이면: GitHub Copilot cloud agent + CODEOWNERS + Actions + Slack/Drive.
- 터미널 중심 개발자면: Codex CLI 또는 Claude Code.
- IDE 중심이면: Cursor, VS Code Agent Mode, Devin Desktop 중 조직 정책에 맞는 것.
- 오픈소스/self-host가 중요하면: Cline, Aider, OpenHands, mini-SWE-agent, OpenCode/Goose/Qwen Code를 비교.
- MVP/데모 앱이면: v0, Replit Agent, Bolt, Lovable. 단, production 전 engineer review 필수.
- 보안 민감 조직이면: local/sandbox agent, read-only connector, PR-only, no prod write, SIEM/audit log.

가장 실용적인 결론은 다음이다. AI 개발 자동화의 최신형은 "AI가 코드를 많이 쓰는 것"이 아니라 **좋은 task brief, 좋은 project context, 강한 test/CI, 작은 PR, 사람 리뷰, 제한된 권한, 감사 가능한 운영**을 갖춘 팀 프로세스다.
