param(
    [switch]$Verbose,
    [switch]$v
)

.\.venv\Scripts\Activate.ps1

if ($Verbose -or $v) {
    pytest -vv
} else {
    pytest -q
}
