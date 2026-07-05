import argparse
import subprocess
import re
import sys
import os
from typing import Optional


def update_changelog_file(
    version: str, changelog_file: str, include_path: Optional[str] = None
) -> None:
    """Runs git-cliff and safely injects the new entries below the static header."""
    print(f"🔄 Running git-cliff to generate changelog for version {version}...")
    try:
        # 1. Capture the new markdown from git-cliff instead of modifying the file directly
        command = ["git-cliff", "--unreleased", "--tag", version]
        if include_path:
            command.extend(["--include-path", f"{include_path}/**"])

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        new_changelog_block = result.stdout.strip()

        # 2. Strip out the default git-cliff header so we don't duplicate your static text
        new_changelog_block = re.sub(
            r"^# Changelog\n+All notable changes to this project will be documented in this file\.\n+",
            "",
            new_changelog_block,
        )

        # 3. Read your current CHANGELOG.md
        if os.path.exists(changelog_file):
            with open(changelog_file, "r") as f:
                content = f.read()
        else:
            content = "# Changelog\nAll notable changes to this project will be documented in this file.\nThis project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n"

        # 4. Find your static header's end point
        injection_marker = (
            "adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
        )

        if injection_marker in content:
            # Check if this version's header is already present to avoid duplicates
            version_header = f"## [{version}]"
            if version_header in content:
                print(
                    f"ℹ️ {version_header} already exists in CHANGELOG.md. Skipping injection."
                )
                return

            # Split the file exactly at the marker and sandwich the new block in between
            parts = content.split(injection_marker)
            updated_content = (
                parts[0]
                + injection_marker
                + "\n\n"
                + new_changelog_block
                + "\n"
                + parts[1]
            )

            with open(changelog_file, "w") as f:
                f.write(updated_content)
            print(
                f"✅ Safely injected new changelog into {changelog_file} below the static header."
            )
        else:
            print(
                f"⚠️ Warning: Injection marker not found in {changelog_file}. Appending to top instead."
            )
            with open(changelog_file, "w") as f:
                f.write(new_changelog_block + "\n\n" + content)

    except FileNotFoundError:
        print("❌ Error: 'git-cliff' is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(
            f"❌ Error: git-cliff failed with exit code {e.returncode}\n{e.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update CHANGELOG.md using git-cliff")
    parser.add_argument("--version", required=True, help="New version tag")
    parser.add_argument("--changelog", required=True, help="Path to CHANGELOG.md")
    parser.add_argument(
        "--path", help="Folder path to include in changelog (e.g. backend)"
    )

    args = parser.parse_args()
    update_changelog_file(args.version, args.changelog, args.path)
