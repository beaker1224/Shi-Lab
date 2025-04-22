import subprocess
import os
import sys

def run_prm_srs():
    """
    Run the MATLAB script for PRM-SRS lipid subtype detection.
    """
    print("Starting MATLAB code for PRM-SRS lipid subtype detection...")
    script = os.path.join(os.getcwd(), "PRM_SRS", "srs5_image_generation.m")
    
    if not os.path.isdir(image_folder):
        print(f"Error: Expected images folder not found at {image_folder}")
        return
    print(f"Running PRM-SRS on images in: {image_folder}")

    if not os.path.isfile(script):
        print(f"Error: MATLAB script not found at {script}")
        return
    # Invoke MATLAB in batch mode
    cmd = [
        "matlab",
        "-nodisplay",
        "-nosplash",
        "-r",
        f"try, image_folder = '{image_folder.replace("'", "''")}'; "
            "srs5_image_generation(image_folder); "
            "catch e, disp(getReport(e)); exit(1); end; exit(0);"
    ]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("MATLAB script completed successfully.")
    else:
        print(f"MATLAB script failed with return code {result.returncode}.")


def run_redox():
    """
    Run the Python script for Redox analysis.
    """
    print("Starting Python code for Redox analysis...")
    script = os.path.join(os.getcwd(), "Redox", "redox.py")
    if not os.path.isfile(script):
        print(f"Error: Python script not found at {script}")
        return
    result = subprocess.run([sys.executable, script])
    if result.returncode == 0:
        print("Redox analysis completed successfully.")
    else:
        print(f"Redox analysis failed with return code {result.returncode}.")


def run_k_means():
    """
    Run the Python script for K-Means clustering.
    """
    print("Starting Python code for K-Means clustering...")
    script = os.path.join(os.getcwd(), "K_Means", "k_means.py")
    if not os.path.isfile(script):
        print(f"Error: Python script not found at {script}")
        return
    result = subprocess.run([sys.executable, script])
    if result.returncode == 0:
        print("K-Means clustering completed successfully.")
    else:
        print(f"K-Means clustering failed with return code {result.returncode}.")


def run_enrichment_conditions():
    """
    Run the Python script for enrichment conditions analysis.
    """
    print("Starting Python code for enrichment conditions analysis...")
    script = os.path.join(os.getcwd(), "Enrichment_Conditions", "enrichment_conditions.py")
    if not os.path.isfile(script):
        print(f"Error: Python script not found at {script}")
        return
    result = subprocess.run([sys.executable, script])
    if result.returncode == 0:
        print("Enrichment conditions analysis completed successfully.")
    else:
        print(f"Enrichment conditions analysis failed with return code {result.returncode}.")


def main():
    image_folder = os.path.join(script, 'images_to_analyze')
    # If missing, create and prompt user to add images
    if not os.path.isdir(image_folder):
        os.makedirs(image_folder)
        print(f"Created images folder at {image_folder}. Please put images into this folder and re-run.")
        return
    
    operations = {
        "1": (run_prm_srs, "PRM-SRS lipid subtype detection"),
        "2": (run_redox, "Redox analysis"),
        "3": (run_k_means, "K-Means clustering"),
        "4": (run_enrichment_conditions, "Enrichment conditions analysis")
    }

    print("Welcome to Shi Lab Integrated Pipeline! Choose an analysis to run, or 'q' to quit:")
    for key, (_, desc) in operations.items():
        print(f"  {key}: {desc}")
    print("  q: Quit")

    choice = input("Your choice: ").strip()
    if choice.lower() == 'q':
        print("Exiting.")
        return

    action = operations.get(choice)
    if action:
        func, _ = action
        func()
    else:
        print("Invalid choice. Please select a valid number.")
        main()


if __name__ == "__main__":
    main()
