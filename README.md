# ALT Exchange - Production-Ready Cryptocurrency Exchange

이 저장소는 설계 문서에 따라 구현된 완전한 암호화폐 거래소입니다. Python 기반의 모듈러 아키텍처로 구성되어 있으며, 실제 운영 환경으로 확장 가능한 구조를 가지고 있습니다.

## 🚀 주요 기능

- **주문 매칭 엔진**: Price-Time 우선순위, IOC/FOK 지원
- **REST API**: FastAPI 기반의 완전한 거래소 API
- **WebSocket**: 실시간 시장 데이터 및 주문 업데이트
- **관리자 시스템**: 2-eyes 승인 워크플로
- **이벤트 기반 아키텍처**: 확장 가능한 마이크로서비스 구조
- **Docker 지원**: 완전한 컨테이너화된 배포

## 🏗️ 아키텍처

```
alt-exchange/
├── src/alt_exchange/
│   ├── api/              # FastAPI REST API & WebSocket
│   ├── core/             # 도메인 모델, 이벤트, 예외
│   ├── infra/            # 데이터스토어, 이벤트 버스
│   └── services/
│       ├── account/      # 계정/잔고/주문 관리
│       ├── matching/     # 매칭 엔진
│       ├── market_data/  # 시장 데이터 브로드캐스터
│       ├── wallet/       # 입출금 관리
│       └── admin/        # 관리자 승인 시스템
├── docker-compose.yml    # 전체 스택 배포
├── docs/                 # API 문서 및 운영 가이드
└── tests/                # 포괄적인 테스트 스위트
```

## 🚀 빠른 시작

### 1. 로컬 개발 환경

```bash
# 의존성 설치
poetry install

# 테스트 실행
poetry run pytest

# API 서버 시작
poetry run python -m alt_exchange.api.main

# WebSocket 서버 시작
poetry run python -m alt_exchange.api.websocket
```

### 2. Docker로 전체 스택 실행

```bash
# 모든 서비스 시작
make up

# 또는 직접 실행
docker-compose up -d

# 서비스 상태 확인
make health
```

### 3. API 사용 예시

```bash
# Health check
curl http://localhost:8000/health

# 주문서 조회
curl http://localhost:8000/orderbook/ALT%2FUSDT

# API 문서 확인
open http://localhost:8000/docs
```

## 📚 API 문서

- **REST API**: http://localhost:8000/docs
- **OpenAPI 스펙**: `docs/openapi.yaml`
- **WebSocket**: ws://localhost:8765

## 🧪 테스트

```bash
# 전체 테스트 실행
make test

# 특정 테스트 실행
poetry run pytest tests/test_matching.py -v

# 커버리지 리포트
poetry run pytest --cov=src/alt_exchange --cov-report=html
```

## 🐳 Docker 서비스

- **API Gateway**: Kong (포트 8000)
- **REST API**: FastAPI (포트 8001)
- **WebSocket**: Market Data (포트 8765)
- **Admin API**: 관리자 인터페이스 (포트 8002)
- **Database**: PostgreSQL + TimescaleDB
- **Cache**: Redis
- **Message Queue**: Kafka + RabbitMQ
- **Auth**: Keycloak (포트 8080)
- **Monitoring**: Prometheus + Grafana

## 🔧 개발 도구

```bash
# 코드 포맷팅
make format

# 린팅
make lint

# 의존성 업데이트
poetry update

# 데이터베이스 마이그레이션
make migrate
```

## 📊 모니터링

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kong Admin**: http://localhost:8001
- **RabbitMQ Management**: http://localhost:15672

## 🔒 보안 기능

- JWT 기반 인증
- 2-eyes 출금 승인
- 감사 로그
- 레이트 리미팅
- 입력 검증

## 🚀 운영 배포

```bash
# 프로덕션 배포
make deploy

# 백업 생성
make backup

# 시스템 메트릭 확인
make metrics
```

## 📖 상세 문서

- [구현 계획](docs/implementation-plan.md)
- [빠른 시작 가이드](docs/runbooks/quickstart.md)
- [OpenAPI 스펙](docs/openapi.yaml)

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
