import io
import datetime as dt
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset

from modules.input_handler import InputHandler


def _make_dicom_bytes(width: int = 128, height: int = 128) -> io.BytesIO:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
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

    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, little_endian=True, implicit_vr=False)
    buf.seek(0)
    buf.name = "test.dcm"
    return buf


def test_validate_report_empty():
    handler = InputHandler()
    ok, error = handler.validate_report("")
    assert not ok
    assert "empty" in error.lower()


def test_validate_report_too_short():
    handler = InputHandler()
    ok, error = handler.validate_report("short report")
    assert not ok
    assert "too short" in error.lower()


def test_validate_report_too_long():
    handler = InputHandler()
    ok, error = handler.validate_report("a" * 50001)
    assert not ok
    assert "too long" in error.lower()


def test_load_dicom_success():
    handler = InputHandler()
    buf = _make_dicom_bytes()
    ok, error = handler.validate_image(buf)
    assert ok, error

    image, metadata = handler.load_image(buf)
    assert image is not None
    assert image.shape[0] == 128
    assert image.shape[1] == 128
    assert image.shape[2] == 3
    assert metadata["format"] == "DICOM"
