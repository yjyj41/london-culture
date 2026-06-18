# London Culture — Archive

런던의 공연 · 전시 · 음악 일정을 여러 소스에서 자동으로 모아 미니멀한 아카이브 페이지로 보여주는 프로젝트입니다.
GitHub Actions가 매일 스크래퍼를 돌려 `docs/events.json`을 갱신하고, GitHub Pages가 그 데이터를 정적 사이트로 발행합니다. **한 번 세팅하면 서버 없이, 무료로, 알아서 굴러갑니다.**

## 소스

| 소스 | 카테고리 | 방식 | 상태 |
|------|----------|------|------|
| **Ticketmaster** | 콘서트 · 공연 | 공식 Discovery API | ✅ 바로 작동 (API 키 필요) |
| **Tate** (Modern·Britain) | 전시 | HTML 스크래핑 | ✅ 바로 작동 |
| **National Gallery** | 전시 | HTML 스크래핑 | ✅ 바로 작동 |
| **Bachtrack** | 클래식·오페라·발레 | 헤드리스 브라우저(Playwright) | ⚠️ best-effort, 셀렉터 조정 필요할 수 있음 |
| **Time Out** | 종합 | 헤드리스 브라우저 | ⚠️ 기본 비활성 (Cloudflare 차단 잦음) |

## 폴더 구조

```
london-culture/
├── docs/                     # GitHub Pages가 발행하는 폴더
│   ├── index.html            # 아카이브 페이지 (events.json을 읽음)
│   └── events.json           # 스크래퍼가 갱신하는 데이터 (초기 seed 포함)
├── scraper/
│   ├── main.py               # 전체 실행: 모든 소스 수집 → events.json
│   ├── normalize.py          # 날짜 파싱 + 이벤트 정규화
│   ├── requirements.txt
│   └── sources/
│       ├── ticketmaster.py
│       ├── tate.py
│       ├── national_gallery.py
│       ├── bachtrack.py
│       └── timeout.py
└── .github/workflows/update.yml   # 매일 06:00 UTC 자동 실행
```

## 세팅 (약 10분)

### 1. GitHub 저장소 만들기
이 `london-culture` 폴더를 새 GitHub 저장소로 올립니다.

```bash
cd london-culture
git init
git add .
git commit -m "London Culture archive"
git branch -M main
git remote add origin https://github.com/<your-id>/london-culture.git
git push -u origin main
```

### 2. Ticketmaster API 키 발급
1. https://developer.ticketmaster.com/ 가입 → 앱 등록 → **Consumer Key** 복사 (무료, 즉시 발급).
2. 저장소 **Settings → Secrets and variables → Actions → New repository secret**
3. 이름 `TICKETMASTER_API_KEY`, 값에 키를 붙여넣고 저장.

### 3. GitHub Pages 켜기
**Settings → Pages → Build and deployment**
- Source: **Deploy from a branch**
- Branch: **main** / 폴더: **/docs** → Save
- 잠시 뒤 `https://<your-id>.github.io/london-culture/` 에서 사이트가 열립니다.

### 4. 첫 실행
**Actions** 탭 → **Update events** 워크플로 → **Run workflow** 버튼으로 수동 실행.
이후엔 매일 06:00 UTC에 자동으로 돌면서 `events.json`을 갱신·커밋합니다.

## 로컬에서 직접 돌려보기

```bash
cd scraper
pip install -r requirements.txt
python -m playwright install chromium      # Bachtrack용 (선택)
export TICKETMASTER_API_KEY=xxxxx
python main.py                             # ../docs/events.json 생성
```

`docs/index.html`은 그냥 더블클릭해도 내장 seed 데이터로 미리보기가 됩니다.
(실데이터는 `events.json`을 통해 GitHub Pages에서 보입니다.)

## 갱신 주기 바꾸기
`.github/workflows/update.yml`의 cron 값을 수정하세요.
- 매일 아침 6시(UTC): `0 6 * * *` (기본)
- 6시간마다: `0 */6 * * *`
- 매주 월요일: `0 6 * * 1`

## 소스 추가·수정하기
1. `scraper/sources/` 에 `def fetch() -> list[dict]` 를 가진 모듈을 추가하고,
   `normalize.event(...)` 로 이벤트를 만들어 반환합니다.
2. `scraper/main.py`의 `SOURCES` 리스트에 등록하면 끝.

## 주의 / 한계
- **Bachtrack·Time Out**은 JS 렌더링·안티봇 때문에 사이트 구조가 바뀌면 셀렉터를 손봐야 합니다.
  각 모듈 상단의 셀렉터 변수만 고치면 됩니다. 실패해도 다른 소스에는 영향이 없습니다.
- 스크래핑은 각 사이트의 이용약관 범위 내에서, 개인용·저빈도로만 사용하세요.
- 표시되는 정보는 참고용입니다. 날짜·가격·예매는 항상 각 항목의 공식 페이지에서 최종 확인하세요.
