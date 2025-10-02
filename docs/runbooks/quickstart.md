# ALT Exchange Quickstart Runbook

## 🚀 빠른 시작 (5분 내 실행)

ALT Exchange는 Clean Architecture 원칙에 따라 구현된 프로덕션 레디 암호화폐 거래소입니다. 93% 이상의 테스트 커버리지를 자랑하며, Limit, Market, Stop, OCO 주문을 지원합니다.

## 1. 환경 설정

### 1.1 시스템 요구사항
- Python 3.8+
- Poetry (의존성 관리)
- Docker & Docker Compose (선택사항)

### 1.2 환경 변수 설정
`.env` 파일을 루트에 생성하고 아래 키를 설정합니다:

```bash
# Database
DATABASE_URL=postgresql://alt_user:alt_password@localhost:5432/alt_exchange

# Security
JWT_SECRET=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key

# External Services
REDIS_URL=redis://localhost:6379
KAFKA_BROKERS=localhost:9092
RABBITMQ_URL=amqp://alt_user:alt_password@localhost:5672

# Blockchain (테스트넷)
BSC_WS_URL=wss://bsc-testnet.nodereal.io/ws/v1/YOUR_API_KEY
ALT_CONTRACT_ADDRESS=0x...

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

## 2. 로컬 개발 환경 설정

### 2.1 의존성 설치
```bash
# Poetry 설치 (없는 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 프로젝트 의존성 설치
poetry install

# 개발 도구 설치
poetry install --with dev
```

### 2.2 데이터베이스 설정
```bash
# PostgreSQL 시작 (Docker 사용)
docker-compose up -d postgres

# 또는 로컬 PostgreSQL 사용
createdb alt_exchange

# 스키마 생성
make db-migrate
```

## 3. 서비스 실행

### 3.1 단일 서비스 실행
```bash
# API 서버 시작
poetry run python -m alt_exchange.api.main

# WebSocket 서버 시작 (별도 터미널)
poetry run python -m alt_exchange.api.websocket
```

### 3.2 전체 스택 실행 (Docker)
```bash
# 모든 서비스 시작
make up
# 또는
docker-compose up -d

# 서비스 상태 확인
make health
```

## 4. API 사용 예시

### 4.1 기본 엔드포인트
- **API 문서**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8765
- **Health Check**: http://localhost:8000/health

### 4.2 사용자 및 계정 생성
```bash
# 사용자 생성
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'

# 계정 생성
curl -X POST "http://localhost:8000/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1
  }'
```

### 4.3 주문 관리
```bash
# 지정가 주문
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "side": "BUY",
    "type": "LIMIT",
    "price": 100.0,
    "amount": 10.0
  }'

# 시장가 주문
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "side": "SELL",
    "type": "MARKET",
    "amount": 5.0
  }'
```

### 4.4 잔고 및 거래 내역 조회
```bash
# 잔고 조회
curl "http://localhost:8000/balances/1"

# 거래 내역 조회
curl "http://localhost:8000/trades/1"

# 주문 내역 조회
curl "http://localhost:8000/orders/1"
```

## 5. 운영 플로우 시뮬레이션

### 5.1 완전한 거래 시나리오
```bash
# 1. 사용자 생성
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "trader@example.com", "password": "securepass123"}'

# 2. 계정 생성
curl -X POST "http://localhost:8000/accounts" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# 3. 입금 시뮬레이션
curl -X POST "http://localhost:8000/wallet/deposits/mock" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "asset": "USDT", "amount": 1000.0}'

# 4. 지정가 매수 주문
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "side": "BUY",
    "type": "LIMIT",
    "price": 100.0,
    "amount": 10.0
  }'

# 5. 잔고 확인
curl "http://localhost:8000/balances/1"

# 6. 출금 요청
curl -X POST "http://localhost:8000/withdrawals" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "asset": "USDT",
    "amount": 100.0,
    "address": "0x..."
  }'
```

### 5.2 관리자 승인 워크플로
```bash
# 출금 승인 (관리자)
curl -X POST "http://localhost:8002/admin/withdrawals/1/approve" \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1, "reason": "Approved after KYC verification"}'

# 계정 동결 (관리자)
curl -X POST "http://localhost:8002/admin/accounts/1/freeze" \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1, "reason": "Suspicious activity detected"}'
```

## 6. 모니터링 및 관찰성

### 6.1 메트릭 및 대시보드
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **API 메트릭**: http://localhost:8000/metrics

### 6.2 로그 및 감사
```bash
# 서비스 로그 확인
make logs

# 감사 로그 조회
curl "http://localhost:8000/admin/audit-logs"

# 시스템 상태 확인
make health
```

### 6.3 성능 모니터링
```bash
# 주문 처리량 모니터링
curl "http://localhost:9090/api/v1/query?query=order_processing_rate"

# 데이터베이스 연결 상태
curl "http://localhost:8000/health/database"

# WebSocket 연결 수
curl "http://localhost:8000/health/websocket"
```

## 7. 테스트 및 품질 보증

### 7.1 전체 테스트 실행
```bash
# 전체 테스트 스위트 (93% 커버리지 목표)
make test

# 특정 모듈 테스트
poetry run pytest tests/test_matching.py -v

# 커버리지 리포트 생성
poetry run pytest --cov=src --cov-report=html
```

### 7.2 코드 품질 검사
```bash
# 코드 포맷팅
make format

# 린팅 및 타입 체크
make lint

# 보안 스캔
make security

# 종합 품질 검사
make quality-check
```

## 8. 장애 대응 및 복구

### 8.1 일반적인 문제 해결
```bash
# 서비스 재시작
make down && make up

# 데이터베이스 재설정 (주의: 데이터 손실)
make db-reset

# 로그 확인
docker-compose logs -f api

# 메모리 사용량 확인
docker stats
```

### 8.2 백업 및 복구
```bash
# 데이터베이스 백업
make backup

# 백업에서 복구
make restore

# 설정 백업
cp .env .env.backup
```

## 9. 개발 및 디버깅

### 9.1 개발 모드 실행
```bash
# 개발 서버 (핫 리로드)
poetry run uvicorn alt_exchange.api.main:app --reload --host 0.0.0.0 --port 8000

# 디버그 모드
export DEBUG=true
poetry run python -m alt_exchange.api.main
```

### 9.2 데이터베이스 쿼리
```bash
# PostgreSQL 접속
make db-shell

# 스키마 확인
\dt

# 사용자 데이터 확인
SELECT * FROM users LIMIT 10;
```

## 10. 프로덕션 배포

### 10.1 프로덕션 환경 설정
```bash
# 프로덕션 설정으로 배포
make deploy

# 환경 변수 확인
docker-compose config

# 서비스 상태 모니터링
make metrics
```

### 10.2 확장성 고려사항
- **로드 밸런싱**: Kong API Gateway 활용
- **데이터베이스**: PostgreSQL 클러스터링
- **캐싱**: Redis 클러스터
- **메시징**: Kafka 파티셔닝

---

## 🎯 다음 단계

1. **API 문서 탐색**: http://localhost:8000/docs
2. **WebSocket 연결 테스트**: ws://localhost:8765
3. **모니터링 대시보드**: http://localhost:3000
4. **테스트 실행**: `make test`

모든 모듈은 Clean Architecture 원칙에 따라 구현되어 있으며, 93% 이상의 테스트 커버리지를 자랑합니다. 외부 인프라 없이도 모든 기능을 테스트할 수 있습니다.
