import datetime as dt
from pathlib import Path

import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset

from modules.input_handler import InputHandler


def _write_dicom(path: Path, width: int = 128, height: int = 128) -> None:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyDate = dt.datetime.now().strftime("%Y%m%d")
    ds.Rows = height
    ds.Columns = width
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0

    pixels = (np.random.rand(height, width) * 4095).astype(np.uint16)
    ds.PixelData = pixels.tobytes()

    pydicom.dcmwrite(str(path), ds, little_endian=True, implicit_vr=False)


def test_dicom_sample_loads(tmp_path: Path):
    dicom_path = tmp_path / "sample.dcm"
    _write_dicom(dicom_path)

    handler = InputHandler()
    with dicom_path.open("rb") as f:
        ok, error = handler.validate_image(f)
        assert ok, error

        image, metadata = handler.load_image(f)

    assert image is not None
    assert image.shape[0] == 128
    assert image.shape[1] == 128
    assert image.shape[2] == 3
    assert metadata["format"] == "DICOM"
    assert metadata["channels"] == 3
