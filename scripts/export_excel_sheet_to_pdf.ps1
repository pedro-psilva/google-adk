param(
    [Parameter(Mandatory = $true)]
    [string]$WorkbookPath,

    [Parameter(Mandatory = $true)]
    [string]$PdfPath,

    [string]$WorksheetName = "Síntese"
)

$ErrorActionPreference = "Stop"

$excel = $null
$workbook = $null
$worksheet = $null
$usedRange = $null

function Normalize-LookupText {
    param(
        [AllowNull()]
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    $normalized = $Value.Normalize([Text.NormalizationForm]::FormD)
    $builder = New-Object System.Text.StringBuilder

    foreach ($character in $normalized.ToCharArray()) {
        $unicodeCategory = [Globalization.CharUnicodeInfo]::GetUnicodeCategory($character)
        if ($unicodeCategory -eq [Globalization.UnicodeCategory]::NonSpacingMark) {
            continue
        }
        [void]$builder.Append([char]::ToLowerInvariant($character))
    }

    return (($builder.ToString()) -replace "\s+", " ").Trim()
}

try {
    $resolvedWorkbookPath = (Resolve-Path -LiteralPath $WorkbookPath).Path
    $resolvedPdfPath = [System.IO.Path]::GetFullPath($PdfPath)
    $targetDirectory = Split-Path -Parent $resolvedPdfPath
    if ($targetDirectory -and -not (Test-Path -LiteralPath $targetDirectory)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false

    $workbook = $excel.Workbooks.Open($resolvedWorkbookPath, $null, $true)
    $normalizedWorksheetName = Normalize-LookupText -Value $WorksheetName

    foreach ($sheet in $workbook.Worksheets) {
        if ((Normalize-LookupText -Value $sheet.Name) -eq $normalizedWorksheetName) {
            $worksheet = $sheet
            break
        }
    }

    if (-not $worksheet) {
        $worksheet = $workbook.ActiveSheet
    }

    $usedRange = $worksheet.UsedRange
    if ([string]::IsNullOrWhiteSpace($worksheet.PageSetup.PrintArea)) {
        $worksheet.PageSetup.PrintArea = $usedRange.Address($false, $false)
    }

    $worksheet.PageSetup.CenterHorizontally = $true
    $worksheet.PageSetup.CenterVertically = $false
    $worksheet.PageSetup.Zoom = $false
    $worksheet.PageSetup.FitToPagesWide = 1
    $worksheet.PageSetup.FitToPagesTall = $false

    $worksheet.ExportAsFixedFormat(0, $resolvedPdfPath)
    Write-Output "PDF_EXPORTED"
}
finally {
    if ($usedRange) {
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($usedRange) | Out-Null
    }

    if ($workbook) {
        $workbook.Close($false)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) | Out-Null
    }

    if ($worksheet) {
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) | Out-Null
    }

    if ($excel) {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
