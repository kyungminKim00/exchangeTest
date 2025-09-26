#!/usr/bin/env python3
"""
WebSocket 테스트 파일들의 async 메서드 호출을 수정하는 스크립트
"""

import os
import re


def fix_websocket_test_file(file_path):
    """WebSocket 테스트 파일의 async 메서드 호출을 수정"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # async 메서드 호출 패턴들
    patterns = [
        # websocket_manager.subscribe_to_market -> await websocket_manager.subscribe_to_market
        (
            r"(\s+)websocket_manager\.subscribe_to_market\(",
            r"\1await websocket_manager.subscribe_to_market(",
        ),
        # websocket_manager.subscribe_to_user -> await websocket_manager.subscribe_to_user
        (
            r"(\s+)websocket_manager\.subscribe_to_user\(",
            r"\1await websocket_manager.subscribe_to_user(",
        ),
        # websocket_manager.send_orderbook_snapshot -> await websocket_manager.send_orderbook_snapshot
        (
            r"(\s+)websocket_manager\.send_orderbook_snapshot\(",
            r"\1await websocket_manager.send_orderbook_snapshot(",
        ),
        # websocket_manager.broadcast_orderbook_update -> await websocket_manager.broadcast_orderbook_update
        (
            r"(\s+)websocket_manager\.broadcast_orderbook_update\(",
            r"\1await websocket_manager.broadcast_orderbook_update(",
        ),
        # websocket_manager.broadcast_trade -> await websocket_manager.broadcast_trade
        (
            r"(\s+)websocket_manager\.broadcast_trade\(",
            r"\1await websocket_manager.broadcast_trade(",
        ),
        # websocket_manager.send_order_update -> await websocket_manager.send_order_update
        (
            r"(\s+)websocket_manager\.send_order_update\(",
            r"\1await websocket_manager.send_order_update(",
        ),
    ]

    # 패턴 적용
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # async 테스트 메서드에 @pytest.mark.asyncio 데코레이터 추가
    # def test_ -> @pytest.mark.asyncio\n    async def test_
    content = re.sub(
        r"(\s+)def test_([^_].*?):",
        r"\1@pytest.mark.asyncio\n\1async def test_\2:",
        content,
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed: {file_path}")


def main():
    """메인 함수"""
    test_dir = "tests"
    websocket_test_files = [
        "test_websocket_simple_coverage.py",
        "test_websocket_comprehensive_coverage.py",
        "test_websocket_basic.py",
        "test_websocket_simple.py",
        "test_websocket_part1.py",
        "test_websocket_part2.py",
    ]

    for filename in websocket_test_files:
        file_path = os.path.join(test_dir, filename)
        if os.path.exists(file_path):
            fix_websocket_test_file(file_path)
        else:
            print(f"File not found: {file_path}")


if __name__ == "__main__":
    main()
