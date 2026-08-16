[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param()

$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath('C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8')
$contentRoot = Join-Path $project 'Content\LineBoss\Candidates\WeldShop\BodyShopUnderbodySlice_v001'
$source = Join-Path $contentRoot '__LegacyLODStaging'
$quarantine = Join-Path $project 'Saved\Quarantine\BodyShop\LegacyLODStaging_v001'
$validation = Join-Path $project 'Saved\Audits\BodyShop\Experimental_v001\validate_underbody_slice_art_receipt_v001.json'
$expectedValidationHash = '551FABEBB5858092161F19143A31AA04C5BEE8221AAF0641C711C539BF71A0EC'
$press = Join-Path $project 'Content\LineBoss\Maps\LB_PressShop_RebuildFromLorry_v20260810_v913.umap'
$expectedPressHash = '26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6'

$expected = [ordered]@{
    'SM_LB_BodyShopRobot_Base_v001__LegacySourceLOD1.uasset' = '294147C17F0ED3AFE2C362E75012720C9A6314496CFE397FCE8C8CC324916668'
    'SM_LB_BodyShopRobot_Base_v001__LegacySourceLOD2.uasset' = '7C8631E405D6F4DCDE8A40D2B46515C4981401F25CC09FD5F4FB74FB90FFAAFB'
    'SM_LB_BodyShopRobot_J1_v001__LegacySourceLOD1.uasset' = 'C0C5B3BCA45859C1FFE52BF05047159F8CB7D9058EE51B3A13C5B34252E79DC6'
    'SM_LB_BodyShopRobot_J1_v001__LegacySourceLOD2.uasset' = '12D0C80DB76AE202C212283ADA9583CFD9DB84D0AA11213422AAC124B799A0A5'
    'SM_LB_BodyShopRobot_J2_v001__LegacySourceLOD1.uasset' = 'C88C045961BD8C3A5FCA35885F200102696FA7F1835083E08C046755E212E824'
    'SM_LB_BodyShopRobot_J2_v001__LegacySourceLOD2.uasset' = '0498416F2F5F0194C575CCE61300D8BBBAB4FC4CC6CBD94D397FF0C4A9E40FF7'
    'SM_LB_BodyShopRobot_J3_v001__LegacySourceLOD1.uasset' = 'A4915D839FC6BF1A1B93C8E886A80392BE80BC399E023E75D938BFA57742C492'
    'SM_LB_BodyShopRobot_J3_v001__LegacySourceLOD2.uasset' = 'A761DC0E2EFB497FE1DA9BF0EDD07103C9A647C4F01DBDFD281BAB651FFD7857'
    'SM_LB_BodyShopRobot_J4_v001__LegacySourceLOD1.uasset' = 'C208A052DF850E698DE6493A31AD0C2E3481F34B2A6A619C7B40F23AD63E8D02'
    'SM_LB_BodyShopRobot_J4_v001__LegacySourceLOD2.uasset' = '2DE7E40B47636C1748FA2269B6EE9F07A2A7F5B3D66FE55E427847740F27E26C'
    'SM_LB_BodyShopRobot_J5_v001__LegacySourceLOD1.uasset' = '455FD3027F27E898D784F3FCBA8EE210ED3D2F77112139E7E294CEF3EF0F3C67'
    'SM_LB_BodyShopRobot_J5_v001__LegacySourceLOD2.uasset' = '4F3132CCAEFE679B69FD3F8882737F70DD4A4AC7246B16339FDBA8A2D4643B74'
    'SM_LB_BodyShopTool_PanelPick8Cup_v001__LegacySourceLOD1.uasset' = '7E77CC2158B647454B739741F4204DA84DC4305C09AB23F9D037157D51C59020'
    'SM_LB_BodyShopTool_PanelPick8Cup_v001__LegacySourceLOD2.uasset' = '365D92F50230438A8009E55DDED7E41E16141FF11EAE3CC528FDECF2A9BD5250'
    'SM_LB_BodyShop_UnderbodyFixture_v001__LegacySourceLOD1.uasset' = '5DDCDB1F7E130E9A6A8651F41C5AAD4AC19E39FC124FCBEA7105065612211DFC'
    'SM_LB_BodyShop_UnderbodyFixture_v001__LegacySourceLOD2.uasset' = '620D4D69F2A8E72ADE97729B1EC3168A2DEC906E091A778102547A252D41B6D2'
    'SM_LB_BodyShop_VisionGate_v001__LegacySourceLOD1.uasset' = '9236BDDB35DEA603BA044BD95216E51E2B51C81F9EADC9B028241F2EB878238E'
    'SM_LB_BodyShop_VisionGate_v001__LegacySourceLOD2.uasset' = '4EED6BECC117ECBA14E13A401CA8C0CB553B64F812092A5679D93C83CC8C7FAF'
}

if ((Get-Process UnrealEditor, UnrealEditor-Cmd -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'Refusing quarantine while Unreal is running.'
}
if (-not (Test-Path -LiteralPath $validation -PathType Leaf) -or
    (Get-FileHash -Algorithm SHA256 -LiteralPath $validation).Hash -ne $expectedValidationHash) {
    throw 'Current underbody art validation receipt is missing or has drifted.'
}
$validationJson = Get-Content -Raw -LiteralPath $validation | ConvertFrom-Json
if ($validationJson.status -ne 'PASS__BODYSHOP_UNDERBODY_ART_SOURCE_LOD_SCALE_NAMESPACE_AND_POLICY_VALIDATION_V001') {
    throw 'Current underbody art validation status is not PASS.'
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $press).Hash -ne $expectedPressHash) {
    throw 'Protected Press Shop v913 hash drift.'
}
if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw 'Legacy LOD staging directory is missing.'
}
if (Test-Path -LiteralPath $quarantine) {
    throw 'Quarantine target already exists; refusing overwrite.'
}
$actual = @(Get-ChildItem -LiteralPath $source -File)
if ($actual.Count -ne 18 -or @(Get-ChildItem -LiteralPath $source -Directory).Count -ne 0) {
    throw "Expected exactly 18 staging packages, found $($actual.Count)."
}
foreach ($file in $actual) {
    if (-not $expected.Contains($file.Name)) { throw "Unexpected staging file: $($file.Name)" }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -ne $expected[$file.Name]) {
        throw "Staging package hash drift: $($file.Name)"
    }
}

if (-not $PSCmdlet.ShouldProcess($source, "Move exact 18-package legacy LOD staging directory to $quarantine")) {
    return
}
New-Item -ItemType Directory -Path (Split-Path -Parent $quarantine) -Force | Out-Null
Move-Item -LiteralPath $source -Destination $quarantine
if (Test-Path -LiteralPath $source) { throw 'Source staging directory still exists after quarantine move.' }
$moved = @(Get-ChildItem -LiteralPath $quarantine -File)
foreach ($file in $moved) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -ne $expected[$file.Name]) {
        throw "Quarantined package hash drift: $($file.Name)"
    }
}
$manifest = [ordered]@{
    schema = 'lineboss/quarantine/bodyshop-legacy-lod-staging-v001/v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    status = 'RECOVERABLE_QUARANTINE__18_LEGACY_LOD_STAGING_PACKAGES__NO_DELETE'
    source = $source
    quarantine = $quarantine
    restore = "With Unreal closed: Move-Item -LiteralPath '$quarantine' -Destination '$source'"
    validation_receipt_sha256 = $expectedValidationHash
    press_v913_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $press).Hash
    files = @($moved | Sort-Object Name | ForEach-Object {
        [ordered]@{ name = $_.Name; bytes = $_.Length; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash }
    })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $quarantine 'QUARANTINE_MANIFEST.json') -Encoding utf8
Write-Output "PASS: quarantined 18 exact staging packages to $quarantine; nothing deleted."
