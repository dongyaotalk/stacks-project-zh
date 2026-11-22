"""Optional locking of the witnessed continuation of one upstream enumerate list."""
import json

from .records import RecordError
from .source_reextractions import _git_bytes, byte_hash

SECTION = 'locked_enumerate_continuation'
CHAPTER = 'algebraization'
LABEL = 'algebraization-lemma-discussion'
TAG = '0EIY'
SOURCE_COMMIT = 'a04446e57ec1fbc252a871afcec7752fb2807b14'
CHAPTER_HASH = 'sha256:a1d15613e36799787f29497ada72268daaa4c3d8bef0f6457c4ca3e60c4262e9'
LEMMA_HASH = 'sha256:e01214d7891e9dd215be55435e8d9228f810261f76491a8e430e07e3daecd878'
LEMMA_SPAN = (218060, 219494)
COMMAND = r'\setcounter{enumi}{6}'
WINDOW = r'\begin{enumerate}' + '\n' + COMMAND + '\n' + r'\item Let '


def parse_policy(text):
    enabled = in_section = False
    fields = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line[0].isspace():
            in_section = line.partition(':')[0] == SECTION
            if in_section:
                if enabled or line != SECTION + ':':
                    raise RecordError('invalid or duplicate enumerate continuation section')
                enabled = True
            continue
        if in_section:
            key, separator, value = line[2:].partition(': ')
            if not line.startswith('  ') or not separator or key in fields or key not in {'source_label','literal'}:
                raise RecordError('invalid enumerate continuation field')
            try:
                fields[key] = json.loads(value)
            except json.JSONDecodeError as exc:
                raise RecordError('enumerate continuation expects exact JSON strings') from exc
    if enabled and fields != {'source_label': LABEL, 'literal': COMMAND}:
        raise RecordError('enumerate continuation requires the recorded lemma and complete literal')
    return enabled


def verify(policy_enabled, english):
    if not policy_enabled:
        return ''
    if english.commit != SOURCE_COMMIT or english.tags.get(LABEL) != TAG:
        raise RecordError('enumerate continuation requires the locked 0EIY source')
    raw = _git_bytes(english.harvest, english.commit, CHAPTER+'.tex')
    start, stop = LEMMA_SPAN
    lemma = raw[start:stop].decode()
    if (byte_hash(raw) != CHAPTER_HASH or byte_hash(lemma) != LEMMA_HASH
            or lemma.count(WINDOW)!=1 or raw.count(COMMAND.encode())!=1):
        raise RecordError('enumerate continuation differs from the recorded complete 0EIY source')
    return lemma


def token_end(text, start, stop, chapter, stack, witness):
    if not witness or chapter != CHAPTER or not stack or stack[-1] != 'enumerate':
        return None
    command_end = start + len(COMMAND)
    if command_end > stop or text[start:command_end] != COMMAND:
        return None
    opening = start - witness.index(COMMAND)
    if opening < 0 or text[opening:opening+len(witness)] != witness:
        return None
    return command_end
