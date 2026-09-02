# 当前翻译计划

> 本文件由 `make plan` 确定性生成。不要手工修改。

英文来源 commit：`a04446e57ec1fbc252a871afcec7752fb2807b14`。
优先级方法：`reader-value-v3-importance-scarcity-ch4`。

选择规则是：显式用户范围 > P0–P4 > wave > 章内 Section 顺序。
Section 的当前状态决定动作，但不会为了选择一个更容易执行的低优先级任务而
跳过更高价值章节所需的 scope preparation。

## 优先级分布

| 优先级 | 定义 | 章数 |
| --- | --- | ---: |
| P0（最高优先级） | 数学与读者价值高，且系统中文资料稀缺或缺失；第 4 章是显式用户覆盖 | 24 |
| P1（高优先级） | 重要性高但中文替代资料较多，或重要且中文资料稀缺但不是第一主线 | 34 |
| P2（中优先级） | 有明确价值但已有成熟中文替代，或属于第二阶段进阶内容 | 29 |
| P3（低优先级） | 中文资料可能稀缺，但受众较窄、依赖较深或边际读者价值较低 | 24 |
| P4（暂缓） | 维护、废弃、许可或自动生成内容；候选完成后不占正文翻译队列 | 6 |

## 当前推荐任务

| 优先级 | 章 | 当前范围 | 准备状态 | 下一动作 |
| --- | --- | --- | --- | --- |
| P0 | 第 4 章 范畴（`categories`） | Section 1 / `0012` | `READY` | `REVIEW` |
| P0 | 第 105 章 代数栈导论（`stacks-introduction`） | Section 1 / `072I` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 7 章 位点与层（`sites`） | Section 1 / `00V0` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 8 章 栈（`stacks`） | Section 1 / `0267` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 34 章 概形上的拓扑（`topologies`） | Section 1 / `020L` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 35 章 下降（`descent`） | Section 1 / `0239` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 41 章 概形的平展态射（`etale`） | Section 1 / `024K` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 21 章 位点上的上同调（`sites-cohomology`） | Section 1 / `01FR` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 59 章 平展上同调（`etale-cohomology`） | Section 1 / `03N2` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 65 章 代数空间（`spaces`） | Section 1 / `025S` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 73 章 代数空间上的拓扑（`spaces-topologies`） | Section 1 / `03Y5` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 74 章 下降与代数空间（`spaces-descent`） | Section 1 / `03YF` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 78 章 代数空间中的群胚（`spaces-groupoids`） | Section 1 / `0438` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 83 章 群胚的商（`groupoids-quotients`） | Section 1 / `048B` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 94 章 代数栈（`algebraic`） | Section 1 / `026L` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 97 章 可表性判据（`criteria`） | Section 1 / `05XF` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 90 章 形式形变理论（`formal-defos`） | Section 1 / `06G8` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 91 章 形变理论（`defos`） | Section 1 / `08KX` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 92 章 余切复形（`cotangent`） | Section 1 / `08P6` | `UNPREPARED` | `PREPARE_SCOPE` |
| P0 | 第 52 章 代数几何与形式几何（`algebraization`） | Section 1 / `0EI6` | `UNPREPARED` | `PREPARE_SCOPE` |

## 全部 117 章

| 优先级 | wave / order | 章 | 轨道 | 当前下一范围 | 下一动作 | 原因 |
| --- | ---: | --- | --- | --- | --- | --- |
| P0 | 1 / 1 | 第 4 章 范畴（`categories`） | `foundations`, `explicit-user-scope` | Section 1 / `0012` | `REVIEW` | 用户明确要求先完成第 4 章候选翻译；这是高于默认稀缺度排序的唯一第一 wave 覆盖 |
| P0 | 2 / 1 | 第 105 章 代数栈导论（`stacks-introduction`） | `entry`, `stacks-moduli` | Section 1 / `072I` | `PREPARE_SCOPE` | 作者设计的代数栈快速入口，重要且系统中文同类材料稀缺 |
| P0 | 2 / 2 | 第 7 章 位点与层（`sites`） | `scheme-to-stack` | Section 1 / `00V0` | `PREPARE_SCOPE` | 位点与层是下降和栈理论核心语言，系统中文资料稀缺 |
| P0 | 2 / 3 | 第 8 章 栈（`stacks`） | `scheme-to-stack` | Section 1 / `0267` | `PREPARE_SCOPE` | 进入代数栈的直接概念前置，系统中文材料稀缺 |
| P0 | 2 / 4 | 第 34 章 概形上的拓扑（`topologies`） | `scheme-to-stack`, `etale-cohomology` | Section 1 / `020L` | `PREPARE_SCOPE` | étale、fppf、fpqc 主线共同基础，系统中文资料稀缺 |
| P0 | 2 / 5 | 第 35 章 下降（`descent`） | `scheme-to-stack` | Section 1 / `0239` | `PREPARE_SCOPE` | 下降是核心通用技术，也是 Stacks Project 中文化边际价值最高的主题之一 |
| P0 | 2 / 6 | 第 41 章 概形的平展态射（`etale`） | `scheme-to-stack`, `etale-cohomology` | Section 1 / `024K` | `PREPARE_SCOPE` | 概形的 étale 态射是 étale 几何主干，中文系统资料稀缺 |
| P0 | 2 / 7 | 第 21 章 位点上的上同调（`sites-cohomology`） | `etale-cohomology` | Section 1 / `01FR` | `PREPARE_SCOPE` | 位点上的 étale、fppf 等上同调是核心主线，系统中文资料稀缺 |
| P0 | 2 / 8 | 第 59 章 平展上同调（`etale-cohomology`） | `etale-cohomology` | Section 1 / `03N2` | `PREPARE_SCOPE` | 研究价值高且高质量系统中文资料稀缺 |
| P0 | 2 / 9 | 第 65 章 代数空间（`spaces`） | `scheme-to-stack` | Section 1 / `025S` | `PREPARE_SCOPE` | 代数空间是从概形到栈的关键桥梁，系统中文资料稀缺 |
| P0 | 2 / 10 | 第 73 章 代数空间上的拓扑（`spaces-topologies`） | `scheme-to-stack` | Section 1 / `03Y5` | `PREPARE_SCOPE` | 代数空间下降与栈理论的重要支撑，系统中文资料稀缺 |
| P0 | 2 / 11 | 第 74 章 下降与代数空间（`spaces-descent`） | `scheme-to-stack` | Section 1 / `03YF` | `PREPARE_SCOPE` | 下降与代数空间的核心桥梁，系统中文资料稀缺 |
| P0 | 2 / 12 | 第 78 章 代数空间中的群胚（`spaces-groupoids`） | `scheme-to-stack` | Section 1 / `0438` | `PREPARE_SCOPE` | 代数空间中的群胚直接通往商和栈，系统中文资料稀缺 |
| P0 | 2 / 13 | 第 83 章 群胚的商（`groupoids-quotients`） | `scheme-to-stack` | Section 1 / `048B` | `PREPARE_SCOPE` | 群胚取商位于商空间和栈的概念链中心，系统中文资料稀缺 |
| P0 | 2 / 14 | 第 94 章 代数栈（`algebraic`） | `stacks-moduli` | Section 1 / `026L` | `PREPARE_SCOPE` | 代数栈是项目核心，系统中文资料稀缺 |
| P0 | 2 / 15 | 第 97 章 可表性判据（`criteria`） | `representability`, `stacks-moduli` | Section 1 / `05XF` | `PREPARE_SCOPE` | 可表性判据是模问题核心，系统中文资料稀缺 |
| P0 | 2 / 16 | 第 90 章 形式形变理论（`formal-defos`） | `representability`, `moduli` | Section 1 / `06G8` | `PREPARE_SCOPE` | Artin 与 Schlessinger 路线的核心前置，系统中文资料稀缺 |
| P0 | 2 / 17 | 第 91 章 形变理论（`defos`） | `representability`, `moduli` | Section 1 / `08KX` | `PREPARE_SCOPE` | 形变理论是模空间核心工具，系统中文资料稀缺 |
| P0 | 2 / 18 | 第 92 章 余切复形（`cotangent`） | `representability`, `moduli` | Section 1 / `08P6` | `PREPARE_SCOPE` | 余切复形是现代形变理论核心，系统中文资料稀缺 |
| P0 | 2 / 19 | 第 52 章 代数几何与形式几何（`algebraization`） | `representability` | Section 1 / `0EI6` | `PREPARE_SCOPE` | 形式几何、代数化与模问题之间的核心桥梁，系统中文资料稀缺 |
| P0 | 2 / 20 | 第 98 章 Artin 公理（`artin`） | `representability`, `stacks-moduli` | Section 1 / `07T0` | `PREPARE_SCOPE` | Artin 公理是代数化与可表性核心，系统中文资料稀缺 |
| P0 | 2 / 21 | 第 100 章 代数栈的性质（`stacks-properties`） | `stacks-moduli` | Section 1 / `04X9` | `PREPARE_SCOPE` | 代数栈性质是高频核心参考，系统中文资料稀缺 |
| P0 | 2 / 22 | 第 101 章 代数栈的态射（`stacks-morphisms`） | `stacks-moduli` | Section 1 / `04XN` | `PREPARE_SCOPE` | 代数栈态射是高频核心参考，系统中文资料稀缺 |
| P0 | 2 / 23 | 第 108 章 模栈（`moduli`） | `stacks-moduli` | Section 1 / `0DLU` | `PREPARE_SCOPE` | 模空间栈是项目最终目标之一，系统中文资料稀缺 |
| P1 | 1 / 1 | 第 6 章 空间上的层（`sheaves`） | `scheme-to-stack` | Section 1 / `006B` | `PREPARE_SCOPE` | 位点、层和栈语言的重要前置；基础层论有中文资料但 Stacks 体系仍有增量价值 |
| P1 | 1 / 2 | 第 26 章 概形（`schemes`） | `scheme-to-stack` | Section 1 / `01H9` | `PREPARE_SCOPE` | 代数几何主干且重要性极高，但已有中文概形教材与中文授课体系 |
| P1 | 1 / 3 | 第 27 章 概形的构造（`constructions`） | `schemes` | Section 1 / `01LF` | `PREPARE_SCOPE` | 概形构造实用价值高，中文系统参考仍少于基础概形入门 |
| P1 | 1 / 4 | 第 28 章 概形的性质（`properties`） | `scheme-to-stack` | Section 1 / `01OI` | `PREPARE_SCOPE` | 概形性质是高频核心，但基础内容已有中文概形教材和课程覆盖 |
| P1 | 1 / 5 | 第 29 章 概形的态射（`morphisms`） | `scheme-to-stack` | Section 1 / `01QM` | `PREPARE_SCOPE` | 概形态射是高频核心，但基础内容已有中文概形教材和课程覆盖 |
| P1 | 1 / 6 | 第 20 章 层上同调（`cohomology`） | `cohomology` | Section 1 / `01DX` | `PREPARE_SCOPE` | 层上同调路线核心；重要性高，但中文同调与层论资料并非空白 |
| P1 | 1 / 7 | 第 30 章 概形上同调（`coherent`） | `cohomology` | Section 1 / `01X7` | `PREPARE_SCOPE` | 概形上同调是后续几何上同调基础，系统中文参考仍有限 |
| P1 | 1 / 8 | 第 38 章 平坦性进阶（`flat`） | `scheme-to-stack` | Section 1 / `057N` | `PREPARE_SCOPE` | 平坦性是下降与模问题核心技术，中文资料虽有但较分散 |
| P1 | 1 / 9 | 第 37 章 态射进阶（`more-morphisms`） | `schemes` | Section 1 / `02GY` | `PREPARE_SCOPE` | 研究中频繁查阅，且完整中文参考稀缺 |
| P1 | 1 / 10 | 第 39 章 群胚概形（`groupoids`） | `scheme-to-stack` | Section 1 / `022M` | `PREPARE_SCOPE` | 群胚概形直接通往商空间与栈，重要且中文系统资料较少 |
| P1 | 1 / 11 | 第 66 章 代数空间的性质（`spaces-properties`） | `algebraic-spaces` | Section 1 / `03BP` | `PREPARE_SCOPE` | 代数空间理论主干，系统中文参考稀缺 |
| P1 | 1 / 12 | 第 67 章 代数空间的态射（`spaces-morphisms`） | `algebraic-spaces` | Section 1 / `03H9` | `PREPARE_SCOPE` | 代数空间理论主干，系统中文参考稀缺 |
| P1 | 1 / 13 | 第 80 章 自举（`bootstrap`） | `algebraic-spaces` | Section 1 / `046B` | `PREPARE_SCOPE` | 构造代数空间的重要技术章，中文系统资料稀缺 |
| P1 | 1 / 14 | 第 96 章 代数栈上的层（`stacks-sheaves`） | `stacks-moduli`, `cohomology` | Section 1 / `06TG` | `PREPARE_SCOPE` | 代数栈上的层与上同调前置，系统中文资料稀缺 |
| P1 | 1 / 15 | 第 56 章 函子与态射（`functors`） | `representability` | Section 1 / `0GNH` | `PREPARE_SCOPE` | 函子与态射是可表性和模函子的关键基础，系统中文参考有限 |
| P1 | 1 / 16 | 第 88 章 形式空间的代数化（`restricted`） | `representability` | Section 1 / `0AM8` | `PREPARE_SCOPE` | 形式空间代数化对可表性理论重要，系统中文资料稀缺 |
| P1 | 1 / 17 | 第 87 章 形式代数空间（`formal-spaces`） | `representability` | Section 1 / `0AHX` | `PREPARE_SCOPE` | Artin 理论相关的形式代数空间内容，重要且中文系统资料稀缺 |
| P1 | 1 / 18 | 第 93 章 形变问题（`examples-defos`） | `representability`, `moduli` | Section 1 / `0DVL` | `PREPARE_SCOPE` | 形变实例能显著降低稀缺理论的学习门槛 |
| P1 | 1 / 19 | 第 95 章 栈的例子（`examples-stacks`） | `entry`, `stacks-moduli` | Section 1 / `04SM` | `PREPARE_SCOPE` | 栈的例子学习价值极高，但依赖主线应先完成 |
| P1 | 1 / 20 | 第 99 章 Quot 空间与 Hilbert 空间（`quot`） | `moduli` | Section 1 / `05X5` | `PREPARE_SCOPE` | Quot 与 Hilbert 空间是模空间经典构造，中文系统参考有限 |
| P1 | 1 / 21 | 第 102 章 代数栈的极限（`stacks-limits`） | `representability`, `stacks-moduli` | Section 1 / `0CMN` | `PREPARE_SCOPE` | Artin 与近似路线的重要内容，系统中文资料稀缺 |
| P1 | 1 / 22 | 第 103 章 代数栈上同调（`stacks-cohomology`） | `stacks-moduli`, `cohomology` | Section 1 / `073Q` | `PREPARE_SCOPE` | 代数栈上同调的研究主干，系统中文资料稀缺 |
| P1 | 1 / 23 | 第 106 章 栈态射进阶（`stacks-more-morphisms`） | `stacks-moduli` | Section 1 / `0BPL` | `PREPARE_SCOPE` | 代数栈态射的高价值研究参考，系统中文资料稀缺 |
| P1 | 1 / 24 | 第 107 章 栈的几何（`stacks-geometry`） | `stacks-moduli` | Section 1 / `0DQS` | `PREPARE_SCOPE` | 汇总代数栈几何性质，系统中文资料稀缺 |
| P1 | 1 / 25 | 第 109 章 曲线的模（`moduli-curves`） | `stacks-moduli` | Section 1 / `0DMH` | `PREPARE_SCOPE` | 曲线模空间是重要应用，但应在通用代数栈与可表性主线之后 |
| P1 | 1 / 26 | 第 43 章 交叉理论（`intersection`） | `intersection` | Section 1 / `0AZ7` | `PREPARE_SCOPE` | 需求广、研究价值高且系统中文参考有限 |
| P1 | 1 / 27 | 第 60 章 晶体上同调（`crystalline`） | `crystalline` | Section 1 / `07GJ` | `PREPARE_SCOPE` | 重要的算术几何专题，中文系统材料稀缺但受众较专门 |
| P1 | 1 / 28 | 第 61 章 Pro-平展上同调（`proetale`） | `etale-cohomology` | Section 1 / `0966` | `PREPARE_SCOPE` | 现代研究价值高，中文系统资料稀缺但属于进阶路线 |
| P1 | 1 / 29 | 第 63 章 平展上同调进阶（`more-etale`） | `etale-cohomology` | Section 1 / `0F4V` | `PREPARE_SCOPE` | étale 上同调的高价值研究参考，中文系统资料稀缺 |
| P1 | 1 / 30 | 第 58 章 概形的基本群（`pione`） | `etale-cohomology` | Section 1 / `0BQ7` | `PREPARE_SCOPE` | 概形基本群是 étale 路线的重要组成，中文系统资料较少 |
| P1 | 1 / 31 | 第 47 章 对偶化复形（`dualizing`） | `duality` | Section 1 / `08XH` | `PREPARE_SCOPE` | 对偶理论的重要前置，研究价值高且系统中文资料稀缺 |
| P1 | 1 / 32 | 第 48 章 概形的对偶性（`duality`） | `duality` | Section 1 / `0DWF` | `PREPARE_SCOPE` | 研究价值高、理论深，系统中文资料稀缺 |
| P1 | 1 / 33 | 第 110 章 例（`examples`） | `reference` | Section 1 / `0270` | `PREPARE_SCOPE` | 实例适合中文读者学习和查阅 |
| P1 | 1 / 34 | 第 111 章 习题（`exercises`） | `reference` | Section 1 / `0276` | `PREPARE_SCOPE` | 对教学型中文译本有较高价值 |
| P2 | 1 / 1 | 第 1 章 引言（`introduction`） | `entry` | Section 1 / `0001` | `REVIEW` | 项目导航价值明确，但篇幅短、已有候选，且不存在系统中文资料缺口 |
| P2 | 1 / 2 | 第 2 章 约定（`conventions`） | `foundations` | Section 1 / `0003` | `REVIEW` | 统一术语和记号很重要，但属于通用辅助材料而非稀缺数学主线 |
| P2 | 1 / 3 | 第 10 章 交换代数（`algebra`） | `foundations` | Section 1 / `00AP` | `PREPARE_SCOPE` | 数学上极重要，但中文交换代数教材和讲义较成熟；优先翻主线实际依赖范围 |
| P2 | 1 / 4 | 第 12 章 同调代数（`homology`） | `foundations` | Section 1 / `00ZV` | `PREPARE_SCOPE` | 重要基础，但已有成熟中文教材与课程材料 |
| P2 | 1 / 5 | 第 13 章 导出范畴（`derived`） | `derived` | Section 1 / `05QJ` | `PREPARE_SCOPE` | 研究价值高且中文系统资料有限，但不是当前第一入口 |
| P2 | 1 / 6 | 第 15 章 代数进阶（`more-algebra`） | `foundations` | Section 1 / `05E4` | `PREPARE_SCOPE` | 参考价值高，但体量和深度都大，且基础部分有中文替代 |
| P2 | 1 / 7 | 第 17 章 模层（`modules`） | `cohomology` | Section 1 / `01AD` | `PREPARE_SCOPE` | 上同调与导出理论的重要支撑，但可由成熟同调代数资料补足 |
| P2 | 1 / 8 | 第 18 章 位点上的模（`sites-modules`） | `cohomology` | Section 1 / `03A5` | `PREPARE_SCOPE` | étale 上同调路线的前置，置于更稀缺的位点上同调主章之后 |
| P2 | 1 / 9 | 第 31 章 除子（`divisors`） | `schemes` | Section 1 / `01WP` | `PREPARE_SCOPE` | 经典且高频，但中文代数几何教材通常已有成体系覆盖 |
| P2 | 1 / 10 | 第 32 章 概形的极限（`limits`） | `schemes` | Section 1 / `01YU` | `PREPARE_SCOPE` | 对 Artin 与近似理论重要，但偏进阶且不是第一主线 |
| P2 | 1 / 11 | 第 33 章 簇（`varieties`） | `schemes` | Section 1 / `020A` | `PREPARE_SCOPE` | 经典重要，但中文教材替代度较高 |
| P2 | 1 / 12 | 第 36 章 概形的导出范畴（`perfect`） | `derived` | Section 1 / `08CV` | `PREPARE_SCOPE` | 概形导出范畴的重要进阶内容 |
| P2 | 1 / 13 | 第 40 章 群胚概形进阶（`more-groupoids`） | `scheme-to-stack` | Section 1 / `04LB` | `PREPARE_SCOPE` | 群胚概形的第二层技术内容 |
| P2 | 1 / 14 | 第 42 章 Chow 同调（`chow`） | `intersection` | Section 1 / `02P4` | `PREPARE_SCOPE` | 重要的相交理论专题，但属于第二阶段应用 |
| P2 | 1 / 15 | 第 44 章 曲线的 Picard 概形（`pic`） | `moduli` | Section 1 / `0B93` | `PREPARE_SCOPE` | 模空间理论的重要经典实例 |
| P2 | 1 / 16 | 第 50 章 德拉姆上同调（`derham`） | `cohomology` | Section 1 / `0FK5` | `PREPARE_SCOPE` | 经典重要，但中文和外部替代资料较多 |
| P2 | 1 / 17 | 第 51 章 局部上同调（`local-cohomology`） | `cohomology` | Section 1 / `0DWP` | `PREPARE_SCOPE` | 交换代数与几何交叉的重要工具，属于第二阶段进阶 |
| P2 | 1 / 18 | 第 53 章 代数曲线（`curves`） | `schemes` | Section 1 / `0BRW` | `PREPARE_SCOPE` | 经典重要主题，但已有较多中文替代资料 |
| P2 | 1 / 19 | 第 64 章 迹公式（`trace`） | `etale-cohomology` | Section 1 / `0F5Q` | `PREPARE_SCOPE` | 重要但路线较专门 |
| P2 | 1 / 20 | 第 69 章 代数空间上同调（`spaces-cohomology`） | `algebraic-spaces`, `cohomology` | Section 1 / `071U` | `PREPARE_SCOPE` | 代数空间上同调的进阶内容 |
| P2 | 1 / 21 | 第 70 章 代数空间的极限（`spaces-limits`） | `algebraic-spaces` | Section 1 / `07SC` | `PREPARE_SCOPE` | 代数空间极限的进阶参考 |
| P2 | 1 / 22 | 第 71 章 代数空间上的除子（`spaces-divisors`） | `algebraic-spaces` | Section 1 / `0839` | `PREPARE_SCOPE` | 代数空间上的除子专题 |
| P2 | 1 / 23 | 第 72 章 域上的代数空间（`spaces-over-fields`） | `algebraic-spaces` | Section 1 / `06DS` | `PREPARE_SCOPE` | 域上代数空间专题 |
| P2 | 1 / 24 | 第 75 章 代数空间的导出范畴（`spaces-perfect`） | `algebraic-spaces`, `derived` | Section 1 / `08EZ` | `PREPARE_SCOPE` | 代数空间导出范畴的进阶内容 |
| P2 | 1 / 25 | 第 76 章 代数空间的态射进阶（`spaces-more-morphisms`） | `algebraic-spaces` | Section 1 / `049G` | `PREPARE_SCOPE` | 代数空间态射的进阶参考 |
| P2 | 1 / 26 | 第 77 章 代数空间上的平坦性（`spaces-flat`） | `algebraic-spaces` | Section 1 / `0CU4` | `PREPARE_SCOPE` | 代数空间平坦性的专门技术 |
| P2 | 1 / 27 | 第 79 章 代数空间中的群胚进阶（`spaces-more-groupoids`） | `algebraic-spaces` | Section 1 / `04P5` | `PREPARE_SCOPE` | 代数空间群胚的第二轮技术内容 |
| P2 | 1 / 28 | 第 82 章 代数空间的 Chow 群（`spaces-chow`） | `algebraic-spaces`, `intersection` | Section 1 / `0EDR` | `PREPARE_SCOPE` | 代数空间的 Chow 群专题 |
| P2 | 1 / 29 | 第 104 章 栈的导出范畴（`stacks-perfect`） | `stacks-moduli`, `derived` | Section 1 / `08MX` | `PREPARE_SCOPE` | 代数栈导出范畴属于高阶进阶 |
| P3 | 1 / 1 | 第 3 章 集合论（`sets`） | `foundations` | Section 1 / `0008` | `REVIEW` | 通用基础内容，中文读者通常可按需查阅 |
| P3 | 1 / 2 | 第 5 章 拓扑（`topology`） | `foundations` | Section 1 / `004D` | `PREPARE_SCOPE` | 通用基础，非 Stacks Project 独有的中文化价值 |
| P3 | 1 / 3 | 第 9 章 域（`fields`） | `foundations` | Section 1 / `09FB` | `PREPARE_SCOPE` | 常用基础但成熟中文教材丰富，翻译边际价值低于专门主线 |
| P3 | 1 / 4 | 第 11 章 布饶尔群（`brauer`） | `foundations` | Section 1 / `073X` | `PREPARE_SCOPE` | 专题性强，优先服务明确读者需求 |
| P3 | 1 / 5 | 第 14 章 单纯方法（`simplicial`） | `derived` | Section 1 / `0163` | `PREPARE_SCOPE` | 技术性强且需求集中 |
| P3 | 1 / 6 | 第 16 章 环映射的平滑化（`smoothing`） | `foundations` | Section 1 / `07BX` | `PREPARE_SCOPE` | 环同态光滑化属于较专门的技术路线 |
| P3 | 1 / 7 | 第 19 章 内射对象（`injectives`） | `cohomology` | Section 1 / `01D5` | `PREPARE_SCOPE` | 技术性基础，可在上同调主线需要时推进 |
| P3 | 1 / 8 | 第 22 章 微分分次代数（`dga`） | `derived` | Section 1 / `09JE` | `PREPARE_SCOPE` | 导出技术专题，受众较集中 |
| P3 | 1 / 9 | 第 23 章 除幂代数（`dpa`） | `crystalline` | Section 1 / `09PE` | `PREPARE_SCOPE` | 主要服务晶体理论，读者面较窄 |
| P3 | 1 / 10 | 第 24 章 微分分次层（`sdga`） | `derived` | Section 1 / `0FQT` | `PREPARE_SCOPE` | 高阶导出技术章节 |
| P3 | 1 / 11 | 第 25 章 超覆盖（`hypercovering`） | `cohomology` | Section 1 / `01FY` | `PREPARE_SCOPE` | 高阶上同调技术，可按需求翻译 |
| P3 | 1 / 12 | 第 45 章 Weil 上同调理论（`weil`） | `cohomology` | Section 1 / `0FFH` | `PREPARE_SCOPE` | 较专门的上同调理论路线 |
| P3 | 1 / 13 | 第 46 章 适足模（`adequate`） | `schemes` | Section 1 / `06Z2` | `PREPARE_SCOPE` | 内容高度专门 |
| P3 | 1 / 14 | 第 49 章 判别式与不同理想（`discriminant`） | `schemes` | Section 1 / `0DWI` | `PREPARE_SCOPE` | 判别式与不同理想是专门主题 |
| P3 | 1 / 15 | 第 54 章 曲面的解消（`resolve`） | `singularities` | Section 1 / `0ADX` | `PREPARE_SCOPE` | 曲面奇点消解是专门研究方向 |
| P3 | 1 / 16 | 第 55 章 半稳定约化（`models`） | `arithmetic` | Section 1 / `0C2Q` | `PREPARE_SCOPE` | 半稳定约化重要但路线较专门 |
| P3 | 1 / 17 | 第 57 章 簇的导出范畴（`equiv`） | `derived` | Section 1 / `0FY1` | `PREPARE_SCOPE` | 专业受众导向的导出范畴专题 |
| P3 | 1 / 18 | 第 62 章 相对循环（`relative-cycles`） | `intersection` | Section 1 / `0H4C` | `PREPARE_SCOPE` | 相对循环属于专门技术内容 |
| P3 | 1 / 19 | 第 68 章 合宜代数空间（`decent-spaces`） | `algebraic-spaces` | Section 1 / `06NL` | `PREPARE_SCOPE` | 代数空间的技术性细化 |
| P3 | 1 / 20 | 第 81 章 代数空间的推出（`spaces-pushouts`） | `algebraic-spaces` | Section 1 / `0AHU` | `PREPARE_SCOPE` | 代数空间推出属于专门构造 |
| P3 | 1 / 21 | 第 84 章 代数空间上同调进阶（`spaces-more-cohomology`） | `algebraic-spaces`, `cohomology` | Section 1 / `0DFS` | `PREPARE_SCOPE` | 代数空间上同调的深度专题 |
| P3 | 1 / 22 | 第 85 章 单纯代数空间（`spaces-simplicial`） | `algebraic-spaces` | Section 1 / `09VJ` | `PREPARE_SCOPE` | 技术性较强的单纯代数空间章节 |
| P3 | 1 / 23 | 第 86 章 代数空间的对偶性（`spaces-duality`） | `algebraic-spaces`, `duality` | Section 1 / `0E4W` | `PREPARE_SCOPE` | 专业受众导向的对偶理论 |
| P3 | 1 / 24 | 第 89 章 曲面解消再论（`spaces-resolve`） | `singularities` | Section 1 / `0BH7` | `PREPARE_SCOPE` | 曲面奇点消解的专门后续 |
| P4 | 1 / 1 | 第 112 章 文献指南（`guide`） | `reference`, `maintenance` | Section 1 / `03B1` | `REVIEW` | 维护型文献指南且候选已完成，不再占正文翻译优先级 |
| P4 | 1 / 2 | 第 113 章 期望事项（`desirables`） | `maintenance` | Section 1 / `02B5` | `REVIEW` | 项目维护说明且候选已完成，不再占正文翻译优先级 |
| P4 | 1 / 3 | 第 114 章 编码风格（`coding`） | `maintenance` | Section 1 / `02BZ` | `REVIEW` | 编码维护说明且候选已完成，不再占正文翻译优先级 |
| P4 | 1 / 4 | 第 115 章 已废弃内容（`obsolete`） | `maintenance` | Section 1 / `073U` | `REVIEW` | 废弃内容候选已完成，后续只按明确维护需求处理 |
| P4 | 1 / 5 | 第 116 章 GNU 自由文档许可证（`fdl`） | `maintenance`, `license` | Section 1 / `05BG` | `REVIEW` | 许可证候选已完成，不再占数学正文翻译优先级 |
| P4 | 1 / 6 | 第 117 章 自动生成索引（`index`） | `generated` | — | `NOT_APPLICABLE` | 上游自动生成索引，无可执行翻译 Section |

## 动作状态机

| 动作 | 含义 |
| --- | --- |
| `RESOLVE_TAG` | 补齐稳定 Tag/ID |
| `PREPARE_SCOPE` | 准备稳定 unit |
| `TRANSLATE` | 生成候选译文 |
| `CONTINUE_TRANSLATION` | 继续候选翻译 |
| `REVIEW` | 开始人工审校 |
| `CONTINUE_REVIEW` | 继续人工审校 |
| `MATHEMATICS_REVIEW` | 完成人工数学审校 |
| `PUBLISH_PREPARATION` | 准备发布 |
| `DONE` | 已完成 |
| `NOT_APPLICABLE` | 不适用 |

显式指定的范围如果已经完成，默认返回“没有剩余可执行工作”，不会悄悄切换
到其他章节；只有显式传入 `--fallback`（Make 接口为 `FALLBACK=1`）才恢复
自动选择。机器调用可使用 `next-task --json`（Make 接口为 `JSON=1`）。
