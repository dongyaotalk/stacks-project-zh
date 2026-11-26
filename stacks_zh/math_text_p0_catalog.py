"""Math roles verified against exact locked source chapters."""

SOURCE_COMMIT = 'a04446e57ec1fbc252a871afcec7752fb2807b14'

SOURCE_HASHES = {
    'sheaves': 'sha256:ac4f9edc7db85e66329806ec9ea42816187a469772844baea663e1c9a9f00b38',
    'schemes': 'sha256:08475a01cf0ddf69734fd7ebc0d14d3831148c25a2ef82aaafdb65666f8fce47',
    'constructions': 'sha256:a642498dbebe4b72547d8e3ac03d8c8a7c3a3c9b1e604439c2899f18beb4cddb',
    'algebraization': 'sha256:a1d15613e36799787f29497ada72268daaa4c3d8bef0f6457c4ca3e60c4262e9',
    'artin': 'sha256:eba90a897b08eebff451e80925d13381b1a7f6ab883a34118733cd24cf061f47',
    'moduli': 'sha256:c9e283b30207bb93ca7c71cd83df78bb7f1962c471348b28968d9fb6a01b11d5',
    'stacks-morphisms': 'sha256:1f81f01c6748709778c0f877f1cb687152b344aa1c455449d2a341bbfe6a8b90',
    'stacks-properties': 'sha256:59d6b6df8f528ed5d3a68d9b9d74622e9b643f3622cc4d381bb46cc27a990016',
}

SOURCE_FRAMES = {
    'sheaves': {
        'sha256:46b1e513d60c438507e7737bf84e2df7da8f3eb37a75d28040156c5e63a7ebc5': {
            9: ('plain', 'textit', 'a final object', 'sheaves-remark-confusion'),
        },
        'sha256:49d3818411c57f0099ba05c0cb3438d63bce1b9dfa0c0bf81e4c3a59964a560f': {
            10: ('plain', 'text', ' continuous', 'sheaves-section-sheaves'),
            21: ('plain', 'text', ' locally constant', 'sheaves-section-sheaves'),
        },
        'sha256:6e27b3731ed8d51a8efcc93242618f746f650f3d0e7dbe809bff491a1adce99f': {
            51: ('plain', 'text', 'restriction for ', 'sheaves-section-presheaves-functorial'),
        },
        'sha256:821f55ab118f4f60deae3e42407386b3a347823ce3cd6587c5b2783dded90d43': {
            27: ('plain', 'text', 'restriction of ', 'sheaves-definition-f-map'),
            53: ('plain', 'text', 'restriction of ', 'sheaves-definition-f-map'),
        },
        'sha256:953555c97ad37854f643b7c35ed9d5e6c0b23197ba5149bd81855456c0050e90': {
            18: ('plain', 'text', ' is continuous', 'sheaves-example-basic-continuous-maps'),
        },
        'sha256:9aabe33f83038bc0e4807821678816366e7b7a1c5ae9575fbb54f16b27256004': {
            50: ('plain', 'text', ' resp. ', 'sheaves-section-sheaves-structures'),
        },
        'sha256:a879f7b2f3906a8300471aee0a01d91c371846f40c6d96aece7da460be4df955': {
            32: ('plain', 'text', 'restr.', 'sheaves-lemma-f-map-basis-above-and-below-structures'),
        },
        'sha256:f52476b7afbde5d996ed54d80ce59a4148e643b3c2dec240fe125b36cbbcb6d1': {
            24: ('plain', 'text', ' is continuous', 'sheaves-example-C0-sheaf-rings'),
        },
    },
    'schemes': {
        'sha256:375a3185432bf74a5ffe42b20562c10a4e543e59db76d02a4485223830b96b74': {
            9: ('plain', 'text', 'the element ', 'schemes-lemma-extension-quasi-coherent'),
            12: ('plain', 'text', ' comes from ', 'schemes-lemma-extension-quasi-coherent'),
        },
        'sha256:5b716b14daf2e2bceadfc727ed157701925f5102fd902b0981b9c18826e7ed71': {
            97: ('plain', 'text', 'open covering ', 'schemes-lemma-glue'),
            111: ('plain', 'text', ' and ', 'schemes-lemma-glue'),
            131: ('plain', 'text', ' such that', 'schemes-lemma-glue'),
            157: ('plain', 'text', ' and ', 'schemes-lemma-glue'),
        },
        'sha256:a900e33b7125563537344910e8f4f9e1d2eb239cabac4b83b1902ebdbc681422': {
            12: ('plain', 'text', 'image ', 'schemes-lemma-f-open'),
        },
        'sha256:c041fefd3a75842b14d0718c424276c620009135aba5d927d8f9df1c0f5eb17b': {
            3: ('symbol', 'text', 'Sym', 'schemes-lemma-widetilde-constructions'),
            11: ('symbol', 'text', 'Sym', 'schemes-lemma-widetilde-constructions'),
        },
        'sha256:dd59f3e9af4b2d3e755d0628a30dc01b017ebb6f3424c00950ed1c09af209b89': {
            2: ('plain', 'textit', 'Locally ringed spaces', 'schemes-section-locally-ringed-spaces'),
            4: ('plain', 'textit', 'Ringed spaces', 'schemes-section-locally-ringed-spaces'),
        },
    },
    'constructions': {
        'sha256:00254a50cab88f56eac6a325b45662fa21ee752b155d758b2f4b010610dd8eed': {
            17: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:00750a5354b98dc0ffb5ea5f203942bcd65c753798ee9346e05a7beed55b11b3': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj-transitive'),
        },
        'sha256:009f9028e2bd3d562c1a0b2ac1b802fe035a3419e5db6fb69e526839e5a2b181': {
            6: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-base-change'),
            30: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-base-change'),
        },
        'sha256:01421d4c78c500ff4f32378dc1debd0c5d7de78ad577967a5ba4109182ee3a4d': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
            32: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
            50: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
            71: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
        },
        'sha256:03aee9495ee53dd17e14a2ad4cfbb498210b8da7d2dc7d218f6841e2650ac790': {
            39: ('plain', 'text', ' is surjective', 'constructions-lemma-gkn-representable'),
        },
        'sha256:03dcadbfb0f721f717016bfc47a0782c4edcfe51b8c232b23558208102e9ed19': {
            6: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj'),
        },
        'sha256:05bf6d4e2b697ee7cac62611eb173cb4663ce3497bda57129868921233601e0b': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-proj'),
        },
        'sha256:0753bba54a3503799fdb950919129e6fcc3e372c653bca478f4f58c4cf9d69d0': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj'),
        },
        'sha256:07e330741ee3b90fd596e8c0851922caa08a5a86620d2976e62f0ca472812bbc': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-sheaves'),
        },
        'sha256:0bc3afcba67ac50f09aae1c1f3fc614af88fb9765922f1c2835884ef26c56f98': {
            1: ('symbol', 'text', 'Sym', 'constructions-example-projective-space'),
        },
        'sha256:0d6166600d25c3f84042cb30a9c2ef3318a511d835ed8201b34d7bb62d4753dc': {
            33: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-base-change'),
            69: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-base-change'),
        },
        'sha256:0dbf99813f697ba3f982f53d5a46492278b5a96017d4fff13933c9afd66d8051': {
            5: ('symbol', 'text', 'Sym', 'constructions-section-projective-bundle'),
            13: ('symbol', 'text', 'Sym', 'constructions-section-projective-bundle'),
            24: ('symbol', 'text', 'Sym', 'constructions-section-projective-bundle'),
        },
        'sha256:106a8f8fa9c1e9115bc2febb4d066ab25f8c401acc1d39c7626b47e80a5031d0': {
            6: ('symbol', 'text', 'Proj', 'constructions-example-not-existence-valuative-big-proj'),
        },
        'sha256:134f9c48aa3e0b451283f6e646338212b225816e2b4e2e2eece852ca5c21147a': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:15cb9b15a7dd8c1ad616165bff5eda831ba971a8da521c13ea9cb06261d50ef6': {
            10: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:15f552e8adf1883363f26c81a7288b1fbe1446cd696cdcf3bb2404f25ea0f32a': {
            18: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:16a11da1ab306be84c782b9a83e6d9bfacbbefa453e60604f54925f07808f6c6': {
            3: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:170f05d72cc17c28f455170181b41c146b7f265df81e73b5b7c4a9a5e7e866ba': {
            17: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-valuative-criterion'),
        },
        'sha256:177007f4f7a7bed1793498014cdde0fef2a6a323bafef96818fb552ec2e5167a': {
            29: ('symbol', 'text', 'Proj', 'constructions-section-morphisms-proj'),
        },
        'sha256:1d115348edb83734a7a73be41f9d5e0f3a2e89e1b669dc2181dc6cb23eb89db5': {
            8: ('symbol', 'text', 'Proj', 'constructions-section-quasi-coherent-proj'),
        },
        'sha256:23c435c899e47914f3d776d044a8043b402a2b63a0cf68385e3c4ff4c877e353': {
            15: ('symbol', 'text', 'Proj', 'constructions-lemma-segre-embedding'),
        },
        'sha256:25fe1b1f0ce1ff18b0a59ed5fef7eaec5a27aa62c439d4fe0ca3f37910c2a1fd': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:27b46388f35f4cc4a94a5018f30234889a90c8d6c8eed62d114d8d313d6683a8': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-sheaves'),
        },
        'sha256:29775a95578b84f8bb38a5c5c91085c4831d39587893c408d2218b5619b9c530': {
            12: ('symbol', 'text', 'Proj', 'constructions-remark-not-in-invertible-locus'),
        },
        'sha256:2a63357bc21766618fa5e9ee58e8d1fb1c2a6e420879bb490af6bc5ec64aa675': {
            19: ('plain', 'text', 'homogeneous', 'constructions-lemma-morphism-proj'),
        },
        'sha256:2cf63be406093246c5aaaf62e022fced0b75943cf71d0fe21de97a12584c3da9': {
            13: ('plain', 'text', 'pairs ', 'constructions-lemma-spec-affine'),
        },
        'sha256:2f702581d832ea44dba48023b69796f60d373d0d1e49d1dae1e79bc62cc3663f': {
            28: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:3137297d162b99fdaed6cc79baeff832cc63565375908cb2f12a4cf51e88cb3d': {
            34: ('symbol', 'text', 'Proj', 'constructions-lemma-invertible-map-into-relative-proj'),
        },
        'sha256:32420e5ee3ce723f6ddcf285c900f7bd142b66b9155fa7e24c54be26aeb64404': {
            10: ('plain', 'text', 'the map ', 'constructions-lemma-gkn-representable'),
            40: ('plain', 'text', ' induced by ', 'constructions-lemma-gkn-representable'),
            50: ('plain', 'text', ' is surjective', 'constructions-lemma-gkn-representable'),
        },
        'sha256:324cf4e0edf5846a8f07a29cda678afd8eafeaaa4ed71c0eb0f1bb01283e1f81': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj'),
        },
        'sha256:33589f49c830b69857c66f4ed93d5f6b99bf3f88e5b6a2a2e3829c0aa080531d': {
            8: ('symbol', 'text', 'Proj', 'constructions-lemma-twisting-and-proj'),
            36: ('symbol', 'text', 'Proj', 'constructions-lemma-twisting-and-proj'),
        },
        'sha256:36e96106ca1b3077eefbd7a5843d5a0c9462e12b149c21c1337c00ba60c8531a': {
            1: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:38c9b78628fa5bd5042ce23278b632e19927dbbad70924a7bfdd915cc0210c77': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
        },
        'sha256:39d9ed5c7dc7c35211b0caf0efd485ec155f228acf04b763f2fa714bbcb6c450': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:3f1ec8808a8ef6574a0f9beb1e6211c4a7b7bdb0ed9caac38fe98160276dc73a': {
            14: ('symbol', 'text', 'Sym', 'constructions-example-projective-space'),
        },
        'sha256:3ff1a4b31716a798bcce85bdf5b5ef49d34d658264b0b2b4844fb01d08b1bfa0': {
            19: ('symbol', 'text', 'Sym', 'constructions-section-vector-bundle'),
        },
        'sha256:4328a3112363f5462b5b4c12732dc46650570e09eeca22000cc31424ff6a4f31': {
            15: ('plain', 'text', ' quasi-compact open', 'constructions-lemma-proj-functor'),
        },
        'sha256:4516cce4e0d2c83d67ea21387a11105c8349d56970c7ae88a9184ddc9682835c': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-base-change'),
        },
        'sha256:48279eecf5002ce70231e5fc5d28ad9291644004643aad493df34574617ce5d9': {
            15: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj'),
        },
        'sha256:4ac8eef3228fecdc7f523338fc4a015f554d95ad3116747f3e1c20c0361d591b': {
            13: ('symbol', 'text', 'Proj', 'constructions-lemma-widetilde-tensor'),
            24: ('symbol', 'text', 'Proj', 'constructions-lemma-widetilde-tensor'),
        },
        'sha256:4adebee8233c4e01e9be53a0bfc3e28867c3169a2883113bdaa3e4e32268a500': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
            23: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:4f9279125fef693e8ad54af690592a9b1b1a0539da5ed6a0031104a7f8f70dd3': {
            35: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj'),
        },
        'sha256:4fc5ece81707727667114308136409cc03a4f0bf524ac0b3200f16c6f31ffadd': {
            17: ('symbol', 'text', 'Proj', 'constructions-definition-projective-bundle'),
            22: ('symbol', 'text', 'Sym', 'constructions-definition-projective-bundle'),
        },
        'sha256:4fc910045e524528e9dc6f62677a7226493a89de707dd4c33283c31e209851ff': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
            8: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
        },
        'sha256:5287f738de074a68590a01459d95d8eb3eb229f9ed2a028396fe47510bf7f7f3': {
            3: ('symbol', 'text', 'lcm', 'constructions-lemma-equivalent'),
        },
        'sha256:52cc535a9b641db2333e8544debce927ef392a14bd990760c43a77c1f4187d2b': {
            1: ('symbol', 'text', 'Sym', 'constructions-section-vector-bundle'),
        },
        'sha256:54747b86b8e6f0b4d813a9d56149a8cf91b6195db85bf4dd0880607f74f446b8': {
            16: ('symbol', 'text', 'Proj', 'constructions-lemma-projective-space-bundle'),
            37: ('symbol', 'text', 'Proj', 'constructions-lemma-projective-space-bundle'),
        },
        'sha256:5776eba7c99e2ad1b6d93290fa03484f1ac61f248c9d5cf75bec1860ab603a24': {
            30: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
            62: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:57b02996a59fe6e58ccd8a660f977425827b2e2155e4bf20a7378f4f282dcd99': {
            3: ('symbol', 'text', 'Proj', 'constructions-definition-twist'),
        },
        'sha256:5d1ea37d12af5cb9d03e6950d89ff0573a10bb44f6aa37c4dda2538d9eb41db0': {
            15: ('symbol', 'text', 'Proj', 'constructions-definition-projective-space'),
        },
        'sha256:5e93dbeb1ef419105ccf40996edb7720b7bfd4390364982cd72301a5dc2c4dd6': {
            31: ('symbol', 'text', 'Sym', 'constructions-section-vector-bundle'),
        },
        'sha256:63e64e4e9ae80f69d66a7429afee9bb42ece194d0d800757ee251f64b2b0df58': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-invertible-map-into-proj'),
        },
        'sha256:64215cdeb2ede628c40e2f754717a47e7d25cbed8ed6c673a7ee763bc9fb855b': {
            20: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-modules'),
        },
        'sha256:6534a70edcdf6469c1b6c6934e2ece7199fd7b15300c720da0182f7eef3fe6bd': {
            19: ('symbol', 'text', 'Sym', 'constructions-lemma-projective-space-bundle'),
        },
        'sha256:6a62603a86a0f6e6e851e81bfb9f403d37e1a9b933b790fa4fe9d75714f48cf7': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-proj'),
        },
        'sha256:6d80422781665bb368781fada1133652bc60c0a682dceefb2af6a8c2d8300202': {
            4: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj'),
            76: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj'),
        },
        'sha256:6fe0bdaf78e090a6e746d8aa0f36c02fc7f75ba3bb6b718f9b8cd05d906ca75b': {
            48: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
            67: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
            78: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:70df971e3cf93e968b0c1a913c62f12e2ef2fa599746bd64cb22d7fbb00f63ba': {
            4: ('symbol', 'text', 'Proj', 'constructions-lemma-transitive-proj'),
            10: ('symbol', 'text', 'Proj', 'constructions-lemma-transitive-proj'),
        },
        'sha256:71382537af45362e69d608a9f7ed381149bf06f6f70773b01680e4a41b6389f0': {
            37: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj'),
        },
        'sha256:7467420f8cf92d4d6ec40c20ed24c522bb42c5d0799f35ff09535b7b99c3b571': {
            1: ('symbol', 'text', 'Proj', 'constructions-example-open-subset-proj'),
        },
        'sha256:761ea60dbf89ac58177fb5956c039e5a98113557c89cad55858e117b5b6e5696': {
            1: ('symbol', 'text', 'Proj', 'constructions-example-not-existence-valuative-small-proj'),
        },
        'sha256:7699e192e46f6d8f936f1aa09e6f87f5a2c5c8e9e6948bcfdf821d3e400ebc64': {
            1: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-separated'),
        },
        'sha256:7990436f685f2a589971f555af53cc1488a157dea58b0d2c2e82621f7a424fd3': {
            1: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-affine'),
        },
        'sha256:7d4761a19ce471e5d6e1b1efebd2e76123756240ab05c915e7be991ecf7dea39': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
        },
        'sha256:7d66fc4bb2d5ae2bb3342240c0ca129f6c2fcd36dd1e28889f3813b66973247b': {
            4: ('symbol', 'text', 'Proj', 'constructions-lemma-d-uple'),
        },
        'sha256:804e5891bfde2472a8cfc9e4ed530c7329d68d760aaf1d72c1fda97c9810eff4': {
            20: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:81bc7a7daab0be7c9bda2b1cb1615b82e1822d0c9fb8c2d76de1ff5e43a3e154': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-closed-in-projective-space'),
        },
        'sha256:82c189f0cdfcdb77967a7c4d0c2deb68bf6dbf88e4bf4b8e46d76e261f7ba509': {
            7: ('symbol', 'text', 'Proj', 'constructions-section-morphisms-proj'),
        },
        'sha256:82f841128109bf942f089cf2db8ed25d18b8d5ca9a448faa256503886270712a': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-glueing-gives-functor-proj'),
        },
        'sha256:8460258b04aaa646ef8183ea7f73557df1a93b5bb9ec50a7b378a73336b8b91a': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj-transitive'),
        },
        'sha256:8871acfe7a2f31f772251c3e10f66f1002955fbe32ac0aa6f8e13b13b2087464': {
            4: ('symbol', 'text', 'Proj', 'constructions-example-projective-bundle'),
            6: ('symbol', 'text', 'Sym', 'constructions-example-projective-bundle'),
        },
        'sha256:8abe9060d05fb76a2b611c8b4b1a97994e3a4f346994bda1df89016621f810cf': {
            6: ('symbol', 'text', 'Proj', 'constructions-lemma-base-change-map-proj'),
            25: ('symbol', 'text', 'Proj', 'constructions-lemma-base-change-map-proj'),
        },
        'sha256:8d7c70110d8f2fa903a4bbe1b9c9e2f8296ecdd71b15fd8079b2cad89b26ac0b': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj'),
        },
        'sha256:946c91d499f97cafe5dfab18de715f7d77bfec9898fcfacaf5159516efe0b032': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-modules'),
        },
        'sha256:96a6c9cb1bf9e82cacbeeefca96220682736fe41d63517cb56fb8c78a0bec1c6': {
            4: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
            17: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
        },
        'sha256:970110251bd1a700ec38f554ab302b51e82ad37e894c0dcd99dab943a8583591': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-transitive-proj'),
            10: ('symbol', 'text', 'Proj', 'constructions-lemma-transitive-proj'),
        },
        'sha256:980c0ad946d15f4492ef7eb995c63468ad4edb64b86740cdafda7d271bde65b5': {
            93: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:984fee850abdd685aacc9fb2832284c97e394b1c5344627463bbfa73cb0268c2': {
            31: ('plain', 'text', 'equivalently', 'constructions-section-projective-bundle'),
        },
        'sha256:98f2ded6ccab3c987d087932651ec6c685a899a785feaba0a9914cb4339703e4': {
            18: ('plain', 'text', ' homogeneous', 'constructions-lemma-invertible-map-into-proj'),
        },
        'sha256:9c22841f58f94b7e59fb904d18605a448ad8e1d436f922cc9c96162fde00f7ef': {
            23: ('plain', 'text', 'strict equivalence classes of triples ', 'constructions-section-morphisms-proj'),
            34: ('plain', 'text', ' as above', 'constructions-section-morphisms-proj'),
        },
        'sha256:9e41f367e53b9ca665283821cbcf6e631ae66e09c9f43f8bcc0a1dad47903fcf': {
            39: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:a011584ba5aa62461b1c15b9ac7adc9a4193988e2e81926244bd2be437de4eeb': {
            10: ('symbol', 'text', 'Proj', 'constructions-definition-standard-covering'),
        },
        'sha256:a0561749d5847f253ed6afb50c984cce2e99e91b6f8f906d011bdcb41b43aed9': {
            2: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
            13: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:a29480e2e5f40b5db0c11293f4c10774ec296df6be80ce3bd69e147bc431c5af': {
            19: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-scheme'),
        },
        'sha256:a340abbe82d98e82a37f6aaa2e0980b9be4ccece6ecd0134fa47bfdb9ea64bf5': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-relative-proj'),
        },
        'sha256:a62368ccccef8f7b991840986e5e685273efb1447ce66c069faf1909e4719866': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-tie-up-psi'),
        },
        'sha256:a872947fdbcec138a825d3e38f7bf1cbf5f94b7af53c3e6362db8184bbf789f9': {
            1: ('symbol', 'text', 'Proj', 'constructions-example-trivial-proj'),
        },
        'sha256:a8d5dc473988567636bd155e217fe7015b9209ab83ad4a6ca3019c60f9319174': {
            26: ('plain', 'text', 'th spot', 'constructions-lemma-gkn-representable'),
        },
        'sha256:aab290c2b224e4cc8b6958246dfdedae5ff8b6106cde1c4fbbfd39166015d689': {
            19: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-sheaves'),
        },
        'sha256:abb3b1cb122f6383939838ff36ccef37ff109ec096d63b41bffb88e1247a30d2': {
            1: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj'),
        },
        'sha256:ac975dc836c99321605eea90eb0ad0fafdc36348af2116d9e11f6f24cc7065b2': {
            8: ('symbol', 'text', 'Proj', 'constructions-section-quasi-coherent-proj'),
        },
        'sha256:adadf28ad3265d6c489bf9683aee41f7f15a55e5917c6790016839c2992127ff': {
            20: ('symbol', 'text', 'Sym', 'constructions-definition-vector-bundle'),
        },
        'sha256:ae78e07016277be6c9f31d45a9af4242cb052cffe7c2811d89feef7ac4f6a27b': {
            1: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj-via-glueing'),
        },
        'sha256:af5d33d859b9f5ebae0d69b58791c5f056742828ad62c4128981205dd2096d2c': {
            3: ('symbol', 'text', 'lcm', 'constructions-lemma-equivalent-relative'),
        },
        'sha256:afccabd24442d54ef31c9d4f4c95b690a20370fbd9f7c3ec7e4d14c33d4fdc4d': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-apply-relative'),
        },
        'sha256:b51f20f570dcba70ac3c825f57f16f26289baa201c9372254fd0ded81ac689cf': {
            5: ('symbol', 'text', 'lcm', 'constructions-lemma-equivalent-relative'),
        },
        'sha256:b5fb060b6953b659eba4f98793638ee2cd0a747ad95b5eb7bf3d21cda1d28a3c': {
            2: ('symbol', 'text', 'Sym', 'constructions-example-projective-bundle'),
        },
        'sha256:badc3c2816467a8d9c2ab107b659ab882f43380b1e83fe86d82b653f42738521': {
            13: ('symbol', 'text', 'Proj', 'constructions-lemma-projective-space-bundle'),
        },
        'sha256:bb6d53a95b737908d1cb388570e1d0b6912af670579fe4507b78d3398c3b3dc2': {
            10: ('symbol', 'text', 'Proj', 'constructions-example-projective-space'),
            12: ('symbol', 'text', 'Sym', 'constructions-example-projective-space'),
        },
        'sha256:bbfde655a13917820a3b7a5a3c8be8209a3faaa632243559b7dcdb3b984494b4': {
            19: ('plain', 'text', ' surjective', 'constructions-lemma-gkn-representable'),
        },
        'sha256:bde7a297aacbf3511a1474601f29b196c52cc7326817b80168957b1ee77ca6bc': {
            1: ('symbol', 'text', 'Sym', 'constructions-example-projective-bundle'),
        },
        'sha256:be3b75dd46fb07f43a2ea66b20a2ce81dd2b954f0e15806b89e743639319f718': {
            20: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:c4d9eef26e60344bccfa3051d0c85c6ca301a6f252341451d78707d37a071f27': {
            30: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-valuative-criterion'),
        },
        'sha256:caccc0a412a6f94347ef80cb2f91bc81d678134c180acab17ec40e3c94a67c71': {
            13: ('plain', 'text', ' quasi-compact open', 'constructions-section-morphisms-proj'),
        },
        'sha256:cb948b73197ac7226194d40e846933f74cd50630c1e461fe6f6fc8ddc985f670': {
            20: ('symbol', 'text', 'Proj', 'constructions-lemma-invertible-map-into-relative-proj'),
        },
        'sha256:ceaaf2519e5eef5a40d025f76e2b2fe9f40ee185a0c57bb23e405ba88c5f8b64': {
            3: ('symbol', 'text', 'lcm', 'constructions-lemma-proj-valuative-criterion'),
        },
        'sha256:cf370829c7890e831d762ac910ce2a9baae792b9d0b4af5e46f264f0207ccf2a': {
            1: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-valuative-criterion'),
        },
        'sha256:cffc1bce7651c328f87e74ffec1981f0a81089f83054df201955d7eb661f4a7b': {
            1: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj-via-glueing'),
            6: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj-via-glueing'),
        },
        'sha256:d0cf8631095045a68f447d9bf6c41ff418c31db33cb6f655a1d9138b9cd3fc41': {
            4: ('symbol', 'text', 'Proj', 'constructions-section-relative-proj-via-glueing'),
        },
        'sha256:d1103d459e38ad9ecd83c0454d8116c529afdd2d82e9b8492f900139964ebcf6': {
            8: ('symbol', 'text', 'Proj', 'constructions-lemma-segre-embedding'),
        },
        'sha256:d1b5e3a38d8ecb028e75f7d8d6c7402b6a55bdca546abb5e41ec2799757ee0c2': {
            1: ('symbol', 'text', 'Proj', 'constructions-lemma-relative-proj-separated'),
        },
        'sha256:d3d044f598b9f85ec37ce6468c001307620d9623d3055f25c290101870447981': {
            7: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:d402d028942fc00b64a020ac8514c84c1ae899432adc7f032f5557cb31bfb8d6': {
            19: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:d479b95335bc1b99cb53ecf895810d67f162dbedb5b04b8ae32f925f46f56c71': {
            9: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:d5d8481996e6207ef6747c49fe7d2d88f88660318419b05dabf93dadfd011d1e': {
            1: ('symbol', 'text', 'Proj', 'constructions-section-projective-space'),
        },
        'sha256:d5f9e2f4181bfa0065e40ac0d5f825e63acaf01a017b92737a0632eef49d2ebd': {
            5: ('symbol', 'text', 'Proj', 'constructions-lemma-invertible-map-into-relative-proj'),
        },
        'sha256:d88fd0082ca3854a1b2ebd97600316da4232bce7dd48a5b4e66a218cfe1c5020': {
            12: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
            28: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-inclusion'),
        },
        'sha256:d99cfa7ba7b62e568617b5c3612537ebd4a004088c27d2638cccb98fafada185': {
            3: ('symbol', 'text', 'Proj', 'constructions-lemma-morphism-proj-transitive'),
        },
        'sha256:da78634c52b8e9e4205afc40b0e71d59f1f53bd1031410135254825ebb21fa3a': {
            10: ('symbol', 'text', 'Proj', 'constructions-section-quasi-coherent-relative-proj'),
        },
        'sha256:dbf1f4d6c4b5c8a475ad140173299b84b301c4d376762fb216bf41c3a7bed45d': {
            2: ('symbol', 'text', 'Sym', 'constructions-definition-abstract-vector-bundle'),
        },
        'sha256:dd65c0baa5acb707dbe8419c24c5c21c8395a8b0812f1b0acae31cb68fd78570': {
            7: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-sheaves'),
        },
        'sha256:de3f85a9fd34ff6ce9ad3101ec265cf94ff33c005a17acff3332f9d9ec951b3c': {
            30: ('symbol', 'text', 'Proj', 'constructions-lemma-glue-relative-proj-twists'),
        },
        'sha256:de6cb2f6147a60e7ef742481eabeb6509c9924eb782112bd38ceb03c4fb2ea9d': {
            4: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:df948b1e4a12603054390290378423caf393bcd63905708ca9468599c2308faf': {
            16: ('symbol', 'text', 'Proj', 'constructions-remark-not-in-invertible-locus'),
        },
        'sha256:df9a4cf218712a8d2090a20e2cc1388f79d60e31708f732d262a245ecb27ec12': {
            26: ('plain', 'text', 'pairs ', 'constructions-section-spec'),
            32: ('plain', 'text', ' as above', 'constructions-section-spec'),
        },
        'sha256:e099f4fd3b213d8a3b1d2fc041dce266c9ae866260a618b7f541445dfd6437bb': {
            8: ('symbol', 'text', 'Sym', 'constructions-lemma-category-vector-bundles'),
        },
        'sha256:e24598f0662fc70b504bb9fbcb1d93262661e7b7be11e2a8998e93f9771000d9': {
            88: ('symbol', 'text', 'Proj', 'constructions-lemma-invertible-map-into-relative-proj'),
        },
        'sha256:e5a5f65994a429b61a0cfc2338d85f6f227b2317af51356475017307c0518a5d': {
            22: ('plain', 'text', '-graded primes of ', 'constructions-lemma-standard-open'),
            69: ('plain', 'text', '-graded primes of ', 'constructions-lemma-standard-open'),
        },
        'sha256:e816798ce1499b4470ee5c1410db571d1c0c70d0ee3b921d72115d831c30833e': {
            2: ('symbol', 'text', 'Sym', 'constructions-section-projective-bundle'),
            36: ('plain', 'text', 'equivalently', 'constructions-section-projective-bundle'),
            41: ('symbol', 'text', 'Sym', 'constructions-section-projective-bundle'),
        },
        'sha256:e8f34ad65ee319ec805a617e526b63142d259c878b9cf974f5b1e003f5a0241e': {
            8: ('symbol', 'text', 'Proj', 'constructions-lemma-segre-embedding'),
        },
        'sha256:e95ca0247300c12e3148f4329caf1f0fa28c224ed6d8f91e8bbf853821bf7ede': {
            4: ('symbol', 'text', 'Proj', 'constructions-lemma-closed-in-projective-space'),
        },
        'sha256:ec2ea5f791859c980b838b9c4f8195b1bdc8230d15a07c702c79f1c9a68c0b9c': {
            1: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-quasi-compact'),
        },
        'sha256:ee941f0ad4e36cf8ce36411f3a7ae8848d58c62c1ff4435f253718f182e7cc18': {
            3: ('symbol', 'text', 'Proj', 'constructions-section-proj'),
        },
        'sha256:f29fb5f965696c4185f978f377206412918db85f2b3380d953610927a5e0ff58': {
            18: ('symbol', 'text', 'Proj', 'constructions-lemma-proj-scheme'),
        },
        'sha256:f5676b2814236c7be8336e34f8b25e366761e56afb8af27e8ebd4320e77c8024': {
            23: ('plain', 'text', 'strict equivalence classes of ', 'constructions-section-relative-proj'),
            40: ('plain', 'text', ' as above', 'constructions-section-relative-proj'),
        },
        'sha256:ff0bf445f9318c49ffb9b049d0db29cea4d287f4621a48d7b1dd27c81383f846': {
            16: ('symbol', 'text', 'Proj', 'constructions-lemma-projective-space'),
        },
    },
    'algebraization': {
        'sha256:003260eac85d5ec143f929c5146cdcd7856fd9ec0c68cf760e0b1c2a9194eeda': {
            12: ('plain', 'text', 'of', 'algebraization-section-algebraization-sections-general'),
        },
        'sha256:00cba87af041e7d36f593f47f6b82fd3d489bf8a8d48afa1921b1734b277da00': {
            57: ('plain', 'text', ' or ', 'algebraization-lemma-blowup'),
        },
        'sha256:00e3a8c1c8c00fa434c4ba0c29bd793366097e136742426eeb7874432f1767f6': {
            1: ('symbol', 'text', 'Ass', 'algebraization-proposition-application-H0'),
        },
        'sha256:09c4802e67525be790db5f99bd1cc7c69b75a8853491061572d38553c964f4eb': {
            3: ('symbol', 'text', 'Ass', 'algebraization-proposition-hilbert-triple'),
            11: ('symbol', 'text', 'Ass', 'algebraization-proposition-hilbert-triple'),
        },
        'sha256:11f9a0dcf377acac6cd3fa1a9ddd5905c42162f3df283201dc2212188d254433': {
            1: ('symbol', 'text', 'depth', 'algebraization-lemma-nonnegative-chi-triple'),
        },
        'sha256:13c23e94e86133334f895634ba0ac035e38ba95cd2081d31917f40fdd3ddab62': {
            126: ('symbol', 'text', 'trdeg', 'algebraization-lemma-blowup'),
        },
        'sha256:13c87210cd6871b97477f20f62366ebb80c1404276e4a74994c88b568a33ca5c': {
            5: ('symbol', 'text', 'codim', 'algebraization-lemma-discussion'),
        },
        'sha256:23b713924bc7e2d45e3444868115e464f71e15f260935b1e12acb300abb7bd7b': {
            6: ('symbol', 'text', 'codim', 'algebraization-lemma-change-distance-function'),
        },
        'sha256:2937880819d29349ca23b0c0bd01cc46d6d7a3a4d96c463219b2562d29f29c18': {
            4: ('symbol', 'text', 'Ass', 'algebraization-lemma-algebraize-local-cohomology-general'),
        },
        'sha256:29d03961f1bb9f88eeab0df12557f38296e813629ebdaa48bf434294bfdccece': {
            1: ('symbol', 'text', 'depth', 'algebraization-lemma-kill-colimit-weak-general'),
        },
        'sha256:2ac928da35cb07abad95d5010cb9c55f02ab87e200997b07ccdb8316e22807fc': {
            1: ('symbol', 'text', 'Ass', 'algebraization-lemma-algebraize-local-cohomology-general'),
        },
        'sha256:2e904f864a7150305c092e85784847edc8cdb20d12e007c3d75320587bfb815b': {
            81: ('symbol', 'text', 'trdeg', 'algebraization-lemma-blowup'),
        },
        'sha256:373ebe5f0af0f5e722336b2fa2617726b5434b6d02847d6c1ff6e3008fcfbc51': {
            4: ('symbol', 'text', 'Ass', 'algebraization-section-algebraization-modules-local'),
        },
        'sha256:4315a4dc21b681ba899f07a4e0fa1bc394f35cbe750d3fa5e61eb3f54e6bc0d9': {
            5: ('symbol', 'text', 'codim', 'algebraization-section-distance'),
        },
        'sha256:550874bb5dd4fc7414eca48d259288e4845fadd24ddad173bd681db2f9a4013d': {
            12: ('symbol', 'text', 'Pro-', 'algebraization-lemma-recognize-formal-coherent-modules'),
        },
        'sha256:56b098ac797f2e5947b88edb76fbd949a35e43140e09269b23133afae7df07d4': {
            1: ('symbol', 'text', 'Ass', 'algebraization-lemma-fully-faithful-very-general'),
        },
        'sha256:5801edd01f3ead9002f758fbe50a0d6401390c4257b9d297313827c033a3da7e': {
            10: ('plain', 'text', ' of ', 'algebraization-section-algebraization-modules-yet-more'),
        },
        'sha256:600be7b41e1f16c3a723095e78ee558c19265f71269594aa1d3511297d49c86b': {
            6: ('symbol', 'text', 'Ass', 'algebraization-lemma-algebraize-local-cohomology-general'),
        },
        'sha256:64befe619e13881a1dcb35a45bb0af2f8114902bdab54ddc48bb5f1a938c2694': {
            5: ('symbol', 'text', 'codim', 'algebraization-section-distance'),
        },
        'sha256:71afd0d1c1f47f8fa2fb05b476da6ce5559c052987efe970cba840d336c5f556': {
            1: ('symbol', 'text', 'codim', 'algebraization-section-algebraization-modules-yet-more'),
        },
        'sha256:816514d6aaa1a33dc9fdf5b38dc2b559e85372795ed156205d80e7f48586a22a': {
            6: ('symbol', 'text', 'codim', 'algebraization-lemma-change-distance-function'),
        },
        'sha256:8a1772ec349639affd752cf4bc492a145d0a92289698b04949bc02059cf2d702': {
            13: ('plain', 'text', ' open', 'algebraization-lemma-equivalence-better'),
        },
        'sha256:9ba5766e2f6a510f431b9fa4eaaa5fe3d18c9c25fc7f5d4785617e950dbab745': {
            3: ('symbol', 'text', 'Ass', 'algebraization-lemma-application-H0-pre'),
        },
        'sha256:9e76010776ed59140328fb975b886fe69d1c32bc70fbcc6ef9e78e6ec47f034e': {
            13: ('plain', 'text', ' open', 'algebraization-lemma-surjective-Pic-first'),
        },
        'sha256:a66ddbc7af5d075e180b000d8e60f521f1dbe0d2a3e800ff7dcd57d4e5f2ee33': {
            16: ('plain', 'text', ' there exist specializations in ', 'algebraization-section-distance'),
            54: ('plain', 'text', ' with ', 'algebraization-section-distance'),
            60: ('plain', 'text', ' and ', 'algebraization-section-distance'),
            69: ('plain', 'text', ' immediate', 'algebraization-section-distance'),
        },
        'sha256:ce47dd2233788684a39933a2d969b6450f7094dea637fb29359bc1f72e9a3af9': {
            1: ('symbol', 'text', 'Ass', 'algebraization-lemma-fully-faithful-very-general'),
            9: ('symbol', 'text', 'Ass', 'algebraization-lemma-fully-faithful-very-general'),
        },
        'sha256:d18aa3c2e8f5d495eaff105fa8f5959116095fdcb0b90748fabf839691b58b5d': {
            1: ('symbol', 'text', 'codim', 'algebraization-lemma-discussion'),
            13: ('symbol', 'text', 'codim', 'algebraization-lemma-discussion'),
        },
        'sha256:dc43dcd9007ff841f1d1bbc3150548a1ac012094d959674794010bacdadb057a': {
            10: ('plain', 'text', ' with ', 'algebraization-lemma-bootstrap'),
        },
    },
    'artin': {
        'sha256:02d14856adb022d6ba3ce917f9dbeeac65254540e4f08898296f4e8f426222a1': {
            9: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:09d3e9acd7b699bc12b961141f520d9943714bfb9239a877bf1ea84f846d8f84': {
            4: ('plain', 'text', '-algebras', 'artin-section-openness-versality'),
        },
        'sha256:0a9b210c7fc5236a88e1b8d7ef6cc065d44d01bb549c411791e7a565b172b0b5': {
            2: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:0c9a19a32579eca92851d410eafcdda9a9b35bfeb05822e4f7b2c7c7a4f74ccf': {
            6: ('symbol', 'textit', 'Noetherian', 'artin-lemma-representable-limit-preserving'),
        },
        'sha256:0ded83d046d3f599c8fb12798213ac8e5763db75ef776d857d032c3a0de00dc5': {
            11: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
            25: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
        },
        'sha256:117d8f5d65ff42e015edcdb40965c853d433ea13b8c5775b19d2a08abcf882a2': {
            37: ('symbol', 'text', 'Inf', 'artin-lemma-finite-dimension'),
            49: ('symbol', 'text', 'Inf', 'artin-lemma-finite-dimension'),
        },
        'sha256:12f63e3847ee163eeb2dee0b35be15015176f49a604e42253dd38013478faf4e': {
            2: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
            26: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:1a6ef5a897e17303045d8f545b682ce0dfb59d117a9e6a2bdbfdddbaa84c643a': {
            4: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:1d702ed54f9788881bce370dafb836c5c57f65589144336ad1ad96d2ead0a930': {
            1: ('symbol', 'textit', 'An', 'artin-section-contractions'),
        },
        'sha256:1dd5d36fd99014b2b1f3df239c906d1614145da8b663d46cbcc00f99e3cce894': {
            5: ('plain', 'text', 'objects ', 'artin-section-formal-objects'),
            7: ('plain', 'text', ' of ', 'artin-section-formal-objects'),
            12: ('plain', 'text', ' such that ', 'artin-section-formal-objects'),
            23: ('plain', 'text', 'where ', 'artin-section-formal-objects'),
            25: ('plain', 'text', ' is Noetherian complete local', 'artin-section-formal-objects'),
            27: ('plain', 'text', 'with ', 'artin-section-formal-objects'),
            32: ('plain', 'text', ' of finite type over ', 'artin-section-formal-objects'),
            41: ('plain', 'text', 'formal objects of ', 'artin-section-formal-objects'),
        },
        'sha256:20629eed262dcc4291ac8ea5553bd136988f82f0e08610288d4ba0a92671b501': {
            21: ('plain', 'text', 'Artinian local ', 'artin-section-introduction'),
            23: ('plain', 'text', '-algebras with residue field ', 'artin-section-introduction'),
        },
        'sha256:271a6e33fa0a67e1fb6667d6c69083197b6b85c729fbbdffd1a5f701483fba44': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-introduction'),
        },
        'sha256:28e752d47c4083af8566380e6eab2643e7ccbe8b6d47191f5a6727fcd3946d65': {
            17: ('symbol', 'text', 'Inf', 'artin-section-inf'),
            40: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:2b3c4129b8941806a8a46a8d85ba4b12fdad0f1edb12b3a0072f6261b5b0e2d9': {
            21: ('plain', 'text', 'with', 'artin-lemma-diagonal-representable'),
        },
        'sha256:31c8c9482fb77a726572475678209dbccf8c7151f4c470b38d82311f9c10a9df': {
            34: ('plain', 'text', 'lying over', 'artin-lemma-single-point'),
        },
        'sha256:32d7afa0aaff1a4e593b46d80c3aef25ef831704fffff514d3dd2fa1dfb24557': {
            2: ('symbol', 'text', 'Inf', 'artin-lemma-finite-dimension'),
        },
        'sha256:32e44d5c1f9cee65aeb01b7a5d727b66ae528640482f02864c42ae0cc2a07bfa': {
            8: ('symbol', 'textit', 'Noetherian', 'artin-lemma-representable'),
        },
        'sha256:352c42023d12d4c5c5bfd85d66bf6dfdcc7de3a450adb09570b74455b005ccac': {
            12: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:35ee6cc07bbb3b4c2059375a7cf3ccfeb642efbdf15f943ebc1686e69b31a821': {
            2: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
            21: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:3700def95f44783c3e2426d81b193b88793af6607bfe9e9597964d9ac3d8de4b': {
            2: ('symbol', 'text', 'Inf', 'artin-section-tangent-spaces'),
        },
        'sha256:3cc6b17206a08f62e924cb06752b51d51253f1e2cd227e27005fcdf9273bb9d7': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:3e9e85f92b5454df89b16cc22031c26e0ed434904bff14c0b56168cb67852886': {
            3: ('symbol', 'text', 'Spf', 'artin-lemma-limit-preserving'),
        },
        'sha256:3f6aa0cf38c0f1056d9013a58e615c6e58c3564ae2c84d30be721c21b6da1de6': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:40623e6d65c315cc69b44bd33e3f5a491b94b4a1f51eecd99a1bed24d96bb92e': {
            3: ('plain', 'text', 'for all fields ', 'artin-section-openness-versality'),
            5: ('plain', 'text', ' of finite type over ', 'artin-section-openness-versality'),
            7: ('plain', 'text', ' and all ', 'artin-section-openness-versality'),
            26: ('plain', 'text', ' the', 'artin-section-openness-versality'),
            28: ('plain', 'text', 'map ', 'artin-section-openness-versality'),
            67: ('plain', 'text', ' of predeformation categories is smooth', 'artin-section-openness-versality'),
        },
        'sha256:455fb670c2d1a1e7ddf9538e53ab42cd46e11ba90c21529c81f24ae5f8c3599d': {
            1: ('symbol', 'text', 'Inf', 'artin-section-inf'),
            16: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:4c27ca3cafd8c8c0adf844e27c7105f8035e8bbbbe918af1c6993bf4a85ff9f8': {
            1: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
        },
        'sha256:4c4e59425c348b64ac4b35b2acf0d248c683d6dd477554c32feaf4c2cc993ed3': {
            3: ('symbol', 'text', 'Spf', 'artin-section-contractions'),
        },
        'sha256:4cd353ffeee4cbfe753bb148e603d77bdf008f9bdd70928d879a97d79de4da1e': {
            1: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:50782be48f5f35ac0366d56a98575fd6ca3234c67a2051e2311b92dbc02d5df4': {
            12: ('plain', 'text', 'if there exist ', 'artin-section-openness-versality'),
            24: ('plain', 'text', ' such that ', 'artin-section-openness-versality'),
            44: ('plain', 'text', ' and ', 'artin-section-openness-versality'),
            57: ('plain', 'text', 'else', 'artin-section-openness-versality'),
        },
        'sha256:50e05f312bb3b93b4ab53e8c9e924f168f9f899e2e73a6faba5600d97b635b5a': {
            6: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
            16: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:5235bc702974e7ac27175f9d21945f344bdbb1e45b78acd999e759891cc1edae': {
            10: ('symbol', 'text', 'Inf', 'artin-lemma-fibre-product-tangent-spaces'),
            35: ('symbol', 'text', 'Inf', 'artin-lemma-fibre-product-tangent-spaces'),
            56: ('symbol', 'text', 'Inf', 'artin-lemma-fibre-product-tangent-spaces'),
            81: ('symbol', 'text', 'Inf', 'artin-lemma-fibre-product-tangent-spaces'),
        },
        'sha256:58b0416f01b671b6cd5c23833ea606a07a6920030cc43b58e4d20964a06d2755': {
            4: ('symbol', 'textit', 'Noetherian', 'artin-section-algebraic-spaces-noetherian'),
        },
        'sha256:59afd3c12c5bcfda5e10f2fb7e28d76614a27468d64bf12ff11dbadd196f2d35': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-proposition-spaces-diagonal-representable-noetherian'),
        },
        'sha256:5ac2728db1e0c0092bbc229f79f76cdfa8f2af513c9f46e8d66891e30ac58c08': {
            1: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:5c2d35088f92f65094883eaf870873ad14fbf8b23ab3f3df08b55889ea7eacd1': {
            2: ('plain', 'text', 'images of ', 'artin-lemma-limit-preserving'),
        },
        'sha256:6f4cd6d77751069e5cf5ea7da231a5233dad63dd1a6064bd821f3f9d5a66af38': {
            1: ('symbol', 'text', 'Inf', 'artin-lemma-finite-dimension'),
        },
        'sha256:6f988ba2cdfbbc08b7730b098b2199a08b86030d3c4c9622d7896549c9cc27e0': {
            4: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:77464701df3e7842db9f6cd6b184258165c21fe74da712f52fcf70dc6df4d656': {
            1: ('symbol', 'text', 'An', 'artin-section-contractions'),
        },
        'sha256:7ffd6f495cee558e6e19322deaff915b0d363dcef8e0cd3f2d59d27828188569': {
            32: ('plain', 'text', 'lying over', 'artin-section-versality'),
        },
        'sha256:8b3e14432d157180bcf270f499e2334d673543ef48d8e2ff1af4fd31fb4c4f74': {
            1: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
            11: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
        },
        'sha256:8c309b7c49d47cf434bd93a741d67e4c746a3377efe770e0724c4f2c6870a639': {
            24: ('plain', 'text', 'isomorphism classes of morphisms', 'artin-section-tangent-spaces'),
            31: ('plain', 'text', ' over ', 'artin-section-tangent-spaces'),
        },
        'sha256:93e2790093d1422c630a3c8fb0e7b1691ebd3711ec4a6126b7af003ed7a809c7': {
            5: ('symbol', 'text', 'Spf', 'artin-lemma-formal-object-effective'),
        },
        'sha256:9e48898eff3a3e5e759b93f8587e6fcc5adb75534c8c4fd979f3086c216e6ced': {
            25: ('plain', 'text', ' such that all have the same image in ', 'artin-lemma-get-openness-obstruction-theory'),
        },
        'sha256:a4e088a1ab3f47a2fa7b85dee5bd561697f6b359e589750eb6590c479c5f211e': {
            56: ('plain', 'text', 'lying over', 'artin-section-versality'),
        },
        'sha256:a4f87854a8ff956c74453868eeba137bf989574908e4a6295e197da42dbceeef': {
            1: ('symbol', 'text', 'Inf', 'artin-section-tangent-spaces'),
        },
        'sha256:aa632d24eeb311a47e46c7a745f2d257f23d8d91520ec69b1b876d36067301f6': {
            2: ('symbol', 'text', 'Inf', 'artin-section-inf'),
            30: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:b0f6fe59df294e9f2812777f5dc8354981e3575692d489f89584f3662daba429': {
            5: ('plain', 'text', 'locally Noetherian formal', 'artin-section-contractions'),
            7: ('plain', 'text', 'algebraic spaces over ', 'artin-section-contractions'),
            13: ('symbol', 'textit', 'An', 'artin-section-contractions'),
        },
        'sha256:b1c6f80ff7279126bbd76f4754d418acee465a3f0ed56d7492bf006bf5d1b3e3': {
            39: ('plain', 'text', 'lying over', 'artin-lemma-approximate-versal'),
        },
        'sha256:b4abc720568738bb6a0345985fb204e6d11fe5329db63917b4eba3531bfbea64': {
            2: ('plain', 'text', 'Noetherian', 'artin-section-algebraic-spaces-noetherian'),
        },
        'sha256:b77d32de16afb09a907dfd19b02dfd19b0d2008ca172693997dca50eb8b9ffb9': {
            10: ('symbol', 'textit', 'Noetherian', 'artin-lemma-representable'),
        },
        'sha256:b78ced47239eccd3c7b67fa235e1ac0eff6a290ac548de605d4cd6188313a189': {
            10: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
        },
        'sha256:bad87655bdb2946536eaed4b9ab9f0f741fbef467d30eb01709edda012102550': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:bb833a54888808b7dd63b6433462e1b17f4e1ada4cecb1378d7e8255a2ca328f': {
            2: ('symbol', 'text', 'Inf', 'artin-lemma-properties-lift-RS-star'),
            10: ('symbol', 'text', 'Inf', 'artin-lemma-properties-lift-RS-star'),
        },
        'sha256:cc43d013ddf216368211002c9f909efb657ed8d8cdc3b6244a8e50bdc1db2630': {
            8: ('symbol', 'text', 'Inf', 'artin-lemma-properties-lift-RS-star'),
        },
        'sha256:d014e3a9dcc16b4d078495516b63e52e1dac90b534162bfeb5aa9bdb6e327428': {
            34: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:d1078c20fd6a3e09ec09bc7d88624d29043aab748b4cdeab6b6e439ed714c6a9': {
            11: ('symbol', 'text', 'Inf', 'artin-lemma-properties-lift-RS-star'),
        },
        'sha256:d9592505480a058567ce11e42902219d1ce5d866f3f2f6197d6fc48a6be1b3a7': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-noetherian'),
        },
        'sha256:d9e0f17b0650a526d25695262943786e69a0501ba9d224145d24c27410560291': {
            29: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
            55: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
            81: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
            92: ('symbol', 'text', 'Spf', 'artin-lemma-closed-immersion'),
        },
        'sha256:ddcf63536e2d592caefa054283cf283d01e11707dfcacfa6d20835daae98709d': {
            16: ('plain', 'text', ' factors through ', 'artin-section-versality'),
            22: ('plain', 'text', 'else', 'artin-section-versality'),
        },
        'sha256:dfb94cee3f7fb4cb757f09633ba8c39d560a1701cc23ea2837fe8334b53f9eae': {
            60: ('plain', 'text', 'lying over', 'artin-lemma-single-point'),
        },
        'sha256:e0748be3c04b9dd5f5cd757317e8df071d16646d3e8d193a7247d079f2ff809c': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-algebraic-spaces-noetherian'),
        },
        'sha256:eac095f48e19bc2e948a9e6b75f1b98197b952cff3d822b801ade0afa39909ab': {
            32: ('plain', 'text', ' is a ', 'artin-lemma-finite-dimension'),
            34: ('plain', 'text', '-algebra map and ', 'artin-lemma-finite-dimension'),
        },
        'sha256:eea21e13ea2ccddcd2ff7e1bd2ef991b749fc48ef7846ee383c35601a2680d9a': {
            1: ('symbol', 'text', 'Inf', 'artin-section-inf'),
        },
        'sha256:f3e168c0fd5c8b534d8910a6b1bfd63debc9a483610196b173335ee8d4da15e5': {
            13: ('plain', 'text', ' lying over', 'artin-lemma-infinite-sequence-pre'),
        },
        'sha256:f5515f20d628df76053102c6014bc2d7e6ec91d5edad51aa5112a49e5b648f8f': {
            1: ('symbol', 'text', 'Inf', 'artin-lemma-finite-dimension'),
        },
        'sha256:f7f6d34d38b3bdc8ca5866a8a18e47723d6663842c943c48ddaf77698d857cde': {
            3: ('plain', 'text', ' is versal at ', 'artin-lemma-versality-matches'),
            9: ('plain', 'text', ' is versal', 'artin-lemma-versality-matches'),
        },
        'sha256:faec145eed71ba500a9ea16fe0044a4ce08b5fa8fc811af94e727ea8fc7e2928': {
            2: ('symbol', 'textit', 'Noetherian', 'artin-section-algebraic-spaces-noetherian'),
        },
    },
    'moduli': {
        'sha256:1572786f6127a051593112fe5f76e36eab6b892cb21d9c54a8a955f8ea84a512': {
            13: ('symbol', 'text', 'Proj', 'moduli-lemma-quot-Pn'),
        },
        'sha256:3275dc014bc2a51fb5e7ac26360fad8eac6ab6ef06005daa3070f34619e15016': {
            20: ('plain', 'text', ' finite', 'moduli-lemma-open-P'),
        },
        'sha256:515cbbf52ffa2dcd772705e31e3eb77585048c8647d49467d3943561174369a7': {
            1: ('symbol', 'textit', 'Curves', 'moduli-section-introduction'),
        },
        'sha256:7f44281f8da3f1cb3d41d7b68a96b0a6cd101be384061665fe91213b2c2e9856': {
            15: ('plain', 'text', ' numerical polynomial', 'moduli-section-stack-coherent-sheaves'),
        },
        'sha256:9ac4aef9ff2b8035c1771a4a8de0181647d9c4445ab692740a59bc4f7281ee7c': {
            37: ('plain', 'text', ' isomorphism in ', 'moduli-lemma-complexes-diagonal-affine-fp'),
        },
        'sha256:c5c4b0ec2e70118007381e3b318e36ded66096dbcfd666672374a52060e708e0': {
            12: ('plain', 'text', ' finite', 'moduli-lemma-open-P'),
        },
    },
    'stacks-morphisms': {
        'sha256:006f6b859bb5ea7bfd2aefa3fb419469224db0e018c6156c6cb9bb8bc90ebf4e': {
            6: ('plain', 'text', 'local complete intersection', 'stacks-morphisms-section-lci'),
        },
        'sha256:0431ebac18a9619d6acc4978c43ab66804c4729c169bfea706a39dba898c1d20': {
            6: ('plain', 'text', 'locally of finite type', 'stacks-morphisms-section-finite-type'),
        },
        'sha256:05bc2b8b356d4a7206903ac14900af0faf3d3ff0d073693c4da2e08ed5962e05': {
            6: ('plain', 'text', 'locally of finite presentation', 'stacks-morphisms-section-finite-presentation'),
        },
        'sha256:0d52a21929a219ccb3a7c6238eb7e18308cc2d106e04388fab0d10dddd5cb6bf': {
            15: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-enough-finite-type-points'),
        },
        'sha256:0f1bee4ebd4b958205e76119f21c97e4932204cf2cdfffd87569a52f816630e3': {
            8: ('plain', 'text', 'fraction field of ', 'stacks-morphisms-lemma-universally-injective-point'),
        },
        'sha256:1e81c2d0b4b050719a5af36a96f7bb2580133a095d8523d2de60272ca35981ba': {
            12: ('plain', 'text', ' lying over ', 'stacks-morphisms-lemma-every-point-residual-gerbe-quasi-DM'),
        },
        'sha256:3b5858b0b0d2091bf2a3435f99e9cd1409f2563243537854bd4db77675804974': {
            8: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-identify-finite-type-points'),
            23: ('plain', 'text', ' smooth', 'stacks-morphisms-lemma-identify-finite-type-points'),
        },
        'sha256:4d1b677a50ccbd1fead614716bf20a2400135d9853c73de934b6294d3d5f91a3': {
            6: ('plain', 'text', 'smooth', 'stacks-morphisms-section-smooth'),
        },
        'sha256:540f41c106658171d93db79cc88c379c9e66906a33c32143c108d1b709f3f2c1': {
            9: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-enough-finite-type-points'),
        },
        'sha256:54925b006fa97808a280cffcba58d84f6c19112d2e4d00fe7e700e588a9c7a90': {
            9: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-surjective-morphism'),
            19: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-surjective-morphism'),
        },
        'sha256:5b469692f023895ea8f8873f5d44f5dea835a825a58124d41caec724127c6cb2': {
            7: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-section-points-finite-type'),
        },
        'sha256:6d28c8850ff2cd3464e1b2d84db145ce5f02a94f642db7bc30acbb05c971ffe9': {
            12: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-morphism'),
        },
        'sha256:6e0d9504e19d33e22a2fbc15f05902d33f998d88e8a6d3e965af2be253a625fa': {
            5: ('component', 'text', " is \\'etale", 'stacks-morphisms-lemma-etale'),
            13: ('component', 'text', " is \\'etale", 'stacks-morphisms-lemma-etale'),
            18: ('component', 'text', " is \\'etale", 'stacks-morphisms-lemma-etale'),
        },
        'sha256:740c0a24b40dbd02ad2686036645e9a7fb5a47c0738a3e2f2107a7f7fe0f26d2': {
            6: ('plain', 'text', ' Noetherian', 'stacks-morphisms-section-noetherian'),
            12: ('plain', 'text', ' locally Noetherian and ', 'stacks-morphisms-section-noetherian'),
            36: ('plain', 'text', ' quasi-compact', 'stacks-morphisms-section-noetherian'),
        },
        'sha256:7a39ff69605864162b0037b02b7bd3b4f8a7450036524a8eba4280fbb98463ce': {
            6: ('plain', 'text', 'flat', 'stacks-morphisms-section-flat'),
        },
        'sha256:8391c72a441107f312c0a8c81085ebd4dc661614c41101a92a1dbaabd759988e': {
            14: ('plain', 'text', ' is finite', 'stacks-morphisms-lemma-property-automorphism-groups'),
        },
        'sha256:9478b9381b8f510779544ca2f33194f4ab8cc9600e359cdb164b105a748ed6a0': {
            9: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-morphism'),
            19: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-morphism'),
        },
        'sha256:96238cf5fe48b4d9248490430d7bece429688b0088ae1a0966cfcdc7bb3ebdc9': {
            7: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-point-finite-type-monomorphism'),
        },
        'sha256:b53ad331179cca9847a83841b3214c576fca8118799b86ce4b064f670e5b781a': {
            46: ('plain', 'text', 'with points', 'stacks-morphisms-lemma-flat-at-point'),
        },
        'sha256:d3c736ee7410a2814b1639d536e38c811ed2afc3eed9491bbe8d06b1ecb961fc': {
            32: ('plain', 'text', 'Categories, Equation', 'stacks-morphisms-lemma-cartesian-square-inertia'),
        },
        'sha256:d52ae9da58b1dd0b63d105ec15a97d8a8740fd7c06a647e975da60af99347901': {
            9: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-finite-type-points-morphism'),
        },
        'sha256:d673e02c8a31345651afd49f0fec8db7a349e99b2901898519622d76364aa2bb': {
            5: ('plain', 'text', ' is unramified', 'stacks-morphisms-lemma-unramified'),
            13: ('plain', 'text', ' is unramified', 'stacks-morphisms-lemma-unramified'),
            18: ('plain', 'text', ' is unramified', 'stacks-morphisms-lemma-unramified'),
        },
        'sha256:e64fa72e12c2289897bd95955e83fa76d790ce96cc11178ff369c7891b071116': {
            9: ('plain', 'text', 'the projection ', 'stacks-morphisms-lemma-check-property-after-fppf-base-change'),
        },
        'sha256:e85dfab5f237efbbca8ca01458e7ee9409cd817bca29ec0dcc8ed4ce7e098863': {
            7: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-enough-finite-type-points'),
            16: ('symbol', 'text', 'ft-pts', 'stacks-morphisms-lemma-enough-finite-type-points'),
        },
    },
    'stacks-properties': {
        'sha256:05164f9795ed40a28247de474418863e5504bd3b49eff24fd3aab98b23330b27': {
            1: ('symbol', 'text', 'pr', 'stacks-properties-lemma-representable-in-terms-presentations'),
        },
        'sha256:1ba3941894f6f0488eaef27c6b36508e2ab139b472582f6ed65c2c1e38d747ac': {
            2: ('symbol', 'text', 'pr', 'stacks-properties-lemma-representable-in-terms-presentations'),
        },
        'sha256:38c730c4ffb88a7d2d4314217b68c4f0af0d581f095d194fb05e0fa61188f020': {
            18: ('symbol', 'text', 'pr', 'stacks-properties-lemma-representable-in-terms-presentations'),
        },
        'sha256:444c5e144b2b0988aed272a9753c3654a9ca31724f0c5b7ddde7d44c755663fe': {
            1: ('symbol', 'textit', 'Spaces', 'stacks-properties-section-properties-morphisms'),
        },
        'sha256:536f1ad40f0e6de89b78259bb90390f2d253d3f672b4950981888992d448aa87': {
            9: ('plain', 'text', 'the projection ', 'stacks-properties-lemma-check-property-covering'),
        },
        'sha256:958aa6efc51046c1a1a93e827ec7fbbc434ee800436b7ec3daa3cfbb0dae2f7e': {
            5: ('symbol', 'textit', 'Spaces', 'stacks-properties-section-properties-morphisms'),
        },
        'sha256:a9eb5a7f262bc6848b6ff562fc634b97c3e7bcf56be4315eef8bb4feb77dc28b': {
            2: ('plain', 'text', 'locally closed substacks ', 'stacks-properties-lemma-substacks-presentation'),
            7: ('plain', 'text', ' of ', 'stacks-properties-lemma-substacks-presentation'),
            14: ('plain', 'text', '-invariant locally closed subspaces ', 'stacks-properties-lemma-substacks-presentation'),
            16: ('plain', 'text', ' of ', 'stacks-properties-lemma-substacks-presentation'),
        },
        'sha256:ccdf49d0761ca2bc51d852984463ce70b56d9321311f9f884f83bce4f45928df': {
            1: ('plain', 'text', 'smooth', 'stacks-properties-lemma-local-source'),
        },
        'sha256:d768526b646548e7075c65818854af83168b567dc14e78fcfd532d7957b90e9e': {
            9: ('plain', 'text', 'the number of geometric branches of ', 'stacks-properties-section-irreducible-local-ring'),
            11: ('plain', 'text', ' is ', 'stacks-properties-section-irreducible-local-ring'),
        },
        'sha256:e64fa72e12c2289897bd95955e83fa76d790ce96cc11178ff369c7891b071116': {
            9: ('plain', 'text', 'the projection ', 'stacks-properties-lemma-check-property-weak-covering'),
        },
    },
}

TRANSLATED_ROLES = {
    'sha256:03d148bd82d3874ceaec2916f00ecf7de17366ad217c2fbea638d29c12669f3c': ((19, 'plain'),),
    'sha256:1023326bee7c7bb05b8a1fd182075947f93a7b1f41ca8a90cf59f1e2542682ef': ((27, 'plain'), (53, 'plain')),
    'sha256:153db947a74e4f6c7113da4d5e68de3a2ace0486371f17fea8c44e6ef6c8d646': ((13, 'plain'),),
    'sha256:2041d2e13d710fb707fa7e3ec5d5c4ad33c30bcb263991d5f4082b3a54210cbe': ((18, 'plain'),),
    'sha256:225b7a998d5d14cdaf4f0933f333d9e8ba3834cc21f288365ffabfc7aed5f925': ((15, 'plain'),),
    'sha256:2cbf53ac253ade05c25fd2815632c525ac9a11710623e0b8f85faa5454c45e76': ((12, 'plain'),),
    'sha256:3ec029a37186350113a5ca817a5f2543c70b83c03dd308542ad6aff4df6f6f1b': ((9, 'plain'),),
    'sha256:5093f4488e290ca4efadc93fd3a5cf9d4d192c8a920c4912b424f6e279862612': ((26, 'plain'), (32, 'plain')),
    'sha256:6990e7a927de3d268c365cbb56e76740c49c317013cf07c8e69485d9dfd6b039': ((24, 'plain'),),
    'sha256:7ecaff8e1cf1e74af325c8f2cf98c980e3fe71573bb5422a538a5727ab9f4383': ((19, 'plain'),),
    'sha256:80903d5c612a4ac69be596e18931be2f7a609cec463c9f0e16ebd376e0412bf6': ((26, 'plain'),),
    'sha256:82552c377b56a64fd74a008606811dcaed432c90525b894bf5d6b5654429bd39': ((23, 'plain'), (40, 'plain')),
    'sha256:8796986582bad71cdf75aa3c7b462e22cb93a93397f6811cc10712c3a4cb8959': ((51, 'plain'),),
    'sha256:9f3f3e9f9a96e49742a0cfe7ae5a4b3665363a54e8dc5b3dcfa75a6205e80ef5': ((18, 'plain'),),
    'sha256:a07a91d0c6806ef42306031dc9de466bf8041f6769a30e2616d1242cc1770110': ((32, 'plain'),),
    'sha256:a52202be83b2d93567be003438f9ffac9c70b48f5287716595e785771b905772': ((9, 'plain'), (12, 'plain')),
    'sha256:c83a0088f569471af8ca34647421382bf1081a4ac4485274c04b9a80a95d328c': ((22, 'plain'), (69, 'plain')),
    'sha256:d2a2e33eb32573bf15836dc1e300795ad02c096cdd24267782310e3108b245db': ((36, 'plain'),),
    'sha256:d5bf80efc5f44855210e037b107a60aea03fad051ac6029b5a82f864d3aed64f': ((13, 'plain'),),
    'sha256:dd931061499f022e7d899bbbd0e23e0e63da87dc84bdf0807e274bf0ec4af2d3': ((97, 'plain'), (111, 'plain'), (131, 'plain'), (157, 'plain')),
    'sha256:dec1ba83002a926108e0a907c1603c949668a145efcac79f2a08bf5b6fde2e62': ((10, 'plain'), (40, 'plain'), (50, 'plain')),
    'sha256:df7544d3c16ab2e21bca7d7bb2cc4bc27fce07194f615ce4fca43f6caed60f52': ((31, 'plain'),),
    'sha256:e29111f70b806499ed2c92c27c24bc0b06001461d1c249caca9e425dc84f2f53': ((10, 'plain'), (21, 'plain')),
    'sha256:e7b4d6566b66092b9f443f1099f4c32c80e779b98ee306567352b1fbc0ac5d18': ((50, 'plain'),),
    'sha256:eb4d4702ca4125378f53a754b099f3f628399e9cda29a6ebb3cf68c5a60db2a7': ((39, 'plain'),),
    'sha256:f71dfac46b22a456b8dd4f19e6519fc01b7f21dc77873a67a1e95a11b2488c57': ((23, 'plain'), (34, 'plain')),
    'sha256:ffa7b1fac499434cbe8ad44a3b51cf9b3f33800e80b0e6dba42f5b76ce6ddc6d': ((2, 'plain'), (4, 'plain')),
    'sha256:0474a69dd463f79b62afde1104837afc371ddfab0cd6c20781cad35f7346f4c3': ((32, 'plain'),),
    'sha256:094a35da6f8cceb7fd16aca9c364e2f7b607b328662313a355a7a6f9bb199d7d': ((24, 'plain'), (31, 'plain')),
    'sha256:0ea5a37f25f7573a58fcf8f7eb8b5fd1628879c423fcb1aaaf8c4ef731559543': ((8, 'plain'),),
    'sha256:0ec6a01ed6079fe9450780181557bb77252f7c69a17df85d41967d979ed5d77c': ((5, 'plain'), (7, 'plain')),
    'sha256:0f32de7b922c59aa2ac7def469a194a7563a31b3655b0c982e06b8607acc743c': ((12, 'plain'),),
    'sha256:1298712e48a626107efd3fc99df01f4f1f408999e645339bb9e7747eeb94a6b9': ((46, 'plain'),),
    'sha256:29db8e7a1851b1b663fee35c892db6ff3fece23ceeb6dbfb27a6f76915a6632f': ((10, 'plain'),),
    'sha256:329a7b52bdd6db07d2202b434809db82914b39961463651c06c5e09aaf8705eb': ((12, 'plain'),),
    'sha256:36e73ba5739effe200832c8c9705486f2c545c1a65ee91a5acf37cc1976e276d': ((5, 'plain'), (7, 'plain'), (12, 'plain'), (23, 'plain'), (25, 'plain'), (27, 'plain'), (32, 'plain'), (41, 'plain')),
    'sha256:38c97aad49373d2389ef1be8b492207df50f137671bd3d48b44b4737ff85595a': ((13, 'plain'),),
    'sha256:39e45452ba5b5496865177c3c29bd1e6b5a375d7539c6d02a1c75f9c86665734': ((16, 'plain'), (54, 'plain'), (60, 'plain'), (69, 'plain')),
    'sha256:4886dac56aa933f9ea350b873437f3659253a479ac3955067de19c47625b6a8b': ((57, 'plain'),),
    'sha256:4d01c9deb54b6b926ebbd453ef1795f3fc0052e200787ba7064148508e482fb0': ((3, 'plain'), (9, 'plain')),
    'sha256:5358bcae82fb5b2b1b1c28f6bad108dd03c68cc2caa53da4da2a7feeb3c0dc67': ((32, 'plain'), (34, 'plain')),
    'sha256:55862398ac5858787dbfb986e159a1c923d0f62abcfe450d5304c85efeec0c41': ((16, 'plain'), (22, 'plain')),
    'sha256:5b84d2ac4e1c0a6d270305a1e6649cbf6e5ce6300e48e36f90944f84ac97706e': ((2, 'plain'), (7, 'plain'), (14, 'plain'), (16, 'plain')),
    'sha256:5e9642f15c193c354992a9f6baa46facd41d7dfa4841bee5ebc4a636a4b054b2': ((4, 'plain'),),
    'sha256:606e16efb9f6e1201ed30c13a5e236102584a109758b379e4f66583dc5a5d0d6': ((5, 'component'), (5, 'plain'), (13, 'component'), (13, 'plain'), (18, 'component'), (18, 'plain')),
    'sha256:63a24e499b73ccb51a7424abb365f9942d81738ae7d668eb5e9e717cce34e65c': ((20, 'plain'),),
    'sha256:687877f3d440dcd6ef181d599a242c25ac2920c3980631d5d8cc385f4aaee371': ((2, 'plain'),),
    'sha256:700ce4038551349b7ecd97dd329d42f91ee7b82504d3827bbece35033f7b2fe2': ((2, 'plain'),),
    'sha256:738274662f612a081699d8a9b6febed46bf6f17a2650f0f417122ad80a19cac5': ((56, 'plain'),),
    'sha256:771f4ee6f8ddfbcdf0b7c4e1c4dd7660325b306b896500438cb10207a35ccb3a': ((12, 'plain'),),
    'sha256:7a2f23fcd922ce3f8985a4f2c62a962b01eea0f871eaa83fc0d91832dc853953': ((23, 'plain'),),
    'sha256:80e7f24728f5ac2dcc6fcf86d2cf63f4c1c66363b885cb0cc776ebc2c2ac3005': ((9, 'plain'),),
    'sha256:81760cae72aad5f5ef974ba881b37535756d60b185b52318477bf6cd9573aa00': ((21, 'plain'), (23, 'plain')),
    'sha256:8734f410b3c58934377e5b6e674cc9a2f714687fc71d577bff8d87f93f78dc9c': ((13, 'plain'),),
    'sha256:91abbf3de4603e0fff5d74da646e4a19e16d9a5920b16aabff63a97425ebba1b': ((10, 'plain'),),
    'sha256:92ce6fcecb6b04b03115d8dc88e34aa2916cd442d210f3815c824a58371db643': ((39, 'plain'),),
    'sha256:9d14115e2d9ad8e64d0a19d93836cc23aecaddcd14fec52c9abef7065d011b71': ((6, 'plain'), (12, 'plain'), (36, 'plain')),
    'sha256:9d8d7b37b801241c3e266ff0d27173f0dfd70824090514ad044def4e0ac622e5': ((21, 'plain'),),
    'sha256:aa8a92c4f7abb5770cbf006a02c0a26dd9beca91f53803fb2f85f40ead10b8c4': ((12, 'plain'), (24, 'plain'), (44, 'plain'), (57, 'plain')),
    'sha256:b20b65b9906b1e3353c3c3d14d09adb14e5902024ec642bed95fe56d1f099808': ((6, 'plain'),),
    'sha256:b782a1d8a41bd37b9c07771fb3190d338ba2bb9670589692c96bc80128d1c08b': ((34, 'plain'),),
    'sha256:bde1273045b935699da713d39895b0ab0fae737833991f9f6622ac99a15398ff': ((13, 'plain'),),
    'sha256:be2d8ca71172b25f3779f30fc72efbd885ae00fc063fe620e162f70140fcf48f': ((60, 'plain'),),
    'sha256:bf0f3652cb873c61c99c8728b88a6f3e824e413403a4dc8d44428e88939449f3': ((9, 'plain'),),
    'sha256:c25597b8a6d656d3f508ffaf82f4f8ec1cd779360c7702233354ab862e36bf1d': ((3, 'plain'), (5, 'plain'), (7, 'plain'), (26, 'plain'), (28, 'plain'), (67, 'plain')),
    'sha256:c33f28c34a3ea7add687bdb576a43caf2061bfe0127a1ea10cb10887ec196ab5': ((15, 'plain'),),
    'sha256:c833fa7e0c1902465025d7fe04d3663b72634e1985a64fe385e609b93d0612c0': ((25, 'plain'),),
    'sha256:d821bdf2ed443417ec729ad7eee7376828bdff534931a210e02d168b4455a342': ((9, 'plain'), (11, 'plain')),
    'sha256:d848f5a663884ff8c94de41f0870c47d596501d3d9da59642c128d62fc81c06d': ((32, 'plain'),),
    'sha256:e923f4cba815c47ddbe009a9938d02c28b1cf16074d9becde96e61f45e3e27ed': ((1, 'plain'),),
    'sha256:f4f54dae8d196f07900373d03f3368fa02a0c3e78bbc440d89c860a9ef9437f1': ((37, 'plain'),),
    'sha256:f6caaef261d7d773dc31fb5b6be10769d9f914bb38119808d14c075385ce39c8': ((14, 'plain'),),
}

SOURCE_WITNESSES = {
    'sheaves': {
        ('plain', 'text', ' continuous'): ('sheaves-section-sheaves', 'section', 1),
        ('plain', 'text', ' is continuous'): ('sheaves-section-sheaves', 'section', 1),
        ('plain', 'text', ' locally constant'): ('sheaves-section-sheaves', 'section', 1),
        ('plain', 'text', ' resp. '): ('sheaves-section-sheaves-structures', 'section', 1),
        ('plain', 'text', 'restr.'): ('sheaves-section-bases', 'section', 1),
        ('plain', 'text', 'restriction for '): ('sheaves-section-presheaves-functorial', 'section', 1),
        ('plain', 'text', 'restriction of '): ('sheaves-section-presheaves-functorial', 'section', 1),
        ('plain', 'textit', 'a final object'): ('sheaves-section-sheaves', 'section', 1),
    },
    'schemes': {
        ('plain', 'text', ' and '): ('schemes-section-glueing-schemes', 'section', 1),
        ('plain', 'text', ' comes from '): ('schemes-section-quasi-coherent-affine', 'section', 1),
        ('plain', 'text', ' such that'): ('schemes-section-glueing-schemes', 'section', 1),
        ('plain', 'text', 'image '): ('schemes-section-category-affine-schemes', 'section', 1),
        ('plain', 'text', 'open covering '): ('schemes-section-glueing-schemes', 'section', 1),
        ('plain', 'text', 'the element '): ('schemes-section-quasi-coherent-affine', 'section', 1),
        ('plain', 'textit', 'Locally ringed spaces'): ('schemes-section-locally-ringed-spaces', 'section', 1),
        ('plain', 'textit', 'Ringed spaces'): ('schemes-section-locally-ringed-spaces', 'section', 1),
    },
    'constructions': {
        ('plain', 'text', ' as above'): ('constructions-section-spec', 'section', 1),
        ('plain', 'text', ' homogeneous'): ('constructions-section-invertible-proj', 'section', 1),
        ('plain', 'text', ' induced by '): ('constructions-section-grassmannian', 'section', 1),
        ('plain', 'text', ' is surjective'): ('constructions-section-grassmannian', 'section', 1),
        ('plain', 'text', ' quasi-compact open'): ('constructions-section-morphisms-proj', 'section', 1),
        ('plain', 'text', ' surjective'): ('constructions-section-grassmannian', 'section', 1),
        ('plain', 'text', '-graded primes of '): ('constructions-section-proj', 'section', 1),
        ('plain', 'text', 'equivalently'): ('constructions-section-projective-bundle', 'section', 1),
        ('plain', 'text', 'homogeneous'): ('constructions-section-functoriality-proj', 'section', 1),
        ('plain', 'text', 'pairs '): ('constructions-section-spec', 'section', 1),
        ('plain', 'text', 'strict equivalence classes of '): ('constructions-section-relative-proj', 'section', 1),
        ('plain', 'text', 'strict equivalence classes of triples '): ('constructions-section-morphisms-proj', 'section', 1),
        ('plain', 'text', 'th spot'): ('constructions-section-grassmannian', 'section', 1),
        ('plain', 'text', 'the map '): ('constructions-section-grassmannian', 'section', 1),
    },
    'algebraization': {
        ('plain', 'text', ' and '): ('algebraization-section-distance', 'section', 1),
        ('plain', 'text', ' immediate'): ('algebraization-section-distance', 'section', 1),
        ('plain', 'text', ' of '): ('algebraization-section-algebraization-modules-yet-more', 'section', 1),
        ('plain', 'text', ' open'): ('algebraization-lemma-equivalence-better', 'lemma', 1),
        ('plain', 'text', ' or '): ('algebraization-lemma-blowup', 'proof', 1),
        ('plain', 'text', ' there exist specializations in '): ('algebraization-section-distance', 'section', 1),
        ('plain', 'text', ' with '): ('algebraization-lemma-bootstrap', 'proof', 1),
        ('plain', 'text', 'of'): ('algebraization-section-algebraization-sections-general', 'section', 1),
    },
    'artin': {
        ('plain', 'text', ' and '): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', ' and all '): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', ' factors through '): ('artin-section-versality', 'section', 1),
        ('plain', 'text', ' is Noetherian complete local'): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', ' is a '): ('artin-lemma-finite-dimension', 'proof', 1),
        ('plain', 'text', ' is versal'): ('artin-lemma-versality-matches', 'lemma', 1),
        ('plain', 'text', ' is versal at '): ('artin-lemma-versality-matches', 'lemma', 1),
        ('plain', 'text', ' lying over'): ('artin-lemma-infinite-sequence-pre', 'proof', 1),
        ('plain', 'text', ' of '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', ' of finite type over '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', ' of predeformation categories is smooth'): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', ' over '): ('artin-section-tangent-spaces', 'section', 1),
        ('plain', 'text', ' such that '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', ' such that all have the same image in '): ('artin-lemma-get-openness-obstruction-theory', 'proof', 1),
        ('plain', 'text', ' the'): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', '-algebra map and '): ('artin-lemma-finite-dimension', 'proof', 1),
        ('plain', 'text', '-algebras'): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', '-algebras with residue field '): ('artin-section-introduction', 'section', 1),
        ('plain', 'text', 'Artinian local '): ('artin-section-introduction', 'section', 1),
        ('plain', 'text', 'Noetherian'): ('artin-section-algebraic-spaces-noetherian', 'section', 1),
        ('plain', 'text', 'algebraic spaces over '): ('artin-section-contractions', 'section', 1),
        ('plain', 'text', 'else'): ('artin-section-versality', 'section', 1),
        ('plain', 'text', 'for all fields '): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', 'formal objects of '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', 'if there exist '): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', 'images of '): ('artin-lemma-limit-preserving', 'proof', 1),
        ('plain', 'text', 'isomorphism classes of morphisms'): ('artin-section-tangent-spaces', 'section', 1),
        ('plain', 'text', 'locally Noetherian formal'): ('artin-section-contractions', 'section', 1),
        ('plain', 'text', 'lying over'): ('artin-section-versality', 'section', 1),
        ('plain', 'text', 'map '): ('artin-section-openness-versality', 'section', 1),
        ('plain', 'text', 'objects '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', 'where '): ('artin-section-formal-objects', 'section', 1),
        ('plain', 'text', 'with'): ('artin-lemma-diagonal-representable', 'proof', 1),
        ('plain', 'text', 'with '): ('artin-section-formal-objects', 'section', 1),
    },
    'moduli': {
        ('plain', 'text', ' finite'): ('moduli-lemma-open-P', 'proof', 1),
        ('plain', 'text', ' isomorphism in '): ('moduli-lemma-complexes-diagonal-affine-fp', 'proof', 1),
        ('plain', 'text', ' numerical polynomial'): ('moduli-section-stack-coherent-sheaves', 'section', 1),
    },
    'stacks-morphisms': {
        ('component', 'text', " is \\'etale"): ('stacks-morphisms-lemma-etale', 'proof', 1),
        ('plain', 'text', ' Noetherian'): ('stacks-morphisms-section-noetherian', 'section', 1),
        ('plain', 'text', ' is finite'): ('stacks-morphisms-lemma-property-automorphism-groups', 'lemma', 1),
        ('plain', 'text', ' is unramified'): ('stacks-morphisms-lemma-unramified', 'proof', 1),
        ('plain', 'text', ' locally Noetherian and '): ('stacks-morphisms-section-noetherian', 'section', 1),
        ('plain', 'text', ' lying over '): ('stacks-morphisms-lemma-every-point-residual-gerbe-quasi-DM', 'proof', 1),
        ('plain', 'text', ' quasi-compact'): ('stacks-morphisms-section-noetherian', 'section', 1),
        ('plain', 'text', ' smooth'): ('stacks-morphisms-lemma-identify-finite-type-points', 'lemma', 1),
        ('plain', 'text', 'Categories, Equation'): ('stacks-morphisms-lemma-cartesian-square-inertia', 'lemma', 1),
        ('plain', 'text', 'flat'): ('stacks-morphisms-section-flat', 'section', 1),
        ('plain', 'text', 'fraction field of '): ('stacks-morphisms-lemma-universally-injective-point', 'proof', 1),
        ('plain', 'text', 'local complete intersection'): ('stacks-morphisms-section-lci', 'section', 1),
        ('plain', 'text', 'locally of finite presentation'): ('stacks-morphisms-section-finite-presentation', 'section', 1),
        ('plain', 'text', 'locally of finite type'): ('stacks-morphisms-section-finite-type', 'section', 1),
        ('plain', 'text', 'smooth'): ('stacks-morphisms-section-smooth', 'section', 1),
        ('plain', 'text', 'the projection '): ('stacks-morphisms-lemma-check-property-after-fppf-base-change', 'lemma', 1),
        ('plain', 'text', 'with points'): ('stacks-morphisms-lemma-flat-at-point', 'lemma', 1),
    },
    'stacks-properties': {
        ('plain', 'text', ' is '): ('stacks-properties-section-irreducible-local-ring', 'section', 1),
        ('plain', 'text', ' of '): ('stacks-properties-lemma-substacks-presentation', 'lemma', 1),
        ('plain', 'text', '-invariant locally closed subspaces '): ('stacks-properties-lemma-substacks-presentation', 'lemma', 1),
        ('plain', 'text', 'locally closed substacks '): ('stacks-properties-lemma-substacks-presentation', 'lemma', 1),
        ('plain', 'text', 'smooth'): ('stacks-properties-lemma-local-source', 'lemma', 1),
        ('plain', 'text', 'the number of geometric branches of '): ('stacks-properties-section-irreducible-local-ring', 'section', 1),
        ('plain', 'text', 'the projection '): ('stacks-properties-lemma-check-property-covering', 'lemma', 1),
    },
}
