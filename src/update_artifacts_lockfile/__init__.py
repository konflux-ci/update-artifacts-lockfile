"""Update artifact checksums in a YAML lockfile."""

import argparse
import hashlib
import json
from typing import Any, Dict, List, Optional

import requests
from ruamel.yaml import YAML


def calculate_checksum(file_content: bytes, algorithm_name: str) -> Optional[str]:
    """Calculate the checksum of file content using the specified algorithm."""
    try:
        hasher = hashlib.new(algorithm_name)
        hasher.update(file_content)
        return hasher.hexdigest()
    except ValueError:
        print(
            f"Error: Unsupported hash algorithm '{algorithm_name}'. "
            f"Supported algorithms include: {hashlib.algorithms_available}"
        )
        return None


def update_artifact_checksums(yaml_file_path: str) -> None:
    """Read the lockfile, refresh all checksums, and write it back."""
    yaml_parser = YAML()
    yaml_parser.default_flow_style = False
    yaml_parser.preserve_quotes = True
    yaml_parser.indent(mapping=2, sequence=4, offset=2)
    data: Dict[str, Any] = {}
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = yaml_parser.load(f)
    except FileNotFoundError:
        print(f"Error: YAML file not found at '{yaml_file_path}'")
        return
    except Exception as e:
        print(f"Error parsing YAML file: {e}")
        return

    if not data or 'artifacts' not in data or not isinstance(data['artifacts'], list):
        print("Error: YAML file must contain an 'artifacts' list.")
        return

    artifacts: List[Dict[str, Any]] = data['artifacts']

    for i, artifact in enumerate(artifacts):
        download_url: Optional[str] = artifact.get('download_url')
        current_checksum: Optional[str] = artifact.get('checksum')
        filename: Optional[str] = artifact.get('filename')

        if not download_url:
            print(f"Warning: Artifact {i+1} is missing 'download_url'. Skipping.")
            continue

        if not current_checksum or ':' not in current_checksum:
            print(
                f"Warning: Artifact {i+1} ('{filename}') has an invalid "
                f"or missing 'checksum' format. Skipping update for this artifact."
            )
            continue

        algorithm_name, _ = current_checksum.split(':', 1)
        algorithm_name = algorithm_name.lower()

        print(f"Processing artifact: {filename} from {download_url}")

        try:
            response = requests.get(download_url, stream=True, timeout=10)
            response.raise_for_status()

            file_content_chunks: List[bytes] = []
            for chunk in response.iter_content(chunk_size=8192):
                file_content_chunks.append(chunk)
            file_content: bytes = b"".join(file_content_chunks)

            new_hash_value: Optional[str] = calculate_checksum(file_content, algorithm_name)

            if new_hash_value:
                new_checksum: str = f"{algorithm_name}:{new_hash_value}"
                if new_checksum != current_checksum:
                    print(f"  Checksum updated for '{filename}': {current_checksum} -> {new_checksum}")
                    artifact['checksum'] = new_checksum
                else:
                    print(f"  Checksum for '{filename}' is already up-to-date: {current_checksum}")
            else:
                print(f"  Failed to calculate checksum for '{filename}'. Keeping old checksum.")

        except requests.exceptions.RequestException as e:
            print(f"  Error downloading '{filename}' from {download_url}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing '{filename}': {e}")

    try:
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            yaml_parser.dump(data, f)
        print(f"\nSuccessfully updated checksums in '{yaml_file_path}'.")
    except Exception as e:
        print(f"Error writing updated YAML file: {e}")


def main() -> None:
    """Entry point for the update_artifacts_lockfile command."""
    parser = argparse.ArgumentParser(description="Refresh checksums in an artifacts lockfile.")
    parser.add_argument("-f", "--file", type=argparse.FileType("r"))
    parser.add_argument(
        "yaml_file_path",
        nargs="?",
        default="artifacts.lock.yaml",
        help="lockfile to update (default: artifacts.lock.yaml)",
    )
    args = parser.parse_args()

    if args.file:
        package_files = dict.fromkeys(
            upgrade["packageFile"] for upgrade in json.load(args.file)
        )
        for package_file in package_files:
            update_artifact_checksums(package_file)
    else:
        update_artifact_checksums(args.yaml_file_path)
