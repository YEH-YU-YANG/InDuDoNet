import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import pydicom
import shutil
from cbct.process import find_dicom_files

class TestProcess(unittest.TestCase):
    @patch('pydicom.dcmread')
    def test_find_dicom_files(self, mock_dcmread):
        # Configure the mock to return a dummy object with an InstanceNumber
        mock_dcmread.return_value = MagicMock(InstanceNumber=1)

        # Create a dummy patient directory with some dummy DICOM files
        patient_dir = Path("test_patient")
        
        # Ensure the directory is clean before starting the test
        if patient_dir.exists():
            shutil.rmtree(patient_dir)
        patient_dir.mkdir(exist_ok=True)
        
        # Create dummy DICOM files with numerical names for sorting
        (patient_dir / "0001.dcm").touch()
        (patient_dir / "0002.dcm").touch()

        files = find_dicom_files(str(patient_dir))
        self.assertEqual(len(files), 2)
        self.assertEqual(Path(files[0]).name, "0001.dcm")
        self.assertEqual(Path(files[1]).name, "0002.dcm")

        # Clean up the dummy directory and files
        shutil.rmtree(patient_dir)

if __name__ == '__main__':
    unittest.main()
