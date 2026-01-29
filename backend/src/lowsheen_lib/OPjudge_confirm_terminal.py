#!/usr/bin/env python3
"""
OPjudge Confirm Mode - Terminal Version
Terminal-based operator judgment for headless/Docker environments
Compatible with WebPDTool measurement_service.py expectations
"""

import sys
import ast
import os
from pathlib import Path


def display_image_info(image_path: str) -> None:
    """Display image information (file check)"""
    if image_path:
        path = Path(image_path)
        if path.exists():
            print(f"\n📷 Reference Image: {image_path}")
            print(f"   File size: {path.stat().st_size} bytes")
            print(f"   Last modified: {path.stat().st_mtime}")
        else:
            print(f"\n⚠️  Warning: Image file not found: {image_path}")
    else:
        print("\n📷 No reference image provided")


def prompt_operator(content: str) -> str:
    """Prompt operator for confirmation"""
    print("\n" + "="*60)
    print("OPERATOR JUDGMENT - CONFIRM MODE")
    print("="*60)

    if content:
        print(f"\n📋 Check: {content}\n")

    print("Press [Enter] to CONFIRM (PASS)")
    print("Press [Ctrl+C] or type 'no' to REJECT (FAIL)")
    print("-"*60)

    try:
        response = input("Your judgment: ").strip().lower()

        if response in ['no', 'n', 'fail', 'reject']:
            return "FAIL"
        else:
            # Empty input or any other input = PASS (confirm)
            return "PASS"

    except (KeyboardInterrupt, EOFError):
        print("\n\n❌ Operator rejected (Ctrl+C)")
        return "FAIL"


def main():
    """Main execution function"""
    try:
        # Validate arguments
        if len(sys.argv) < 3:
            print("ERROR: Invalid arguments", file=sys.stderr)
            print("Usage: python3 OPjudge_confirm_terminal.py <test_point_id> <TestParams>",
                  file=sys.stderr)
            print("Example: python3 OPjudge_confirm_terminal.py 'LED_Check' \"['ImagePath=/test.jpg', 'content=Check LED']\"",
                  file=sys.stderr)
            sys.exit(1)

        test_point_id = sys.argv[1]
        test_params_str = sys.argv[2]

        # Parse TestParams
        try:
            # Handle both list and dict formats
            test_params = ast.literal_eval(test_params_str)

            # Extract parameters
            if isinstance(test_params, list):
                # List format: ['ImagePath=/path', 'content=text']
                params_dict = {}
                for param in test_params:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params_dict[key] = value

                image_path = params_dict.get('ImagePath', '')
                content = params_dict.get('content', '')

            elif isinstance(test_params, dict):
                # Dict format: {'ImagePath': '/path', 'content': 'text'}
                image_path = test_params.get('ImagePath', '')
                content = test_params.get('content', '')

            else:
                raise ValueError(f"TestParams must be list or dict, got {type(test_params)}")

        except (ValueError, SyntaxError) as e:
            print(f"ERROR: Failed to parse TestParams: {e}", file=sys.stderr)
            print(f"TestParams string: {test_params_str}", file=sys.stderr)
            sys.exit(1)

        # Validate required parameters
        if not image_path and not content:
            print("ERROR: Missing required parameters (ImagePath or content)", file=sys.stderr)
            sys.exit(1)

        # Display header
        print(f"\n{'='*60}")
        print(f"Test Point: {test_point_id}")
        print(f"{'='*60}")

        # Display image info
        display_image_info(image_path)

        # Prompt operator
        result = prompt_operator(content)

        # Output result (consumed by measurement_service.py)
        print(result)

        # Exit with success code
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
