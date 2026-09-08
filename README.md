# London Culture — My London collection

흑백 아카이브 UI에 취향 분류와 음악 장르 필터를 더한 개인 런던 문화 일정입니다.

## 화면
- 취향: 유명 아티스트 / 한국 가수 / 놓치기 아쉬운 클래식 / 클래식 전체 / 전시
- 음악 장르: Rock, Pop, K-pop, Metal, Hip-hop / R&B, Jazz, Electronic, Folk / Country, Classical, Other
- 기간(7·30·90일), 곡목·연주자 검색, 날짜·마감일·이름·공연장 정렬
- 일정 저장(localStorage, 현재 브라우저에만 저장), 모바일 화면, 40개씩 더 보기
- 종료된 일정 숨김, 수집 상태와 이전 데이터 표시. 가짜 seed 일정은 사용하지 않습니다.

장르는 관심 목록에 들어온 음악 안에서 필터링합니다. 전체 런던 음악 목록은 아닙니다. 클래식 추천은 별점이나 Bachtrack 에디터 추천이 아니라 아래 관심 목록과의 일치입니다.

## 취향 수정
`scraper/preferences.json`을 수정하면 다음 수집부터 적용됩니다.
- `headline_artists`: Bon Jovi 등 유명 아티스트 초기 목록
- `korean_artists`: 한국 가수·밴드·인디 초기 목록
- `korean_pop_artists`: 한국 아티스트 중 K-pop 장르로 표시할 목록
- `classical_soloists`, `classical_conductors`, `visiting_orchestras`: 추천 근거
- `exclude_terms`: 트리뷰트·클럽 파티·별도 VIP 상품 등 제외

국적이나 인기도를 이름으로 자동 추측하지 않습니다. 제공된 attraction 이름이 있으면 정확히 일치해야 합니다. 구형 데이터에는 제한적인 제목 일치만 적용하며 DEAN, ROSÉ, LISA 등 동명이인 가능성이 큰 이름은 제외합니다. 현재 목록 밖의 가수나 Ticketmaster에 등록되지 않은 공연은 빠질 수 있습니다.

## 데이터
| 소스 | 역할 | 범위 / 한계 |
|---|---|---|
| Bachtrack | 클래식 중심 목록, 연주자·곡목·공연 시간 | 공개 콘서트 검색과 More results 페이지네이션, 최대 1,000개 목록. 모든 날짜·회차를 분리. 오페라·발레 검색은 별도 수집하지 않음 |
| Wigmore Hall | 리사이틀 공식 목록 | 공식 첫 목록 페이지 |
| Barbican | 클래식 및 전시 보완 | 공식 첫 목록 페이지 |
| Tate | Tate Modern / Britain 전시 | 목록과 상세 페이지. 불명확한 가격은 표시하지 않음 |
| National Gallery | 전시 | 공식 목록 페이지 |
| Ticketmaster | 유명 아티스트·한국 가수 | 아티스트별 검색 + K-pop 검색. API 키 필요. 일반 재즈 대량 수집 제거 |

Bachtrack HTML과 공개 More results 응답은 2026-09-08 실제 페이지로 검증했습니다. 연주자 이름이 들어가도 실연이 아닌 것으로 확인된 `Playing with Fire: Yuja Wang` 디지털 아바타 체험은 클래식 리사이틀 목록에서 제외했습니다. 근거: [Southbank Centre 공식 안내](https://bynder.southbankcentre.co.uk/asset/840b6004-0f6a-4059-b33e-2cd6e3342b7c/Autumn_Winter-2026_27-Classical-Guide-WEB.pdf).

수집 실패 시 해당 소스의 마지막 확인으로부터 7일 이내 데이터만 보존합니다. 실패는 성공 시각을 갱신하지 않습니다. 날짜를 확인하지 못한 일정은 게시하지 않습니다. 동일 제목·공연장·날짜·시간은 중복 제거하지만 공급자 간 제목 차이가 큰 경우 중복이 남을 수 있습니다. 아직 모든 미술관·티켓 판매처를 포괄하지 않습니다.

`docs/events.json`의 `updated`는 마지막 실행 시각이며, 소스별 `last_success`와 이벤트별 `last_seen`으로 실제 확인 시점을 구분합니다. 초기 로컬 검증에서는 Ticketmaster 키가 없어 이전 저장소의 데이터 중 최근 확인한 항목만 재분류했습니다. 저장소의 기존 Actions secret을 이용하면 새 검색을 실행합니다.

## 자동 갱신 / 배포
GitHub Pages 설정은 기존과 동일하게 **main / docs**입니다.
- `.github/workflows/update.yml`: 매일 06:00 UTC, 수동 실행, main의 수집기 변경 시 실행
- 저장소 secret `TICKETMASTER_API_KEY`를 그대로 사용. 새 키를 코드나 브라우저에 넣지 않습니다.
- 수집 전 테스트 실행. 중복 실행은 직렬화하고 JSON은 임시 파일에서 원자적으로 교체.
- UI 변경은 main에 병합하면 Pages에 반영됩니다.
- [Ticketmaster 공식 API 문서](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/)

## 개발 / 검증
Python 3.12 이상:
```sh
pip install -r scraper/requirements.txt
python -m unittest discover -s tests -v
python scraper/main.py
python -m http.server 8000 --directory docs
```
미리보기는 http://localhost:8000 에서 엽니다. 파일을 직접 더블클릭하면 fetch 제한으로 데이터 로드 오류가 표시될 수 있습니다.

검증 범위: 관심 목록·트리뷰트·동명이인·장르, 날짜·회차 식별, 소스 실패/보존 만료/정상 0건, Bachtrack 응답 페이지네이션, Ticketmaster 취소 일정. 실 API의 관심 아티스트 검색은 Actions secret이 있는 환경에서 추가 확인해야 합니다.

## 추가 소스와 장소 필터 (2026-09-08)
- 공연장·갤러리 필터는 현재 취향 분류에 맞는 장소로 갱신됩니다. Barbican Hall/Centre/The Pit는 Barbican으로 묶고 실제 홀 이름은 각 일정에 유지합니다. Royal Albert Hall, Royal Festival Hall, Queen Elizabeth Hall 등은 구분합니다.
- 신규 전시 수집: V&A(런던 3개 관), Design Museum, Serpentine North/South, Whitechapel Gallery, The Photographers’ Gallery, Courtauld Gallery. 총 8개 전시 소스(Tate·National Gallery 포함).
- 전시별 정확한 종료일이 확인되는 항목만 게시합니다. 월만 제공하는 일정, 종료일이 없는 상설전, 투어·강연·온라인 행사는 제외합니다. 각 갤러리의 모든 미래 전시를 포괄하지는 않습니다.
- Royal Academy·National Portrait Gallery·Dulwich는 이번 실행에서 접근이 차단돼 아직 자동 수집에 포함하지 않았습니다. Hayward도 아직 추가하지 않았습니다.

### DICE / 누락 공연을 추가하는 방법
1. `scraper/preferences.json`의 `korean_artists`에 정확한 영문 아티스트 표기를 추가합니다(예: Chang Kiha / Jang Kiha / 장기하).
2. `scraper/extra_sources.json`의 `dice_events`에 전체 `https://dice.fm/event/...` 링크를 추가합니다. `artists`(실제 확인한 출연진), `subtitle`(한국어 검색 이름), `genre`는 선택 필드입니다.
3. 다음 수집 시 공개 MusicEvent 정보에서 런던 공연의 날짜·시간·장소를 갱신합니다. DICE 전체 검색을 자동으로 훑는 기능은 아니며 링크를 등록한 공연을 추적합니다.
4. DICE 접근이 실패하면 등록된 공식 EartH 페이지(`evidence_url`)에서 확인합니다. 다른 공연장용 보완 파서는 아직 없습니다.
5. 자동 접근이 모두 실패할 때 사용하려면 직접 확인한 `verified_event`를 함께 기록합니다. title, start(YYYY-MM-DD), time(HH:MM), venue, verified_at(시간대 포함 ISO)을 작성합니다. 직접 확인한 이벤트는 종료일까지 게시하되 확인 시각을 자동 갱신하지 않고 화면에 ‘직접 확인’을 표시합니다. 원본에서 취소·연기가 확인되면 제외합니다. 자동 접근이 차단된 상태의 취소는 감지할 수 없으므로 원본 확인이 필요합니다.

장기하 공연은 2026-09-28 19:30, EartH Theatre의 K-Music Festival로 DICE 및 공식 공연장 페이지에서 확인해 등록했습니다. ADG7, Chang Kiha, Lil Cherry & GOLDBUUDA가 함께 출연하는 공연입니다. [공식 예매](https://dice.fm/event/xeovae-k-music-festival-adg7-chang-kiha-lil-cherry-goldbuuda-28th-sep-earth-london-tickets).
