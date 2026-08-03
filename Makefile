SHELL     := /bin/bash
RUNTIME   ?= docker
MODEL     ?=
PROMPT    ?= explain this project
WORKSPACE ?= $(CURDIR)
ENV_FILE  ?=
FAST      ?= true
RUNS      ?= 1

# LLM gateway. Leave these empty and run.sh reads ./.env (see .env.example);
# setting them here or on the command line overrides the file.
export LLM_GW_BASE_URL ?=
export LLM_GW_API_KEY  ?=

# --- Available models ---
# Claude:     claude-sonnet-4.6, claude-sonnet-4.5, claude-opus-4.6,
#             claude-opus-4.5, claude-haiku-4.5
# Gemini:     vertex_ai/gemini-3-pro, vertex_ai/gemini-3-flash,
#             vertex_ai/gemini-2.5-pro, vertex_ai/gemini-2.5-flash,
#             vertex_ai/gemini-2.0-flash
# Azure/GPT:  azure/gpt-4.1, azure/gpt-4.1-mini, azure/gpt-5.1,
#             azure/gpt-5, azure/gpt-5-mini, azure/gpt-5-nano,
#             azure/gpt-4o, azure/gpt-4o-mini

# --- Derived flags for run.sh ---
RUN_FLAGS := --runtime $(RUNTIME)

ifneq ($(MODEL),)
  RUN_FLAGS += --model $(MODEL)
endif
ifneq ($(ENV_FILE),)
  RUN_FLAGS += --env-file $(ENV_FILE)
endif
ifeq ($(FAST),false)
  RUN_FLAGS += --no-fast
endif

RUN_FLAGS += --workspace $(WORKSPACE)

.PHONY: help claude codex experiment experiment-dry pull models test paper paper-clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables:"
	@echo "  LLM_GW_BASE_URL  API gateway base URL   (default: from ./.env)"
	@echo "  LLM_GW_API_KEY   API gateway key        (default: from ./.env)"
	@echo "  MODEL             Model name (see: make models)"
	@echo "  PROMPT            Prompt text (default: explain this project)"
	@echo "  WORKSPACE         Mount directory (default: current dir)"
	@echo "  RUNTIME           docker or podman (default: docker)"
	@echo "  FAST              true/false (default: true)"
	@echo "  RUNS              Runs per combination for experiment (default: 1)"
	@echo ""
	@echo "Examples:"
	@echo '  make claude MODEL=claude-sonnet-4.6 PROMPT="list files"'
	@echo '  make experiment RUNS=3'
	@echo '  make experiment-dry RUNS=5'

claude: ## Run Claude sandbox
	./run.sh --backend claude $(RUN_FLAGS) -p "$(PROMPT)"

codex: ## Run Codex sandbox
	./run.sh --backend codex $(RUN_FLAGS) -p "$(PROMPT)"

experiment: ## Run all backend × model combinations
	./experiment.sh --runs $(RUNS) --runtime $(RUNTIME)

experiment-dry: ## Dry-run: show what experiment would execute
	./experiment.sh --runs $(RUNS) --runtime $(RUNTIME) --dry-run

models: ## List available models
	@echo "Claude (use with: make claude)"
	@echo "  claude-sonnet-4.6"
	@echo "  claude-sonnet-4.5"
	@echo "  claude-opus-4.6"
	@echo "  claude-opus-4.5"
	@echo "  claude-haiku-4.5"
	@echo ""
	@echo "Gemini (use with: make codex)"
	@echo "  vertex_ai/gemini-3-pro"
	@echo "  vertex_ai/gemini-3-flash"
	@echo "  vertex_ai/gemini-2.5-pro"
	@echo "  vertex_ai/gemini-2.5-flash"
	@echo "  vertex_ai/gemini-2.0-flash"
	@echo ""
	@echo "Azure/GPT (use with: make codex)"
	@echo "  azure/gpt-4.1"
	@echo "  azure/gpt-4.1-mini"
	@echo "  azure/gpt-5.1"
	@echo "  azure/gpt-5"
	@echo "  azure/gpt-5-mini"
	@echo "  azure/gpt-5-nano"
	@echo "  azure/gpt-4o"
	@echo "  azure/gpt-4o-mini"

test: ## Run run.sh config/dotenv regression tests (no image or network needed)
	./test-run-config.sh

IMAGE_TAG ?= v0.0.14

pull: ## Pull the sandbox harness image (both backends run in it)
	$(RUNTIME) pull ghcr.io/latere-ai/sandbox-harness:$(IMAGE_TAG)

paper: ## Build papers/paper.pdf (forces rebuild)
	$(MAKE) -B -C papers

paper-clean: ## Remove LaTeX build intermediates
	$(MAKE) -C papers clean
