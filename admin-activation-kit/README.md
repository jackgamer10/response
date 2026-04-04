# MagxxicVOT XII - Admin Activation Kit

This kit is used by administrators to generate machine-specific activation tokens for the **MagxxicVOT XII - Professional Security Auditor**.

## Usage

1.  Ask the user for their unique **HWID** (displayed when they run the main application).
2.  Run `run_admin.bat` (Windows) or `python generator.py` (Linux/macOS).
3.  Enter the user's HWID.
4.  Copy the generated **TOKEN** and send it back to the user.
5.  The user will enter this token into the main application to unlock it.

## Technical Details

- **Salt**: Uses the standard `MAGXXIC` salt.
- **Algorithm**: SHA256 (HWID + Salt).
- **Format**: Upper-case hexadecimal, truncated to 24 characters.
