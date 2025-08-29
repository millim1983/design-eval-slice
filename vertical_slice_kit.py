# Fallback: create a regular tar (no compression) to avoid environment limitations.
import tarfile, os

base = "/mnt/data/vertical_slice_kit"
tar_path = "/mnt/data/vertical_slice_kit.tar"

with tarfile.open(tar_path, "w") as tar:
    tar.add(base, arcname="vertical_slice_kit")

tar_path

