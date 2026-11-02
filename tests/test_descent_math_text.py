"""Independent literal frames and synthetic Git; no real model output."""
import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture, selector, git
from test_group_derivations import fixture as history_fixture, read, write
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import (find_slots, validate_regions, validate_translation,
                                complete_math_nodes)
from stacks_zh.records import RecordError, stamp_unit_hashes, term_display_text, sha256_value, write_jsonl
from stacks_zh.schema_validation import validate_named_schema, validate_repository_schemas
from stacks_zh.source_containers import Containers, lower_container, load_source_containers
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import source_projection, source_inventory, validate_source_terms
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.workflow import render_batch

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
BASE = re.sub(r'(?ms)^locked_math_text_notations:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', '', BASE)

CHAIN = r"""\begin{align*}
\mathcal{F}\text{ finite locally free in fppf topology}
& \Leftrightarrow
\mathcal{H}\text{ finite locally free on }S \\
& \Leftrightarrow
\mathcal{F}\text{ finite locally free in \'etale topology} \\
& \Leftrightarrow
\mathcal{H}\text{ finite locally free on }S \\
& \Leftrightarrow
\mathcal{F}\text{ finite locally free in Zariski topology}
\end{align*}"""
DATA = r"""$$
\begin{matrix}
\text{category of descent data } \\
\text{relative to the family } \{X_i \to S\}_{i \in I}
\end{matrix}
\longrightarrow
\begin{matrix}
\text{ category of descent data} \\
\text{ relative to } X/S
\end{matrix}
$$"""
ARROW = r"""$$
\text{descent data relative to }
\mathcal{V}
\longrightarrow
\text{descent data relative to }
\mathcal{U}
$$"""
SETS = r"""$$
\left\{
\begin{matrix}
\text{descent data }(X_i, \varphi_{ii'})\text{ such that}\\
\text{each }X_i \in \Ob((\Sch/S)_\tau)
\end{matrix}
\right\}
\leftrightarrow
\left\{
\begin{matrix}
\text{sheaves }F\text{ on }(\Sch/S)_\tau\text{ such that}\\
\text{each }h_{S_i} \times F\text{ is representable}
\end{matrix}
\right\}.
$$"""
REFERENCES = r"""$$
\xymatrix{
DD(Y/S) \ar[r] & DD(X/S) \\
DD(\mathcal{V}) \ar[u]^{\text{Lemma }\ref{lemma-family-is-one}} \ar[r] &
DD(\mathcal{U}) \ar[u]_{\text{Lemma }\ref{lemma-family-is-one}}
}
$$"""
PROJ = r"""$$
r_{\mathcal{L}, \psi} : X \longrightarrow \underline{\text{Proj}}_S(\mathcal{A})
$$"""
PROJECTIONS = [
    r"$\text{pr} : Y \times_Z Y \to Y$",
    r"$\text{pr}|_{\Delta(Y)} : \Delta(Y) \to Y$",
    r"$\text{pr}|_{Y'} : Y' \to Y$",
    r"$\text{pr} \circ f_Y$",
    r"""$$
\xymatrix{
X \times_Z Y \ar[d] \ar[r]_{f_Y} &
Y \times_Z Y \ar[d] \ar[r]_-{\text{pr}} &
Y \ar[d] \\
X \ar[r]^f &
Y \ar[r]^g &
Z
}
$$""",
    r"""$$
\xymatrix{
X \amalg X' \ar@{=}[d] \ar[r]_-{f \amalg f'} &
\Delta(Y) \amalg Y' \ar@{=}[d] \ar[r] &
Y \ar@{=}[d] \\
X \times_Z Y \ar[r]^{f_Y} &
Y \times_Z Y \ar[r]^-{\text{pr}} &
Y
}
$$""",
]
LITERALS = [
    (' finite locally free in fppf topology', 'descent-finite-free-chain'),
    (' finite locally free on ', 'descent-finite-free-chain'),
    (' finite locally free in Zariski topology', 'descent-finite-free-chain'),
    ('category of descent data ', 'descent-data-matrices'),
    ('relative to the family ', 'descent-data-matrices'),
    (' category of descent data', 'descent-data-matrices'),
    (' relative to ', 'descent-data-matrices'),
    ('descent data ', 'descent-sheaf-set-matrices'),
    (' such that', 'descent-sheaf-set-matrices'),
    ('each ', 'descent-sheaf-set-matrices'),
    ('sheaves ', 'descent-sheaf-set-matrices'),
    (' on ', 'descent-sheaf-set-matrices'),
    (' is representable', 'descent-sheaf-set-matrices'),
    ('Lemma ', 'descent-lemma-reference'),
    ('descent data relative to ', 'descent-data-arrow'),
]


def policy_text():
    text = BASE + '''
locked_math_text_notations:
  pr:
    commands: ["text"]
    usages: ["subscripted"]
    source_label: test-lemma-one
  Proj:
    commands: ["text"]
    usages: ["descent-relative-proj"]
    source_label: test-lemma-one
locked_math_text_contexts:
  finite-projection:
    base_notation: "pr"
    commands: ["text"]
    usages: ["descent-projection"]
    source_label: "test-lemma-one"
translatable_math_text:
'''
    for index, (literal, role) in enumerate(LITERALS):
        text += (f'  source-{index}:\n    literal: {json.dumps(literal)}\n'
                 f'    command: "text"\n    usage: "{role}"\n'
                 '    source_label: "test-lemma-one"\n'
                 '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text + r'''
translatable_math_text_components:
  accented-topology:
    literal: " finite locally free in \\'etale topology"
    command: "text"
    usage: "descent-etale-component"
    components: [" finite locally free in ", "tale topology"]
    separator: "\\'e"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''


PROOF = '\\begin{proof}\nCafé δ.\n' + '\n'.join([CHAIN, DATA, ARROW, SETS, REFERENCES, PROJ] + PROJECTIONS) + '\n\\end{proof}'


def fixture(base, *, policy=None, proof=PROOF):
    root, harvest, _ = english_fixture(base, proof=proof)
    (root/'config/macro-policy.yml').write_text(policy or policy_text())
    native = Containers(root, harvest)
    selected = native.select(selector())
    unit = lower_container(selected, native.policy)[0]
    return root, harvest, native, selected, unit


def synthetic_fields(unit):
    # Literal synthetic translations, not outputs claimed from a model.
    if not unit.get('math_text_regions'):
        tokens = re.findall(r'<[A-Z][A-Z0-9]*_[0-9]{4}>', unit['source_text'])
        tail = re.search(r'\s*$', unit['source_text']).group()
        return dict(translation=''.join(tokens)+'合成测试。'+tail, allowed_english=[],
                    term_occurrences=[], unknown_terms=[], term_status='CLEAR',
                    notes=['Literal synthetic fixture; no actual model generation.'])
    mapping = {
        ' finite locally free in fppf topology': ' 在合成拓扑中有限局部自由',
        ' finite locally free on ': ' 有限局部自由于 ',
        ' finite locally free in Zariski topology': ' 在合成拓扑中有限局部自由',
        ' finite locally free in ': ' 有限局部自由于平展（',
        'tale topology': 'tale）拓扑',
        'category of descent data ': '下降数据的范畴 ',
        'relative to the family ': '相对于族 ',
        ' category of descent data': ' 下降数据的范畴',
        ' relative to ': ' 相对于 ',
        'descent data ': '下降数据 ', ' such that': ' 满足', 'each ': '每个 ',
        'descent data relative to ': '下降数据相对于 ',
        'sheaves ': '层 ', ' on ': ' 在 ', ' is representable': ' 可表', 'Lemma ': '引理 ',
    }
    text = unit['source_text']
    for source, target in sorted(mapping.items(), key=lambda item: -len(item[0])):
        text = text.replace(source, target)
    text = text.replace('Café δ.', '合成测试。')
    terms = ([dict(source_term='étale', target_term='平展')]
             if unit.get('schema_version') == 3 else [])
    return dict(translation=text, allowed_english=[], term_occurrences=terms,
                unknown_terms=[dict(**term, context='Synthetic pending term, never approved.') for term in terms],
                term_status='DECISION_REQUIRED' if terms else 'CLEAR',
                notes=['Literal synthetic fixture; no actual model generation or approval.'])


class DescentMathTextTests(unittest.TestCase):
    def test_root_condition_module_literal_has_one_exact_exception(self):
        math = r"""$$
\mathcal{F}\text{ has }\mathcal{P}
\Leftrightarrow
\mathcal{F}^a\text{ has }\mathcal{P}\text{ as an }\mathcal{O}\text{-module}
$$"""
        text = BASE+'\ntranslatable_math_text:\n'
        for i, (literal, role) in enumerate([(' has ', 'root-phrase'),
                                             (' as an ', 'root-phrase'), ('-module', 'root-condition')]):
            text += (f'  module-{i}:\n    literal: {json.dumps(literal)}\n    command: "text"\n'
                     f'    usage: "{role}"\n    source_label: "test-lemma-one"\n'
                     '    witness_kind: "proof"\n    witness_ordinal: 1\n')
        rules = Policy(text).math_text_rules
        self.assertEqual([s['value'] for s in find_slots(math, rules)], [' has ', ' has ', ' as an ', '-module'])
        for other in ['-Module', '-modules', '-isomorphism', ' -module', '-other']:
            with self.subTest(other=other), self.assertRaises(RecordError):
                Policy(text.replace('literal: "-module"', 'literal: '+json.dumps(other)))
        for source in [r'$x\text{-module}y$', r'$x^{\text{-module}}$', r'$\unknown x\text{-module}$']:
            self.assertEqual(find_slots(source, rules), [])
        with tempfile.TemporaryDirectory() as tmp:
            proof = '\\begin{proof}\n'+math+'\n\\end{proof}'
            _, _, _, _, unit = fixture(Path(tmp), policy=text, proof=proof)
            self.assertEqual(unit['schema_version'], 2)
            self.assertEqual(source_tex(unit), proof)
            self.assertEqual(validate_regions(unit), [])
            translated = unit['source_text'].replace(' has ', ' 具有 ').replace(' as an ', ' 作为 ').replace('-module', '-模（module）')
            self.assertEqual(validate_translation(unit, translated), [])

    def test_complete_frames_have_independent_literal_leaf_counts(self):
        rules = Policy(policy_text()).math_text_rules
        self.assertEqual([s['value'] for s in find_slots(CHAIN, rules)],
            [' finite locally free in fppf topology', ' finite locally free on ',
             ' finite locally free in ', 'tale topology', ' finite locally free on ',
             ' finite locally free in Zariski topology'])
        self.assertEqual([s['value'] for s in find_slots(DATA, rules)],
            ['category of descent data ', 'relative to the family ',
             ' category of descent data', ' relative to '])
        self.assertEqual([s['value'] for s in find_slots(SETS, rules)],
            ['descent data ', ' such that', 'each ', 'sheaves ', ' on ',
             ' such that', 'each ', ' is representable'])
        self.assertEqual([s['value'] for s in find_slots(REFERENCES, rules)], ['Lemma ', 'Lemma '])
        self.assertEqual([s['value'] for s in find_slots(ARROW, rules)], ['descent data relative to ']*2)

    def test_data_arrow_needs_its_whole_frame_without_relaxing_root_phrase(self):
        rules = Policy(policy_text()).math_text_rules
        for source in [ARROW.replace(r'\longrightarrow', r'\longleftarrow'),
                       ARROW.replace(r'\mathcal{V}', r'\mathcal{W}'),
                       ARROW.replace(r'\mathcal{U}', r'\mathcal{T}'),
                       ARROW.replace('$$\n', '$$\n% hidden\n', 1),
                       r'$\text{descent data relative to }\mathcal{V}$']:
            self.assertEqual(find_slots(source, rules), [])
        text = policy_text().replace('usage: "descent-data-arrow"', 'usage: "root-phrase"')
        self.assertEqual([s['value'] for s in find_slots(ARROW, Policy(text).math_text_rules)],
                         ['descent data relative to '])

    def test_wrong_complete_frames_positions_commands_objects_and_gaps_reject(self):
        rules = Policy(policy_text()).math_text_rules
        cases = [CHAIN.replace(r'\Leftrightarrow', r'\Rightarrow', 1),
                 CHAIN.replace(r'\mathcal{H}', r'\mathcal{G}', 1),
                 CHAIN.replace(r"\'e", 'é'), CHAIN.replace('S \\\\', 'S& \\\\', 1),
                 DATA.replace(r'\longrightarrow', r'\longleftarrow'),
                 DATA.replace(r'\{X_i', r'\{Y_i'), DATA.replace('X/S', 'Y/S'),
                 SETS.replace(r'\Ob', r'\unknown'), SETS.replace(r'\varphi', r'\psi'),
                 SETS.replace(r'\times F', r'\times G'),
                 REFERENCES.replace(r'\ref{lemma-family-is-one}', r'\ref{other}'),
                 REFERENCES.replace(r'\ar[u]_', r'\ar[d]_'),
                 DATA.replace(r'\text{relative', r'\textit{relative'),
                 DATA.replace('$$\n', '$$\n% hidden\n', 1),
                 DATA.replace('$$\n', '$$\n\\unknown ', 1),
                 '$x^{'+DATA[2:-2]+'}$', '$\\verb|'+DATA[2:-2]+'|$',
                 DATA.replace('$$\n', '$$\n ', 1),
                 r'$\text{each }X_i \in \Ob((\Sch/S)_\tau)$',
                 r'$\text{Lemma }\ref{lemma-family-is-one}$',
                 r'$\begin{matrix}\text{relative to the family }X\end{matrix}$']
        for source in cases:
            with self.subTest(source=source):
                try: slots = find_slots(source, rules)
                except ValueError: slots = []
                self.assertEqual(slots, [])

    def test_exact_literals_fonts_and_component_contract_are_not_inferred(self):
        rules = Policy(policy_text()).math_text_rules
        for source in [DATA.replace('relative to the family ', 'Relative to the family '),
                       DATA.replace('relative to the family ', 'relative to the family'),
                       CHAIN.replace(r"\'etale", r"\'{e}tale"),
                       CHAIN.replace(r"\'etale", r"\`etale"),
                       CHAIN.replace(r'\text{ finite locally free in fppf topology}',
                                     r'\text{\text{ finite locally free in fppf topology}}')]:
            self.assertLess(len(find_slots(source, rules)),
                            6 if 'align*' in source else 4)
        for before, after in [
            ('usage: "descent-etale-component"', 'usage: "indexed-component-description"'),
            ('separator: "\\\\\'e"', 'separator: " "'),
            ('components: [" finite locally free in ", "tale topology"]', 'components: ["other", "tale topology"]')]:
            with self.subTest(after=after), self.assertRaises(RecordError):
                Policy(policy_text().replace(before, after))

    def test_same_each_literal_needs_its_separate_context(self):
        text = policy_text()
        text = text.replace('literal: "each "\n    command: "text"\n    usage: "descent-sheaf-set-matrices"',
                            'literal: "each "\n    command: "text"\n    usage: "root-phrase"')
        self.assertEqual(len(find_slots(SETS, Policy(text).math_text_rules)), 6)
        text += '''
translatable_math_text_contexts:
  each-in-descent-sets:
    base_rule: "source-9"
    usage: "descent-sheaf-set-matrices"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''
        self.assertEqual(len(find_slots(SETS, Policy(text).math_text_rules)), 8)
        with self.assertRaises(RecordError): Policy(text.replace('base_rule: "source-9"', 'base_rule: "source-8"'))

    def test_finite_notations_cover_declarations_restrictions_composition_and_arrows(self):
        policy = Policy(policy_text())
        for source, role in [(PROJ, 'descent-relative-proj')] + [(p, 'descent-projection') for p in PROJECTIONS]:
            with self.subTest(source=source):
                scanner = Scanner(source, policy)
                text, placeholders, diagnostics = scanner.protect(0, len(source))
                self.assertEqual(diagnostics, [])
                self.assertEqual(text, '<MATH_0001>')
                self.assertEqual(placeholders, {'MATH_0001': source})
                self.assertEqual([c['usage'] for c in scanner.math_text_classifications], [role])

    def test_notation_context_is_opt_in_and_old_negative_projection_shapes_stay_blocked(self):
        policy = Policy(policy_text())
        legacy = Policy(policy_text().split('locked_math_text_contexts:')[0])
        for source in PROJECTIONS:
            scanner = Scanner(source, legacy)
            self.assertTrue(scanner.protect(0, len(source))[2])
        for source in [r'$\text{pr}$', r'$\text{pr} : A \to B$', r'$\text{pr}^*$',
                       PROJECTIONS[0].replace('Y', 'X'), PROJECTIONS[3].replace('f_Y', 'f_X'),
                       PROJECTIONS[4].replace(r'\ar[r]_-', r'\ar[l]_-'),
                       PROJ.replace(r'\underline', r'\unknown'),
                       PROJ.replace(r'\text{Proj}', r'\textit{Proj}'),
                       PROJ.replace('_S', '_T')]:
            scanner = Scanner(source, policy)
            self.assertTrue(scanner.protect(0, len(source))[2], source)
        for before, after in [('usages: ["descent-projection"]', 'usages: ["descent-projection", "starred-subscripted"]'),
                              ('usages: ["descent-relative-proj"]', 'usages: ["descent-relative-proj", "symbol"]')]:
            with self.assertRaises(RecordError): Policy(policy_text().replace(before, after))

    def test_locked_git_lowering_schema_utf8_replay_and_math_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, native, _, unit = fixture(Path(tmp))
            self.assertEqual(unit['schema_version'], 3)
            self.assertEqual(validate_named_schema(unit, 'unit.schema.json', 'synthetic'), [])
            self.assertEqual(validate_regions(unit), [])
            self.assertEqual(source_tex(unit), PROOF)
            self.assertEqual(complete_math_nodes(unit), [CHAIN, DATA, ARROW, SETS, REFERENCES, PROJ] + PROJECTIONS)
            self.assertEqual([len(r['slots']) for r in unit['math_text_regions']], [6, 4, 2, 8, 2])
            region = unit['math_text_regions'][0]
            self.assertEqual(unit['placeholders'][region['pieces'][6]['placeholder']], r"\'e")
            for slot in region['slots']:
                span = slot['slot_byte_span']
                self.assertEqual(region['source'].encode()[span['start']:span['end']], slot['source'].encode())
            self.assertTrue(native.policy.math_text_witnesses)
            translated = synthetic_fields(unit)['translation']
            self.assertEqual(validate_translation(unit, translated), [])
            self.assertIn('平展（étale）', term_display_text(translated, unit['placeholders'], unit=unit))

    def test_ordinary_v2_frames_have_no_component_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = policy_text().split('translatable_math_text_components:')[0]
            # Drop unused chain rules so every synthetic source witness is real.
            text = re.sub(r'(?ms)^  source-[012]:\n.*?(?=^  source-|\Z)', '', text)
            proof = PROOF.replace(CHAIN+'\n', '')
            _, _, _, _, unit = fixture(Path(tmp), policy=text, proof=proof)
            self.assertEqual(unit['schema_version'], 2)
            self.assertEqual(validate_named_schema(unit, 'unit.schema.json', 'synthetic-v2'), [])
            self.assertEqual(validate_regions(unit), [])
            self.assertEqual(validate_translation(unit, synthetic_fields(unit)['translation']), [])
            self.assertEqual(source_tex(unit), proof)

    def test_unregistered_neighbor_stays_blocked_despite_other_valid_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, native, _, _ = fixture(Path(tmp))
            source = SETS.replace('sheaves ', 'unregistered prose ', 1)
            scanner = Scanner(source, native.policy)
            _, _, diagnostics = scanner.protect(0, len(source))
            self.assertEqual([d['source'] for d in diagnostics], ['unregistered prose '])
            self.assertEqual(len(scanner.math_text_regions[0]['slots']), 7)

    def test_accent_and_all_natural_leaves_remain_visible_to_term_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            projected, _ = source_projection(unit)
            self.assertIn('étale topology', projected)
            self.assertIn('descent data', projected)
            catalog = dict(terms=[dict(id='etale', forms=['étale'], chapters=[], evidence=[])],
                           nonmathematical_declarations={})
            self.assertEqual([o['source_term'] for o in source_inventory(unit, catalog)['occurrences']], ['étale'])
            candidate = synthetic_fields(unit)
            self.assertEqual(validate_source_terms(unit, candidate, catalog), [])
            candidate['term_occurrences'] = []
            self.assertTrue(validate_source_terms(unit, candidate, catalog))
            candidate = synthetic_fields(unit)
            candidate['translation'] = candidate['translation'].replace('平展（', '别称（')
            self.assertTrue(validate_source_terms(unit, candidate, catalog))
            # Without a verified unit no generic math token becomes visible.
            self.assertEqual(term_display_text('<MATHSEG_0001>tale', {'MATHSEG_0001': r"\'e"}), '<MATHSEG_0001>tale')

    def test_tampered_schema_source_components_tokens_and_injection_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, original = fixture(Path(tmp))
            for fault in ['version', 'separator', 'parent', 'ordinal', 'span', 'role', 'math', 'missing']:
                unit = copy.deepcopy(original)
                region = unit['math_text_regions'][0]
                slot = region['slots'][2]
                component = slot['parameter_components']
                if fault == 'version': unit['schema_version'] = 2
                if fault == 'separator': component['separator'] = r'\ '
                if fault == 'parent': component['parameter_source'] = 'other'
                if fault == 'ordinal': component['component_index'] = 2
                if fault == 'span': component['parameter_byte_span']['start'] += 1
                if fault == 'role': slot['classification_witness']['usage'] = 'indexed-component-description'
                if fault == 'math': unit['placeholders'][region['pieces'][0]['placeholder']] += 'x'
                if fault == 'missing': region['slots'].pop(3)
                try: unit = stamp_unit_hashes(unit)
                except (KeyError, IndexError): pass
                self.assertTrue(validate_regions(unit), fault)
            translated = synthetic_fields(original)['translation']
            for value in ['', r'\alpha', 'a%b', 'a\nb', '<MATHSEG_9999>']:
                self.assertTrue(validate_translation(original, translated.replace(' 有限局部自由于平展（', value)))

    def test_false_owner_wrong_proof_and_fake_label_cannot_authorize_a_source(self):
        for before, after in [('"test-lemma-one"', '"test-lemma-two"'),
                              ('witness_ordinal: 1', 'witness_ordinal: 2'),
                              ('witness_kind: "proof"', 'witness_kind: "lemma"')]:
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RecordError):
                fixture(Path(tmp), policy=policy_text().replace(before, after))

    def test_two_complete_history_generations_replay_and_render_all_four_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), count=2, proof=PROOF,
                math_policy=policy_text(), synthetic_fields=synthetic_fields)
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            current = records[-1]
            paths = render_batch(root/current['files']['output_units']['path'],
                root/current['files']['output_candidates']['path'], root/'upstream.lock',
                root/'preview', 'fixture', 'Synthetic fixture', chapter_source_dir=harvest)
            text = ''.join(path.read_text() for path in paths)
            self.assertIn(r"平展（\'etale）拓扑", text)
            self.assertIn(r'\text{引理 }\ref', text)
            self.assertNotIn('MATHSEG_', text)
            evidence = root/'translation-data/source-container-restorations/fixture-group-2-proof.json'
            value = read(evidence)
            value['tool']['version'] = 'source-container-v13'
            write(evidence, value)
            self.assertTrue(load_source_containers(root, harvest)[1])
            self.assertTrue(validate_repository_provenance(root, harvest))

    def test_first_adoption_validates_complete_v3_raw_context_qa_and_render(self):
        from test_source_adoptions import synthetic_fixture
        from stacks_zh.source_adoptions import (POLICIES, assemble_source_adoption,
                                               load_repository_source_adoptions)
        from stacks_zh.source_reextractions import byte_hash
        from stacks_zh.harness import resolve_harness
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, fp, rp, previous, _ = synthetic_fixture(Path(tmp), typed=False)
            # Retain the independent fixture's runtime/policy scaffolding only;
            # its uncommitted data is replaced by this explicit source scope.
            for name in ['translation-data', 'task-scopes', 'docs/evidence']:
                shutil.rmtree(root/name)
            statement = r'\begin{lemma}\label{lemma-one}A claim.\end{lemma}'
            referenced = r'\begin{lemma}\label{lemma-family-is-one}A referenced claim.\end{lemma}'
            (harvest/'test.tex').write_text('\\begin{document}\n\\section{Basics}\n'
                '\\label{section-basic}\n'+statement+'\n'+PROOF+'\n'+referenced+'\n\\end{document}\n')
            (harvest/'tags/tags').write_text('0000,test-section-basic\n0001,test-lemma-one\n'
                                           '0002,test-lemma-family-is-one\n')
            git(harvest, 'add', 'test.tex', 'tags/tags')
            git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Independent complete descent frames')
            source = git(harvest, 'rev-parse', 'HEAD')
            (root/'upstream.lock').write_text(f'commit = "{source}"\n')
            (root/'config/macro-policy.yml').write_text(policy_text())
            native = Containers(root, harvest)
            groups = [native.select(selector('section_title', owner='0000')),
                      native.select(selector('lemma')), native.select(selector('proof'))]
            units = [lower_container(group, native.policy)[0] for group in groups]
            from stacks_zh.source_terms import source_tex_hash
            write(root/'config/source-terms.json', dict(schema_version=1, source_commit=source,
                nonmathematical_declarations={}, terms=[dict(id='etale', forms=['étale'], chapters=[],
                    evidence=[dict(chapter='test', unit_id=units[2]['unit_id'], source_term='étale',
                                   source_tex_hash=source_tex_hash(units[2]))])]))
            git(root, 'add', 'config', 'upstream.lock')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Synthetic accepted frame policy; no facts')
            origin = git(root, 'rev-parse', 'HEAD')
            batches = []
            for name, owned_groups, owned_units in [('title', groups[:1], units[:1]),
                                                    ('lemma-proof', groups[1:], units[1:])]:
                up = f'translation-data/units/test-{name}.jsonl'
                cp = f'translation-data/candidates/synthetic/test-{name}.jsonl'
                write_jsonl(root/up, owned_units)
                batches.append(dict(units_path=up, candidates_path=cp, units=owned_units,
                    containers=[dict(selector=group['selector'], selected=group, unit_ids=[unit['unit_id']])
                                for group, unit in zip(owned_groups, owned_units)],
                    prior_attempts=[]))
            runtime = copy.deepcopy(previous['runtime'])
            runtime['harness']['version'] = resolve_harness('synthetic', root/'config/harnesses.yml').version
            ids = [unit['unit_id'] for unit in units]
            frozen = dict(schema_version=1, tool_version='source-adoption-input-v1',
                adoption_id='synthetic-first', origin_commit=origin, source_commit=source,
                task_id='synthetic-only', created_at='2026-10-19T00:00:00Z', runtime=runtime,
                policies=[dict(path=name, hash=byte_hash((root/name).read_bytes())) for name in POLICIES],
                contexts=[], batches=batches, outside_preferred_reason='Complete independent synthetic frames.',
                unit_ids=ids, chapter='test', parent_tags=['0000'], run_id='run-synthetic-first')
            for row in native.document('test')[1]:
                value = dict(kind='locked-English-neighbor', location=row['location'], source_commit=source,
                    source_unit=row['unit'], owner_tag=row['owner_tag'], parent_tag=row['parent_tag'])
                if row['owner_tag'] == '0002' and row['unit']['node_kind'] == 'lemma':
                    value.update(kind='locked-English-reference', requested_label='test-lemma-family-is-one',
                                 requested_tag='0002')
                frozen['contexts'].append(dict(context_id=row['unit']['unit_id'], value=value, hash=sha256_value(value)))
            scope_path = 'task-scopes/synthetic-first.json'
            files = [scope_path, fp.relative_to(root).as_posix(), rp.relative_to(root).as_posix(),
                     'translation-data/runs/run-synthetic-first.json',
                     'translation-data/source-adoptions/synthetic-first.json']
            files += [batch[role] for batch in batches for role in ['units_path', 'candidates_path']]
            branch = git(root, 'branch', '--show-current')
            scope = dict(schema_version=1, task_id='synthetic-only', owner='synthetic', branch=branch,
                source_commit=source, allowed_write_files=files, data_scopes=[dict(scope_id='synthetic',
                    chapter='test', parent_tags=['0000'], historical_parent_tags=[], unit_ids=ids,
                    input_unit_ids=ids, output_unit_ids=ids, allowed_write_files=files[1:],
                    run_scope=['run-synthetic-first'], model_scope=['synthetic', 'synthetic:fixture:declared'])])
            write(root/scope_path, scope)
            frozen['task'] = dict(issue=1, owner='synthetic', branch=branch, scope_manifest=scope_path,
                scope_manifest_sha256=byte_hash((root/scope_path).read_bytes()), scope_bytes=(root/scope_path).read_text())
            write(fp, frozen)
            raw = [dict(unit_id=unit['unit_id'], **synthetic_fields(unit)) for unit in units]
            for item in raw: item.pop('term_status')
            write_jsonl(rp, raw)
            assemble_source_adoption(root, fp, [rp], harvest)
            self.assertEqual(load_repository_source_adoptions(root, harvest)[1], [])
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            paths = render_batch([root/b['units_path'] for b in batches],
                [root/b['candidates_path'] for b in batches], root/'upstream.lock', root/'preview',
                'synthetic', 'Synthetic fixture', chapter_source_dir=harvest)
            self.assertIn(r"平展（\'etale）拓扑", ''.join(path.read_text() for path in paths))
            # Frozen source/context and immutable raw cannot be omitted later.
            broken = copy.deepcopy(frozen)
            broken['contexts'] = []
            write(fp, broken)
            self.assertTrue(load_repository_source_adoptions(root, harvest)[1])


if __name__ == '__main__':
    unittest.main()
