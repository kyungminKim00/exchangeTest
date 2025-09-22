# ALT Exchange (Python Prototype)

이 저장소는 다중 서비스 기반 거래소 설계를 단일 Python 모듈로 축소한 테스트/실습용 구현입니다. InMemory 데이터스토어와 이벤트 버스를 통해 주문 매칭, 잔고 정산, 입출금 플로우를 빠르게 검증할 수 있습니다.

## 빠른 시작
```
poetry install
poetry run pytest
```

`tests/` 폴더를 참고하여 사용자 생성, 입금, 주문, 체결, 출금 시나리오를 확인할 수 있습니다.
