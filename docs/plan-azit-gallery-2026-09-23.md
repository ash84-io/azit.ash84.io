# Plan: azit.ash84.io — udara.io/photos 스타일 사진 갤러리 구축
- date: 2026-09-23
- status: in-progress
- author: claude
- approved-by: ash84 (2026-09-23, 열린 질문 5개 모두 제안안으로 결정)

## 1. 목적 및 배경

"아지트를 만드는 데 영감을 주는 사진들"(작업실, 창고, 카페 외관 등)을 모아두는 개인 사진 갤러리 정적 사이트를 만든다.
기존 `../leica`(gallery.ash84.io: GitHub Pages + `manifest.json` + 라이트박스)의 운영 방식은 그대로 가져오되, 디자인은 확정된 3차 시안(https://udara.io/photos 방식)을 따른다.

확정된 디자인 (디자인 캔버스 3차 시안 페이지 U1–U4):
- 상단 고정 nav: 작은 로고 마크 + 링크(사진 · 무작위 | ash84.io). 현재 페이지만 연한 pill.
- 본문 상단에 회색 한 줄 "아지트를 만드는 데 영감을 주는 사진들"과 큰 여백(240px / 320px). 제목·분류·태그 없음.
- 사진 흐름: 가로 사진 50%, 세로 사진 25% 너비의 flex-wrap, 사진마다 18px 안쪽 여백. 모바일(≤1025px)은 한 열 100%.
- 캡션은 hover 시에만 사진 하단에 앰버색 모노 글씨 `제목 · YYYY.MM`.
- 사진 클릭 → 배경색 전체 화면 뷰어(사진 한 장 + 11px 메타). 클릭/Esc 닫기, ←/→ 이동, 모바일 스와이프.
- 라이트/다크: 흰 배경 `#FFFFFF`/글씨 `#0B0B0B`, 다크 `#1A1818`/`#F3F3F3`. 글꼴 Geist + Geist Mono + Noto Sans KR (Google Fonts).

## 2. 예상 임팩트

- 신규 저장소(현재 폴더 `atelier.ash84.io`, 비어 있음). 기존 서비스·모듈·API에 영향 없음. `../leica`는 수정하지 않는다.
- 배포: GitHub Pages(`https://azit.ash84.io`). DNS에 `azit` CNAME 레코드 추가는 사용자 작업.
- 성능: 정적 파일만 제공. 격자용 썸네일(긴 변 1200px)과 뷰어용 원본(긴 변 2400px)을 분리해 첫 화면 전송량을 leica(사진당 0.3–1.4MB 단일 파일) 대비 크게 줄인다. `width/height`를 manifest에 넣어 레이아웃 시프트(CLS)를 없앤다.
- 사용자 경험: 사진 추가 흐름은 leica와 같다 — 원본을 폴더에 넣고 `make build` 후 커밋.

## 3. 구현 방법 비교

### 3-1. 사이트 구현 방식

| 방법 | 장점 | 단점 |
|---|---|---|
| A. leica 코드 복사 후 리스타일 | 빠름, 익숙한 구조 | leica `script.js`에 죽은 코드가 많음(VirtualScroller, InfiniteScroll, 성능 모니터링, `addEventListener` 몽키패치). 세로/가로 폭 배치를 위해 결국 데이터 구조를 바꿔야 함 |
| B. Astro/Eleventy 같은 정적 생성기 | 반응형 이미지·빌드 파이프라인이 표준화됨 | Node 의존성과 빌드 설정이 늘어남. 페이지 1장짜리 사이트에 과함 |
| **C. 바닐라 HTML/CSS/JS를 새로 작성 + Python 빌드 스크립트 (선택)** | 런타임 의존성 0, 코드가 작고 전부 설명 가능. 순수 함수(배치·셔플·인덱스)를 분리해 테스트 가능. 이미지 변환·manifest 생성은 Python(Pillow)으로 한 곳에서 처리 | 처음부터 작성하는 비용. leica의 서비스 워커·GA 등은 필요한 것만 다시 넣어야 함 |

**선택: C.** 디자인이 leica와 구조적으로 다르고(가로/세로 폭, hover 메타, 전체 화면 뷰어), leica의 JS는 재사용할 가치가 있는 부분이 라이트박스 키보드/스와이프 처리 정도라서 새로 쓰는 편이 짧고 깨끗하다.

### 3-2. 배포 폴더

| 방법 | 장점 | 단점 |
|---|---|---|
| A. leica처럼 `docs/`를 Pages 소스로 | 설정 없음 | 이 저장소의 `docs/`는 plan 문서 위치(규칙). plan `.md`가 공개 사이트에 그대로 서빙됨 |
| B. 저장소 루트를 Pages 소스로 | 설정 없음 | 루트에 css/js/images가 섞여 저장소가 지저분해짐 |
| **C. `site/`를 GitHub Actions(`actions/deploy-pages`)로 배포 (선택)** | plan은 `docs/`, 사이트는 `site/`로 분리. 이후 CI에서 lint/test를 함께 돌릴 수 있음 | 워크플로 파일 1개 필요. Pages 설정을 "GitHub Actions"로 바꿔야 함(사용자 1회 작업) |

### 3-3. 이미지 처리

| 방법 | 장점 | 단점 |
|---|---|---|
| A. leica처럼 `cwebp`로 단일 크기 변환 | 단순 | 격자에도 3000px 원본이 내려감. 세로/가로 판별에 필요한 크기 정보를 얻으려면 별도 도구가 또 필요 |
| **B. Python + Pillow 스크립트 하나로 썸네일/원본 WebP 생성 + 크기·EXIF 날짜 추출 → manifest (선택)** | 도구 하나로 변환·메타 추출·manifest 생성. 테스트 가능. Pillow 12가 이미 설치됨 | HEIC는 별도 플러그인 필요 → v1 범위 밖(사진 앱에서 JPG로 내보내기) |

## 4. 구현 단계

저장소 구조(목표):

```
azit.ash84.io/                 ← 현재 폴더명 atelier.ash84.io (이름 변경은 열린 질문 1)
├── Makefile                   help(기본) · format · lint · test · build · images · manifest · verify · server · clean
├── README.md
├── pyproject.toml             ruff · pytest 설정 (uv로 실행)
├── eslint.config.js / .prettierrc
├── .gitignore                 originals/ · .venv · node_modules 등
├── docs/plan-*.md
├── originals/                 원본 사진(JPG/PNG/WebP). git에 올리지 않음
├── site/                      GitHub Pages 산출물
│   ├── index.html · CNAME(azit.ash84.io) · robots.txt
│   ├── css/styles.css
│   ├── js/layout.js           순수 함수: orientationOf · shuffle · wrapIndex · formatMonth · metaText · sortNewestFirst
│   ├── js/gallery.js          manifest 로드 · 렌더 · hover 메타 · 뷰어 · 무작위 버튼
│   └── images/manifest.json · thumb/*.webp · full/*.webp
├── tools/
│   ├── build_images.py        originals → site/images/{thumb,full}/*.webp, EXIF 날짜 추출
│   ├── build_manifest.py      full/*.webp → manifest.json (기존 title 보존, 최신순 정렬)
│   └── tests/                 pytest
└── tests/js/layout.test.mjs   node --test
```

`manifest.json` 스키마:

```json
{
  "version": 1,
  "photos": [
    {
      "id": "IMG_5751",
      "thumb": "images/thumb/IMG_5751.webp",
      "full": "images/full/IMG_5751.webp",
      "width": 3024, "height": 4032,
      "orientation": "portrait",
      "date": "2026-09-14",
      "title": ""
    }
  ]
}
```

체크리스트 (각 단계는 독립적으로 검증 가능):

- [x] Step 1: 저장소 골격 — `git init`, `.gitignore`, `README.md`, `pyproject.toml`(ruff/pytest), `eslint.config.js`, `.prettierrc`, `Makefile`(`help` 기본, `.PHONY`, `PORT ?= 8000`, `THUMB_MAX ?= 1200`, `FULL_MAX ?= 2400`, `QUALITY ?= 80`). 검증: `make help`, `make lint`가 빈 프로젝트에서 통과.
- [x] Step 2: `tools/build_images.py` — `originals/*.{jpg,jpeg,png,webp}` → `site/images/thumb|full/<id>.webp`(긴 변 THUMB_MAX/FULL_MAX, EXIF 방향 보정, 품질 QUALITY), 이미 최신이면 건너뜀. EXIF `DateTimeOriginal` → 없으면 파일 수정시각. 검증: pytest.
- [x] Step 3: `tools/build_manifest.py` — `site/images/full/*.webp`를 읽어 크기·orientation(`width > height` → landscape)·date로 `manifest.json` 생성. 기존 manifest의 `title`을 `id`로 이어받음. 최신순 정렬. 검증: pytest.
- [x] Step 4: `site/js/layout.js` — 순수 함수 6개. 검증: `node --test`.
- [x] Step 5: `site/index.html` + `site/css/styles.css` — 3차 시안 U1/U3/U4를 CSS 변수(`prefers-color-scheme`)와 미디어 쿼리(≤1025px 한 열)로 구현. SEO/OG 메타, `lang="ko"`. 사진 없이도 헤더·푸터가 정상 렌더. 검증: `tidy -q -e`, 브라우저 확인.
- [x] Step 6: `site/js/gallery.js` — manifest fetch → `<img width height loading="lazy">`(첫 4장은 eager) 렌더, hover 메타(`title · YYYY.MM`, title 없으면 날짜만), 전체 화면 뷰어(U2: 클릭/Esc 닫기, ←/→, 스와이프, 뷰어 열릴 때 `full` 이미지 로드), "무작위" 버튼(Fisher–Yates 셔플로 재배치). manifest 로드 실패 시 한 줄 안내 문구. 검증: `make server` 후 브라우저 수동 시나리오.
- [x] Step 7: `make verify` — manifest의 모든 경로가 실제 파일인지, `thumb`/`full` 짝이 맞는지 검사. 검증: 의도적으로 파일을 빼고 실패하는지 확인.
- [x] Step 8: `.github/workflows/pages.yml` — push(main) 시 `make lint test verify` 후 `site/`를 Pages로 배포. PR에서는 lint/test만. 검증: 첫 배포 후 `https://azit.ash84.io` 200.
- [x] Step 9: 문서 — README(사진 추가 절차: `originals/`에 넣기 → `make build` → 커밋), 열린 질문 결정 사항 반영.
- [ ] Step 10: 저장소 `ash84-io/azit.ash84.io` 생성·push(claude), Pages 소스를 "GitHub Actions"로 설정, DNS `azit` CNAME → `ash84-io.github.io`, 첫 사진들을 `originals/`에 넣기(사용자).

## 5. 테스트 계획

**단위 테스트:**

`tools/tests/test_build_images.py` (pytest, Pillow로 임시 이미지 생성)
- [x] 케이스 1: 4000×3000 JPG → thumb 긴 변 1200, full 긴 변 2400, 비율 유지, WebP로 저장
- [x] 케이스 2: 원본이 목표보다 작으면 확대하지 않음
- [x] 케이스 3: EXIF Orientation=6(90° 회전) 원본이 세로로 바로 저장됨
- [x] 케이스 4: EXIF `DateTimeOriginal` → `YYYY-MM-DD`; EXIF 없으면 파일 mtime
- [x] 케이스 5: 출력이 원본보다 최신이면 건너뜀(재실행 시 변환 0건)
- [x] 케이스 6: 지원하지 않는 확장자(.heic, .txt)는 무시하고 이름을 경고로 출력

`tools/tests/test_build_manifest.py`
- [x] 케이스 1: width>height → landscape, 그 외(정방형 포함) → portrait
- [x] 케이스 2: date 내림차순(최신 먼저), 같은 날짜는 id 오름차순
- [x] 케이스 3: 기존 manifest의 `title`이 같은 id에 보존되고, 사라진 사진은 제거됨
- [x] 케이스 4: `thumb`이 없는 `full`은 오류로 종료(exit code ≠ 0)
- [x] 케이스 5: 출력 JSON이 스키마(필수 키 8개, version=1)를 만족

`tests/js/layout.test.mjs` (node --test)
- [x] 케이스 1: `orientationOf(3000, 2000)` → `"landscape"`, `(2000, 3000)`·`(2000, 2000)` → `"portrait"`
- [x] 케이스 2: `shuffle(list, rng)` — 원소 집합 보존, 주입한 rng로 결정적, 원본 배열 불변
- [x] 케이스 3: `wrapIndex(-1, 5)` → 4, `wrapIndex(5, 5)` → 0
- [x] 케이스 4: `formatMonth("2026-09-14")` → `"2026.09"`, 빈 값 → `""`
- [x] 케이스 5: `metaText({title:"창가 책상", date:"2026-09-14"})` → `"창가 책상 · 2026.09"`, title 없음 → `"2026.09"`, 둘 다 없음 → `""`
- [x] 케이스 6: `sortNewestFirst` — 날짜 내림차순, 동일 날짜 id 오름차순, 입력 불변

**통합 테스트:**

- [x] 시나리오 1: `make build`(leica 사진 3장을 `originals/`에 임시 복사) → `make verify` 통과 → `make server` → `curl -I` 로 `/`, `/images/manifest.json`, thumb 1장, full 1장이 200
- [x] 시나리오 2 (브라우저 1920px, openchrome): nav pill·회색 한 줄·가로 50%/세로 25% 배치·hover 시 앰버 메타·사진 클릭 → 뷰어 → Esc 닫힘, ←/→ 순환
- [ ] 시나리오 3 (브라우저 390px, CSS 구현 완료·실기기 확인 대기): 한 열, 메뉴가 오른쪽 세로 정렬, 스와이프로 이전/다음
- [ ] 시나리오 4 (CSS 구현 완료·OS 다크 모드 확인 대기): OS 다크 모드에서 배경 `#1A1818`·글씨 `#F3F3F3`, 뷰어 배경도 다크
- [x] 시나리오 5: "무작위" 클릭 시 순서가 바뀌고 새로고침하면 최신순으로 돌아옴
- [x] 시나리오 6: manifest.json을 지운 상태에서 열면 빈 격자 대신 안내 문구 한 줄
- [ ] 시나리오 7 (Step 10 이후): GitHub Actions 배포 후 `https://azit.ash84.io` 200, `CNAME` 반영, Lighthouse 성능 90 이상(모바일)

## 6. 사이드 이펙트

- 기존 기능: `../leica`(gallery.ash84.io)는 건드리지 않음 — 해당 없음
- 하위 호환성: 신규 프로젝트 — 해당 없음
- 마이그레이션: 없음. leica 사진을 가져오지 않는다(주제가 다름). 검증용으로 잠깐 쓰더라도 커밋하지 않음
- 원본 사진은 git에 올리지 않으므로(`originals/` ignore) 원본 보관은 사용자 책임. 생성된 WebP와 manifest만 커밋 — CI는 재변환 없이 배포만 한다
- 서비스 워커 없음: leica와 달리 오프라인 캐시·"새 버전" 확인창이 없다(단순화, 의도된 차이)

## 7. 보안 검토

- OWASP Top 10: 사용자 입력·서버 로직·인증이 없는 정적 사이트. 해당 항목 — A05(보안 설정 오류): 디렉터리 목록 노출 없음(GitHub Pages), `robots.txt`만 제공. A08(무결성): Google Fonts CSS는 SRI를 붙일 수 없음 — 필요 시 폰트 self-host로 전환 가능(후속). manifest는 same-origin fetch만 사용, HTML에 넣는 값은 `textContent`/속성 설정으로만 처리(innerHTML에 문자열 결합 금지)
- 인증/인가 변경: 없음
- 민감 데이터: 없음. 단, EXIF는 WebP 재인코딩 시 제거되어 GPS 위치가 공개되지 않는다(Pillow `save`에 exif를 넘기지 않음) — 테스트 케이스로 확인
- PCI-DSS: 해당 없음
- 서드파티 스크립트: 기본 없음. GA 포함 여부는 열린 질문 2

## 결정 사항 (2026-09-23 사용자 확인)

1. 폴더·저장소 이름은 `azit.ash84.io`. 폴더 이름 변경은 구현 마지막에 `mv`로, 저장소는 `ash84-io` 조직 아래 `gh repo create ash84-io/azit.ash84.io --public` (사용자 지시로 AhnSeongHyun 개인 계정에서 변경)
2. Google Analytics는 v1에서 제외
3. 기본 정렬은 최신순 고정, "무작위" 버튼으로만 섞음
4. 다크 모드는 `prefers-color-scheme`만 따름, 토글 없음
5. nav는 `사진 · 무작위 | ash84.io`. "소개"는 v1 범위 밖
