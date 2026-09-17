from pathlib import Path
import json
import re
from pypdf import PdfReader

download_pdf = Path(r"C:\Users\IT\Downloads\Amategeko y'umuhanda (1).pdf")
pdf_path = download_pdf if download_pdf.exists() else next(Path('.').glob('*.pdf'))
reader = PdfReader(str(pdf_path))
pages = reader.pages
text = '\n'.join((page.extract_text() or '') for page in pages)
start_pattern = re.compile(r'(?<!\d)(?<![A-Za-z])(\d{1,3})\.(?!\d)')
choice_pattern = re.compile(r'^\s*((?:\([a-dA-D]\s*\))|(?:[a-dA-D][.)]))\s*(.*)$')

image_dir = Path('assets/signs/pdf')
image_dir.mkdir(parents=True, exist_ok=True)
page_image_map = {}
for page_number, page in enumerate(pages, start=1):
    if page_number < 39 or not page.images:
        continue
    page_text = page.extract_text() or ''
    page_ids = [int(match.group(1)) for match in start_pattern.finditer(page_text) if 1 <= int(match.group(1)) <= 433]
    first_question = start_pattern.search(page_text)
    prefix = page_text[:first_question.start()] if first_question else ''
    continuation_count = len(re.findall(r'(?:\([a-dA-D]\s*\))|(?:[a-dA-D][.)])', prefix))
    image_paths = []
    for image_number, image in enumerate(page.images, start=1):
        extension = Path(image.name).suffix.lower().lstrip('.') or 'png'
        image_path = image_dir / f'pdf-p{page_number:03d}-i{image_number:02d}.{extension}'
        image_path.write_bytes(image.data)
        image_paths.append(image_path.as_posix())
    page_image_map[page_number] = {'ids': page_ids, 'images': image_paths, 'continuation_count': continuation_count}

candidates = {}
matches = [match for match in start_pattern.finditer(text) if 1 <= int(match.group(1)) <= 433]
for index, match in enumerate(matches):
    question_id = int(match.group(1))
    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
    block = text[match.end():end]
    lines = [line.strip() for line in block.splitlines()]
    options = []
    question_lines = []
    current = None
    for line in lines:
        line = re.sub(r'^\d+\s+RESTRICTED\s*', '', line)
        line = re.sub(r'^RESTRICTED\s*', '', line)
        if not line or line.isdigit() or line == 'RESTRICTED':
            continue
        choice = choice_pattern.match(line)
        if choice:
            marker = choice.group(1).replace(' ', '')
            is_correct = marker.startswith('(') and marker.endswith(')')
            value = choice.group(2).strip()
            current = {'text': value, 'correct': is_correct}
            options.append(current)
        elif current is not None:
            current['text'] = (current['text'] + ' ' + line).strip()
        else:
            question_lines.append(line)
    question = re.sub(r'\s+', ' ', ' '.join(question_lines)).strip()
    options = [{'text': re.sub(r'\s+', ' ', option['text']).strip(), 'correct': option['correct']} for option in options[:4]]
    if not question or not options:
        continue
    while len(options) < 4:
        options.append({'text': '', 'correct': False})
    correct = next((index for index, option in enumerate(options) if option['correct']), None)
    if correct is None:
        continue
    item = {'id': question_id, 'question': question, 'options': [option['text'] for option in options], 'answer': correct}
    previous = candidates.get(question_id)
    if previous is None or len(item['question']) > len(previous['question']):
        candidates[question_id] = item

if 236 not in candidates:
    candidates[236] = {'id': 236, 'question': 'Nikihe cyapa cyerekena ko nta kinyabiziga gifite moteri cyemerewe kuhanyura?', 'options': ['a', 'b', 'c', 'd'], 'answer': 1}
if 249 not in candidates:
    candidates[249] = {'id': 249, 'question': 'Icyapa gitanga uburenganzira bwo gutambuka mbere kigira iyihe shusho?', 'options': ['a', 'b', 'c', 'd'], 'answer': 3}

known_ids = sorted(candidates)
for page_number, page_data in page_image_map.items():
    target_ids = [question_id for question_id in page_data['ids'] if question_id in candidates]
    if not target_ids:
        previous = [question_id for question_id in known_ids if question_id < max(page_data['ids'], default=433)]
        target_ids = [previous[-1]] if previous else known_ids[:1]
    image_index = 0
    if page_data['continuation_count']:
        first_id = min(page_data['ids'], default=433)
        previous = [question_id for question_id in known_ids if question_id < first_id]
        if previous:
            previous_item = candidates[previous[-1]]
            continued_images = page_data['images'][:page_data['continuation_count']]
            previous_item.setdefault('optionImages', []).extend(continued_images)
            image_index = len(continued_images)
    for question_id in target_ids:
        question_item = candidates[question_id]
        remaining = page_data['images'][image_index:]
        simple_options = all(not option or len(option) <= 3 for option in question_item['options'])
        remaining_questions = len(target_ids) - target_ids.index(question_id)
        if simple_options and remaining:
            if page_number == 43 and question_id in (229, 230):
                option_images = remaining[:1]
            elif page_number == 45 and question_id == 235:
                option_images = remaining[:4]
            elif page_number == 45 and question_id == 236:
                option_images = remaining[:2]
            else:
                option_images = remaining[:min(4, max(1, len(remaining) // remaining_questions))]
            question_item['optionImages'] = option_images
            image_index += len(option_images)
        elif remaining:
            question_item.setdefault('images', []).extend(remaining)
            image_index = len(page_data['images'])

pdf_layout_overrides = {
    224: {'options': ['a', 'b', 'c', 'd'], 'answer': 1, 'optionImages': ['assets/signs/pdf/pdf-p041-i01.png', 'assets/signs/pdf/pdf-p041-i02.jpg', 'assets/signs/pdf/pdf-p042-i01.jpg', 'assets/signs/pdf/pdf-p042-i02.jpg']},
    229: {'options': ['Umuvuduko ntarengwa 30 km/h', 'Iherezo ry’umuvuduko muke ntarengwa utegetswe', 'Umuvuduko uri hejuru ya 30 km/h', 'Nta gisubizo cy’ukuri'], 'answer': 1, 'optionImages': ['assets/signs/pdf/pdf-p042-i03.png']},
    230: {'optionImages': ['assets/signs/pdf/pdf-p043-i01.png', 'assets/signs/pdf/pdf-p043-i02.png']},
    235: {'options': ['a', 'b', 'c', 'd'], 'answer': 2, 'optionImages': ['assets/signs/pdf/pdf-p045-i01.png', 'assets/signs/pdf/pdf-p045-i02.png', 'assets/signs/pdf/pdf-p045-i03.png', 'assets/signs/pdf/pdf-p045-i04.png']},
    236: {'options': ['a', 'b', 'c', 'd'], 'answer': 1, 'optionImages': ['assets/signs/pdf/pdf-p045-i05.jpg', 'assets/signs/pdf/pdf-p045-i06.jpg', 'assets/signs/pdf/pdf-p046-i01.jpg', 'assets/signs/pdf/pdf-p046-i02.jpg']},
    266: {'options': ['a', 'b', 'c', 'd'], 'answer': 1, 'optionImages': ['assets/signs/pdf/pdf-p055-i01.jpg', 'assets/signs/pdf/pdf-p055-i02.png', 'assets/signs/pdf/pdf-p056-i01.jpg', 'assets/signs/pdf/pdf-p056-i02.png']},
    303: {'options': ['Itonde , witegereze ni biba ngongwa ubaburire unitegura kuba wahagarara.', 'Ihute urenge aho abo bana bari', 'Komeza ugume ku muvuduko munini', 'Komeza ugendere kuruhande rw’iburyo'], 'answer': 0, 'images': ['assets/signs/pdf/pdf-p068-i01.jpg'], 'optionImages': []},
    287: {'images': ['assets/signs/pdf/pdf-p065-i01.jpg', 'assets/signs/pdf/pdf-p065-i02.jpg'], 'optionImages': []},
    248: {'images': [], 'optionImages': []},
    249: {'options': ['a', 'b', 'c', 'd'], 'answer': 3, 'optionImages': ['assets/signs/pdf/pdf-p050-i01.png', 'assets/signs/pdf/pdf-p050-i02.png', 'assets/signs/pdf/pdf-p050-i03.jpg', 'assets/signs/pdf/pdf-p050-i04.jpg']},
    250: {'images': ['assets/signs/pdf/pdf-p050-i05.png', 'assets/signs/pdf/pdf-p050-i06.jpg'], 'optionImages': []},
    251: {'images': ['assets/signs/pdf/pdf-p051-i01.jpg', 'assets/signs/pdf/pdf-p051-i02.jpg', 'assets/signs/pdf/pdf-p051-i03.png'], 'optionImages': []},
    275: {'images': ['assets/signs/pdf/pdf-p059-i03.jpg'], 'optionImages': []},
    276: {'images': ['assets/signs/pdf/pdf-p060-i01.png'], 'optionImages': []},
    273: {'optionImages': ['assets/signs/pdf/pdf-p059-i01.jpg', 'assets/signs/pdf/pdf-p059-i02.png']},
}
for question_id, override in pdf_layout_overrides.items():
    if question_id in candidates:
        candidates[question_id].update(override)

duplicate_cleanup = {
    219: ['assets/signs/pdf/pdf-p041-i01.png', 'assets/signs/pdf/pdf-p041-i02.jpg'],
    227: ['assets/signs/pdf/pdf-p042-i03.png'],
    262: ['assets/signs/pdf/pdf-p055-i01.jpg', 'assets/signs/pdf/pdf-p055-i02.png'],
    300: ['assets/signs/pdf/pdf-p068-i01.jpg'],
}
for question_id, image_paths in duplicate_cleanup.items():
    question = candidates.get(question_id)
    if question:
        question['images'] = [image for image in question.get('images', []) if image not in image_paths]
        question['optionImages'] = [image for image in question.get('optionImages', []) if image not in image_paths]
        if not question['images']:
            question.pop('images', None)
        if not question['optionImages']:
            question.pop('optionImages', None)

questions = [candidates[question_id] for question_id in sorted(candidates)]
Path('questions.js').write_text('window.pdfQuestions = ' + json.dumps(questions, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print(f'generated {len(questions)} questions; first={questions[0]["id"]}; last={questions[-1]["id"]}')
print('missing ids:', sorted(set(range(1, 434)) - set(candidates)))
