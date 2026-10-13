"""User-supplied TIFF input for the early, image-specific teaching lessons."""
import argparse
import os
from pathlib import Path


def teaching_tiff_path():
    parser=argparse.ArgumentParser(description='Inspect a user-supplied TIFF for this teaching lesson.')
    parser.add_argument('--image',default=os.environ.get('TEM_PARTICLE_LAB_TIFF'),
                        help='TIFF path, or set TEM_PARTICLE_LAB_TIFF. Personal images are not included.')
    args=parser.parse_args()
    if not args.image:parser.error('Supply --image PATH or set TEM_PARTICLE_LAB_TIFF. See PROJECT_GUIDE.md for the portable public-data workflow.')
    path=Path(args.image).expanduser()
    if not path.is_file():parser.error('TIFF file does not exist: '+str(path))
    return path
