#!/usr/bin/env python3
"""
마크다운 파일 -> 노션 페이지 본문 적재 (REST 직송).

왜 이게 필요한가:
  MCP 로 페이지 본문을 넣으면 모델이 한글을 토큰으로 재생성하는 경로를 타서
  받침이 4~12% 손상된다(2026-07 실측). 주제 노트 5종은 합계 39만 자라
  MCP 로 넣으면 1.6만~4.7만 자가 깨진다.
  이 스크립트는 python 이 파일을 읽어 Notion REST API 로 직송하므로
  모델이 텍스트를 만지지 않는다 -> 손상이 구조적으로 불가능.
  (DB 행에 대한 notion_sync.py 와 같은 원리, 대상이 페이지 본문일 뿐)

사용법:
  python3 notion_page.py plan                    # 무엇을 어디에 넣을지 보기만(변경 없음)
  python3 notion_page.py push <slug>             # 한 페이지 교체
  python3 notion_page.py push-all                # 전부 교체
  python3 notion_page.py verify <slug>           # 적재본 vs 로컬 대조

지원 문법: # h1 / ## h2 / ### h3 / - 불릿 / 1. 번호 / --- 구분선 / 문단
          인라인: [텍스트](url), **굵게**
"""
import json, os, re, sys, time, urllib.request, urllib.error

TOKEN = open(os.path.expanduser('~/.notion_token')).read().strip()
H = {"Authorization": "Bearer " + TOKEN, "Notion-Version": "2022-06-28",
     "Content-Type": "application/json"}
def _load_config():
    """페이지 매핑을 외부 JSON 에서 읽는다 (스크립트에 하드코딩하지 않는다).

    탐색 순서: --config <경로>  ->  환경변수 NOTION_PAGES  ->  ./notion_pages.json
    형식:
      {"pages": {"<slug>": {"page_id": "32자hex", "file": "상대경로.md"}},
       "append_only": ["<slug>", ...]}
    file 경로는 **설정 파일이 있는 디렉터리 기준**으로 해석한다.
    append_only 에 넣은 슬러그는 push(전체 삭제 후 재적재)가 거부된다 —
    사람이 내용을 채우는 페이지나 누적 페이지를 이렇게 보호한다.
    """
    argv, path = sys.argv, None
    if '--config' in argv:
        k = argv.index('--config')
        path = argv[k + 1]
        del argv[k:k + 2]                      # 이후 명령어 파싱에 방해되지 않게 제거
    elif os.environ.get('NOTION_PAGES'):
        path = os.environ['NOTION_PAGES']
    else:
        path = os.path.join(os.getcwd(), 'notion_pages.json')

    if not os.path.exists(path):
        sys.exit(
            "설정 파일이 없습니다: {}\n"
            "  프로젝트 디렉터리에 notion_pages.json 을 만들거나 --config 로 지정하세요.\n"
            "  예시:\n"
            '  {{\n'
            '    "pages": {{"note": {{"page_id": "0123...ef", "file": "note.md"}}}},\n'
            '    "append_only": []\n'
            '  }}'.format(path))

    cfg = json.load(open(path, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(path))
    pages = {k: (v['page_id'], v['file']) for k, v in cfg['pages'].items()}
    return base, pages, set(cfg.get('append_only', []))


BASE, PAGES, APPEND_ONLY = _load_config()

MAX_TEXT = 2000      # rich_text 요소 하나의 content 상한
MAX_BLOCKS = 100     # children 요청당 블록 상한


def api(method, url, body=None, retries=5):
    for attempt in range(retries):
        try:
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(url, data=data, headers=H, method=method)
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            if e.code == 429 or e.code >= 500:
                wait = 2 ** attempt
                print("    (HTTP {} - {}s 후 재시도)".format(e.code, wait))
                time.sleep(wait)
                continue
            raise RuntimeError("HTTP {}: {}".format(e.code, raw[:400]))
        except urllib.error.URLError:
            time.sleep(2 ** attempt)
    raise RuntimeError("재시도 소진")


# ---------- 마크다운 -> 노션 rich_text ----------

TOKEN_RE = re.compile(r'(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*)')


def rich(text):
    """인라인 마크다운을 rich_text 배열로. [텍스트](url) 과 **굵게** 지원."""
    out = []
    for part in TOKEN_RE.split(text):
        if not part:
            continue
        m = re.match(r'^\[([^\]]+)\]\(([^)]+)\)$', part)
        if m:
            label, url = m.group(1), m.group(2)
            # 라벨 안의 **굵게** 는 링크에선 무시(노션 링크는 단일 span)
            label = re.sub(r'\*\*([^*]+)\*\*', r'\1', label)
            out.append({"type": "text",
                        "text": {"content": label[:MAX_TEXT], "link": {"url": url}}})
            continue
        m = re.match(r'^\*\*([^*]+)\*\*$', part)
        if m:
            out.append({"type": "text", "text": {"content": m.group(1)[:MAX_TEXT]},
                        "annotations": {"bold": True}})
            continue
        # 일반 텍스트 - 2000자 초과 시 쪼갬
        s = part
        while s:
            out.append({"type": "text", "text": {"content": s[:MAX_TEXT]}})
            s = s[MAX_TEXT:]
    return out[:100]      # 블록당 rich_text 요소 상한


def md_to_blocks(md):
    """마크다운 전문 -> 노션 블록 리스트."""
    blocks = []
    for raw in md.split('\n'):
        s = raw.rstrip()
        if not s.strip():
            continue
        if re.match(r'^-{3,}$', s.strip()):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue
        m = re.match(r'^(#{1,3})\s+(.*)$', s)
        if m:
            lvl = len(m.group(1))
            key = {1: "heading_1", 2: "heading_2", 3: "heading_3"}[lvl]
            blocks.append({"object": "block", "type": key,
                           key: {"rich_text": rich(m.group(2))}})
            continue
        m = re.match(r'^\s*[-*]\s+\[([ xX])\]\s+(.*)$', s)
        if m:
            blocks.append({"object": "block", "type": "to_do",
                           "to_do": {"rich_text": rich(m.group(2)),
                                     "checked": m.group(1).lower() == 'x'}})
            continue
        m = re.match(r'^\s*[-*]\s+(.*)$', s)
        if m:
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": rich(m.group(1))}})
            continue
        m = re.match(r'^\s*\d+\.\s+(.*)$', s)
        if m:
            blocks.append({"object": "block", "type": "numbered_list_item",
                           "numbered_list_item": {"rich_text": rich(m.group(1))}})
            continue
        blocks.append({"object": "block", "type": "paragraph",
                       "paragraph": {"rich_text": rich(s)}})
    return blocks


# ---------- 페이지 조작 ----------

def clear_page(pid):
    """페이지의 기존 자식 블록 전부 삭제(=regenerate 를 위해)."""
    n = 0
    while True:
        r = api("GET", "https://api.notion.com/v1/blocks/{}/children?page_size=100".format(pid))
        ids = [b['id'] for b in r['results']]
        if not ids:
            break
        for bid in ids:
            api("DELETE", "https://api.notion.com/v1/blocks/{}".format(bid))
            n += 1
            time.sleep(0.34)
        if not r.get('has_more'):
            # 삭제 후에도 남아있을 수 있으니 한 번 더 확인
            r2 = api("GET", "https://api.notion.com/v1/blocks/{}/children?page_size=100".format(pid))
            if not r2['results']:
                break
    return n


def append(slug):
    """기존 내용을 지우지 않고 페이지 끝에 이어붙인다(누적 페이지용)."""
    pid, path = PAGES[slug]
    md = open(os.path.join(BASE, path)).read()
    blocks = md_to_blocks(md)
    print("[{}] {} -> 블록 {}개 추가(기존 유지)".format(slug, path, len(blocks)))
    for i in range(0, len(blocks), MAX_BLOCKS):
        batch = blocks[i:i + MAX_BLOCKS]
        api("PATCH", "https://api.notion.com/v1/blocks/{}/children".format(pid),
            {"children": batch})
        print("    {}/{}".format(min(i + MAX_BLOCKS, len(blocks)), len(blocks)))
        time.sleep(0.34)
    print("  완료")


def push(slug):
    if slug in APPEND_ONLY:
        raise RuntimeError(
            "'{}' 는 누적 페이지입니다. push(전체 삭제) 하면 과거 기록이 전부 사라집니다.\n"
            "  append 를 쓰세요: python3 notion_page.py append {}".format(slug, slug))
    pid, path = PAGES[slug]
    md = open(os.path.join(BASE, path)).read()
    blocks = md_to_blocks(md)
    print("[{}] {} -> 블록 {}개".format(slug, path, len(blocks)))
    print("  기존 블록 삭제 중...")
    d = clear_page(pid)
    print("  {}개 삭제".format(d))
    print("  적재 중...")
    for i in range(0, len(blocks), MAX_BLOCKS):
        batch = blocks[i:i + MAX_BLOCKS]
        api("PATCH", "https://api.notion.com/v1/blocks/{}/children".format(pid),
            {"children": batch})
        print("    {}/{}".format(min(i + MAX_BLOCKS, len(blocks)), len(blocks)))
        time.sleep(0.34)
    print("  완료")


def plaintext_of(pid):
    """페이지 본문을 평문으로 회수(검증용)."""
    out, cur = [], None
    while True:
        u = "https://api.notion.com/v1/blocks/{}/children?page_size=100".format(pid)
        if cur:
            u += "&start_cursor=" + cur
        r = api("GET", u)
        for b in r['results']:
            t = b.get('type')
            d = b.get(t) or {}
            for rt in (d.get('rich_text') or []):
                out.append(rt.get('plain_text', ''))
            out.append('\n')
        if not r.get('has_more'):
            break
        cur = r['next_cursor']
    return ''.join(out)


def verify(slug):
    pid, path = PAGES[slug]
    md = open(os.path.join(BASE, path)).read()
    got = plaintext_of(pid)

    # 로컬에서 마크다운 문법을 걷어낸 '표시될 텍스트'
    want = md
    want = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', want)   # 링크 -> 라벨
    want = re.sub(r'\*\*([^*]+)\*\*', r'\1', want)          # 굵게 해제
    # ★ 줄마다 접두사는 '하나만' 벗긴다. md_to_blocks 가 heading 을 먼저 매치하므로
    #   '## 1. 제목' 은 heading_2 의 본문 '1. 제목' 이 된다 — 여기서 '1. '까지 벗기면
    #   멀쩡한 노션 내용을 불일치로 오판한다(실측: 다이제스트 16자 오차의 원인).
    out = []
    for ln in want.split('\n'):
        if re.match(r'^-{3,}$', ln.strip()):
            continue
        m = re.match(r'^#{1,3}\s+(.*)$', ln)
        if m:
            out.append(m.group(1)); continue
        m = re.match(r'^\s*[-*]\s+\[[ xX]\]\s+(.*)$', ln)
        if m:
            out.append(m.group(1)); continue
        m = re.match(r'^\s*[-*]\s+(.*)$', ln)
        if m:
            out.append(m.group(1)); continue
        m = re.match(r'^\s*\d+\.\s+(.*)$', ln)
        if m:
            out.append(m.group(1)); continue
        out.append(ln)
    want = '\n'.join(out)

    norm = lambda s: re.sub(r'\s+', '', s)
    a, b = norm(want), norm(got)
    same = a == b
    print("[{}] 로컬 {:,}자 / 노션 {:,}자 -> {}".format(
        slug, len(a), len(b), "일치" if same else "불일치"))
    if not same:
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                print("  첫 불일치 @{}: 로컬 {!r} vs 노션 {!r}".format(i, a[i:i+30], b[i:i+30]))
                break
        else:
            print("  길이만 다름: {} vs {}".format(len(a), len(b)))
    # 링크 보존 확인
    want_links = set(re.findall(r'youtu\.be/([A-Za-z0-9_-]{8,})', md))
    print("  로컬 고유 링크 {}개".format(len(want_links)))
    return same


def plan():
    print("{:<10} {:>10} {:>8}  {}".format("slug", "자수", "블록", "page_id"))
    print("-" * 62)
    for slug, (pid, path) in PAGES.items():
        p = os.path.join(BASE, path)
        if not os.path.exists(p):
            print("{:<10} {:>10}  (파일 없음)".format(slug, "-"))
            continue
        md = open(p).read()
        print("{:<10} {:>10,} {:>8}  {}".format(slug, len(md), len(md_to_blocks(md)), pid))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        plan()
    elif cmd == "push":
        push(sys.argv[2])
    elif cmd == "append":
        append(sys.argv[2])
    elif cmd == "push-all":
        for s in PAGES:
            if s in APPEND_ONLY:
                print("[{}] 누적 페이지 — push-all 에서 건너뜀".format(s))
                continue
            if os.path.exists(os.path.join(BASE, PAGES[s][1])):
                push(s)
    elif cmd == "verify":
        verify(sys.argv[2])
    elif cmd == "verify-all":
        ok = all(verify(s) for s in PAGES if os.path.exists(os.path.join(BASE, PAGES[s][1])))
        print("\n전체: {}".format("일치" if ok else "불일치 있음"))
    else:
        print(__doc__)
