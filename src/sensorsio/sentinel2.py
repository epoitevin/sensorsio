#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021 CESBIO / Centre National d'Etudes Spatiales

from enum import Enum
import dateutil
from typing import List, Tuple, Union
import glob
import os
import numpy as np
import xarray as xr
import rasterio as rio
from sensorsio import utils


"""
This module contains Sentinel2 (L2A MAJA) related functions
"""

class Sentinel2:
    """
    Class for Sentinel2 L2A (MAJA format) product reading
    """     
    def __init__(self, product_dir:str, offsets:Tuple[float]=None):
        """
        Constructor

        :param product_dir: Path to product directory
        :param offsets: Shifts applied to image orgin (as computed by StackReg for instance)
        """
        # Store product DIR
        self.product_dir = os.path.normpath(product_dir)
        self.product_name = os.path.basename(self.product_dir)

        # Store offsets
        self.offsets = offsets

        # Get
        self.satellite = Sentinel2.Satellite(self.product_name[0:10])
                
        # Get tile
        self.tile = self.product_name[35:41]

        # Get acquisition date
        self.date = dateutil.parser.parse(self.product_name[11:19])
        self.year = self.date.year
        self.day_of_year = self.date.timetuple().tm_yday
        
        with rio.open(self.build_band_path(Sentinel2.B2)) as ds:
        # Get bounds
            self.bounds  = ds.bounds
        # Get crs
            self.crs = ds.crs

    def __repr__(self):
        return f'{self.satellite.value}, {self.date}, {self.tile}'

    # Enum class for sensor
    class Satellite(Enum):
        S2A = 'SENTINEL2A'
        S2B = 'SENTINEL2B'

    # Aliases
    S2A = Satellite.S2A
    S2B = Satellite.S2B

    # Enum class for Sentinel2 bands
    class Band(Enum):
        B2 = 'B2'
        B3 = 'B3'
        B4 = 'B4'
        B5 = 'B5'
        B6 = 'B6'
        B7 = 'B7'
        B8 = 'B8'
        B8A = 'B8A'
        B9 = 'B9'
        B10 = 'B10'
        B11 = 'B11'
        B12 = 'B12'
        
    # Aliases
    B2 = Band.B2
    B3 = Band.B3
    B4 = Band.B4
    B5 = Band.B5
    B6 = Band.B6
    B7 = Band.B7
    B8 = Band.B8
    B8A = Band.B8A
    B9 = Band.B9
    B10 = Band.B10
    B11 = Band.B11
    B12 = Band.B12


    # Enum class for Sentinel2 L2A masks
    class Mask(Enum):
        SAT = 'SAT'
        CLM = 'CLM'
        EDG = 'EDG'
        MG2 = 'MG2'

    # Aliases
    SAT = Mask.SAT
    CLM = Mask.CLM
    EDG = Mask.EDG
    MG2 = Mask.MG2
    
    
    # Enum class for mask resolutions
    class MaskRes(Enum):
        R1 = 'R1'
        R2 = 'R2'

    # Aliases for resolution
    R1 = MaskRes.R1
    R2 = MaskRes.R2

    # Band groups
    GROUP_10M = [B2, B3, B4, B8]
    GROUP_20M = [B5, B6, B7, B8A, B11, B12]
    GROUP_60M = [B9, B10]

    # Enum for BandType
    class BandType(Enum):
        FRE = 'FRE'
        SRE = 'SRE'

    # Aliases for band type
    FRE = BandType.FRE
    SRE = BandType.SRE
    
    # MTF
    MTF = {
        B2: 0.304,
        B3: 0.276,
        B4: 0.233,
        B5: 0.343,
        B6: 0.336,
        B7: 0.338,
        B8: 0.222,
        B8A: 0.325,
        B9: 0.39,
        B11: 0.21,
        B12: 0.19}

    # Resolution
    RES = {
        B2: 10,
        B3: 10,
        B4: 10,
        B5: 20,
        B6: 20,
        B7: 20,
        B8: 10,
        B8A: 20,
        B9: 60,
        B11: 60,
        B12: 60}

    def PSF(
        self,
        bands: List[Band],
        resolution: float = 0.5,
        half_kernel_width: int = None):
        """
        Generate PSF kernels from list of bands

        :param bands: A list of Sentinel2 Band Enum to generate PSF kernel for
        :param resolution: Resolution at which to sample the kernel
        :param half_kernel_width: The half size of the kernel
                                  (determined automatically if None)

        :return: The kernels as a Tensor of shape
                 [len(bands),2*half_kernel_width+1, 2*half_kernel_width+1]
        """
        return np.stack([(utils.generate_psf_kernel(resolution,
                                                    Sentinel2.RES[b],
                                                    Sentinel2.MTF[b],
                                                    half_kernel_width)) for b in bands])

        
    def build_xml_path(self) -> str:
        """
        Return path to root xml file
        """
        p = glob.glob(f"{self.product_dir}/*MTD_ALL.xml")
        # Raise
        if len(p) == 0:
            raise FileNotFoundError(f"Could not find root XML file in product directory {self.product_dir}")

    def build_band_path(
        self,
        band: Band,
        band_type: BandType = FRE) -> str:
        """
        Build path to a band for product
        :param band: The band to build path for as a Sentinel2.Band enum value
        :param prefix: The band prefix (FRE_ or SRE_)

        :return: The path to the band file
        """
        p = glob.glob(f"{self.product_dir}/*{band_type.value}_{band.value}.tif")
        # Raise
        if len(p) == 0:
            raise FileNotFoundError(f"Could not find band {band.value} of type {band_type.value} in product directory {self.product_dir}")
        return p[0]

    def build_mask_path(
        self,
        mask: Mask,
        resolution: MaskRes = R1) -> str:
        """
        Build path to a band for product
        :param band: The band to build path for as a Sentinel2.Band enum value
        :param prefix: The band prefix (FRE_ or SRE_)

        :return: The path to the band file
        """
        p = glob.glob(f"{self.product_dir}/MASKS/*{mask.value}_{resolution.value}.tif")
        # Raise
        if len(p) == 0:
            raise FileNotFoundError(f"Could not find mask {mask.value} of resolution {resolution.value} in product directory {self.product_dir}")
        return p[0]

    def read_bands(self,
                   bands:List[Band],
                   band_type:BandType = FRE,
                   scale:float=10000,
                   crs: str=None,
                   resolution:float = 10,
                   offsets:Tuple[float,float]=None,
                   region:Union[Tuple[int,int,int,int],rio.coords.BoundingBox]=None,
                   no_data_value:float=np.nan,
                   bounds:rio.coords.BoundingBox=None,
                   algorithm=rio.enums.Resampling.cubic,
                   dtype:np.dtype=np.float32) -> np.ndarray:
        """
        TODO
        """
        img_files = [self.build_band_path(b, band_type) for b in bands]

        np_arr =  utils.read_as_numpy(img_files,
                                    crs=crs,
                                    resolution=resolution,
                                    offsets=self.offsets,
                                    region=region,
                                    output_no_data_value = no_data_value,
                                    input_no_data_value = -10000,
                                    bounds = bounds,
                                    algorithm = algorithm,
                                    separate=True,
                                    dtype = dtype,
                                    scale = scale)

        # Skip first dimension
        return np_arr[0,...]
        
