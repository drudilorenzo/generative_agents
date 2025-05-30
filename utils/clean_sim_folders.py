import os
import re
import shutil
import argparse
from collections import defaultdict

# Get the absolute path to the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of utils)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def parse_sim_name(folder_name):
  # Extract the base name and the s-number
  match = re.match(r"(.+)-s-(\d+)-", folder_name)
  if match:
    return match.group(1), int(match.group(2))
  return None, None


def get_movement_steps_range(folder_path):
  movement_dir = os.path.join(folder_path, "movement")
  if not os.path.exists(movement_dir):
    return None

  step_files = []
  for file in os.listdir(movement_dir):
    if file.endswith(".json"):
      try:
        step_num = int(file.split(".")[0])
        step_files.append(step_num)
      except ValueError:
        continue

  if not step_files:
    return None

  min_step = min(step_files)
  max_step = max(step_files)

  # Verify continuous coverage from min to max
  expected_steps = set(range(min_step, max_step + 1))
  actual_steps = set(step_files)
  missing_steps = expected_steps - actual_steps

  if missing_steps:
    print(f"Warning: Missing steps in {folder_path}: {sorted(missing_steps)}")
    return None

  return min_step, max_step


def cleanup_simulation_folders(directory, dry_run=True, interactive=True):
  subdirs = os.listdir(directory)
  # Dictionary to store folders by base name
  sim_folders = defaultdict(list)
  total_deletions = 0  # Track total number of deletions

  print("Directories found:", len(subdirs))

  # Get all folders in the directory
  for subdir in subdirs:
    full_path = os.path.join(directory, subdir)
    if os.path.isdir(full_path):
      base_name, s_num = parse_sim_name(subdir)
      if base_name and s_num is not None:
        sim_folders[base_name].append((s_num, subdir))

  print("Simulation groups to process:", len(sim_folders))

  # For each simulation name, find the highest s-number
  for base_name, folders in sim_folders.items():
    if not folders:
      continue

    # Sort by s-number and get the highest
    folders.sort(key=lambda x: x[0])
    max_s_num = folders[-1][0]
    latest_folder = next(
      folder_name for s_num, folder_name in folders if s_num == max_s_num
    )
    latest_folder_path = os.path.join(directory, latest_folder)

    # Print all folders for this simulation name
    print(f"\nSimulation: {base_name}")
    print("Available folders:")
    for s_num, folder_name in sorted(folders, key=lambda x: x[0]):
      status = "KEEP" if s_num == max_s_num else "DELETE"
      print(f"  {status}: {folder_name}")

    # Get movement steps range for the latest folder
    steps_range = get_movement_steps_range(latest_folder_path)
    if steps_range:
      min_step, max_step = steps_range
      print(
        f"\nLatest folder ({latest_folder}) contains complete steps {min_step} to {max_step}"
      )
    else:
      print(
        f"\nWarning: Latest folder ({latest_folder}) does not have complete step coverage"
      )

    # Get folders to delete
    folders_to_delete = [
      (s_num, folder_name) for s_num, folder_name in folders if s_num < max_s_num
    ]

    if not folders_to_delete:
      print("  No folders to delete")
      continue

    if interactive:
      dry_run_text = "[DRY RUN] " if dry_run else ""
      while True:
        response = input(
          f"\n{dry_run_text}Delete {len(folders_to_delete)} folders for {base_name}? [y/n]: "
        ).lower()
        if response in ["y", "n"]:
          break
        print("Please enter 'y' or 'n'")
      if response == "n":
        print(f"Skipping deletion for {base_name}")
        continue

    if dry_run:
      print("\n[DRY RUN] Would remove these folders:")
      for _, folder_name in folders_to_delete:
        print(f"  {folder_name}")
    else:
      print(f"\nRemoving {len(folders_to_delete)} folders for {base_name}:")
      for _, folder_name in folders_to_delete:
        folder_path = os.path.join(directory, folder_name)
        print(f"  {folder_name}")
        shutil.rmtree(folder_path)

    total_deletions += len(folders_to_delete)

  return total_deletions


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Clean up simulation folders by keeping only the latest version"
  )
  parser.add_argument(
    "--dir",
    type=str,
    help="Directory containing simulation folders (default: ../environment/frontend_server/storage/)",
  )
  parser.add_argument(
    "--execute",
    action="store_true",
    help="Actually delete the folders (default is dry run)",
  )
  parser.add_argument(
    "--automatic",
    action="store_true",
    help="Skip confirmation prompts (default is interactive)",
  )

  args = parser.parse_args()

  # Set default directory if none provided
  if args.dir is None:
    args.dir = os.path.join(PROJECT_ROOT, "environment", "frontend_server", "storage")

  if not os.path.exists(args.dir):
    print(f"Error: Directory '{args.dir}' does not exist")
    exit(1)

  print(f"Starting cleanup in directory: {args.dir}")

  if not args.execute:
    print("DRY RUN - No files will be deleted. Use --execute to turn off dry mode.")

  total_deletions = cleanup_simulation_folders(
    args.dir, dry_run=not args.execute, interactive=not args.automatic
  )

  if args.execute:
    print(f"{total_deletions} total directories deleted.")
  else:
    print(
      f"[DRY RUN] {total_deletions} total directories would be deleted. Use --execute to turn off dry mode."
    )

  print("Done!")
