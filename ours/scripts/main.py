import argparse
from pathlib import Path
from cbct.process import convert_cbct_to_nifti
from cbct.visualize import save_mar_png
from cbct.compare import view_before_after
from cbct.inspect import inspect_dicom_cbct
from cbct.debug import debug_mask

def main():
    parser = argparse.ArgumentParser(description='CBCT processing and visualization tool.')
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for the convert command
    convert_parser = subparsers.add_parser('convert', help='Convert DICOM to NIfTI')
    convert_parser.add_argument('patients', nargs='+', help='List of patient IDs')
    convert_parser.add_argument('--base_dir', required=True, help='Base directory for patient data')
    convert_parser.add_argument('--output_dir', required=True, help='Output directory for NIfTI files')
    convert_parser.add_argument('--spacing', type=float, required=True, help='Target spacing for resampling')

    # Subparser for the visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Save MAR PNGs')
    visualize_parser.add_argument('--mar', required=True, help='MAR NIfTI file')
    visualize_parser.add_argument('--out_dir', required=True, help='Output directory for PNGs')
    visualize_parser.add_argument('--target', type=int, default=640, help='Target size')
    visualize_parser.add_argument('--vmin', type=float, default=-1000, help='Window vmin (HU)')
    visualize_parser.add_argument('--vmax', type=float, default=4500, help='Window vmax (HU)')
    visualize_parser.add_argument('--start', type=int, default=0, help='Start slice')
    visualize_parser.add_argument('--end', type=int, default=-1, help='End slice')
    visualize_parser.add_argument('--every', type=int, default=1, help='Save every N slices')
    visualize_parser.add_argument('--no_hu', action='store_true', help='Do not convert to HU')

    # Subparser for the compare command
    compare_parser = subparsers.add_parser('compare', help='Compare before and after MAR')
    compare_parser.add_argument('--raw_root', required=True, help='Root directory of raw NIfTI files')
    compare_parser.add_argument('--mar_root', required=True, help='Root directory of MAR NIfTI files')
    compare_parser.add_argument('--out_root', required=True, help='Output root directory')
    compare_parser.add_argument('--case_id', default='', help='Case ID to process')
    compare_parser.add_argument('--vmin', type=float, default=-1000, help='Window vmin (HU)')
    compare_parser.add_argument('--vmax', type=float, default=4500, help='Window vmax (HU)')
    compare_parser.add_argument('--start', type=int, default=0, help='Start slice')
    compare_parser.add_argument('--end', type=int, default=-1, help='End slice')
    compare_parser.add_argument('--every', type=int, default=1, help='Save every N slices')
    compare_parser.add_argument('--rot90', type=int, default=0, help='Rotate 90 degrees')
    compare_parser.add_argument('--flipud', action='store_true', help='Flip up-down')
    compare_parser.add_argument('--fliplr', action='store_true', help='Flip left-right')

    # Subparser for the inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect DICOM files')
    inspect_parser.add_argument('--root', required=True, help='Root directory of DICOM files')
    inspect_parser.add_argument('--pattern', default='cbct', help='Pattern for DICOM directories')
    inspect_parser.add_argument('--ext', default='.dcm', help='File extension for DICOM files')
    inspect_parser.add_argument('--pixel_sample', type=int, default=0, help='Number of pixels to sample')

    # Subparser for the debug command
    debug_parser = subparsers.add_parser('debug', help='Debug mask thresholds')
    debug_parser.add_argument('--nii_path', required=True, help='Path to NIfTI file')
    debug_parser.add_argument('--out_dir', default='threshold_debug', help='Output directory')
    debug_parser.add_argument('--slice_k', type=int, default=-1, help='Slice to visualize')
    debug_parser.add_argument('--thrs', type=int, nargs='+', default=[1500, 2000, 2500, 3000, 4000], help='Thresholds to test')


    args = parser.parse_args()

    if args.command == 'convert':
        convert_cbct_to_nifti(args.patients, args.base_dir, args.output_dir, args.spacing)
    elif args.command == 'visualize':
        save_mar_png(Path(args.mar), Path(args.out_dir), args.target, args.vmin, args.vmax, args.start, args.end, args.every, args.no_hu)
    elif args.command == 'compare':
        view_before_after(
            raw_root=Path(args.raw_root),
            mar_root=Path(args.mar_root),
            out_root=Path(args.out_root),
            case_id=args.case_id,
            vmin=args.vmin,
            vmax=args.vmax,
            start=args.start,
            end=args.end,
            every=args.every,
            rot90=args.rot90,
            flipud=args.flipud,
            fliplr=args.fliplr
        )
    elif args.command == 'inspect':
        inspect_dicom_cbct(Path(args.root), args.pattern, args.ext, args.pixel_sample)
    elif args.command == 'debug':
        debug_mask(Path(args.nii_path), Path(args.out_dir), args.slice_k, args.thrs)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()