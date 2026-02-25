
try:
    print("Importing numpy...")
    import numpy
    print(f"Numpy version: {numpy.__version__}")
    print("Numpy imported successfully.")
except Exception as e:
    print(f"Failed to import numpy: {e}")

try:
    print("\nImporting scipy...")
    import scipy
    print(f"Scipy version: {scipy.__version__}")
    print("Scipy imported successfully.")
except Exception as e:
    print(f"Failed to import scipy: {e}")

try:
    print("\nImporting sklearn (scikit-learn)...")
    import sklearn
    print(f"Sklearn version: {sklearn.__version__}")
    print("Sklearn imported successfully.")
    
    print("Importing sklearn.ensemble...")
    from sklearn.ensemble import IsolationForest
    print("sklearn.ensemble imported successfully.")
except Exception as e:
    print(f"Failed to import sklearn: {e}")
