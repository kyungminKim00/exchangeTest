# ALT Exchange Quickstart Runbook (로컬)

## 1. 환경 변수
`.env` 파일을 루트에 생성하고 아래 키를 설정합니다 (값이 없으면 기본값 사용).

```
DATABASE_URL=sqlite:///./alt_exchange.db
JWT_SECRET=local-secret
WS_ENABLED=false
```

## 2. 최초 셋업
```
poetry install
poetry run alembic upgrade head  # (미구현 상태에서는 migrations 스텁)
```

## 3. 로컬 서비스 실행
```
poetry run uvicorn alt_exchange.main:app --reload
```

- `/docs`: OpenAPI 스펙 (FastAPI 자동 생성)
- `/ws`: 주문/체결 브로드캐스트 (테스트 모드)

## 4. 운영 플로우 시뮬레이션
1. `POST /users` → 계정 생성
2. `POST /wallet/deposits/mock` → 입금 컨펌 시뮬레이션
3. `POST /orders` → 지정가 주문 제출
4. 체결 후 `/balances` → 잔고 확인
5. `POST /withdrawals` → 2-eyes 승인 큐로 이동, `/admin/approvals` 으로 승인

## 5. 모니터링 포인트 (스텁)
- `GET /metrics` → Prometheus 형식 지표 (매칭 지연, 주문 처리량)
- `logs/` → 감사 로그 파일, `audit.log`

## 6. 장애 대응 절차
- **입금 누락**: `poetry run alt_exchange.tools.replay_deposits` 실행 → 체인 이벤트 재처리
- **호가 불일치**: `poetry run alt_exchange.tools.rebuild_orderbook` → Redis 스냅샷 대신 InMemory 스냅샷 재작성
- **출금 지연**: RabbitMQ 큐 대신 in-memory 큐 점검 → `poetry run alt_exchange.tools.inspect_withdrawals`

## 7. 테스트
```
poetry run pytest
```

모든 모듈은 인메모리 구현을 우선 제공하므로 외부 인프라 없이 즉시 시나리오 검증이 가능합니다.
