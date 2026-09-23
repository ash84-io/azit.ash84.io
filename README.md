# azit.ash84.io

아지트를 만드는 데 영감을 주는 사진들을 모아두는 정적 사진 갤러리. GitHub Pages로 배포한다.

- 디자인: https://udara.io/photos 방식 — 작은 고정 nav, 회색 한 줄 설명, 가로 사진 50% / 세로 사진 25%의 사진 흐름, hover 시 앰버색 모노 캡션, 클릭하면 전체 화면.
- 분류·태그 없음. 사진마다 `title`(선택)과 촬영일만 갖는다. 기본 정렬은 최신순, "무작위" 버튼으로만 섞는다.
- 라이트/다크는 OS 설정(`prefers-color-scheme`)을 따른다.

## 사진 추가하기

1. 원본(JPG/PNG/WebP)을 `originals/`에 넣는다. 이 폴더는 git에 올라가지 않는다.
2. `make build` — 썸네일(긴 변 1200px)과 뷰어용(2400px) WebP를 `site/images/{thumb,full}/`에 만들고, `site/images/manifest.json`을 다시 생성한 뒤 정합성을 검사한다. EXIF(GPS 포함)는 모두 제거되고 촬영일만 `site/images/sources.json`에 남는다.
3. 제목을 붙이고 싶으면 `manifest.json`의 `title`을 편집한다. 다시 `make build`를 해도 제목은 유지된다.
4. `make server`로 http://localhost:8000 에서 확인하고 커밋·push한다. `main`에 push되면 GitHub Actions가 검사 후 배포한다.

HEIC는 지원하지 않는다. 사진 앱에서 JPG로 내보내서 넣는다.

## 개발

```
make help          # 명령어 목록
make format        # prettier(html/css/js) + ruff format(python)
make lint          # format 후 eslint + ruff check + html-validate
make test          # pytest(tools/tests) + node --test(tests/js)
make build         # images → manifest → verify
make server        # 로컬 서버 (PORT=8000)
```

필요한 도구: `uv`, `node`(npx), Python 3.12. 나머지는 `uv run`/`npx`가 내려받는다.

```
site/                GitHub Pages로 배포되는 파일
  index.html · css/styles.css · js/gallery.js(렌더·뷰어) · js/layout.js(순수 함수)
  images/manifest.json · images/thumb/ · images/full/ · images/sources.json
tools/               build_images.py · build_manifest.py · verify_site.py (+ tests/)
tests/js/            layout.js 테스트
docs/                plan 문서
```

`manifest.json` 항목:

```json
{
  "id": "IMG_5751",
  "thumb": "images/thumb/IMG_5751.webp",
  "full": "images/full/IMG_5751.webp",
  "width": 1935,
  "height": 2400,
  "orientation": "portrait",
  "date": "2026-09-14",
  "title": ""
}
```

## 배포 설정 (1회)

- 저장소: https://github.com/ash84-io/azit.ash84.io — Settings → Pages → Source를 **GitHub Actions**로.
- DNS에 `azit` CNAME 레코드 → `ash84-io.github.io`. `site/CNAME`에 `azit.ash84.io`가 들어 있다.
