import numpy as np
from contextlib import contextmanager
import rasterio
from rasterio.profiles import DefaultGTiffProfile


# use context manager so DatasetReader and MemoryFile get cleaned up automatically
@contextmanager
def mem_raster(array, source_ds):
    profile = source_ds.profile
    profile.update(driver='GTiff', dtype=array.dtype)

    with rasterio.MemoryFile() as memfile:
        with memfile.open(**profile) as dataset: # Open as DatasetWriter
            dataset.write(array,1)

        with memfile.open() as dataset:  # Reopen as DatasetReader
            yield dataset  # Note yield not return


def transform(array, xmin, ymax, dx, dy):

    transform = rasterio.Affine(dx, 0.0, xmin, 0.0, -dy, ymax)
    new_transform = rasterio.transform.from_origin(xmin, ymax, dx, dy)

    new_dataset = rasterio.open(
                    "carmel.tif", "w", 
                    driver = "GTiff",
                    height = array.shape[0],
                    width = array.shape[1],
                    count = 1,
                    nodata = -9999,
                    dtype = array.dtype,
                    crs = 32636,
                    transform = new_transform
                    )

    tiff = mem_raster(array, new_dataset)
    with tiff as mem:
        print(mem.dtypes, mem.crs, mem.bounds)

    return tiff


if __name__ == "__main__":
    a = np.random.rand(100,100)
    xmin = 123
    dx = 500
    ymax = 456
    dy = 300

    tiff = transform(a, xmin, ymax, dx, dy)
    

