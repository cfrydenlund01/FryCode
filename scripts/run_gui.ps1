param(
    [switch]$Verbose,
    [switch]$v
)

.\.venv\Scripts\Activate.ps1

if ($Verbose -or $v) {
    python main.py --verbose
} else {
    python main.py
}
