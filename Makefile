# 🌍 WRLD Relief Crisis Monitor - Makefile

.PHONY: help install dev build test clean docker-build docker-run docker-stop lint format check-deps

# 기본 타겟
help: ## 사용 가능한 명령어 표시
	@echo "🌍 WRLD Relief Crisis Monitor - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 개발 환경 설정
install: ## 의존성 설치 및 환경 설정
	@echo "📦 Installing dependencies..."
	cd api-server && python3 -m venv venv
	cd api-server && source venv/bin/activate && pip install --upgrade pip
	cd api-server && source venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

setup: ## 초기 프로젝트 설정
	@echo "🔧 Setting up project..."
	cp api-server/.env.example api-server/.env
	@echo "📝 Please edit api-server/.env file with your configuration"
	@echo "✅ Project setup completed!"

# 개발 서버
dev: ## 개발 서버 실행
	@echo "🚀 Starting development server..."
	cd api-server && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-bg: ## 개발 서버 백그라운드 실행
	@echo "🚀 Starting development server in background..."
	cd api-server && source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
	@echo "✅ Server started in background. Check server.log for logs."

stop: ## 백그라운드 서버 중지
	@echo "🛑 Stopping background server..."
	pkill -f "uvicorn app.main:app" || echo "No server process found"

# 테스트
test: ## 테스트 실행
	@echo "🧪 Running tests..."
	cd api-server && source venv/bin/activate && python -m pytest tests/ -v

test-cov: ## 테스트 커버리지 실행
	@echo "📊 Running tests with coverage..."
	cd api-server && source venv/bin/activate && python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# 코드 품질
lint: ## 코드 린팅
	@echo "🔍 Running linter..."
	cd api-server && source venv/bin/activate && flake8 app/
	cd api-server && source venv/bin/activate && pylint app/

format: ## 코드 포맷팅
	@echo "✨ Formatting code..."
	cd api-server && source venv/bin/activate && black app/
	cd api-server && source venv/bin/activate && isort app/

check: ## 코드 품질 검사
	@echo "🔍 Running code quality checks..."
	cd api-server && source venv/bin/activate && black --check app/
	cd api-server && source venv/bin/activate && isort --check-only app/
	cd api-server && source venv/bin/activate && flake8 app/

# Docker
docker-build: ## Docker 이미지 빌드
	@echo "🐳 Building Docker image..."
	docker build -t wrld-relief-api ./api-server
	@echo "✅ Docker image built successfully!"

docker-run: ## Docker 컨테이너 실행
	@echo "🐳 Running Docker container..."
	docker run -d --name wrld-relief-api -p 8000:8000 wrld-relief-api
	@echo "✅ Docker container started!"

docker-stop: ## Docker 컨테이너 중지
	@echo "🐳 Stopping Docker container..."
	docker stop wrld-relief-api || echo "Container not running"
	docker rm wrld-relief-api || echo "Container not found"

docker-compose-up: ## Docker Compose로 전체 스택 실행
	@echo "🐳 Starting full stack with Docker Compose..."
	docker-compose up -d
	@echo "✅ Full stack started!"

docker-compose-down: ## Docker Compose 스택 중지
	@echo "🐳 Stopping Docker Compose stack..."
	docker-compose down
	@echo "✅ Stack stopped!"

docker-logs: ## Docker 로그 확인
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f api

# 데이터베이스
db-init: ## 데이터베이스 초기화
	@echo "🗄️ Initializing database..."
	cd api-server && source venv/bin/activate && python -c "from app.database.connection import init_db; import asyncio; asyncio.run(init_db())"
	@echo "✅ Database initialized!"

db-reset: ## 데이터베이스 리셋
	@echo "🗄️ Resetting database..."
	rm -f api-server/disasters.db
	$(MAKE) db-init
	@echo "✅ Database reset completed!"

db-backup: ## 데이터베이스 백업
	@echo "💾 Creating database backup..."
	mkdir -p backups
	cp api-server/disasters.db backups/disasters_$(shell date +%Y%m%d_%H%M%S).db
	@echo "✅ Database backup created!"

# 유틸리티
clean: ## 임시 파일 정리
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "✅ Cleanup completed!"

check-deps: ## 의존성 보안 검사
	@echo "🔒 Checking dependencies for security issues..."
	cd api-server && source venv/bin/activate && pip-audit

update-deps: ## 의존성 업데이트
	@echo "📦 Updating dependencies..."
	cd api-server && source venv/bin/activate && pip list --outdated
	@echo "💡 Run 'pip install --upgrade <package>' to update specific packages"

# API 테스트
api-test: ## API 엔드포인트 테스트
	@echo "🔌 Testing API endpoints..."
	curl -f http://localhost:8000/health || echo "❌ Health check failed"
	curl -f http://localhost:8000/api/disasters/ || echo "❌ Disasters API failed"
	curl -f http://localhost:8000/api/mcp/mock?count=3 || echo "❌ MCP API failed"
	@echo "✅ API tests completed!"

# 문서
docs: ## API 문서 열기
	@echo "📚 Opening API documentation..."
	open http://localhost:8000/docs

# 로그
logs: ## 애플리케이션 로그 확인
	@echo "📋 Showing application logs..."
	tail -f api-server/server.log

# 모니터링
monitor: ## 시스템 모니터링 정보
	@echo "📊 System monitoring info:"
	@echo "API Server: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Health Check: http://localhost:8000/health"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

# 배포
deploy-prep: ## 배포 준비
	@echo "🚀 Preparing for deployment..."
	$(MAKE) clean
	$(MAKE) test
	$(MAKE) check
	$(MAKE) docker-build
	@echo "✅ Deployment preparation completed!"

# 전체 설정
all: install setup db-init ## 전체 프로젝트 설정
	@echo "🎉 Project setup completed!"
	@echo "Run 'make dev' to start the development server"

# 기본 타겟을 help로 설정
.DEFAULT_GOAL := help
