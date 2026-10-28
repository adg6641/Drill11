# Drill #11 — 소년 자동 무적 런(AutoRun)

Pico2D 소년의 `Idle`, `Run`, `Sleep`에 별도 `AutoRun` 상태 클래스를 추가한 과제입니다.
좌우 방향은 소년의 `face_dir` 속성으로 관리하며, 상태와 방향 전이는 아래 그림에 정리했습니다.

![통합 상태 다이어그램](state_diagram.png)

[확대·편집용 SVG](state_diagram.svg) · [개발 기획·요구사항 PRD](PRD.md)

## 실행

Python 3.13, Pico2D 1.5.1, transitions 0.9.3 환경에서 검증했습니다.

```powershell
python -m pip install -r requirements.txt
python main.py
```

VS Code에서 이 폴더를 열고 Python 인터프리터를 선택한 다음 `Run Drill11` 구성을 실행할 수도 있습니다.
이미지 경로는 소스 파일 위치를 기준으로 찾으므로 다른 작업 디렉터리에서 실행해도 됩니다.

## 조작과 상태

| 입력·조건 | 동작 |
| --- | --- |
| `←`, `→` | 입력한 방향으로 일반 달리기. 키를 놓으면 쉬기 |
| 좌우 키를 동시에 누름 | Idle로 정지. 한쪽을 놓으면 남은 방향으로 달리기 |
| Idle에서 입력 없이 5초 | Sleep으로 전이 |
| Sleep에서 `Space` | Idle로 복귀 |
| Sleep에서 방향키 | Run으로 전이 |
| Idle에서 `a` | 바라보던 방향으로 AutoRun 시작 |
| AutoRun 중 화면 좌우 끝 | 방향만 반전. 상태와 시작 타이머 유지 |
| AutoRun 진입 후 5초 이상 | Idle로 복귀하고 기본 속도·크기로 복구 |
| AutoRun 중 `←` 또는 `→` 누름 | 무적 런 취소 후 누른 방향의 일반 Run으로 전이 |
| `Esc` 또는 창 닫기 | 종료 |

## 제공된 채점 기준과 구현 위치

| 기준 | 구현 |
| --- | --- |
| `a` 키로 AutoRun 이동 (1점) | `main.py`의 이벤트 처리, `Boy.request_auto_run()`, `AutoRun.enter()` |
| 5초 이상 경과 후 Idle 복귀 (1점) | `AutoRun.update()`의 실제 경과 시간 검사와 `finish_auto_run` 전이 |
| 속도 증가·크기 확대 (1점) | 250 → 500 px/s, 100×100 → 160×160. 종료 시 원상 복구 |
| 화면 좌우 끝 자동 방향 전환 (1점) | `AutoRun.update()`의 확대된 크기 기준 경계 반사 |
| 상태 다이어그램 (1점) | 저장소의 `state_diagram.png`, `state_diagram.svg` |
| 필수 별도 상태 클래스 | `boy.py`의 `class AutoRun(BoyState)` |

AutoRun에서는 `is_invulnerable`이 활성화됩니다. 이 과제의 기본 장면에는 적이나 피격 시스템이 없습니다.
Idle의 대기 5초와 AutoRun의 지속 5초는 서로 다른 타이머입니다. 방향 반전·`a` 재입력·키 해제로 AutoRun 시간이 늘어나지 않습니다.

## 검증

```powershell
python -m unittest discover -s tests -v
```

경계값 4.999초/5.000초, 좌우 반전, 느린 프레임의 다중 반사, 방향키 취소, 속도·크기 복구,
Sleep 깨우기, 동시 키 입력, 반복 키 입력, 실제 이벤트 처리 경로를 자동 테스트합니다.

실제 창·이미지·SDL 이벤트 큐와 실제 시간까지 확인하려면 다음 검증을 실행합니다(약 17초).

```powershell
python tests/runtime_smoke.py
```

확인한 결과는 [실행 검증 기록](VALIDATION.md)에 정리했습니다.

직접 확인할 순서:

1. 시작 후 `a` → 커진 소년이 빠르게 자동 이동하며 양쪽 끝에서 반전하는지 확인합니다.
2. 5초 뒤 크기가 돌아오고 Idle이 되는지 확인합니다.
3. 다시 `a`를 누른 뒤 `←` 또는 `→` → 즉시 일반 크기의 Run으로 바뀌는지 확인합니다.
4. 방향키를 놓고 5초 대기 → Sleep, `Space` → Idle, 방향키 → Run을 확인합니다.

## 작업 이력

기존 완성본의 변경 내용을 17개의 기능·문서·검증 단계로 나누어 main 이력을 재구성했습니다. 각 커밋에는 실제 변경이 있으며, 과거 작업 시각을 재현하거나 커밋 날짜를 변경하지 않았습니다. 단계별 내용은 [PRD의 개발 단계](PRD.md#11-개발-단계와-이력-관리)에 정리했습니다.

AI 도구 Codex를 사용해 구현, 검증, 다이어그램 작성을 보조했습니다. 최종 제출 방식과 AI 활용 표기는 수업 디스코드 공지를 따르세요.
