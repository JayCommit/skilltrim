# Security

Report a vulnerability privately through GitHub's private vulnerability reporting on this repository:

https://github.com/JayCommit/skilltrim/security/advisories/new

Use the Security tab if that link is not available. There is no separate security email address.

Please include the skilltrim version, the command you ran, and the smallest example that demonstrates the issue. Remove secrets and private skill text before sending anything. Do not open a public issue for an unfixed vulnerability.

skilltrim reads local skill files and can write a new export directory and a JSON report. Reports and diffs can contain the original skill text. Do not send those artifacts unless you intend to disclose that text. The analyzer does not execute scripts inside skills it reviews; still, only point it at collections you trust and that do not contain secrets you would not want copied into an export.
