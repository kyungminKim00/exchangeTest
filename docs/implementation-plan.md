# ALT Exchange – Adapted Implementation Plan

이 문서는 다중 언어/서비스로 구성된 원 설계를 현재 Python 중심의 실습/테스트 환경에 맞춰 축소·재구성한 실행 계획입니다. 개발자는 아래 범위를 기반으로 즉시 구현을 진행할 수 있으며, 추후 Rust/Node.js 마이크로서비스로의 확장이 가능하도록 계층을 나누었습니다.

## 1. 기술 스택 & 런타임
- **언어**: Python 3.12 (Poetry 기반). Rust/Node 대신 Python으로 핵심 서비스를 모듈화.
- **프레임워크**: FastAPI(HTTP), Pydantic(스키마), uvicorn(개발 서버), SQLAlchemy + SQLite(로컬 트랜잭션 시뮬레이션), aiokafka/redis 대신 in-memory 이벤트 버스 및 캐시 스텁.
- **메시징/캐시**: 표준 인터페이스 정의 후 InMemory 구현. 실제 환경 전환 시 Kafka/Redis 어댑터 추가만으로 확장 가능.
- **DB**: SQLite + SQLAlchemy(테스트), PostgreSQL로 마이그레이션 가능한 마이그레이션 스크립트 템플릿 제공.
- **테스트**: pytest + coverage, hypothesis(선택)로 비즈니스 로직 검증.
- **관측**: loguru 로깅, Prometheus 클라이언트 인터페이스 스텁.

## 2. 모노레포 구조 (Python 중심)
```
alt-exchange/
 ├─ pyproject.toml
 ├─ docs/
 │   ├─ implementation-plan.md
 │   └─ runbooks/
 │       └─ quickstart.md
 ├─ src/
 │   └─ alt_exchange/
 │       ├─ core/           # 공통 모델, DTO, 예외, 설정
 │       ├─ infra/          # InMemory db/event bus, 시뮬레이터
 │       └─ services/
 │           ├─ account/    # 계정/잔고/주문쓰기
 │           ├─ matching/   # 가격-시간 우선 매칭엔진
 │           ├─ market_data/# 오더북/체결 브로드캐스터
 │           └─ wallet/     # 입출금/체인 스텁
 ├─ tests/
 │   ├─ test_matching.py
 │   └─ test_exchange_flow.py
 └─ README.md (추가 예정)
```

## 3. 데이터 모델 & 영속화
- 도메인 객체는 `pydantic.BaseModel` 기반 DTO와 `dataclasses`로 분리.
- SQLite/SQLAlchemy 스키마는 원 설계의 정밀도를 반영해 NUMERIC(36, 18) 대신 Decimal 컬럼, Enum은 `Enum` 타입으로 정의.
- 트랜잭션 래퍼(`infra.db.UnitOfWork`)를 통해 ACID 시뮬레이션, 실제 PG 전환 시 커넥션 스트링만 교체.

## 4. 서비스 책임
- **AccountService**: 사용자/계정 생성, 잔고 이중장부, 주문 사전 검증, 매칭 결과 정산(idempotent).
- **MatchingEngine**: 단일 스레드 이벤트 루프를 모사하기 위해 동기 함수로 주문 큐 처리. 가격-시간 우선, IOC/FOK 지원, 체결 이벤트 발행.
- **MarketDataBroadcaster**: 이벤트 버스 구독 후 인메모리 스냅샷 관리 및 WebSocket 브로드캐스트 스텁.
- **WalletService**: 입금/출금 요청 처리, 컨펌 시나리오 시뮬레이션, RabbitMQ 큐 대신 in-memory 큐 사용.

## 5. 메시지 & 이벤트 흐름
1. API 계층(현 단계에서는 FastAPI 단일 앱) → AccountService → MatchingEngine.
2. MatchingEngine 체결 → AccountService 정산 → MarketDataBroadcaster → WebSocket/CLI.
3. Wallet 입금 이벤트 → AccountService 잔고 반영. 출금은 2-eyes 승인 큐를 통과한 뒤 처리.

## 6. 보안/운영 고려 (로컬 대응)
- JWT 인증 대신 서명 검증 스텁 제공. 실제 키클록 연동 시 토큰 검증 어댑터만 교체.
- 감사 로그, 런북, 모니터링 포인트를 문서화 (`docs/runbooks/quickstart.md`).
- 환경변수 로딩 `.env` → `pydantic-settings` 기반 설정 객체로 통합.

## 7. 테스트 & 검증 전략
- `pytest`로 단위/통합 시나리오 (주문 흐름, 잔고 롤백, 입금 컨펌, 체결 이벤트 중복 방지).
- `tests/test_exchange_flow.py`에서 엔드투엔드(사용자 생성 → 입금 → 주문 → 체결 → 출금).
- `tests/test_matching.py`에서 가격/시간 우선, IOC/FOK 케이스 검증.

## 8. 향후 확장 포인트
- Rust/Node.js 서비스와의 경계는 gRPC/REST 인터페이스로 분리 예정. 현재 Python 인터페이스는 동일 시그니처를 유지.
- SQLite → PostgreSQL 전환 시 DDL 스크립트(`docs/sql/ddl_postgres.sql`)를 추가하여 마이그레이션.
- Kafka/Redis 어댑터 구현을 위한 공용 인터페이스(`infra.messaging` 모듈) 유지.

---
본 계획을 토대로 이후 커밋에서는 코드 스켈레톤 구현 및 pytest 기반 검증을 진행합니다.
