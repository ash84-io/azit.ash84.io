# azit.ash84.io — static photo gallery
# Usage: make help

PORT ?= 8000
THUMB_MAX ?= 1200
FULL_MAX ?= 2400
QUALITY ?= 80
ORIGINALS_DIR ?= originals
SITE_DIR ?= site

UV ?= uv
NPX ?= npx --yes
PY := $(UV) run --quiet python

.DEFAULT_GOAL := help
.PHONY: help format lint test build images manifest verify server clean clean-images

help: ## 사용 가능한 명령어
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

format: ## 포맷팅 (prettier: html/css/js, ruff format: python)
	$(NPX) prettier@3 --log-level warn --write "$(SITE_DIR)/**/*.{html,css,js}" "tests/js/**/*.mjs" "*.js" ".github/**/*.yml"
	$(UV) run --quiet ruff format tools

lint: format ## 정적 분석 (eslint, ruff check, html-validate)
	$(NPX) eslint@9 "$(SITE_DIR)/js/**/*.js" "tests/js/**/*.mjs"
	$(UV) run --quiet ruff check tools
	$(NPX) html-validate@9 "$(SITE_DIR)/index.html"

test: ## 테스트 (pytest, node --test)
	$(UV) run --quiet pytest -q
	node --test 'tests/js/**/*.test.mjs'

images: ## originals/ → site/images/{thumb,full}/*.webp
	$(PY) -m tools.build_images --source $(ORIGINALS_DIR) --site $(SITE_DIR) \
		--thumb-max $(THUMB_MAX) --full-max $(FULL_MAX) --quality $(QUALITY)

manifest: images ## site/images/manifest.json 생성
	$(PY) -m tools.build_manifest --site $(SITE_DIR)

verify: ## manifest와 이미지 파일의 정합성 검사
	$(PY) -m tools.verify_site --site $(SITE_DIR)

build: manifest verify ## 이미지 변환 + manifest 생성 + 검증

server: ## 로컬 서버 (http://localhost:$(PORT))
	python3 -m http.server $(PORT) --directory $(SITE_DIR)

clean: ## 캐시 정리
	rm -rf .pytest_cache .ruff_cache tools/__pycache__ tools/tests/__pycache__

clean-images: ## 생성된 WebP와 manifest 삭제 (originals/ 에서 다시 만들 수 있을 때만)
	rm -rf $(SITE_DIR)/images/thumb $(SITE_DIR)/images/full $(SITE_DIR)/images/manifest.json
