import os
import sys
import argparse

def is_windows1252_file(path):
    b = open(path, 'rb').read()
    # reject UTF-8 BOM
    if b.startswith(b'\xef\xbb\xbf'):
        return False, 'UTF-8 BOM present'
    # if it's valid UTF-8, check whether its UTF-8 bytes match what cp1252 would produce
    try:
        s = b.decode('utf-8')
    except UnicodeDecodeError:
        # not valid UTF-8 -> likely single-byte encoding (ok for cp1252)
        return True, None
    # valid UTF-8: check if every character can be encoded to cp1252
    try:
        b_cp = s.encode('cp1252')
    except UnicodeEncodeError:
        return False, 'Contains characters not representable in windows-1252'
    # if cp1252-encoding of the decoded text doesn't equal original bytes,
    # original is UTF-8 (multi-byte) rather than cp1252 single-byte
    if b_cp != b:
        return False, 'File is UTF-8 encoded (bytes differ from cp1252)'
    return True, None

def main():
    p = argparse.ArgumentParser(description='Verify localisation files are windows-1252')
    p.add_argument('folder', nargs='?', default=os.path.normpath(os.path.join(os.path.dirname(__file__),'..','localisation')))
    args = p.parse_args()
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f'Folder not found: {folder}', file=sys.stderr)
        sys.exit(2)

    files = 0
    failures = []
    for root, _, filenames in os.walk(folder):
        for fn in filenames:
            files += 1
            path = os.path.join(root, fn)
            ok, reason = is_windows1252_file(path)
            if not ok:
                failures.append((path, reason))
                print(f'BAD: {path} -> {reason}')

    if failures:
        print(f'\n{len(failures)} file(s) not windows-1252')
        print(failures)
        sys.exit(1)
    
    print(f'\nAll {files} files appear to be windows-1252')
    sys.exit(0)

if __name__ == '__main__':
    main()
