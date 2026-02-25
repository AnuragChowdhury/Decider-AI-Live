
try:
    print("Importing numpy...")
    import numpy
    print(f"Numpy version: {numpy.__version__}")
except Exception as e:
    print(f"Failed to import numpy: {e}")

try:
    print("Importing numpy.fft...")
    import numpy.fft
    print("numpy.fft imported successfully.")
except Exception as e:
    print(f"Failed to import numpy.fft: {e}")

try:
    print("Importing _pocketfft_umath directly...")
    from numpy.fft import _pocketfft_umath
    print("_pocketfft_umath imported successfully.")
except Exception as e:
    print(f"Failed to import _pocketfft_umath: {e}")
