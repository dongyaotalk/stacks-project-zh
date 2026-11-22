"""Math roles verified against the five locked P0 source chapters."""

SOURCE_COMMIT = 'a04446e57ec1fbc252a871afcec7752fb2807b14'

SOURCE_HASHES = {
    'algebraization': 'sha256:a1d15613e36799787f29497ada72268daaa4c3d8bef0f6457c4ca3e60c4262e9',
    'artin': 'sha256:eba90a897b08eebff451e80925d13381b1a7f6ab883a34118733cd24cf061f47',
    'moduli': 'sha256:c9e283b30207bb93ca7c71cd83df78bb7f1962c471348b28968d9fb6a01b11d5',
    'stacks-morphisms': 'sha256:1f81f01c6748709778c0f877f1cb687152b344aa1c455449d2a341bbfe6a8b90',
    'stacks-properties': 'sha256:59d6b6df8f528ed5d3a68d9b9d74622e9b643f3622cc4d381bb46cc27a990016',
}

SOURCE_FRAMES = {
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
