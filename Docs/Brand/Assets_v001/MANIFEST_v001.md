# Delivered 2D assets — v001 manifest

**Source:** commissioned brand asset sheet, delivered 2026-08-29 in
`Star Factory Tycoon brand identityd.zip`.
**Status:** Source candidate — SVG source exists; nothing is yet an
approved Unreal runtime asset.

## Why these live in Docs/

`Content/` and `SourceAssets/` are gitignored, so an asset placed there
is invisible to git and to the release gate. These are 154 KB of plain
text and they exist nowhere else — the export zip reuses one filename
and has already overwritten itself four times. Losing them would mean
re-commissioning work that has already been paid for.

## What is usable, and what is not

Measured at 24 px, the size the build menu actually renders, comparing
every pair within its class pixel-for-pixel:

| class | count | mean identical pixels | pairs over 90% |
|---|---|---|---|
| buildings | 15 | 70.2% | 0 of 105 |
| stations | 10 | **90.3%** | **25 of 45** |

- **patterns (28), decals (9), overlays (6) — USABLE AS DELIVERED.**
  Clear at both sizes, correctly hue-free, no baked text.
- **stations (10) — NOT USABLE.** They share a base plate and mast, so
  around 90% of every station's pixels are the same chassis and only a
  small head distinguishes them. `station-drill` and `station-nozzle`
  are 94.4% identical. This fails the spec's own acceptance test, that
  every icon stay uniquely identifiable within its class.
- **buildings (15) — NOT USABLE.** Distinguishable, but 42–50% of each
  tile is solid fill, so they read as heavy and crude rather than
  designed. The "solid mass" rule is over-applied at this size.

A redraw has been requested. These are kept rather than deleted because
the convention here is to supersede and retain the superseded artifact
as evidence — and because the patterns and decals in this set are
final.

## Files

| file | bytes | sha256 |
|---|---|---|
| `decals/decal-chicane-gate-bars.svg` | 153 | `bb67f58bc76a344280b6f686b39758a682a3ba92374449146ea41872f1ea5069` |
| `decals/decal-hazard-striping.svg` | 129 | `f0b7464a442d0f69d64d9fc49c7a74d943b94783f8f6ad55087c140ed6d8e5bf` |
| `decals/decal-hover-pad-ring.svg` | 641 | `cbca995859c577773a65f6d3b2660d70e941d6bfa4c57c5fab0a591790b2d06b` |
| `decals/decal-keep-clear-hatch.svg` | 179 | `3c6bc6ccea5e73c119718084f45e8d989b3a92c299d3adfbc330e200ee5e1e27` |
| `decals/decal-lane-edge-line.svg` | 131 | `fec7066b6367137014331d658b1291511a6f51b55ac3c572d232e312be52ab69` |
| `decals/decal-runway-centreline.svg` | 135 | `1b34f3b12c70b5b0eeaa56df4ca802d361e14d1b61b92b367433a229ab513ac2` |
| `decals/decal-survey-grid-20m.svg` | 163 | `c68420b2548a209082636e6edfaaa06aa7bd8ef396d2a5036d4c6d91df8fe02f` |
| `decals/decal-threshold-bars.svg` | 284 | `51ffebcb058ec59877711ce97c9daa8b282e42953c15177d5ada736f8ce86643` |
| `decals/decal-walkway-edging.svg` | 147 | `93541c3a42ab18238ae34d0b004fd98344f786346c75800d3152acbef8d41be8` |
| `icons/building-delivery-dock-16.svg` | 153 | `8b77afa9641fbd10026257f60c4ce19c1bfe93e75bd9cbb425c748afaf482cf9` |
| `icons/building-delivery-dock.svg` | 187 | `8fc7d1acad88693e9621ceb7c1fd72d1b90bb22825770c7053774e107e7be7e4` |
| `icons/building-drone-depot-16.svg` | 151 | `b407144ab11e05d4b82fb628385f4b3e9c6caf5ab64dfd34f2d692e3780ccd30` |
| `icons/building-drone-depot.svg` | 200 | `5cbde4736db4e1b9787a9b3733150d8e7f16914f627d9b139df1106110586521` |
| `icons/building-electronics-shop-16.svg` | 141 | `969ea5bdce6ed81bb06b0bf700cdd9dc93f6c264f5a121ae7b4688f4b2deb40e` |
| `icons/building-electronics-shop.svg` | 222 | `eff5a50bf5aa88d11592b853f3d92f8fd730b016cbdf972e9c92efdee86b9060` |
| `icons/building-foundry-16.svg` | 153 | `d7adb339aab3128a368988fcb0cedfb661a8754bc9a63c417857681ba428e53a` |
| `icons/building-foundry.svg` | 187 | `ff4ce7fefbb6b15fe88697d7ba6ba3fc3f163bc261bc90b168e876a41b91b2c8` |
| `icons/building-fuel-store-16.svg` | 141 | `3a684647eb420eb4d066c8a33dee2215b1a82fa3c52ae786d51b9711d89fc7c1` |
| `icons/building-fuel-store.svg` | 208 | `bc8b4fc0d574b748f85425936144c855cae9929222954598339ae3dc8a32a47a` |
| `icons/building-land-office-16.svg` | 161 | `bb7263f15354114d249be60c871708a9b8a5532337557d0316f3fbc6511cc9fb` |
| `icons/building-land-office.svg` | 212 | `1fa7f29c8e9d6dad1a028644fa853d819eb9582d6a5fb03fd0ac735aa4f96655` |
| `icons/building-launch-control-16.svg` | 170 | `e98edf3089c643cd8f160294a6f70028772ead55d3aab59a9aa0f918141533cd` |
| `icons/building-launch-control.svg` | 203 | `ab1e7f0fa6c7abc594f4af7160b5f530f991979c629b47fab7c57cfc675d58b7` |
| `icons/building-maintenance-shed-16.svg` | 151 | `9c3a183bf93d28e7b8388807faf53df8a9ec882062df3f4722d9b3c58d4957ae` |
| `icons/building-maintenance-shed.svg` | 307 | `8ab38bfd46e54603ea4617774f77591c2b4a3a35747c025891588665eac92864` |
| `icons/building-power-plant-16.svg` | 152 | `e3a3d869f90e571eccd1512113fdd77b6f8a5377df7f35052d2d5a90bcfd8cec` |
| `icons/building-power-plant.svg` | 234 | `58f873856c873661db155d7774ebf7da363b0a904aac657aa094b78a13f08a0c` |
| `icons/building-propulsion-shop-16.svg` | 170 | `aead60dc72f7051c4c3ae2bdb5a8ed11b14c3adfa691217ccf282f73705e73d6` |
| `icons/building-propulsion-shop.svg` | 235 | `28d39e638bf83b99a2dc93b917a171bf47a3777f25a6a217bd9f88cb81d2c5ab` |
| `icons/building-research-lab-16.svg` | 149 | `f8a9698ab1ea99269605defd7a350fc8202317189be5f73f62859ba7a168879d` |
| `icons/building-research-lab.svg` | 184 | `ee788a4fb227fa5222ea998ffc3c83c3fa23bf295a3d910df6871eea5048ec85` |
| `icons/building-ship-factory-16.svg` | 149 | `9d6dc0b1b5396ab3aebcc64fbcff2158375a69c15fa7b75b22ffb57dd94a5d83` |
| `icons/building-ship-factory.svg` | 181 | `363e72259a0160a2b918938482cfab3760d991bcf74fb0f78473fec1ed61b69b` |
| `icons/building-staff-block-16.svg` | 170 | `5d2912d253930177c24f4567cc7b338f9a934d107a63d14c03af1258d98b5364` |
| `icons/building-staff-block.svg` | 249 | `d264a31b9fd68cc5a3516253a2c3586152935e2fed6871a50daa7c4456890cc9` |
| `icons/building-storage-warehouse-16.svg` | 141 | `85e727a2e726729891bd7513202007bc7bff93f1d350cbf542d0a930368a8260` |
| `icons/building-storage-warehouse.svg` | 206 | `ca9570ca7a1273a617b9968062c8b7dde2cb052bdb8570ab0e28068293d3d53d` |
| `icons/building-sub-assembly-works-16.svg` | 151 | `974e490f1698a01e67368ae93c837fb212864573e77466f6ffc92463afade516` |
| `icons/building-sub-assembly-works.svg` | 262 | `04a4a4ee93a718caffb4dcf4238bcdb6da66a6aad18db9ba44d9e1113476a34b` |
| `icons/station-clamp-16.svg` | 179 | `ff09454f7cedd5aaf9cc8e0bdc71e2c4ed9fa8cfec9e7c8c347bd19dc498eae3` |
| `icons/station-clamp.svg` | 663 | `92769194de0bf4ae629efc60c6e00f1f7e765734789b108d458d94d27c3cfc93` |
| `icons/station-drill-16.svg` | 154 | `2124ced293d1dcb80ee37547932f8386bfff2fd32cd26f224d0ffe15717d09ec` |
| `icons/station-drill.svg` | 548 | `d82aebc4238405616f2f24116e2dc2cf337fc575dec82c7dad71913d944df058` |
| `icons/station-fork-16.svg` | 177 | `0bc04067d2ae02c8dbb5b114faeadc0ed678cb374732d799f68920de7f49a839` |
| `icons/station-fork.svg` | 656 | `f3b05800009c2fc7bf84534682fac10a002b3a04dc5ad61b2b3a99bbe4477396` |
| `icons/station-gripper-16.svg` | 180 | `dce197e7fdc18ba9ffc78ffd0c63849211bb1dd7bc182b38cd32f7965722091e` |
| `icons/station-gripper.svg` | 547 | `f89c4799c48e8facd0830d7c36b6d582676e9c6dd4228e1c572ca4b8cf422f01` |
| `icons/station-hose-16.svg` | 180 | `977a9b58356ea59b818693e9f19138f3c490a555b06bd9201cdff31ed9bfddf4` |
| `icons/station-hose.svg` | 561 | `a40714e1c4df232aaa0db46c946befee5f22d2746565e553b7578e75b60c872f` |
| `icons/station-nozzle-16.svg` | 156 | `12cd4a367b24d99198d733814ac74415f0b4c164d098f1d0844394661fe4f8e2` |
| `icons/station-nozzle.svg` | 670 | `9c201f11481c96147362dc9b76d5ce565045beb1ce65fab348534283cb310201` |
| `icons/station-press-16.svg` | 165 | `9f6d0eabbef28d6160e657371a1d8340aec52600a7c2d09a9cb4ede7c31a8f13` |
| `icons/station-press.svg` | 545 | `4b1b77075edcb858c6c5980fccbe51831d93334d0d7f23748ee92b0e7bdb6218` |
| `icons/station-roller-16.svg` | 164 | `1e8090cb98f80af231a8b4899c9b78415547b156c1d3e1b3b5dbbb90d36534a4` |
| `icons/station-roller.svg` | 555 | `556d3af346d4665c355c17a36756fa46488bb76030b760ba09ffcfba14c6bd6b` |
| `icons/station-scanner-sweep-16.svg` | 162 | `c4eb0bf16c071326df2c977c5acc116681e7fb8b4f7066a4dc77ed48cd5f3bd9` |
| `icons/station-scanner-sweep.svg` | 699 | `902f14b1d3ee3675c60b7f367f5d0ef437f4e6c734ac0f16af9c336fbbea0555` |
| `icons/station-welder-arc-16.svg` | 160 | `1786bebdfab80bb68f9a5ecff673a652971687bd3036450e73579c855b1f7ec9` |
| `icons/station-welder-arc.svg` | 669 | `1d2ae8ea3e05ed240297220dcfae2d23ac27aa62e1c9023c5b9475ef2ed5bfaa` |
| `overlays/overlay-pip-1.svg` | 132 | `17b003fc950fe169ec4421dff6eb696c91d30156da04cc592984fdb3006ff2f0` |
| `overlays/overlay-pip-2.svg` | 148 | `a0a0f53156504283634d319d4580d35f5b64189d388da9775e87decf945f0e71` |
| `overlays/overlay-pip-3.svg` | 164 | `56be686516ee5605a43b77aea678f3959f8303479f73070f45ab0c0f264a2f97` |
| `overlays/overlay-refused.svg` | 202 | `699201cfcede206700f35735094e8ebd83a32cdc39c36b2ebd79201373196aa9` |
| `overlays/overlay-research-locked.svg` | 375 | `87523626a4434080e3680672543584d0cf25d3230ed4565d683797d1e9059a9f` |
| `overlays/overlay-too-expensive.svg` | 1257 | `79ee962f92b79656e2e8679f28588d011c8619fc3c36a34a0fb8af0eef9d4c15` |
| `patterns/pattern-arrow-tier-a.svg` | 142 | `e20c5b4b90a2cfe4c256ff7fcbd4e87fc78a2f09acacb7cb186648354ca93475` |
| `patterns/pattern-arrow-tier-b.svg` | 170 | `c5d965c583ee648be7da366f28c78d7f16ddaaa0d72fbd575d0cce8022cfab89` |
| `patterns/pattern-checker-tier-a.svg` | 228 | `fc406679c659e6f520e39578737f6c8dcc556245362bb11da5663fbce0a15203` |
| `patterns/pattern-checker-tier-b.svg` | 346 | `950b30336d96c9dd3f9f5ef51bcf88bc49ddfb1329453c2d1acea03202c08f86` |
| `patterns/pattern-chevron-tier-a.svg` | 147 | `70c8f7d417df4b0cb8c2c4227b2f886d53760796b8e0abb8f919d4865470b7cd` |
| `patterns/pattern-chevron-tier-b.svg` | 191 | `b30598ed1e0d48673799968b774adf7fe4dec42a71df1d68a2299ee99af0420a` |
| `patterns/pattern-cross-band-tier-a.svg` | 145 | `084e2bf4ae4818e94e6b9b2a2c7613af1fe13898a15cc685a7b3b1a07e1bdff5` |
| `patterns/pattern-cross-band-tier-b.svg` | 206 | `5e7328550dbcf7606f08981477f32e8b29b1f8499c8de22c3a6c9df36a00203f` |
| `patterns/pattern-dashed-spine-tier-a.svg` | 162 | `c25eb79eaf98cfbba8ebd355e3c7f7b8ba076582c9231d64dd7ec460dcbda94e` |
| `patterns/pattern-dashed-spine-tier-b.svg` | 207 | `27ac0e63ef33427476af3a7228d1db14d207b98b4b767be717f8247663493f42` |
| `patterns/pattern-diagonal-split-tier-a.svg` | 129 | `5a5a905547780cd8cfdb1c5408b34755467ea600e767d07c4248b0a220cec41d` |
| `patterns/pattern-diagonal-split-tier-b.svg` | 146 | `90ef246168240b83c5c2f4fc1d816d369942adca3f749bef03605c11adb0986c` |
| `patterns/pattern-dot-trio-tier-a.svg` | 231 | `26b58c642375f5496f265972c73e93f93c3e0220f7f3ba4003c372025d94ebe8` |
| `patterns/pattern-dot-trio-tier-b.svg` | 346 | `40f1730632135a5be620a754d39a3ee49a724a0ced756d075f3e42991e6a7a93` |
| `patterns/pattern-double-stripe-tier-a.svg` | 143 | `f200b1fd75dc33764c2d90f5473bed758441a39c279a1113441a725f98e040a7` |
| `patterns/pattern-double-stripe-tier-b.svg` | 171 | `0a1ff1a18f92dab26ff52038f8631a5e89e66f04a7da517169b12a740cb0583f` |
| `patterns/pattern-half-split-tier-a.svg` | 129 | `ad35f702461f688dbd8ad55054136c3222745db52ba08a6a548a1083a724e4c4` |
| `patterns/pattern-half-split-tier-b.svg` | 142 | `84fb15220b79b49f1d4182945b4467440fe2f77aa213343da4728b31d2951391` |
| `patterns/pattern-notch-tier-a.svg` | 148 | `81477040c7e708f4a7590da3cb665e23cae31e231eab0b47fb433688a789feb7` |
| `patterns/pattern-notch-tier-b.svg` | 184 | `16d85ea24dcaf365dc20f9a3a679c66df8fdbd4ca534da8a60278f923ca5416e` |
| `patterns/pattern-quartered-tier-a.svg` | 145 | `62107cf40a9299c2b5e233baded1fd0134cb559af0adf17e620649c56386acd2` |
| `patterns/pattern-quartered-tier-b.svg` | 174 | `66a8216dfd4645afe6f40688e03ff009faebaf55383dae57f5bfc5ad7c71e89f` |
| `patterns/pattern-ring-tier-a.svg` | 196 | `b1a39c20e3dd5a84f624e696845f24ebc66e7681b5db6939b9486c3f544a504c` |
| `patterns/pattern-ring-tier-b.svg` | 274 | `c75702e1e04fe9f47624fb93f909a75d727b6d1c581003263079a258a72263d8` |
| `patterns/pattern-single-stripe-tier-a.svg` | 130 | `af6d0554b1e83fb10db99e26535833f7eca2ee02da35aaf78a96d627d62f4648` |
| `patterns/pattern-single-stripe-tier-b.svg` | 144 | `70ad785166d25578f24eb911de93c4c520c3c68f27456962bf0a76960d4a24a3` |
| `patterns/pattern-solid-tier-a.svg` | 129 | `e9f2927927c0cb2e37c730cc5fa707ac4460d0ee92fc50224151fc94538254f9` |
| `patterns/pattern-solid-tier-b.svg` | 142 | `f0864ca67377591ee889314dafebf4107578d46d64239e95fcfaea3374b6e391` |
