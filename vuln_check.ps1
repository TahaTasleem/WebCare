git pull > $null
python -m pip install -U --quiet pip > $null 2> $null
python -m pip install -U --quiet pipenv > $null 2> $null
pipenv --rm --bare > $null 2> $null
pipenv update  --bare > $null 2> $null
pipenv run pip install -U --quiet safety > $null  2> $null
Write-Output ""
Write-Output "Vulnerability Scan Results"
Write-Output "**************************"
$output = (pipenv run python -m safety check --output json | ConvertFrom-Json)
foreach($data in $output.vulnerabilities) {
    Write-Host $data.package_name - $data.vulnerable_spec - $data.CVE;
}
Write-Output "**************************"