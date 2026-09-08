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

