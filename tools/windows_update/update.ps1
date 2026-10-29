$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.Application]::EnableVisualStyles()
    Write-Host '请先关闭正在制作视频的窗口。'
    Write-Host '在弹出的窗口里，找到原来那套工具，选择“制作视频-Windows.bat”。'
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = '选择原来使用的“制作视频-Windows.bat”'
    $picker.Filter = '原来的制作入口 (制作视频-Windows.bat)|制作视频-Windows.bat'
    $picker.InitialDirectory = [Environment]::GetFolderPath('Desktop')
    $picker.CheckFileExists = $true
    if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        Write-Host '已取消，原来的工具没有改动。'
        exit 0
    }
    $folder = [IO.Path]::GetDirectoryName($picker.FileName)
    $picker.Dispose()
    $python = Join-Path $folder '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw '这里没有找到已安装的运行环境。请重新选择之前能正常制作视频的那套工具。'
    }
    & $python (Join-Path $PSScriptRoot 'update.py') --target-dir $folder
    exit $LASTEXITCODE
} catch {
    Write-Host ('更新没有完成：' + $_.Exception.Message)
    Write-Host '请把这个窗口的报错拍照交给协助者。'
    exit 1
}
