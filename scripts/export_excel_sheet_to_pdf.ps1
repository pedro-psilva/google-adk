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

try {
    $resolvedWorkbookPath = (Resolve-Path -LiteralPath $WorkbookPath).Path
    $targetDirectory = Split-Path -Parent $PdfPath
    if ($targetDirectory -and -not (Test-Path -LiteralPath $targetDirectory)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false

    $workbook = $excel.Workbooks.Open($resolvedWorkbookPath, $null, $true)

    foreach ($sheet in $workbook.Worksheets) {
        if ($sheet.Name -eq $WorksheetName) {
            $worksheet = $sheet
            break
        }
    }

    if (-not $worksheet) {
        $worksheet = $workbook.ActiveSheet
    }

    $usedRange = $worksheet.UsedRange
    $values = $usedRange.Value2
    $minRowOffset = $null
    $maxRowOffset = $null
    $minColumnOffset = $null
    $maxColumnOffset = $null

    function Update-Bounds {
        param(
            [int]$RowOffset,
            [int]$ColumnOffset
        )

        if ($null -eq $minRowOffset -or $RowOffset -lt $minRowOffset) { $script:minRowOffset = $RowOffset }
        if ($null -eq $maxRowOffset -or $RowOffset -gt $maxRowOffset) { $script:maxRowOffset = $RowOffset }
        if ($null -eq $minColumnOffset -or $ColumnOffset -lt $minColumnOffset) { $script:minColumnOffset = $ColumnOffset }
        if ($null -eq $maxColumnOffset -or $ColumnOffset -gt $maxColumnOffset) { $script:maxColumnOffset = $ColumnOffset }
    }

    if ($values -is [System.Array]) {
        $rowCount = $values.GetLength(0)
        $columnCount = $values.GetLength(1)
        for ($rowIndex = 1; $rowIndex -le $rowCount; $rowIndex++) {
            for ($columnIndex = 1; $columnIndex -le $columnCount; $columnIndex++) {
                $cellValue = $values.GetValue($rowIndex, $columnIndex)
                if ($null -eq $cellValue) { continue }
                if ($cellValue -is [string] -and [string]::IsNullOrWhiteSpace($cellValue)) { continue }
                Update-Bounds -RowOffset $rowIndex -ColumnOffset $columnIndex
            }
        }
    }
    elseif ($null -ne $values -and -not [string]::IsNullOrWhiteSpace([string]$values)) {
        Update-Bounds -RowOffset 1 -ColumnOffset 1
    }

    if ($null -ne $minRowOffset) {
        $firstRow = $usedRange.Row + $minRowOffset - 1
        $lastRow = $usedRange.Row + $maxRowOffset - 1
        $firstColumn = $usedRange.Column + $minColumnOffset - 1
        $lastColumn = $usedRange.Column + $maxColumnOffset - 1

        $topLeft = $worksheet.Cells.Item($firstRow, $firstColumn)
        $bottomRight = $worksheet.Cells.Item($lastRow, $lastColumn)
        $printRange = $worksheet.Range($topLeft, $bottomRight)

        $worksheet.PageSetup.PrintArea = $printRange.Address($false, $false)
        $worksheet.PageSetup.Zoom = $false
        $worksheet.PageSetup.FitToPagesWide = 1
        $worksheet.PageSetup.FitToPagesTall = $false
    }

    $worksheet.ExportAsFixedFormat(0, $PdfPath)
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
