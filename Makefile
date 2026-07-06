# sebastianruss.com — fully static site. No build step; the only "tooling" is a
# local web server so relative asset paths behave like they do in production.
PORT ?= 8000

.DEFAULT_GOAL := help

.PHONY: help start serve open previews

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

start: ## Serve the site at http://localhost:$(PORT) (Ctrl+C to stop)
	@echo "Serving sebastianruss.com on http://localhost:$(PORT)  —  Ctrl+C to stop"
	@python3 -m http.server $(PORT)

serve: start ## Alias for `start`

open: ## Open the running site in the default browser
	@open "http://localhost:$(PORT)"

previews: ## Generate 1x1 dominant-colour LQIP placeholders (assets/img/**/<name>_preview.gif)
	@python3 tools/generate-previews.py
