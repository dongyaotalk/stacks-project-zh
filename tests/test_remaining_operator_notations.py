"""Explicit mathematical names stay opaque; ordinary language stays blocked."""
import unittest
from pathlib import Path

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.records import RecordError

RAW = (Path(__file__).resolve().parents[1]/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
POLICY = Policy(RAW)
CASES = {
    'Equalizer':r'\text{Equalizer}(a,b)', 'Fun':r'\text{Fun}(A,B)',
    'GL':r'\text{GL}_n', 'Br':r'\text{Br}(X)', 'Quot':r'\text{Quot}(F/S)',
    'Bun':r'\textit{Bun}_G(X)', 'length':r'\text{length}_R(M)', 'ord':r'\text{ord}_R(x)',
    'div':r'\text{div}(f)', 'depth':r'\text{depth}_R(M)', 'cd':r'\text{cd}(A,I)',
    'Coh':r'\textit{Coh}(X)', 'Gr':r'\text{Gr}_I(C)', 'cosk':r'\text{cosk}_1',
    'sk':r'\text{sk}_1', 'Vect':r'\text{Vect}_k', 'Lift':r'\text{Lift}(F,A)',
    'Bad':r'\text{Bad}(i,j)', 'Good':r'\text{Good}(i,j)', 'Gal':r'\text{Gal}_k',
    'Groupoids':r'\textit{Groupoids}', 'Map':r'\text{Map}(E,G)',
    'Ext':r'\text{Ext}^{-i}_A(M,N)', 'Tor':r'\text{Tor}^R_i(M,N)',
    'ilb':r'\mathcal{H}\text{ilb}(F/S)', 'om':r'\mathcal{H}\text{om}_S(T,X)',
    'Inf':r'\text{Inf}_x(F)', 'End':r'\text{End}_k(V)', 'Der':r'\text{Der}_k(P,P)',
}


class RemainingOperatorNotationsTests(unittest.TestCase):
    def test_each_independently_written_operator_context_keeps_all_math_bytes(self):
        self.assertEqual(len(CASES),29)
        for name,math in CASES.items():
            with self.subTest(name=name):
                source='$'+math+'$';scanner=Scanner(source,POLICY)
                text,protected,errors=scanner.protect(0,len(source))
                self.assertEqual(errors,[])
                self.assertEqual(text,'<MATH_0001>')
                self.assertEqual(protected,{'MATH_0001':source})
                self.assertEqual([r['notation'] for r in scanner.math_text_classifications],[name])

    def test_wrong_commands_roles_and_case_do_not_receive_the_new_classifications(self):
        for source in [r'$\textbf{Fun}(A,B)$',r'$\text{GL}(n)$',r'$\text{Equalizer}_x$',
                       r'$\text{Length}_R(M)$',r'$\text{fun}(A,B)$',r'$\text{Bun}_G(X)$']:
            scanner=Scanner(source,POLICY);_,protected,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):
                self.assertTrue(any(e['kind']=='math-text' for e in errors))
                self.assertEqual(protected,{'MATH_0001':source})

    def test_natural_annotations_and_unsupported_syntax_remain_blocked(self):
        for literal in ['unit','counit',' in ',' and ',' composes to ',' monomorphism',
                        ' lying over ','restriction of ',r' irred.\ comp. with ']:
            source=r'$x\text{'+literal+r'}y$';scanner=Scanner(source,POLICY)
            _,_,errors=scanner.protect(0,len(source))
            with self.subTest(literal=literal):self.assertTrue(any(e['kind']=='math-text' for e in errors))
        for source in [r'$\text{Ext}^{}(M,N)$',r'$\text{Tor}^{ }_i(M,N)$',r'$\foo{\mathcal{H}\text{ilb}(X)}$']:
            scanner=Scanner(source,POLICY);_,_,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):self.assertTrue(any(e['kind']=='math-text' for e in errors))

    def test_ordinary_prose_is_still_translatable_without_math_classification(self):
        source='An Equalizer is a limit; a functor gives a map.';scanner=Scanner(source,POLICY)
        text,protected,errors=scanner.protect(0,len(source))
        self.assertEqual((text,protected,errors),(source,{},[]))
        self.assertEqual(scanner.math_text_classifications,[])

    def test_independent_prime_script_standalone_and_arrow_target_shapes(self):
        cases=[(r"$\text{Br}'(X)$",'primed-applied'),(r'$\text{Tor}_1^R(A,B)$','subscripted'),
               (r'$\textit{Coh}$','symbol'),(r'$\text{Quot}$','symbol'),
               (r'$\text{sk}$','symbol'),(r'$\text{cosk}$','symbol'),(r'$\text{ord}$','symbol'),
               (r'$\text{Aut}(X)$','applied'),(r'$\textit{Lift}_R(F,A)$','subscripted'),
               (r'$\text{div}_X(f)$','subscripted'),
               (r'$\Sh(S_\etale)\to G\textit{-Sets}$','arrow-target-prefixed-symbol')]
        for source,usage in cases:
            scanner=Scanner(source,POLICY);_,protected,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):
                self.assertEqual(errors,[]);self.assertEqual(protected,{'MATH_0001':source})
                self.assertEqual(scanner.math_text_classifications[-1]['usage'],usage)

    def test_split_symbols_and_arrow_targets_cannot_borrow_nested_or_script_arguments(self):
        cases=[r'$\foo{\mathcal{H}\text{ilb}(X)}$',r'$x^{\mathcal{H}\text{om}_S(T,X)}$',
               r'$\mathcal{K}\text{ilb}(X)$',r'$\mathcal{H}\textit{ilb}(X)$',
               r'$\mathcal{H}\text{om}_{}(T,X)$',
               r'$\foo{(X)\to G\textit{-Sets}}$',r'$x^G\textit{-Sets}$',
               r'$\foo G\textit{-Sets}$',r'$\Sh(S)\to H\textit{-Sets}$']
        for source in cases:
            scanner=Scanner(source,POLICY);_,_,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):self.assertTrue(any(e['kind']=='math-text' for e in errors))

    def test_exact_command_usage_pairs_do_not_expand_to_the_cartesian_product(self):
        for source in [r'$\text{Vect}(X)$',r'$\textit{Vect}_k$',r'$\text{Lift}_R(F,A)$']:
            scanner=Scanner(source,POLICY);_,_,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):self.assertTrue(any(e['kind']=='math-text' for e in errors))
        for source in [r'$\text{Vect}_k$',r'$\textit{Vect}(X)$',r'$\text{Lift}(F,A)$',
                       r'$\textit{Lift}(F,A)$',r'$\textit{Lift}_R(F,A)$']:
            scanner=Scanner(source,POLICY);_,protected,errors=scanner.protect(0,len(source))
            with self.subTest(source=source):
                self.assertEqual(errors,[]);self.assertEqual(protected,{'MATH_0001':source})

    def test_exact_context_policy_rejects_unknown_duplicate_and_uncovered_pairs(self):
        original='contexts: ["text/subscripted", "textit/applied"]'
        for value in ['[]','"text/subscripted"','["text/unknown", "textit/applied"]',
                      '["text/subscripted", "text/subscripted", "textit/applied"]',
                      '["text/subscripted"]','["textbf/subscripted", "textit/applied"]']:
            with self.subTest(value=value),self.assertRaises(RecordError):
                Policy(RAW.replace(original,'contexts: '+value))
