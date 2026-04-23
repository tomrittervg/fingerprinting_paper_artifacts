import hashlib

"""## Define the abstract FingerprintAlgorithm and Filter classes"""

"""
This is the base class for any fingerprinting algorithm.  It implementes the same API
as the hashlib hash function for simplicity.  Other algorithms should be implemented as subclasses
and then plugged into the fingerprint() function below
"""
class FingerprintAlgorithm:
  def __init__(self):
    raise NotImplementedError("Not Implemented")
  def update(self, value):
    raise NotImplementedError("Not Implemented")
  def hexdigest(self):
    raise NotImplementedError("Not Implemented")

"""
We also define a default fingerprint algorithm using SHA-1 to use as a default.
We chose SHA-1 because it was the fastest
"""
class SHA1Fingerprint(FingerprintAlgorithm):
  def __init__(self):
    self.hasher = hashlib.sha1(usedforsecurity=False)
    self.string = ""
  def update(self, value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    else:
        value = str(value)
    self.string += value + "|"
  def digest(self):
    self.hasher.update(self.string.encode('utf-8'))
    return self.hasher.digest()
  def hexdigest(self):
    return self.digest().hex()

class ConcatFingerprint(FingerprintAlgorithm):
  def __init__(self):
    self.value = ""
  def update(self, value):
    self.value += " | " + str(value)
  def hexdigest(self):
    return self.value
