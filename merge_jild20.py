#!/usr/bin/env python3
"""Merge Jild 20 tashreeh chunks into jild-20.json.

Re-runnable: reads every jild-20-chunk-*.json listed in the manifest,
merges in chunk order, validates (unique ids, page coverage, no empty
jawab), writes jild-20.json, and updates the manifest statuses.

INPUT (verified on disk by the parent):
  12 chunk files (no splits), 272 chunk items, volume_id 44.
  Source export ~/workspace/fatawa-app/content/jild-20.json: 530 unique
  pages pp. 5-629. Gaps (95, nothing invented): pp. 9-94 (86), 178,
  212, 268, 270, 354, 453, 510, 580, 600 — every gap listed in each
  chunk's manifest missing_pages (Jild 17 lesson).

COMBINE RULES (6 cases; parts ordered by min page; sawal from the
FIRST part; jawab = all parts concatenated in page order; pages =
UNION of all parts' pages; notes = all parts' notes):
  masala 23:   chunk 01 [125-134] + chunk 02 [135-138] -> [125-138].
              Sawal from chunk 01 (1,071); jawab = 11,366 + 4,778.
  masala 83:   chunk 03 'jild20-83' [224-226] + chunk 04
              'jild20-masala-83' [227] -> ONE item 'jild20-masala-83',
              pages [224-227]. Sawal from chunk 03 (518);
              jawab = 1,860 + 847. (Chunk 03's ids are bare — do NOT
              normalise them; only this combine renames jild20-83.)
  masala 192:  chunk 06 [367-368] + chunk 07 [369] -> [367-369].
              Sawal from chunk 06 (449); jawab = 1,128 + 603.
  masala 203:  RISALA MEGA-COMBINE (13 parts -> 1). Chunk 07
              'jild20-masala-203' [382-418] (sawal 8,959, jawab
              22,053) + 12 chunk-08 parts, all with empty sawal:
              tanbih-15 [419-420] (2,105), tanbih-16 [421-422]
              (1,384), tanbih-17 [422-423] (2,240), tanbih-18
              [423-425] (1,478), tanbih-19 [425] (520), tanbih-20
              [425-428] (2,322), tanbih-21 [428-429] (1,473),
              tanbih-22 [429-430] (1,261), tanbih-23 [430-431]
              (1,249), tanbih-24 [431-432] (404), tanbih-25
              [432-433] (1,832), tadhyeel [433-435] (1,893) ->
              ONE item 'jild20-masala-203', pages [382-435].
              Sawal = chunk 07's; jawab = all 13 parts' jawabs
              concatenated in page order. (Risala ھادی الاضحیۃ,
              lesson 227, pp. 382-508: ONLY the masala-203 portion
              pp. 382-435 is one item. Masail 204-292, pp. 436-508,
              are separately numbered masail — NOT part of this
              combine.)
  masala 242:  chunk 08 [467-468] + chunk 09 [469-471] -> [467-471].
              Sawal from chunk 08 (193); jawab = 2,634 + 3,566.
              (Chunk 09 verified: 33 items, 40 pages [469-508]; no
              mas'ala continues into chunk 10 — masala-292 ends
              complete on p. 508 with «واﷲ تعالٰی اعلم»; p. 509
              opens رسالہ الصافیۃ with masala-293.)
  masala 293:  chunk 10 'jild20-masala-293' [509, 511-558] (sawal
              470, jawab 43,537) + chunk 11 'jild20-safia-tail'
              [559-561] (empty sawal, jawab 2,237) -> ONE item
              'jild20-masala-293', pages [509, 511-561]. Sawal from
              chunk 10; jawab concatenated. (Risala الصافیۃ الموحیۃ,
              lesson 228, pp. 509-579: masala-293 covers pp. 509-561
              only; masail 294-334, pp. 562-597, are separate items.
              Note p. 510 is a source gap — the combined pages skip
              it, as the chunk files do.)
After all 6 combines: 272 - 17 = 255 items covering 530 unique pages.

RENAMES: NONE to apply at merge — all 5 print-error renames were
ALREADY applied in the chunk files (do NOT re-apply, do NOT search
for the old ids):
  printed 448 (p. 477) -> 'jild20-masala-248' [477-478] (chunk 09)
  printed 174 (p. 349) -> 'jild20-masala-184' [349-350] (chunk 06)
  printed 335 (p. 459) -> 'jild20-masala-235' [459] (chunk 08)
  printed 337 (p. 460) -> 'jild20-masala-237' [460-461] (chunk 08)
  second printed 204 (p. 442) -> 'jild20-p442' [442] (chunk 08)

SORT: merged items are sorted by start_page for the final file.

DO-NOT-COMBINES: masala-153 (NO combine — chunk 06 has NO
masala-153 item; chunk 05's item pages stay [313-318]; do NOT create
a phantom half or extend its pages); masala-43 (NOT split — p. 174
tail ends it, p. 175 opens کتاب القسمۃ with masala-44); chunk 03
bare ids (do NOT globally normalise); no khatima item — the volume
ends at p. 629 with zamima entry 143 (ہمعات); the last two items are
'jild20-maakhiz' [598-622] and 'jild20-maakhiz-zamima' [623-629]
(bibliography, empty sawal by design). Risala سُبُل الاصفیاء
(lesson 224, pp. 269-341) is a SEQUENCE of separately numbered
masail 125-153 — no mega-combine. Shared pages by design: p. 442 in
both 'jild20-masala-204' [436-442] and 'jild20-p442' [442]; tanbih
sections share boundary pages (422, 423, 425, 428, 429, 430, 431,
432). Page union must still be exactly 530. PUA-garbled Quran
pages: 0 in Jild 20.

EMPTY FIELDS: ZERO empty jawabs among all 272 chunk items. After
merging, the only empty sawals are pesh-lafz, maakhiz and
maakhiz-zamima (by design; their notes explain).
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

# result id -> list of selectors, in page order.
# Selector forms:
#   ('id', sid)            — every item with this id (1 or 2 halves)
#   ('id_start', sid, sp)  — the item with this id starting at page sp
COMBINES = {
    'jild20-masala-23': [
        ('id', 'jild20-masala-23'),
    ],
    'jild20-masala-83': [
        ('id', 'jild20-83'),
        ('id', 'jild20-masala-83'),
    ],
    'jild20-masala-192': [
        ('id', 'jild20-masala-192'),
    ],
    'jild20-masala-203': [
        ('id', 'jild20-masala-203'),
        ('id', 'jild20-tanbih-15'),
        ('id', 'jild20-tanbih-16'),
        ('id', 'jild20-tanbih-17'),
        ('id', 'jild20-tanbih-18'),
        ('id', 'jild20-tanbih-19'),
        ('id', 'jild20-tanbih-20'),
        ('id', 'jild20-tanbih-21'),
        ('id', 'jild20-tanbih-22'),
        ('id', 'jild20-tanbih-23'),
        ('id', 'jild20-tanbih-24'),
        ('id', 'jild20-tanbih-25'),
        ('id', 'jild20-tadhyeel'),
    ],
    'jild20-masala-242': [
        ('id', 'jild20-masala-242'),
    ],
    'jild20-masala-293': [
        ('id', 'jild20-masala-293'),
        ('id', 'jild20-safia-tail'),
    ],
}

# Sawal handling per combined id (default: sawal from the first part).
# All 6 combines take the sawal from the first part, so no overrides.
SAWAL_RULES = {}

# No renames to apply at merge — all 5 were already applied in the
# chunk files (see module docstring). Kept empty deliberately.
RENAMES = {}

# Expected pages for every combined item (spot-check anchors).
EXPECTED_COMBINED_PAGES = {
    'jild20-masala-23': list(range(125, 139)),
    'jild20-masala-83': list(range(224, 228)),
    'jild20-masala-192': list(range(367, 370)),
    'jild20-masala-203': list(range(382, 436)),
    'jild20-masala-242': list(range(467, 472)),
    'jild20-masala-293': [509] + list(range(511, 562)),
}

# Expected sawal/jawab char counts for every combined item.
# masala-203 jawab: 22053 + (2105+1384+2240+1478+520+2322+1473+1261+1249+404+1832+1893=18161) = 40214
EXPECTED_COMBINED_TEXT = {
    'jild20-masala-23': (1071, 16144),
    'jild20-masala-83': (518, 2707),
    'jild20-masala-192': (449, 1731),
    'jild20-masala-203': (8959, 40214),
    'jild20-masala-242': (193, 6200),
    'jild20-masala-293': (470, 45774),
}

# The only ids that may be absorbed by a combine (must be gone after).
ABSORBED = ['jild20-tanbih-15', 'jild20-tanbih-16', 'jild20-tanbih-17',
            'jild20-tanbih-18', 'jild20-tanbih-19', 'jild20-tanbih-20',
            'jild20-tanbih-21', 'jild20-tanbih-22', 'jild20-tanbih-23',
            'jild20-tanbih-24', 'jild20-tanbih-25', 'jild20-tadhyeel',
            'jild20-safia-tail']

# The only items allowed to keep an empty sawal after merging.
EMPTY_SAWAL_ALLOWED = {'jild20-pesh-lafz', 'jild20-maakhiz',
                       'jild20-maakhiz-zamima'}

# Renamed ids (already applied in the chunk files) that must exist
# exactly once; the old printed ids must NOT exist anywhere.
RENAMED_PRESENT = {
    'jild20-masala-248': [477, 478],
    'jild20-masala-184': [349, 350],
    'jild20-masala-235': [459],
    'jild20-masala-237': [460, 461],
    'jild20-p442': [442],
}
OLD_IDS_ABSENT = ['jild20-masala-448', 'jild20-masala-174',
                  'jild20-masala-335', 'jild20-masala-337']


def combine_parts(result_id, parts):
    parts = sorted(parts, key=lambda it: min(it['pages']))
    first = parts[0]
    rule = SAWAL_RULES.get(result_id)
    if rule and rule[0] == 'concat':
        sawal = ''.join((parts[i].get('tashreeh_sawal', '') or '')
                        for i in rule[1])
    elif rule and rule[0] == 'from':
        sawal = parts[rule[1]].get('tashreeh_sawal', '') or ''
    else:
        sawal = first.get('tashreeh_sawal', '') or ''
    title = first.get('title') or ''
    combined = {
        'id': result_id,
        'title': title,
        'volume_id': 44,
        'pages': sorted(set().union(*[set(p['pages']) for p in parts])),
        'start_page': min(min(p['pages']) for p in parts),
        'tashreeh_sawal': sawal,
        'tashreeh_jawab': ''.join((p.get('tashreeh_jawab', '') or '') for p in parts),
        'notes': [n for p in parts for n in (p.get('notes') or [])],
    }
    return combined


def select_parts(all_items, selectors):
    """Resolve selectors to the matching items (each used at most once)."""
    parts = []
    used = set()
    for sel in selectors:
        if sel[0] == 'id':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and id(it) not in used]
        elif sel[0] == 'id_start':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and it['start_page'] == sel[2]
                    and id(it) not in used]
        else:
            raise ValueError(f'unknown selector {sel}')
        assert hits, f'no items matched selector {sel}'
        for it in hits:
            used.add(id(it))
        parts.extend(hits)
    return parts


def run_merge(manifest_path, base, write=False):
    manifest = json.load(open(manifest_path, encoding='utf-8'))
    all_items = []
    merged_chunks = []
    for entry in manifest['chunks']:
        nn = entry['chunk']
        if entry.get('status') == 'split-halves':
            print(f'chunk {nn}: split-halves placeholder — halves are separate entries, skipping')
            continue
        # A chunk may be one file ("file") or split halves ("files").
        file_list = entry.get('files') or [entry['file']]
        items = []
        for fname in file_list:
            path = os.path.join(base, fname)
            if not os.path.exists(path):
                print(f'chunk {nn}: {fname} not yet written')
                continue
            try:
                d = json.load(open(path, encoding='utf-8'))
            except json.JSONDecodeError as e:
                # File may still be streaming from its translator; skip it
                # for now instead of crashing the whole merge.
                print(f'chunk {nn}: {fname} not valid JSON yet ({e}) — skipping for now')
                continue
            items.extend(d['masail'])
        if not items:
            print(f'chunk {nn}: no items loaded — skipping')
            continue
        # Normalize: some translators omit start_page; derive it from pages.
        for it in items:
            if 'start_page' not in it:
                assert it.get('pages'), f'chunk {nn} item {it.get("id")} has no pages'
                it['start_page'] = it['pages'][0]
                print(f'chunk {nn}: derived start_page={it["start_page"]} for {it["id"]}')
            assert it['start_page'] == min(it['pages']), \
                f'chunk {nn} item {it["id"]}: start_page != first page'
            it['_src_file'] = file_list[0]
        all_items.extend(items)
        merged_chunks.append(nn)
        entry['status'] = 'merged'
        print(f'chunk {nn}: {len(items)} items merged')
    print(f'items before combines: {len(all_items)}')
    assert len(all_items) == 272, f'expected 272 chunk items, got {len(all_items)}'
    # COMBINE the 6 cases (one mas'ala split across chunks).
    for result_id, selectors in COMBINES.items():
        parts = select_parts(all_items, selectors)
        combined = combine_parts(result_id, parts)
        assert combined['pages'] == EXPECTED_COMBINED_PAGES[result_id], \
            f'{result_id}: pages {combined["pages"]} != expected {EXPECTED_COMBINED_PAGES[result_id]}'
        exp_sawal, exp_jawab = EXPECTED_COMBINED_TEXT[result_id]
        assert len(combined['tashreeh_sawal']) == exp_sawal, \
            f'{result_id}: sawal {len(combined["tashreeh_sawal"])} chars != expected {exp_sawal}'
        assert len(combined['tashreeh_jawab']) == exp_jawab, \
            f'{result_id}: jawab {len(combined["tashreeh_jawab"])} chars != expected {exp_jawab}'
        assert combined['tashreeh_jawab'], f'{result_id}: combined jawab is empty!'
        assert combined['tashreeh_sawal'], f'{result_id}: combined sawal is empty!'
        assert combined['start_page'] == min(combined['pages']), f'{result_id}: start_page != min(pages)'
        used_ids = set(id(p) for p in parts)
        all_items = [it for it in all_items if id(it) not in used_ids]
        all_items.append(combined)
        print(f'COMBINED {result_id}: {len(parts)} parts, pages {combined["pages"][0]}-{combined["pages"][-1]} '
              f'({len(combined["pages"])} pages), sawal {len(combined["tashreeh_sawal"])} chars, '
              f'jawab {len(combined["tashreeh_jawab"])} chars, notes {len(combined["notes"])}')
    # RENAMES: none to apply (all 5 were already applied in the chunks).
    for old_id, new_id in RENAMES.items():
        assert not any(it['id'] == new_id for it in all_items), \
            f'rename target {new_id} already exists!'
        hits = [it for it in all_items if it['id'] == old_id]
        assert len(hits) == 1, f'rename source {old_id}: expected exactly 1 item, found {len(hits)}'
        hits[0]['id'] = new_id
        print(f'RENAMED {old_id} -> {new_id} (pages {hits[0]["pages"][0]}-{hits[0]["pages"][-1]})')
    # Verify the already-applied renames are present exactly once.
    for rid, exp_pages in RENAMED_PRESENT.items():
        hits = [it for it in all_items if it['id'] == rid]
        assert len(hits) == 1, f'renamed id {rid}: expected exactly 1 item, found {len(hits)}'
        assert hits[0]['pages'] == exp_pages, f'{rid}: pages {hits[0]["pages"]} != {exp_pages}'
        print(f'RENAMED-ID PRESENT {rid}: pages {exp_pages}')
    for oid in OLD_IDS_ABSENT:
        assert not any(it['id'] == oid for it in all_items), \
            f'old printed id {oid} must not exist!'
    print(f'old printed ids absent: {OLD_IDS_ABSENT}')
    ids = [it['id'] for it in all_items]
    assert len(ids) == len(set(ids)), f'STILL DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}'
    empty = [it['id'] for it in all_items if not it.get('tashreeh_jawab')]
    assert not empty, f'EMPTY JAWAB: {empty}'
    empty_sawal = [it['id'] for it in all_items if not it.get('tashreeh_sawal')]
    assert set(empty_sawal) == EMPTY_SAWAL_ALLOWED, \
        f'EMPTY SAWAL mismatch: {sorted(empty_sawal)} != {sorted(EMPTY_SAWAL_ALLOWED)}'
    print(f'empty sawal (by design only): {sorted(empty_sawal)}')
    pages = set()
    for it in all_items:
        pages.update(it['pages'])
    # PRIMARY coverage check (Jild 17 lesson): validate against the 530
    # unique pages directly, not against a range-minus-gaps computation.
    assert len(pages) == 530, f'expected 530 unique pages, got {len(pages)}'
    assert min(pages) == 5 and max(pages) == 629, \
        f'page span {min(pages)}-{max(pages)} != 5-629'
    # Secondary cross-check: manifest ranges minus listed gap pages.
    expected = set()
    for entry in manifest['chunks']:
        if entry['chunk'] in merged_chunks:
            expected.update(range(entry['start_page'], entry['end_page'] + 1))
            expected.difference_update(entry['missing_pages'])
    missing_covered = expected - pages
    extra = pages - expected
    print(f'total items: {len(all_items)} | pages covered: {len(pages)} | expected (manifest): {len(expected)}')
    print(f'uncovered expected pages: {sorted(missing_covered)}')
    print(f'extra pages (outside merged chunks): {sorted(extra)}')
    assert not missing_covered, 'pages missing from merged chunks!'
    assert not extra, 'pages outside merged chunks!'
    assert len(all_items) == 255, f'expected 255 items after combines, got {len(all_items)}'
    # sort by start_page for the final file
    all_items.sort(key=lambda it: it['start_page'])
    for it in all_items:
        it.pop('_src_file', None)
    if write:
        with open(os.path.join(base, 'jild-20.json'), 'w', encoding='utf-8') as f:
            json.dump({'masail': all_items}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(base, 'chunks-manifest-jild20.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f'WROTE jild-20.json: {len(all_items)} items, {len(pages)} pages, chunks merged: {merged_chunks}')
    return all_items, pages, merged_chunks


def main():
    manifest_path = os.path.join(BASE, 'chunks-manifest-jild20.json')
    run_merge(manifest_path, BASE, write=True)


if __name__ == '__main__':
    main()
