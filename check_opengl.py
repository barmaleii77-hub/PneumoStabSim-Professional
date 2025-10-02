import sys
try:
    import OpenGL.GL as gl
    print('? PyOpenGL installed')
    print(f'Version: {gl.__version__}')
except ImportError as e:
    print(f'? PyOpenGL NOT installed: {e}')
    sys.exit(1)
