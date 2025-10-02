# ALT Exchange Architecture

## Overview

ALT Exchange는 Clean Architecture 원칙을 따르는 암호화폐 거래소 시스템입니다.

## Architecture Layers

### 1. Core Layer (`src/alt_exchange/core/`)
- **목적**: 비즈니스 규칙과 도메인 모델
- **의존성**: 외부 의존성 없음
- **구성요소**:
  - `models.py`: 도메인 엔티티 (User, Account, Order, Trade 등)
  - `enums.py`: 도메인 열거형 (OrderType, OrderStatus, Asset 등)
  - `events.py`: 도메인 이벤트 (OrderAccepted, TradeExecuted 등)
  - `exceptions.py`: 도메인 예외 (InsufficientBalanceError 등)
  - `config.py`: 설정 클래스

### 2. Services Layer (`src/alt_exchange/services/`)
- **목적**: 비즈니스 로직 구현
- **의존성**: Core Layer만 의존
- **구성요소**:
  - `account/`: 계정 관리 서비스
  - `admin/`: 관리자 서비스
  - `matching/`: 주문 매칭 엔진
  - `market_data/`: 시장 데이터 브로드캐스팅
  - `wallet/`: 지갑 서비스

### 3. Infrastructure Layer (`src/alt_exchange/infra/`)
- **목적**: 외부 시스템과의 통합
- **의존성**: Core와 Services Layer에 의존
- **구성요소**:
  - `database/`: 데이터베이스 구현체
  - `event_bus.py`: 이벤트 버스 구현
  - `bootstrap.py`: 애플리케이션 컨텍스트 구성

### 4. API Layer (`src/alt_exchange/api/`)
- **목적**: 외부 인터페이스 (REST API, WebSocket)
- **의존성**: 모든 레이어에 의존
- **구성요소**:
  - `main.py`: FastAPI REST API
  - `websocket.py`: WebSocket 핸들러

## Design Principles

### 1. Clean Architecture
- 의존성 방향: Core → Services → Infrastructure → API
- 비즈니스 로직은 외부 의존성에 독립적
- 인터페이스와 구현체 분리

### 2. Dependency Injection
- Bootstrap을 통한 의존성 주입
- 테스트 가능한 구조
- 런타임 의존성 구성

### 3. Interface Segregation
- Repository 패턴으로 데이터 접근 추상화
- 작은 단위의 인터페이스 제공
- 단일 책임 원칙 준수

### 4. Event-Driven Architecture
- 도메인 이벤트를 통한 느슨한 결합
- 비동기 처리 지원
- 확장 가능한 이벤트 시스템

## Key Components

### Matching Engine
- 가격-시간 우선순위 매칭
- 다양한 주문 타입 지원 (Limit, Market, Stop, OCO)
- 실시간 거래 실행

### Database Layer
- 추상화된 Database 인터페이스
- InMemory와 PostgreSQL 구현체
- Unit of Work 패턴 지원

### Event System
- InMemoryEventBus 구현
- 도메인 이벤트 발행/구독
- WebSocket을 통한 실시간 알림

## Code Quality

### Naming Conventions
- 클래스: PascalCase
- 함수/변수: snake_case
- 모듈: snake_case
- 상수: UPPER_CASE

### Import Organization
- 표준 라이브러리
- 서드파티 라이브러리
- 로컬 모듈 (절대 경로)
- 상대 경로 (같은 패키지 내)

### Error Handling
- 도메인별 예외 클래스
- 명확한 에러 메시지
- 적절한 HTTP 상태 코드

## Testing Strategy

### Test Structure
- 단위 테스트: 각 컴포넌트 독립 테스트
- 통합 테스트: 컴포넌트 간 상호작용 테스트
- API 테스트: 엔드포인트 기능 테스트

### Test Coverage
- 목표: 95% 이상
- 현재: 93.78% (1,722 passed, 27 skipped)

## Future Improvements

### 1. Repository Pattern
- 현재 Database 인터페이스를 Repository로 분리
- 더 세밀한 데이터 접근 제어

### 2. CQRS Pattern
- 명령과 쿼리 분리
- 읽기/쓰기 최적화

### 3. Microservices
- 서비스별 독립 배포
- 확장성 향상

### 4. Event Sourcing
- 모든 상태 변경을 이벤트로 기록
- 감사 추적 및 복구 지원
