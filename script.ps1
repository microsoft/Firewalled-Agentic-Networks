# Define the base directory name (relative to project root)
$baseDirName = "all_outputs_with_judge"
$baseDir = ".\$baseDirName"
$configPath = "judge/config_judge.yaml"
$pythonScript = "judge/special_judge.py"

# Load the original config file content
$configTemplate = Get-Content $configPath -Raw

# Loop through each persona folder
Get-ChildItem -Path $baseDir -Directory | ForEach-Object {
    $folderName = $_.Name

    # Extract persona number using regex
    if ($folderName -match "taskConfined" -and $folderName -match "persona(\d+)")  {
        $personaNumber = $matches[1]

        # Use the baseDirName variable in the replacement
        $updatedConfig = $configTemplate `
            -replace 'user_env_file: ".*?"', "user_env_file: `"resources/env_persona$personaNumber.txt`"" `
            -replace 'outputs: ".*?"', "outputs: `"$baseDirName/$folderName`""

        # Write the updated config back to the file
        Set-Content -Path $configPath -Value $updatedConfig

        # Read the config again and print it
        $verifiedConfig = Get-Content $configPath -Raw
        Write-Host "========================================="
        Write-Host "Updated config for: $folderName"
        Write-Host $verifiedConfig
        Write-Host "========================================="

        # Run the Python script
        python $pythonScript
    }
}
