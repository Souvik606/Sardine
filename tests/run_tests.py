
import os
import subprocess
import sys

def run_tests():
    tests_dir = os.path.join(os.path.dirname(__file__), 'features')
    sards_executable = os.path.join(os.path.dirname(__file__), '..', 'sards', 'shell.py')
    
    passed_count = 0
    failed_count = 0

    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith('.sad'):
                test_path = os.path.join(root, file)
                output_path = test_path.replace('.sad', '.out')

                if not os.path.exists(output_path):
                    print(f"SKIPPING: No .out file for {test_path}")
                    continue

                try:
                    # Run the .sad file using the interpreter
                    result = subprocess.run(
                        [sys.executable, sards_executable, test_path],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    actual_output = result.stdout.strip()

                    with open(output_path, 'r') as f:
                        expected_output = f.read().strip()

                    if actual_output == expected_output:
                        print(f"PASS: {test_path}")
                        passed_count += 1
                    else:
                        print(f"FAIL: {test_path}")
                        print("Expected:")
                        print(expected_output)
                        print("Got:")
                        print(actual_output)
                        failed_count += 1
                except subprocess.CalledProcessError as e:
                    print(f"ERROR: {test_path} failed to run.")
                    print(e.stderr)
                    failed_count += 1
                except FileNotFoundError:
                    print(f"ERROR: Could not find {sards_executable}. Make sure it's in the right path.")
                    sys.exit(1)

    print("\n--- Test Summary ---")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
