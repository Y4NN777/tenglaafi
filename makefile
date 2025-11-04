# Makefile pour TengLaafi RAG
# Version stable, sans emojis, avec cibles cohérentes et messages clairs.

SHELL := /bin/bash
.ONESHELL:

# ===== Phony targets =====
.PHONY: help install conda-env conda-install conda-info install-dev setup verify-setup \
        collect validate-corpus stats-corpus \
        index reindex check-index \
        test test-unit test-integration test-fast test-coverage test-parallel \
        evaluate evaluate-verbose benchmark \
        run dev debug shell \
        format lint check \
        clean clean-data clean-index clean-all clean-cache \
        docker-build docker-run docker-stop docker-logs docker-shell \
        full-setup ci pre-commit pre-push demo \
        logs health stats query-test profile \
        readme license version info env-check watch quick-start

# ===== Couleurs (désactivables avec NO_COLOR=1) =====
YELLOW    := \033[1;33m
GREEN     := \033[1;32m
RED       := \033[1;31m
NC        := \033[0m

# Wrapper pour imprimer des lignes colorées de façon portable
ECHO = printf '%b\n'

ifeq ($(NO_COLOR),1)
  GREEN :=
  YELLOW :=
  RED :=
  NC :=
endif

# ===== Variables =====
PYTHON      ?= python
PIP         ?= pip
PYTEST      ?= pytest
SRC_DIR     ?= src
DATA_DIR    ?= data
CHROMA_DIR  ?= chroma_db
EVAL_DIR    ?= evaluation

# Détection open (macOS) vs xdg-open (Linux)
OPEN_CMD := xdg-open
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
  OPEN_CMD := open
endif

.DEFAULT_GOAL := help

##@ Aide

help: ## Affiche cette aide
	@awk 'BEGIN {FS = ":.*##"; \
	  printf "Usage: make $(YELLOW)<target>$(NC)\n\n"} \
	  /^[a-zA-Z0-9_%-]+:.*##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } \
	  /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Installation & Setup

install: ## Installe les dépendances
	@$(ECHO) "$(GREEN)Installation des dépendances...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@$(ECHO) "$(GREEN)Installation terminée.$(NC)"

.PHONY: conda-env conda-install conda-info conda-activate-install conda-activate

conda-env: ## Crée (si besoin) l'environnement conda 'tenglaafi'
	@$(ECHO) "$(GREEN)Configuration de l'environnement conda...$(NC)"
	@if command -v conda >/dev/null 2>&1; then \
		if ! conda env list | awk '{print $$1}' | grep -qx "tenglaafi"; then \
			$(ECHO) "$(YELLOW)Création de l'env conda 'tenglaafi' (python=3.12)...$(NC)"; \
			conda create -n tenglaafi python=3.12 -y; \
		else \
			$(ECHO) "$(YELLOW)L'environnement 'tenglaafi' existe déjà.$(NC)"; \
		fi; \
		$(ECHO) "$(YELLOW)Pour activer:  conda activate tenglaafi$(NC)"; \
		$(ECHO) "$(YELLOW)Puis installer deps: make conda-install$(NC)"; \
	else \
		$(ECHO) "$(RED)Conda n'est pas installé.$(NC)"; \
		$(ECHO) "$(YELLOW)Installe Miniconda ou utilise un venv pip:$(NC)"; \
		$(ECHO) "  python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"; \
		exit 1; \
	fi

conda-install: ## Installe requirements dans l'env conda sans l'activer dans le shell courant
	@if command -v conda >/dev/null 2>&1; then \
		conda run -n tenglaafi $(PIP) install -r requirements.txt; \
	else \
		$(ECHO) "$(RED)Conda introuvable. Utilise plutôt: make install$(NC)"; \
		exit 1; \
	fi

conda-activate: ## Active l'env conda 'tenglaafi' dans le shell courant
	@$(ECHO) "$(GREEN)Activation de l'env conda 'tenglaafi'...$(NC)"
	@if command -v conda >/dev/null 2>&1; then \
		eval "$$(conda shell.bash hook)"; \
		conda activate tenglaafi; \
		$(ECHO) "$(YELLOW)Environnement 'tenglaafi' activé.$(NC)"; \
	else \
		$(ECHO) "$(RED)Conda introuvable.$(NC)"; \
		exit 1; \
	fi

conda-activate-install: ## Active l'env conda et installe les dépendances (pour shell interactif)
	@$(ECHO) "$(GREEN)Activation de l'env conda et installation des dépendances...$(NC)"
	@if command -v conda >/dev/null 2>&1; then \
		eval "$$(conda shell.bash hook)"; \
		conda activate tenglaafi; \
		$(ECHO) "$(YELLOW)Environnement 'tenglaafi' activé.$(NC)"; \
		$(ECHO) "$(YELLOW)Installation des dépendances...$(NC)"; \
		$(PIP) install -r requirements.txt; \
		$(ECHO) "$(GREEN)Installation terminée. Vous êtes dans l'env 'tenglaafi'.$(NC)"; \
	else \
		$(ECHO) "$(RED)Conda introuvable.$(NC)"; \
		exit 1; \
	fi

conda-info: ## Affiche info de l'environnement conda
	@if command -v conda >/dev/null 2>&1; then \
		conda env list; \
		conda run -n tenglaafi python --version || true; \
	else \
		$(ECHO) "$(RED)Conda introuvable.$(NC)"; \
	fi


install-dev: install ## Installe dépendances + outils dev
	@$(ECHO) "$(GREEN)Installation des outils de développement...$(NC)"
	$(PIP) install black flake8 pytest-cov pytest-xdist ipython
	@$(ECHO) "$(GREEN)Outils dev installés.$(NC)"

setup: ## Configuration initiale du projet (arborescence et fichiers)
	@$(ECHO) "$(GREEN)Configuration initiale...$(NC)"
	mkdir -p $(DATA_DIR)/raw
	mkdir -p research/notebooks research/scripts research/experiments
	mkdir -p $(SRC_DIR)/core $(SRC_DIR)/data_collection $(SRC_DIR)/rag_pipeline $(SRC_DIR)/server
	mkdir -p $(EVAL_DIR)/tests/unit $(EVAL_DIR)/tests/integration $(EVAL_DIR)/tests/performance
	mkdir -p frontend
	mkdir -p $(CHROMA_DIR)
	mkdir -p logs
	touch $(SRC_DIR)/__init__.py
	touch $(SRC_DIR)/core/__init__.py
	touch $(SRC_DIR)/data_collection/__init__.py
	touch $(SRC_DIR)/rag_pipeline/__init__.py
	touch $(SRC_DIR)/server/__init__.py
	touch $(EVAL_DIR)/tests/unit/__init__.py
	touch $(EVAL_DIR)/tests/integration/__init__.py
	touch $(EVAL_DIR)/tests/performance/__init__.py
	if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; echo "$(YELLOW).env créé, pensez à le configurer.$(NC)"; fi
	@$(ECHO) "$(GREEN)Structure complète créée.$(NC)"

verify-setup: ## Vérifie que le setup est correct
	$(ECHO) "$(GREEN)Vérification du setup...$(NC)"
	test -f .env || (echo "$(RED).env manquant$(NC)"; exit 1)
	test -d $(DATA_DIR) || (echo "$(RED)$(DATA_DIR)/ manquant$(NC)"; exit 1)
	@if ! grep -q "^HF_TOKEN" .env 2>/dev/null; then echo "$(YELLOW)Avertissement: HF_TOKEN non configuré dans .env$(NC)"; fi
	$(ECHO) "$(GREEN)Setup vérifié.$(NC)"

##@ Collecte de Données

collect: ## Collecte les données (≥500 docs) via vos scripts
	@$(ECHO) "$(GREEN)Collecte des données...$(NC)"
	$(PYTHON) $(SRC_DIR)/data_collection/tropical_medical_data_collector.py
	@$(ECHO) "$(GREEN)Collecte terminée.$(NC)"

validate-corpus: ## Valide le corpus (>= 500 docs)
	@$(ECHO) "$(GREEN)Validation du corpus...$(NC)"
	@$(PYTHON) - <<'PY'
	import json, sys
	p = '$(DATA_DIR)/corpus.json'
	try:
		with open(p, 'r', encoding='utf-8') as f:
			corpus = json.load(f)
	except Exception as e:
		print("Erreur: impossible de lire", p, ":", e)
		sys.exit(1)
	n = len(corpus)
	print(f"{n} documents dans le corpus")
	assert n >= 500, f"Insuffisant: {n}/500 documents"
	print("Corpus valide")
	PY

stats-corpus: ## Affiche des statistiques simples sur le corpus
	@$(ECHO) "$(GREEN)Statistiques du corpus:$(NC)"
	@$(PYTHON) - <<'PY'
	import json, collections
	with open('$(DATA_DIR)/corpus.json','r',encoding='utf-8') as f:
		corpus = json.load(f)
	sources = collections.Counter(d.get('source','Unknown') for d in corpus)
	print("Total:", len(corpus), "documents")
	for src, c in sorted(sources.items()):
		print(f"  {src}: {c}")
	PY

##@ Indexation

index: validate-corpus ## Indexe le corpus dans ChromaDB
	@$(ECHO) "$(GREEN)Indexation du corpus...$(NC)"
	$(PYTHON) store_index.py
	@$(ECHO) "$(GREEN)Indexation terminée.$(NC)"

reindex: ## Réindexation complète (supprime l'index actuel)
	@$(ECHO) "$(YELLOW)Réindexation complète (suppression de l'index actuel).$(NC)"
	read -p "Continuer ? [y/N] " confirm; [ "$$confirm" = "y" ] || exit 1
	rm -rf $(CHROMA_DIR)/*
	$(MAKE) index

check-index: ## Vérifie l'état de l'index ChromaDB
	@$(ECHO) "$(GREEN)Vérification de l'index...$(NC)"
		@$(PYTHON) - <<'PY'
	from $(SRC_DIR).rag_pipeline.vector_store import ChromaVectorStore
	store = ChromaVectorStore()
	count = store.count_documents()
	print(f"{count} documents indexés")
	assert count > 0, "Index vide"
	print("Index opérationnel")
	PY

##@ Tests

test: ## Exécute tous les tests
	@$(ECHO) "$(GREEN)Exécution des tests...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/ -v --tb=short


individual-unit-test: ## Exécute un test individuel (usage: make individual-test TEST=path/to/test_file.py)
	@if [ -z "$(TEST)" ]; then \
		$(ECHO) "$(RED)Erreur: variable TEST non définie. Usage: make individual-test TEST=path/to/test_file.py$(NC)"; \
		exit 1; \
	fi
	@$(ECHO) "$(GREEN)Exécution du test individuel: $(TEST)$(NC)"
	$(PYTEST) $(TEST) -v --tb=short

test-unit: ## Tests unitaires uniquement
	@$(ECHO) "$(GREEN)Tests unitaires...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/unit/ -v

test-integration: ## Tests d'intégration uniquement
	@$(ECHO) "$(GREEN)Tests d'intégration...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/integration/ -v -m integration

test-fast: ## Tests rapides (sans les lents)
	@$(ECHO) "$(GREEN)Tests rapides...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/ -v -m "not slow"

test-coverage: ## Tests avec coverage
	@$(ECHO) "$(GREEN)Coverage...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@$(ECHO) "$(GREEN)Report HTML: htmlcov/index.html$(NC)"

test-parallel: ## Tests en parallèle (plus rapide)
	@$(ECHO) "$(GREEN)Tests parallèles...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/ -v -n auto

##@ Évaluation

evaluate: ## Évalue le système RAG
	@$(ECHO) "$(GREEN)Évaluation du système...$(NC)"
	$(PYTHON) $(EVAL_DIR)/evaluate.py

evaluate-verbose: ## Évaluation avec détails
	@$(ECHO) "$(GREEN)Évaluation détaillée...$(NC)"
	$(PYTHON) $(EVAL_DIR)/evaluate.py --verbose

benchmark: ## Benchmark de performance (tests perf)
	@$(ECHO) "$(GREEN)Benchmark...$(NC)"
	$(PYTEST) $(EVAL_DIR)/tests/performance/ -v
	@$(ECHO) "$(GREEN)Benchmark terminé.$(NC)"

##@ Développement & Debug

run: verify-setup check-index ## Lance le serveur API
	@$(ECHO) "$(GREEN)Démarrage du serveur...$(NC)"
	$(PYTHON) $(SRC_DIR)/server/main.py

dev: ## Mode développement (auto-reload via uvicorn)
	@$(ECHO) "$(GREEN)Mode développement (auto-reload)...$(NC)"
	uvicorn $(SRC_DIR).server.main:app --reload --host 0.0.0.0 --port 8000

debug: ## Démarre avec logs de debug
	@$(ECHO) "$(GREEN)Mode debug...$(NC)"
	LOG_LEVEL=DEBUG $(PYTHON) $(SRC_DIR)/server/main.py

shell: ## Shell Python avec imports utilitaires
	@$(ECHO) "$(GREEN)Shell Python interactif...$(NC)"
	$(PYTHON) - <<'PY'
	import sys; sys.path.insert(0, '$(SRC_DIR)')
	from rag_pipeline.rag import get_rag_pipeline
	from rag_pipeline.embeddings import get_embedding_manager
	from rag_pipeline.vector_store import ChromaVectorStore
	print('Imports chargés: rag_pipeline, embeddings, ChromaVectorStore')
	import code; code.interact(local=locals())
	PY

##@ Qualité du Code

format: ## Formate le code avec black
	@$(ECHO) "$(GREEN)Formatage...$(NC)"
	black $(SRC_DIR)/ $(EVAL_DIR)/ --line-length 100
	@$(ECHO) "$(GREEN)Code formaté.$(NC)"

lint: ## Vérifie le style avec flake8
	@$(ECHO) "$(GREEN)Lint...$(NC)"
	flake8 $(SRC_DIR)/ --max-line-length=100 --exclude=__pycache__
	@$(ECHO) "$(GREEN)Lint OK.$(NC)"

check: format lint test-fast ## Format + lint + tests rapides
	@$(ECHO) "$(GREEN)Vérifications complètes OK.$(NC)"

##@ Nettoyage

clean: ## Nettoie fichiers temporaires
	@$(ECHO) "$(YELLOW)Nettoyage...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/
	@$(ECHO) "$(GREEN)Nettoyage terminé.$(NC)"

clean-data: ## Nettoie les données collectées (ATTENTION)
	@$(ECHO) "$(RED)ATTENTION: suppression de $(DATA_DIR)/corpus.json et sources.$(NC)"
	read -p "Êtes-vous sûr ? [y/N] " confirm; [ "$$confirm" = "y" ] || exit 1
	rm -f $(DATA_DIR)/corpus.json $(DATA_DIR)/sources.txt
	@$(ECHO) "$(GREEN)Données nettoyées.$(NC)"

clean-index: ## Nettoie l'index ChromaDB (ATTENTION)
	@$(ECHO) "$(RED)ATTENTION: suppression de l'index ChromaDB.$(NC)"
	read -p "Êtes-vous sûr ? [y/N] " confirm; [ "$$confirm" = "y" ] || exit 1
	rm -rf $(CHROMA_DIR)/*
	@$(ECHO) "$(GREEN)Index nettoyé.$(NC)"

clean-all: clean clean-data clean-index ## Nettoie TOUT (DANGER)
	@$(ECHO) "$(RED)ATTENTION: nettoyage complet (corpus + index).$(NC)"
	read -p "Confirmer ? [y/N] " confirm; [ "$$confirm" = "y" ] || exit 1
	rm -rf logs/*
	@$(ECHO) "$(GREEN)Nettoyage complet terminé.$(NC)"

clean-cache: ## Vide un éventuel cache de pipeline
	@$(ECHO) "$(YELLOW)Nettoyage du cache...$(NC)"
	@$(PYTHON) - <<'PY'
	try:
		from $(SRC_DIR).rag_pipeline.rag import get_rag_pipeline
		rag = get_rag_pipeline()
		rag.clear_cache()
		print("Cache vidé")
	except Exception as e:
		print("Avertissement:", e)
	PY

##@ Docker

docker-build: ## Build l'image Docker
	@$(ECHO) "$(GREEN)Build de l'image Docker...$(NC)"
	docker build -t tenglaafi-rag:latest .
	@$(ECHO) "$(GREEN)Image construite.$(NC)"

docker-run: ## Lance le container Docker
	@$(ECHO) "$(GREEN)Lancement du container...$(NC)"
	docker run -d \
	  --name tenglaafi-rag \
	  -p 8000:8000 \
	  --env-file .env \
	  -v $(PWD)/$(CHROMA_DIR):/app/$(CHROMA_DIR) \
	  tenglaafi-rag:latest
	@$(ECHO) "$(GREEN)Container lancé sur http://localhost:8000$(NC)"

docker-stop: ## Arrête le container
	@$(ECHO) "$(YELLOW)Arrêt du container...$(NC)"
	docker stop tenglaafi-rag || true
	docker rm tenglaafi-rag || true
	@$(ECHO) "$(GREEN)Container arrêté.$(NC)"

docker-logs: ## Affiche les logs du container
	docker logs -f tenglaafi-rag

docker-shell: ## Shell interactif dans le container
	docker exec -it tenglaafi-rag /bin/bash

##@ Workflow Complet

full-setup: conda-env conda-install setup collect index ## Setup complet (conda-env → conda-install → setup → collect)
	@$(ECHO) "$(GREEN)Setup complet terminé.$(NC)"
	@$(ECHO) "$(YELLOW)Prochaine étape: make run$(NC)"

ci: install test lint ## Pipeline CI (tests + qualité)
	@$(ECHO) "$(GREEN)CI pipeline OK.$(NC)"

pre-commit: format lint test-fast ## Vérifications avant commit
	@$(ECHO) "$(GREEN)Prêt pour commit.$(NC)"

pre-push: check test ## Vérifications avant push
	@$(ECHO) "$(GREEN)Prêt pour push.$(NC)"

demo: run ## Lance le serveur et ouvre le navigateur
	@$(ECHO) "$(GREEN)Lancement de la démo...$(NC)"
	$(OPEN_CMD) http://localhost:8000/static/index.html >/dev/null 2>&1 || true

##@ Monitoring & Debug

logs: ## Affiche les logs récents
	@$(ECHO) "$(GREEN)Logs récents:$(NC)"
	@test -d logs && tail -n 50 logs/app.log || $(ECHO) "$(YELLOW)Aucun log trouvé.$(NC)"

health: ## Vérifie la santé du système (endpoint /health)
	@$(ECHO) "$(GREEN)Vérification santé...$(NC)"
	curl -fsS http://localhost:8000/health | $(PYTHON) -m json.tool || $(ECHO) "$(RED)API non accessible.$(NC)"

stats: ## Affiche les statistiques (endpoint /stats)
	@$(ECHO) "$(GREEN)Statistiques du système:$(NC)"
	curl -fsS http://localhost:8000/stats | $(PYTHON) -m json.tool || $(ECHO) "$(RED)API non accessible.$(NC)"

query-test: ## Test simple de requête /query
	@$(ECHO) "$(GREEN)Test de requête...$(NC)"
	curl -s -X POST http://localhost:8000/query \
	  -H "Content-Type: application/json" \
	  -d '{"question":"Quels sont les symptômes du paludisme?","include_sources":true}' \
	| $(PYTHON) -m json.tool

profile: ## Profiling des performances du code
	@$(ECHO) "$(GREEN)Profiling...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats $(SRC_DIR)/server/main.py
	@$(ECHO) "$(GREEN)Analyse du profiling:$(NC)"
	$(PYTHON) - <<'PY'
	import pstats
	p = pstats.Stats('profile.stats')
	p.sort_stats('cumulative').print_stats(20)
	PY

readme: ## Affiche le README
	@cat README.md

license: ## Affiche la licence
	@cat LICENSE

##@ Informations

version: ## Affiche la version et paquets clés
	@$(ECHO) "$(GREEN)TengLaafi RAG v1.0.0$(NC)"
	@$(PYTHON) --version
	@$(ECHO) "Packages:"
	@$(PIP) list | grep -E "fastapi|chromadb|sentence-transformers|langchain" || true

info: ## Informations système
	@$(ECHO) "$(GREEN)==========================================$(NC)"
	@$(ECHO) "$(GREEN)  Informations Système$(NC)"
	@$(ECHO) "$(GREEN)==========================================$(NC)"
	@$(ECHO) "Python: $$($(PYTHON) --version)"
	@$(ECHO) "Pip: $$($(PIP) --version | cut -d' ' -f1-2)"
	@$(ECHO) "Corpus: $$([ -f $(DATA_DIR)/corpus.json ] && echo 'Présent' || echo 'Absent')"
	@$(ECHO) "Index ChromaDB: $$([ -d $(CHROMA_DIR) ] && echo 'Présent' || echo 'Absent')"
	@$(ECHO) ".env: $$([ -f .env ] && echo 'Configuré' || echo 'Manquant')"
	@$(ECHO) "$(GREEN)==========================================$(NC)"

env-check: ## Vérifie les variables d'environnement
	@$(ECHO) "$(GREEN)Vérification des variables d'environnement:$(NC)"
	test -f .env || (echo "$(RED).env manquant$(NC)"; exit 1)
	@grep -q "^HF_TOKEN" .env && echo "HF_TOKEN configuré" || echo "$(YELLOW)HF_TOKEN manquant$(NC)"
	@grep -q "^LLM_MODEL" .env && echo "LLM_MODEL configuré" || echo "$(YELLOW)LLM_MODEL manquant$(NC)"

##@ Helpers

watch: ## Relance les tests à chaque modification (nécessite inotifywait)
	@$(ECHO) "$(GREEN)Watch mode (Ctrl+C pour arrêter)...$(NC)"
	@while true; do \
	  $(PYTEST) $(EVAL_DIR)/tests/ -v --tb=short -x; \
	  inotifywait -r -e modify $(SRC_DIR) $(EVAL_DIR); \
	done

quick-start: ## Guide de démarrage rapide (résumé)
	@$(ECHO) "$(GREEN)=== Démarrage rapide ===$(NC)"
	@$(ECHO) "1) make install"
	@$(ECHO) "2) make setup  # puis configurez .env"
	@$(ECHO) "3) make collect"
	@$(ECHO) "4) make index"
	@$(ECHO) "5) make run"
