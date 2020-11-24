$files = Get-ChildItem
foreach ($f in $files){
    if ($f.Extension -eq '.py') {
        $zip_name = $f.Name.replace('.py', '.zip')
        Compress-Archive -Update -Path $f.Name -DestinationPath $zip_name
    }
} 