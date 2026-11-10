"""Source-only lexical cores; proper-name accent and all source bytes stay opaque."""
import unittest
from stacks_zh.source_terms import _qualified_declaration_parts, source_projection

PREFIX = '<GROUPOPEN_0001><ACCENT_0001><GROUPCLOSE_0001>ech '
BODY = 'zeroth ' + PREFIX + 'cohomology group'
TOKENS = {'GROUPOPEN_0001':'{','ACCENT_0001':r'\v C','GROUPCLOSE_0001':'}',
          'TEXTITOPEN_0001':r'{\it ','TEXTITCLOSE_0001':'}'}

class EtaleCohomologyTermProjectionTests(unittest.TestCase):
    def test_complete_zeroth_declaration_exposes_both_actual_cores(self):
        unit={'node_kind':'definition','placeholders':TOKENS,
              'source_text':'We define <TEXTITOPEN_0001>'+BODY+'<TEXTITCLOSE_0001>.'}
        text, declarations=source_projection(unit)
        self.assertEqual(declarations,['cohomology group','zeroth'])
        self.assertEqual(text,'We define '+BODY+'.')
        self.assertEqual(unit['source_text'],'We define <TEXTITOPEN_0001>'+BODY+'<TEXTITCLOSE_0001>.')

    def test_existing_plural_and_complex_cores_remain_unchanged(self):
        for word in ['complex','cohomology groups']:
            self.assertEqual(_qualified_declaration_parts(PREFIX+word,{'placeholders':TOKENS}),[word])

    def test_unknown_ordinal_accent_wrapper_and_partial_phrase_stay_closed(self):
        for body in [BODY.replace('zeroth','first'),BODY+' of something',
                     BODY.replace('0001>ech','0002>ech'),BODY.replace('cohomology group','cohomology')]:
            self.assertIsNone(_qualified_declaration_parts(body,{'placeholders':TOKENS}))
        for field, value in [('ACCENT_0001',r'\v X'),('GROUPOPEN_0001','['),('GROUPCLOSE_0001',']')]:
            self.assertIsNone(_qualified_declaration_parts(BODY,{'placeholders':{**TOKENS,field:value}}))
